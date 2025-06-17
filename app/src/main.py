import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.src.api.routes.v1 import v1_router
from app.src.core.auth.api_key_service import APIKeyService
from app.src.core.config import get_settings
from app.src.core.exceptions.exception_handlers import setup_exception_handlers
from app.src.core.middleware.auth import AuthenticationMiddleware
from app.src.core.middleware.ip_rate_limiting import IPRateLimitMiddleware
from app.src.core.middleware.rate_limiting import PerKeyRateLimitMiddleware
from app.src.core.middleware.request_tracking import setup_request_tracking_middleware
from app.src.core.security.secrets_manager import SecretsManager

# TODO:
# from core.logging import setup_logging

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

    secrets_manager = SecretsManager()
    api_key_service = APIKeyService(secrets_manager)

    # Middleware stack LIFO
    if settings.rate_limit_enabled:
        app.add_middleware(PerKeyRateLimitMiddleware)

    if settings.require_auth:
        app.add_middleware(AuthenticationMiddleware, api_key_service=api_key_service)

    app.add_middleware(IPRateLimitMiddleware)

    app.include_router(v1_router, prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.src.main:app",
        host="0.0.0.0",  # nosec B104 # noqa: S104
        port=8000,
        reload=True,
        # log_level="info",
        log_level="debug",
    )
