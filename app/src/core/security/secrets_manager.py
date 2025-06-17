import json
import logging
from typing import List

import boto3
from botocore.exceptions import ClientError

from app.src.core.config import get_settings

logger = logging.getLogger(__name__)


class SecretsManager:
    def __init__(self):
        self.settings = get_settings()
        self.client = boto3.client("secretsmanager", region_name="eu-west-1")

    async def get_api_keys(self) -> List[str]:
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

            string_keys = [str(key) for key in api_keys if isinstance(key, str)]

            logger.debug(f"Retrieved {len(string_keys)} API keys from AWS")
            return string_keys

        except ClientError as e:
            logger.error(f"Failed to retrieve API keys from AWS: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in secret: {e}")
            return []
