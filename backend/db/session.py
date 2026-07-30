from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from logger import get_logger
from .database import DatabaseManager

logger = get_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator that yields an isolated AsyncSession for request lifecycles.
    
    Guarantees session scope isolation: each request receives its own AsyncSession instance.
    Ensures that database sessions are automatically closed and rolled back on unhandled exceptions.
    """
    db_manager = DatabaseManager.get_instance()
    session = db_manager.get_session()
    try:
        yield session
    except Exception:
        logger.exception("Database session encountered an unhandled exception")
        await session.rollback()
        raise
    finally:
        await session.close()
