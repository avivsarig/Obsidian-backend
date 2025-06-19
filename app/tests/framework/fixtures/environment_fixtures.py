from typing import Generator

import pytest

from app.tests.framework.infrastructure.environment import (
    EnvironmentFactory,
    VaultEnvironment,
)


@pytest.fixture
def vault_env() -> Generator[VaultEnvironment, None, None]:
    with EnvironmentFactory.create_isolated("unit") as env:
        yield env


@pytest.fixture
def integration_env() -> Generator[VaultEnvironment, None, None]:
    with EnvironmentFactory.create_isolated("integration") as env:
        yield env


@pytest.fixture
def populated_vault(vault_env: VaultEnvironment) -> VaultEnvironment:
    from app.tests.framework.builders.vault_builder import VaultBuilder

    return (
        VaultBuilder(vault_env)
        .with_task("Daily Review", done=False, do_date="2025-06-18")
        .with_task("Project Planning", done=False, is_project=True)
        .with_completed_task("Old Task", done=True, completed_at="2025-06-10T15:00:00")
        .build()
    )
