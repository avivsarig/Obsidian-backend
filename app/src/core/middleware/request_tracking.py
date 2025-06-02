import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get(None)


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)


def setup_request_tracking_middleware(
    app: FastAPI,
) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
