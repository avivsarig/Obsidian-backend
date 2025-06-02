import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.src.api.routes.v1 import v1_router
from app.src.core.config import get_settings
from app.src.core.exceptions.exception_handlers import setup_exception_handlers
from app.src.core.middleware.request_tracking import setup_request_tracking_middleware

# TODO:
# from core.logging import setup_logging
# from api.middleware.auth import APIKeyMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting API in {settings.environment if settings else 'development'} mode"
    )

    if settings.vault_path:
        logger.info(f"Using vault: {settings.vault_path}")
        if not settings.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {settings.vault_path}")
    else:
        logger.warning("No vault path configured")

    yield

    logger.info("Shutting down API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Task Automation API",
        description="API wrapper for Obsidian task automation",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=(
            "/docs" if settings and settings.environment == "development" else "/docs"
        ),
        redoc_url=(
            "/redoc" if settings and settings.environment == "development" else "/redoc"
        ),
    )

    setup_request_tracking_middleware(app)
    setup_exception_handlers(app)

    # TODO:
    # app.add_middleware(APIKeyMiddleware)

    app.include_router(v1_router, prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.src.main:app",
        host="0.0.0.0",  # nosec B104 # noqa: S104
        port=8000,
        reload=True,
        log_level="info",
    )
