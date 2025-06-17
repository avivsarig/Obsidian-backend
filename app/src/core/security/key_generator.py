import secrets
import string
from typing import List

KEY_LENGTH = 32
KEY_ALPHABET = string.ascii_letters + string.digits


def generate_api_key(length: int = KEY_LENGTH) -> str:
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(length))


def generate_multiple_keys(count: int, length: int = KEY_LENGTH) -> List[str]:
    return [generate_api_key(length) for _ in range(count)]


def format_for_env_file(keys: List[str]) -> str:
    return f"API_KEYS={','.join(keys)}"
