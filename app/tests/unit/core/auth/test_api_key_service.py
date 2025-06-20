import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.src.core.auth.api_key_service import APIKeyService
from app.src.core.security.secrets_manager import SecretsManager

CACHE_TTL_SECONDS = 300
EXPIRED_TIME_OFFSET = 400
TIMING_TOLERANCE_MS = 0.001
TIMING_TEST_STRING_LENGTH = 100
SHORT_TTL_FOR_TESTING = 1

VALID_DEV_KEYS = ["dev-key-1", "dev-key-2"]
VALID_PROD_KEYS = ["prod-key-1", "prod-key-2"]
INTEGRATION_DEV_KEYS = ["dev-api-key-123", "dev-api-key-456"]
CONCURRENT_TEST_KEYS = ["valid-key-1", "valid-key-2"]
CACHED_KEY = "cached-key"
INVALID_KEY = "invalid-key"
TEST_KEY = "test-key"
OLD_CACHE_KEY = "old-key"

EQUAL_STRINGS = ("test-key", "test-key")
DIFFERENT_SAME_LENGTH = ("test-key", "diff-key")
DIFFERENT_LENGTHS = ("short", "longer-string")
EMPTY_STRINGS = ("", "")
EMPTY_VS_NON_EMPTY = ("", "non-empty")


class APIKeyServiceTestBase:
    """Base class with common test utilities following DRY principle."""

    @pytest.fixture
    def secrets_manager_mock(self):
        """Create a properly configured secrets manager mock."""
        mock = AsyncMock(spec=SecretsManager)
        mock.get_api_keys.return_value = VALID_PROD_KEYS
        return mock

    @pytest.fixture
    def service(self, secrets_manager_mock):
        """Create service instance with mocked dependencies."""
        return APIKeyService(secrets_manager=secrets_manager_mock)

    def configure_service_settings(self, service, environment, api_keys=None):
        settings_patch = patch.object(service, "settings")
        settings_mock = settings_patch.start()
        settings_mock.environment = environment
        if environment == "development":
            settings_mock.api_keys = api_keys or VALID_DEV_KEYS
        return settings_patch


class TestAPIKeyValidation(APIKeyServiceTestBase):
    """Test API key validation functionality with clear intent."""

    @pytest.mark.asyncio
    async def test_accepts_valid_development_key(self, service):
        settings_patch = self.configure_service_settings(service, "development")
        try:
            result = await service.validate_key(VALID_DEV_KEYS[0])
            assert result is True
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_rejects_invalid_development_key(self, service):
        settings_patch = self.configure_service_settings(service, "development")
        try:
            result = await service.validate_key(INVALID_KEY)
            assert result is False
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_accepts_valid_production_key(self, service, secrets_manager_mock):
        settings_patch = self.configure_service_settings(service, "production")
        try:
            secrets_manager_mock.get_api_keys.return_value = VALID_PROD_KEYS
            result = await service.validate_key(VALID_PROD_KEYS[0])
            assert result is True
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_rejects_invalid_production_key(self, service, secrets_manager_mock):
        settings_patch = self.configure_service_settings(service, "production")
        try:
            secrets_manager_mock.get_api_keys.return_value = VALID_PROD_KEYS
            result = await service.validate_key(INVALID_KEY)
            assert result is False
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_handles_concurrent_key_validation(self, service):
        settings_patch = self.configure_service_settings(
            service, "development", CONCURRENT_TEST_KEYS
        )
        try:
            validation_tasks = [
                service.validate_key("valid-key-1"),
                service.validate_key("valid-key-2"),
                service.validate_key(INVALID_KEY),
                service.validate_key("valid-key-1"),
            ]

            results = await asyncio.gather(*validation_tasks)
            assert results == [True, True, False, True]
        finally:
            settings_patch.stop()


class TestCachingMechanism(APIKeyServiceTestBase):
    """Test the caching system for performance optimization."""

    def reset_service_cache(self, service):
        service._cached_keys = []
        service._cache_timestamp = 0

    @pytest.mark.asyncio
    async def test_cache_prevents_redundant_calls_within_ttl(
        self, service, secrets_manager_mock
    ):
        settings_patch = self.configure_service_settings(service, "production")
        try:
            secrets_manager_mock.get_api_keys.return_value = [CACHED_KEY]

            await service.validate_key(CACHED_KEY)
            first_call_count = secrets_manager_mock.get_api_keys.call_count

            await service.validate_key(CACHED_KEY)
            second_call_count = secrets_manager_mock.get_api_keys.call_count

            assert first_call_count == second_call_count == 1
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_cache_refreshes_after_ttl_expiration(
        self, service, secrets_manager_mock
    ):
        self.reset_service_cache(service)
        settings_patch = self.configure_service_settings(service, "production")

        try:
            secrets_manager_mock.get_api_keys.return_value = [CACHED_KEY]

            await service._refresh_cache()
            first_timestamp = service._cache_timestamp
            assert secrets_manager_mock.get_api_keys.call_count == 1

            with patch("app.src.core.auth.api_key_service.time.time") as time_mock:
                time_mock.return_value = first_timestamp + EXPIRED_TIME_OFFSET
                await service._get_valid_keys()

            assert secrets_manager_mock.get_api_keys.call_count == 2
        finally:
            settings_patch.stop()


