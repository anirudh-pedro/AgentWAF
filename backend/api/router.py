from fastapi import APIRouter

from dashboard import dashboard_router
from .agent import router as agent_router
from .health import router as health_router

api_router = APIRouter()

# Register core health router
api_router.include_router(health_router)

# Register operational dashboard router
api_router.include_router(dashboard_router)

# Register agent execution & WAF proxy router
api_router.include_router(agent_router)
