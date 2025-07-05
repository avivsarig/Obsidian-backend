import json
import logging

import boto3
from botocore.exceptions import ClientError

from app.src.core.config import get_settings

logger = logging.getLogger(__name__)


class SecretsManager:
    """AWS Secrets Manager client for retrieving API keys."""

    def __init__(self, region_name: str = "eu-west-1"):
        """Initialize SecretsManager.

        Args:
            region_name: AWS region for Secrets Manager client
        """
        self.settings = get_settings()
        self.client = boto3.client("secretsmanager", region_name=region_name)

    async def get_api_keys(self) -> list[str]:
        """Retrieve API keys from AWS Secrets Manager.

        Returns:
            List of API key strings, empty list if retrieval fails
        """
        if not self.settings.aws_secrets_manager_key_name:
            logger.warning("No AWS secrets manager key name configured")
            return []

        try:
            response = self.client.get_secret_value(
                SecretId=self.settings.aws_secrets_manager_key_name
            )

            secret_data = json.loads(response["SecretString"])
            api_keys = secret_data.get("api_keys", [])

            if not isinstance(api_keys, list):
                logger.error("API keys in secret is not a list")
                return []

            string_keys = [str(key) for key in api_keys if key and isinstance(key, str)]

            logger.debug(f"Retrieved {len(string_keys)} API keys from AWS")
            return string_keys

        except ClientError as e:
            logger.error(f"Failed to retrieve API keys from AWS: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in secret: {e}")
            return []
