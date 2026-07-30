from typing import Any
from fastapi import APIRouter, Response, status

from config import get_settings
from db import DatabaseManager

router = APIRouter(tags=["Health & Status"])


@router.get(
    "/",
    summary="Root Service Status",
    description="Returns root application metadata and running status.",
)
async def root_info() -> dict[str, Any]:
    settings = get_settings()
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@router.get(
    "/health",
    summary="General Health Check",
    description="Simple health check for server availability.",
)
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Checks downstream database connectivity to confirm application readiness.",
)
async def readiness_check(response: Response) -> dict[str, Any]:
    db_manager = DatabaseManager.get_instance()
    is_healthy = await db_manager.check_health()

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"database": "unhealthy", "ready": False}

    return {"database": "healthy", "ready": True}


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Kubernetes/AWS ECS liveness probe.",
)
async def liveness_check() -> dict[str, bool]:
    return {"alive": True}
