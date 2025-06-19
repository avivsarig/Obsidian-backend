import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from pydantic import BaseModel

from app.src.core.config import Settings


class TestProfile(BaseModel):
    vault_path: Path
    environment: str = "test"
    log_level: str = "DEBUG"
    require_auth: bool = False
    rate_limit_enabled: bool = False
    api_keys: list[str] = ["test-key-123"]


class TestConfigManager:
    def __init__(self) -> None:
        self._test_profiles: dict[str, TestProfile] = {}
        self._feature_toggles: dict[str, bool] = {}

    def get_test_profile(self, test_type: str) -> TestProfile:
        if test_type not in self._test_profiles:
            self._test_profiles[test_type] = self._create_default_profile(test_type)
        return self._test_profiles[test_type]

    @contextmanager
    def override_settings(self, **kwargs) -> Generator[Settings, None, None]:
        original_values = {}
        for key, value in kwargs.items():
            env_key = key.upper()
            original_values[env_key] = os.environ.get(env_key)
            if value is not None:
                os.environ[env_key] = str(value)
            elif env_key in os.environ:
                del os.environ[env_key]

        try:
            import app.src.core.config

            app.src.core.config._settings = None

            yield Settings()
        finally:
            for env_key, original_value in original_values.items():
                if original_value is not None:
                    os.environ[env_key] = original_value
                elif env_key in os.environ:
                    del os.environ[env_key]

            import app.src.core.config

            app.src.core.config._settings = None

    def enable_feature_toggle(self, feature: str) -> None:
        self._feature_toggles[feature] = True

    def disable_feature_toggle(self, feature: str) -> None:
        self._feature_toggles[feature] = False

    def is_feature_enabled(self, feature: str) -> bool:
        return self._feature_toggles.get(feature, False)

    def _create_default_profile(self, test_type: str) -> TestProfile:
        if test_type == "unit":
            return TestProfile(
                vault_path=Path(tempfile.mkdtemp(prefix="vault-unit-test-")),
                environment="test",
                require_auth=False,
                rate_limit_enabled=False,
            )
        elif test_type == "integration":
            return TestProfile(
                vault_path=Path(tempfile.mkdtemp(prefix="vault-integration-test-")),
                environment="test",
                require_auth=True,
                rate_limit_enabled=True,
            )
        elif test_type == "e2e":
            return TestProfile(
                vault_path=Path(tempfile.mkdtemp(prefix="vault-e2e-test-")),
                environment="test",
                require_auth=True,
                rate_limit_enabled=True,
            )
        else:
            raise ValueError(f"Unknown test type: {test_type}")


test_config = TestConfigManager()
