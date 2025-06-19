from typing import Any

from fastapi.testclient import TestClient

from app.src.main import create_app
from app.tests.framework.infrastructure.environment import VaultEnvironment


class APIClient:
    def __init__(
        self,
        environment: VaultEnvironment,
        api_key: str | None = None,
    ):
        self._app = create_app()
        self._client = TestClient(self._app)
        self._api_key = api_key
        self._base_headers = {}

        if api_key:
            self._base_headers["Authorization"] = f"Bearer {api_key}"

    def get(self, path: str, **kwargs) -> Any:
        return self._client.get(
            path, headers={**self._base_headers, **kwargs.pop("headers", {})}, **kwargs
        )

    def post(self, path: str, **kwargs) -> Any:
        return self._client.post(
            path, headers={**self._base_headers, **kwargs.pop("headers", {})}, **kwargs
        )

    def put(self, path: str, **kwargs) -> Any:
        return self._client.put(
            path, headers={**self._base_headers, **kwargs.pop("headers", {})}, **kwargs
        )

    def delete(self, path: str, **kwargs) -> Any:
        return self._client.delete(
            path, headers={**self._base_headers, **kwargs.pop("headers", {})}, **kwargs
        )
