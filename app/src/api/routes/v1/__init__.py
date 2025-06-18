from fastapi import APIRouter

from .health import router as health_router
from .tasks import router as tasks_router
from .vault import router as vault_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(
    tasks_router,
    prefix="/tasks",
    tags=["tasks"],
)
v1_router.include_router(
    vault_router,
    prefix="/vault",
    tags=["vault"],
)
