import logging
import time
from typing import List

from app.src.core.config import get_settings
from app.src.core.security.secrets_manager import SecretsManager

logger = logging.getLogger(__name__)


class APIKeyService:
    def __init__(
        self,
        secrets_manager: SecretsManager | None = None,
    ):
        self.secrets_manager = secrets_manager or SecretsManager()
        self.settings = get_settings()
        self._cached_keys: List[str] = []
        self._cache_timestamp: float = 0
        self._cache_ttl_seconds: int = 300

    async def validate_key(self, api_key: str) -> bool:
        valid_keys = await self._get_valid_keys()

        # Constant-time comparison to prevent timing attacks
        return any(
            self._constant_time_compare(api_key, valid_key) for valid_key in valid_keys
        )

    async def _get_valid_keys(self) -> List[str]:
        current_time = time.time()

        if (current_time - self._cache_timestamp) > self._cache_ttl_seconds:
            await self._refresh_cache()

        return self._cached_keys

    async def _refresh_cache(self) -> None:
        try:
            if self.settings.environment == "development":
                self._cached_keys = self.settings.api_keys
            else:
                self._cached_keys = await self.secrets_manager.get_api_keys()

            self._cache_timestamp = time.time()
            logger.debug(f"Refreshed API keys cache: {len(self._cached_keys)} keys")

        except Exception as e:
            logger.error(f"Failed to refresh API keys cache: {e}")
            # Keep using stale cache in case of failure

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)

        return result == 0
