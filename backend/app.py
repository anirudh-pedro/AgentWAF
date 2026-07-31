import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api import api_router, register_exception_handlers
from config import get_settings
from dashboard.websocket import ws_manager
from db import DatabaseManager
from logger import get_logger
from middleware import RequestIDMiddleware, RequestLoggingMiddleware
from middleware.rate_limit import RateLimiterMiddleware
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
            "waf_mode": settings.WAF_MODE,
        },
    )

    # Register built-in agent tools
    register_builtin_tools()

    # Non-blocking background database initialization & table creation
    # Allows Uvicorn to open port 8000 immediately so ALB health checks pass without delay
    asyncio.create_task(_init_db_background())

    logger.info("Application startup completed successfully - port open for health checks")

    yield

    # Clean up database resources on shutdown
    logger.info("Executing application shutdown sequence")
    db_manager = DatabaseManager.get_instance()
    await db_manager.close()
    logger.info("Application shutdown completed successfully")


async def _init_db_background() -> None:
    """Initialize database tables and verify health asynchronously in background."""
    try:
        db_manager = DatabaseManager.get_instance()
        await db_manager.create_tables()
        is_db_ready = await db_manager.check_health()
        if is_db_ready:
            logger.info("Database connectivity check succeeded during background startup")
        else:
            logger.warning("Database connectivity check failed during background startup")
    except Exception as exc:
        logger.error("Background database initialization encountered an exception", extra={"error": str(exc)})


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

    # Register Request Lifecycle Middleware (Order: Rate Limiter -> Logging -> Request ID)
    app.add_middleware(RateLimiterMiddleware, max_requests=30, window_seconds=60)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Register Global Exception Handlers
    register_exception_handlers(app)

    # Register Primary API Router (both at root level and with /api/v1 prefix for endpoint flexibility)
    app.include_router(api_router)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Register WebSocket Real-time Endpoint /ws/dashboard
    @app.websocket("/ws/dashboard")
    async def websocket_dashboard_endpoint(websocket: WebSocket) -> None:
        """Real-time WebSocket endpoint for live audit log updates and metric broadcasts."""
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    logger.info("API routers and WebSocket endpoint registered successfully")

    return app


# Export application instance for Uvicorn ASGI server execution
app: FastAPI = create_app()
