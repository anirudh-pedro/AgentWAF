import asyncio
from threading import Lock
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings
from logger import get_logger

logger = get_logger(__name__)

_lock = Lock()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models in Agent WAF."""
    pass


class DatabaseManager:
    """Singleton manager responsible for SQLAlchemy async engine lifecycle and session management."""

    _instance: "DatabaseManager | None" = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._initialize()

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Thread-safe singleton accessor for DatabaseManager."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the async engine and session factory based on configuration settings."""
        logger.info(
            "Initializing database engine",
            extra={"database_url_schema": self.settings.DATABASE_URL.split("://")[0]}
        )

        engine_kwargs: dict[str, Any] = {
            "echo": self.settings.DB_ECHO,
            "pool_pre_ping": True,
        }

        # PostgreSQL/Neon pool tuning (SQLite ignores pool_size/max_overflow)
        if not self.settings.DATABASE_URL.startswith("sqlite"):
            engine_kwargs.update({
                "pool_size": self.settings.DB_POOL_SIZE,
                "max_overflow": self.settings.DB_MAX_OVERFLOW,
                "pool_timeout": self.settings.DB_POOL_TIMEOUT,
                "pool_recycle": 1800,
            })

        try:
            self._engine = create_async_engine(
                self.settings.DATABASE_URL,
                **engine_kwargs
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            logger.info("Database engine and session factory created successfully")
        except Exception:
            logger.exception("Failed to initialize database engine")
            raise

    @property
    def engine(self) -> AsyncEngine:
        """Return the initialized AsyncEngine instance."""
        if self._engine is None:
            raise RuntimeError("DatabaseManager is not initialized")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Return the configured AsyncSession factory."""
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager session factory is not initialized")
        return self._session_factory

    def get_session(self) -> AsyncSession:
        """Provide a new, isolated AsyncSession instance from the session factory."""
        return self.session_factory()

    async def create_tables(self) -> None:
        """Create all registered database tables in PostgreSQL if they do not exist."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema initialized successfully in PostgreSQL (Neon)")
        except Exception as exc:
            logger.exception("Failed to create database tables", extra={"error": str(exc)})

    async def check_health(self) -> bool:
        """Perform lightweight database connectivity check using SELECT 1 with strict 3s timeout."""
        try:
            async with self.session_factory() as session:
                val = await asyncio.wait_for(session.scalar(text("SELECT 1")), timeout=3.0)
                if val == 1:
                    logger.debug("Database health check passed")
                    return True
                logger.warning("Database health check returned unexpected scalar value", extra={"result": val})
                return False
        except Exception as exc:
            logger.error("Database health check failed or timed out", extra={"error": str(exc)})
            return False

    async def close(self) -> None:
        """Dispose the SQLAlchemy async engine and release connection pool resources."""
        if self._engine is not None:
            logger.info("Disposing database engine connection pool")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed successfully")
