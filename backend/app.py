from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router, register_exception_handlers
from config import get_settings
from db import DatabaseManager
from logger import get_logger
from middleware import RequestIDMiddleware, RequestLoggingMiddleware
from tools import register_builtin_tools

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown lifecycle management."""
    settings = get_settings()
    logger.info(
        "Starting application lifespan",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )

    # Initialize DatabaseManager and test database connection
    db_manager = DatabaseManager.get_instance()
    is_db_ready = await db_manager.check_health()
    if is_db_ready:
        logger.info("Database connectivity check succeeded during startup")
    else:
        logger.warning("Database connectivity check failed during startup")

    # Register built-in agent tools
    register_builtin_tools()

    logger.info("Application startup completed successfully")

    yield

    # Clean up database resources on shutdown
    logger.info("Executing application shutdown sequence")
    await db_manager.close()
    logger.info("Application shutdown completed successfully")


def create_app() -> FastAPI:
    """Application factory for constructing and configuring the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Request Lifecycle Middleware (Order: Logging then Request ID)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Register Global Exception Handlers
    register_exception_handlers(app)

    # Register Primary API Router
    app.include_router(api_router)
    logger.info("API routers registered successfully")

    return app


# Export application instance for Uvicorn ASGI server execution
app: FastAPI = create_app()
