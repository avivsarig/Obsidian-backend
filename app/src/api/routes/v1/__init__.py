from fastapi import APIRouter

from .health import router as health_router

# TODO:
# from .tasks import router as tasks_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router, tags=["health"])
# TODO:
# v1_router.include_router(tasks_router, tags=["tasks"])
