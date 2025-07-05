import re
import string
from collections import Counter

import pytest

from app.src.core.security.key_generator import (
    KEY_ALPHABET,
    KEY_LENGTH,
    format_for_env_file,
    generate_api_key,
    generate_multiple_keys,
)


class TestGenerateApiKey:
    """Test the generate_api_key function."""

    def test_default_length(self):
        """Test API key generation with default length."""
        key = generate_api_key()
        assert len(key) == KEY_LENGTH
        assert len(key) == 32

    def test_custom_length(self):
        """Test API key generation with custom lengths."""
        for length in [1, 16, 64, 128]:
            key = generate_api_key(length)
            assert len(key) == length

    def test_character_set(self):
        """Test that generated keys only contain valid characters."""
        key = generate_api_key(100)  # Use longer key for better validation
        for char in key:
            assert char in KEY_ALPHABET
            assert char in string.ascii_letters + string.digits

    def test_no_special_characters(self):
        """Test that keys don't contain special characters."""
        key = generate_api_key(100)
        # Should not contain any special characters
        assert not re.search(r"[^a-zA-Z0-9]", key)

    def test_randomness(self):
        """Test that generated keys are random and unique."""
        keys = [generate_api_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

        # Keys should not be identical
        assert len(set(keys)) == len(keys)

    def test_character_distribution(self):
        """Test that character distribution appears random."""
        # Generate a long key to analyze distribution
        key = generate_api_key(1000)
        char_counts = Counter(key)

        # Should use a variety of characters (not just a few)
        assert len(char_counts) > 10

        # No single character should dominate (rough check)
        max_frequency = max(char_counts.values())
        assert max_frequency < len(key) * 0.1  # No char more than 10%

    def test_minimum_length(self):
        """Test minimum valid length."""
        key = generate_api_key(1)
        assert len(key) == 1
        assert key in KEY_ALPHABET

    def test_zero_length_raises_error(self):
        """Test that zero length raises ValueError."""
        with pytest.raises(ValueError, match="Key length must be at least 1"):
            generate_api_key(0)

    def test_negative_length_raises_error(self):
        """Test that negative length raises ValueError."""
        with pytest.raises(ValueError, match="Key length must be at least 1"):
            generate_api_key(-1)

        with pytest.raises(ValueError, match="Key length must be at least 1"):
            generate_api_key(-10)


class TestGenerateMultipleKeys:
    """Test the generate_multiple_keys function."""

    def test_zero_keys(self):
        """Test generating zero keys."""
        keys = generate_multiple_keys(0)
        assert keys == []

    def test_single_key(self):
        """Test generating single key."""
        keys = generate_multiple_keys(1)
        assert len(keys) == 1
        assert len(keys[0]) == KEY_LENGTH

    def test_multiple_keys(self):
        """Test generating multiple keys."""
        for count in [2, 5, 10]:
            keys = generate_multiple_keys(count)
            assert len(keys) == count
            for key in keys:
                assert len(key) == KEY_LENGTH

    def test_custom_length_multiple_keys(self):
        """Test generating multiple keys with custom length."""
        keys = generate_multiple_keys(5, length=16)
        assert len(keys) == 5
        for key in keys:
            assert len(key) == 16

    def test_keys_are_unique(self):
        """Test that all generated keys are unique."""
        keys = generate_multiple_keys(50)
        assert len(set(keys)) == 50  # All keys should be unique

    def test_negative_count_raises_error(self):
        """Test that negative count raises ValueError."""
        with pytest.raises(ValueError, match="Count must be non-negative"):
            generate_multiple_keys(-1)

        with pytest.raises(ValueError, match="Count must be non-negative"):
            generate_multiple_keys(-5)

    def test_large_count(self):
        """Test generating large number of keys."""
        keys = generate_multiple_keys(100)
        assert len(keys) == 100
        assert len(set(keys)) == 100  # All should be unique


class TestFormatForEnvFile:
    """Test the format_for_env_file function."""

    def test_single_key(self):
        """Test formatting single key."""
        keys = ["abc123"]
        result = format_for_env_file(keys)
        assert result == "API_KEYS=abc123"

    def test_multiple_keys(self):
        """Test formatting multiple keys."""
        keys = ["key1", "key2", "key3"]
        result = format_for_env_file(keys)
        assert result == "API_KEYS=key1,key2,key3"

    def test_empty_list(self):
        """Test formatting empty key list."""
        keys = []
        result = format_for_env_file(keys)
        assert result == "API_KEYS="

    def test_keys_with_alphanumeric_chars(self):
        """Test formatting keys containing various alphanumeric characters."""
        keys = ["abc123", "XYZ789", "MixEd456"]
        result = format_for_env_file(keys)
        assert result == "API_KEYS=abc123,XYZ789,MixEd456"

    def test_large_number_of_keys(self):
        """Test formatting large number of keys."""
        keys = [f"key{i}" for i in range(10)]
        result = format_for_env_file(keys)
        expected = "API_KEYS=" + ",".join(keys)
        assert result == expected


class TestKeyGeneratorIntegration:
    """Integration tests combining multiple functions."""

    def test_generate_and_format_workflow(self):
        """Test complete workflow: generate keys and format them."""
        keys = generate_multiple_keys(3, length=16)
        formatted = format_for_env_file(keys)

        assert formatted.startswith("API_KEYS=")
        key_part = formatted[9:]  # Remove "API_KEYS=" prefix
        parsed_keys = key_part.split(",")

        assert len(parsed_keys) == 3
        for key in parsed_keys:
            assert len(key) == 16

    def test_constants_consistency(self):
        """Test that constants are used consistently."""
        key = generate_api_key()
        assert len(key) == KEY_LENGTH

        # Verify KEY_ALPHABET matches expected character set
        expected_alphabet = string.ascii_letters + string.digits
        assert KEY_ALPHABET == expected_alphabet


class TestSecurityProperties:
    """Test security properties of key generation."""

    def test_entropy_quality(self):
        """Test that keys have good entropy."""
        # Generate multiple keys and ensure they're sufficiently different
        keys = [generate_api_key(32) for _ in range(10)]

        # Calculate similarity between keys (should be low)
        for i, key1 in enumerate(keys):
            for key2 in keys[i + 1 :]:
                # Count matching characters at same positions
                matches = sum(c1 == c2 for c1, c2 in zip(key1, key2))
                similarity = matches / len(key1)
                # Should have low positional similarity (< 20%)
                assert similarity < 0.2

    def test_no_predictable_patterns(self):
        """Test that keys don't follow predictable patterns."""
        keys = [generate_api_key(20) for _ in range(5)]

        for key in keys:
            # Should not be all the same character
            assert len(set(key)) > 1

            # Should not be sequential
            assert key != "".join(sorted(key))

            # Should not be reverse sequential
            assert key != "".join(sorted(key, reverse=True))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
