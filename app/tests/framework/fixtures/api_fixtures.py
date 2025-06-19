import pytest

from app.tests.framework.infrastructure.api_client import APIClient
from app.tests.framework.infrastructure.environment import VaultEnvironment


@pytest.fixture
def api_client(vault_env: VaultEnvironment) -> APIClient:
    return APIClient(vault_env)


@pytest.fixture
def authenticated_client(vault_env: VaultEnvironment) -> APIClient:
    return APIClient(vault_env, api_key="test-key-123")