class TestCacheRefreshBehavior(APIKeyServiceTestBase):
    """Test cache refresh logic in different environments."""

    @pytest.mark.asyncio
    async def test_development_cache_uses_settings(self, service):
        settings_patch = self.configure_service_settings(service, "development")
        try:
            await service._refresh_cache()

            assert service._cached_keys == VALID_DEV_KEYS
            assert service._cache_timestamp > 0
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_production_cache_uses_secrets_manager(
        self, service, secrets_manager_mock
    ):
        settings_patch = self.configure_service_settings(service, "production")
        try:
            secrets_manager_mock.get_api_keys.return_value = VALID_PROD_KEYS

            await service._refresh_cache()

            assert service._cached_keys == VALID_PROD_KEYS
            assert service._cache_timestamp > 0
            secrets_manager_mock.get_api_keys.assert_called_once()
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_cache_preserved_on_secrets_manager_failure(
        self, service, secrets_manager_mock
    ):
        settings_patch = self.configure_service_settings(service, "production")
        try:
            secrets_manager_mock.get_api_keys.side_effect = Exception(
                "AWS connection failed"
            )

            service._cached_keys = [OLD_CACHE_KEY]
            original_timestamp = service._cache_timestamp

            await service._refresh_cache()

            assert service._cached_keys == [OLD_CACHE_KEY]
            assert service._cache_timestamp == original_timestamp
        finally:
            settings_patch.stop()

    @pytest.mark.asyncio
    async def test_initial_cache_population(self, service):
        settings_patch = self.configure_service_settings(
            service, "development", [TEST_KEY]
        )
        try:
            assert service._cache_timestamp == 0

            keys = await service._get_valid_keys()

            assert keys == [TEST_KEY]
            assert service._cache_timestamp > 0
        finally:
            settings_patch.stop()


class TestSecurityFeatures:
    """Test security-critical constant-time string comparison."""

    def test_identical_strings_return_true(self):
        result = APIKeyService._constant_time_compare(*EQUAL_STRINGS)
        assert result is True

    def test_different_strings_same_length_return_false(self):
        result = APIKeyService._constant_time_compare(*DIFFERENT_SAME_LENGTH)
        assert result is False

    def test_different_length_strings_return_false(self):
        result = APIKeyService._constant_time_compare(*DIFFERENT_LENGTHS)
        assert result is False

    def test_empty_strings_return_true(self):
        result = APIKeyService._constant_time_compare(*EMPTY_STRINGS)
        assert result is True

    def test_empty_vs_non_empty_returns_false(self):
        result = APIKeyService._constant_time_compare(*EMPTY_VS_NON_EMPTY)
        assert result is False

    def test_timing_attack_resistance(self):
        string_a = "a" * TIMING_TEST_STRING_LENGTH
        string_b = "b" * TIMING_TEST_STRING_LENGTH
        string_c = "a" * (TIMING_TEST_STRING_LENGTH - 1) + "b"

        start_time = time.perf_counter()
        APIKeyService._constant_time_compare(string_a, string_b)
        duration_all_different = time.perf_counter() - start_time

        start_time = time.perf_counter()
        APIKeyService._constant_time_compare(string_a, string_c)
        duration_last_different = time.perf_counter() - start_time

        timing_difference = abs(duration_all_different - duration_last_different)
        assert timing_difference < TIMING_TOLERANCE_MS


class TestServiceInitialization:
    """Test service instantiation and dependency injection."""

    @pytest.mark.asyncio
    async def test_creates_default_secrets_manager(self):
        with patch(
            "app.src.core.auth.api_key_service.SecretsManager"
        ) as secrets_manager_class:
            mock_instance = AsyncMock()
            secrets_manager_class.return_value = mock_instance

            service = APIKeyService()

            assert service.secrets_manager == mock_instance
            self._assert_initial_cache_state(service)

    @pytest.mark.asyncio
    async def test_uses_provided_secrets_manager(self):
        provided_secrets_manager = AsyncMock(spec=SecretsManager)

        service = APIKeyService(secrets_manager=provided_secrets_manager)

        assert service.secrets_manager == provided_secrets_manager

    def _assert_initial_cache_state(self, service):
        assert service._cached_keys == []
        assert service._cache_timestamp == 0
        assert service._cache_ttl_seconds == CACHE_TTL_SECONDS


class TestIntegrationScenarios:
    """Integration tests with minimal mocking for realistic behavior."""

    @pytest.mark.asyncio
    async def test_complete_development_workflow(self):
        with patch("app.src.core.auth.api_key_service.get_settings") as settings_mock:
            settings_mock.return_value.environment = "development"
            settings_mock.return_value.api_keys = INTEGRATION_DEV_KEYS

            service = APIKeyService()

            # Valid keys should be accepted
            assert await service.validate_key("dev-api-key-123")
            assert await service.validate_key("dev-api-key-456")

            # Invalid variations should be rejected
            assert not await service.validate_key(INVALID_KEY)
            assert not await service.validate_key("")
            assert not await service.validate_key("dev-api-key-12")  # partial match

    @pytest.mark.asyncio
    async def test_cache_expiration_with_real_timing(self):
        with patch("app.src.core.auth.api_key_service.get_settings") as settings_mock:
            settings_mock.return_value.environment = "development"
            settings_mock.return_value.api_keys = [TEST_KEY]

            service = APIKeyService()
            service._cache_ttl_seconds = SHORT_TTL_FOR_TESTING

            # Initial validation should populate cache
            assert await service.validate_key(TEST_KEY)
            first_cache_timestamp = service._cache_timestamp

            # Immediate revalidation should use cache
            assert await service.validate_key(TEST_KEY)
            assert service._cache_timestamp == first_cache_timestamp

            # After TTL expiry, cache should refresh
            await asyncio.sleep(SHORT_TTL_FOR_TESTING + 0.1)
            assert await service.validate_key(TEST_KEY)
            assert service._cache_timestamp > first_cache_timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
