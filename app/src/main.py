from contextlib import asynccontextmanager

import uvicorn

# Import your API routes
from api.routes.v1 import v1_router

# TODO: Import core components
# from core.config import get_settings
# from core.exceptions import TaskAutomationException
# from core.logging import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO: Import middleware components
# from api.middleware.auth import APIKeyMiddleware
# from api.middleware.logging import LoggingMiddleware


# TODO:
def get_settings():
    return {}


settings = get_settings()

# TODO:
# setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        "Starting Task Automation API in "
        f"{settings.environment if settings else 'development'} mode"
    )

    if settings and not settings.vault_path.exists():
        raise ValueError(f"Vault path does not exist: {settings.vault_path}")

    yield

    logger.info("Shutting down Task Automation API")


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

    # TODO: Consider actual need
    # Allows browser-based clients to call API from different domains
    # In Phase 1 might not be needed, but sets foundation for future web UI
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # TODO:
    # API keys are simpler than OAuth for automation tasks
    # app.add_middleware(APIKeyMiddleware)

    # TODO:
    # app.add_middleware(LoggingMiddleware)

    # TODO:
    # Converts internal errors to consistent API responses
    # @app.exception_handler(TaskAutomationException)
    # async def task_automation_exception_handler(
    #     request: Request, exc: TaskAutomationException
    # ):
    #     return JSONResponse(
    #         status_code=exc.status_code,
    #         content={"error": exc.message, "detail": exc.detail},
    #     )

    app.include_router(v1_router, prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # nosec B104 # noqa: S104 - Required for container networking
        port=8000,
        reload=True,
        log_level="info",
    )
