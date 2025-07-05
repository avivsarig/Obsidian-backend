import secrets
import string

KEY_LENGTH = 32
KEY_ALPHABET = string.ascii_letters + string.digits


def generate_api_key(length: int = KEY_LENGTH) -> str:
    """Generate a cryptographically secure API key.

    Args:
        length: Length of the key to generate (default: 32)

    Returns:
        A random API key string using alphanumeric characters

    Raises:
        ValueError: If length is less than 1
    """
    if length < 1:
        raise ValueError("Key length must be at least 1")
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(length))


def generate_multiple_keys(count: int, length: int = KEY_LENGTH) -> list[str]:
    """Generate multiple API keys.

    Args:
        count: Number of keys to generate
        length: Length of each key (default: 32)

    Returns:
        List of generated API keys

    Raises:
        ValueError: If count is less than 0
    """
    if count < 0:
        raise ValueError("Count must be non-negative")
    return [generate_api_key(length) for _ in range(count)]


def format_for_env_file(keys: list[str]) -> str:
    """Format API keys for environment file.

    Args:
        keys: List of API keys to format

    Returns:
        Formatted string suitable for .env file
    """
    return f"API_KEYS={','.join(keys)}"
