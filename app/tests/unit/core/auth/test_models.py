from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.src.core.auth.models import AuthContext, KeyMetadata


class TestKeyMetadata:
    """Test KeyMetadata Pydantic model."""

    def test_creates_with_required_fields(self):
        """Test creating KeyMetadata with required fields only."""
        metadata = KeyMetadata(
            key_id="test-key-123",
            created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert metadata.key_id == "test-key-123"
        assert metadata.created_at == datetime(
            2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )
        assert metadata.last_used is None
        assert metadata.requests_today == 0

    def test_creates_with_all_fields(self):
        """Test creating KeyMetadata with all fields provided."""
        created_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_used_time = datetime(2025, 1, 2, 15, 30, 0, tzinfo=timezone.utc)

        metadata = KeyMetadata(
            key_id="comprehensive-key",
            created_at=created_time,
            last_used=last_used_time,
            requests_today=42,
        )

        assert metadata.key_id == "comprehensive-key"
        assert metadata.created_at == created_time
        assert metadata.last_used == last_used_time
        assert metadata.requests_today == 42

    def test_validates_key_id_required(self):
        """Test that key_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(created_at=datetime.now(timezone.utc))

        error = exc_info.value.errors()[0]
        assert error["type"] == "missing"
        assert "key_id" in error["loc"]

    def test_validates_created_at_required(self):
        """Test that created_at is required."""
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(key_id="test-key")

        error = exc_info.value.errors()[0]
        assert error["type"] == "missing"
        assert "created_at" in error["loc"]

    def test_validates_key_id_type(self):
        """Test that key_id must be a string."""
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(
                key_id=123,  # Invalid type
                created_at=datetime.now(timezone.utc),
            )

        error = exc_info.value.errors()[0]
        assert error["type"] == "string_type"
        assert "key_id" in error["loc"]

    def test_validates_created_at_type(self):
        """Test that created_at accepts datetime and valid strings."""
        # Valid datetime string gets converted
        metadata = KeyMetadata(
            key_id="test-key",
            created_at="2025-01-01T12:00:00Z",
        )
        assert isinstance(metadata.created_at, datetime)

        # Invalid datetime string raises error
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(
                key_id="test-key",
                created_at="invalid-date",
            )

        error = exc_info.value.errors()[0]
        assert "created_at" in error["loc"]

    def test_validates_last_used_type(self):
        """Test that last_used must be datetime or None."""
        # Valid None
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
            last_used=None,
        )
        assert metadata.last_used is None

        # Valid datetime
        last_used_time = datetime.now(timezone.utc)
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
            last_used=last_used_time,
        )
        assert metadata.last_used == last_used_time

        # Valid datetime string gets converted
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
            last_used="2025-01-01T12:00:00Z",
        )
        assert isinstance(metadata.last_used, datetime)

        # Invalid datetime string
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(
                key_id="test-key",
                created_at=datetime.now(timezone.utc),
                last_used="invalid-date",
            )

        error = exc_info.value.errors()[0]
        assert "last_used" in error["loc"]

    def test_validates_requests_today_type(self):
        """Test that requests_today accepts integers and numeric strings."""
        # Valid string number gets converted
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
            requests_today="10",
        )
        assert metadata.requests_today == 10
        assert isinstance(metadata.requests_today, int)

        # Invalid non-numeric string
        with pytest.raises(ValidationError) as exc_info:
            KeyMetadata(
                key_id="test-key",
                created_at=datetime.now(timezone.utc),
                requests_today="not-a-number",
            )

        error = exc_info.value.errors()[0]
        assert "requests_today" in error["loc"]

    def test_requests_today_defaults_to_zero(self):
        """Test that requests_today defaults to 0."""
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.requests_today == 0

    def test_allows_negative_requests_today(self):
        """Test that negative requests_today values are allowed."""
        metadata = KeyMetadata(
            key_id="test-key",
            created_at=datetime.now(timezone.utc),
            requests_today=-5,
        )

        assert metadata.requests_today == -5

    def test_serialization_to_dict(self):
        """Test serializing KeyMetadata to dictionary."""
        created_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_used_time = datetime(2025, 1, 2, 15, 30, 0, tzinfo=timezone.utc)

        metadata = KeyMetadata(
            key_id="serialize-test",
            created_at=created_time,
            last_used=last_used_time,
            requests_today=100,
        )

        data = metadata.model_dump()

        assert data["key_id"] == "serialize-test"
        assert data["created_at"] == created_time
        assert data["last_used"] == last_used_time
        assert data["requests_today"] == 100

    def test_json_serialization(self):
        """Test JSON serialization of KeyMetadata."""
        metadata = KeyMetadata(
            key_id="json-test",
            created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            last_used=None,
            requests_today=50,
        )

        json_str = metadata.model_dump_json()
        assert "json-test" in json_str
        assert "2025-01-01T12:00:00" in json_str
        assert "null" in json_str  # last_used is None
        assert "50" in json_str


class TestAuthContext:
    """Test AuthContext Pydantic model."""

    def test_creates_with_api_key_only(self):
        """Test creating AuthContext with only required api_key."""
        context = AuthContext(api_key="test-api-key")

        assert context.api_key == "test-api-key"
        assert context.metadata is None

    def test_creates_with_api_key_and_metadata(self):
        """Test creating AuthContext with api_key and metadata."""
        metadata = KeyMetadata(
            key_id="context-key",
            created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            requests_today=25,
        )

        context = AuthContext(api_key="context-test-key", metadata=metadata)

        assert context.api_key == "context-test-key"
        assert context.metadata == metadata
        assert context.metadata.key_id == "context-key"
        assert context.metadata.requests_today == 25

    def test_validates_api_key_required(self):
        """Test that api_key is required."""
        with pytest.raises(ValidationError) as exc_info:
            AuthContext()

        error = exc_info.value.errors()[0]
        assert error["type"] == "missing"
        assert "api_key" in error["loc"]

    def test_validates_api_key_type(self):
        """Test that api_key must be a string."""
        with pytest.raises(ValidationError) as exc_info:
            AuthContext(api_key=12345)  # Invalid type

        error = exc_info.value.errors()[0]
        assert error["type"] == "string_type"
        assert "api_key" in error["loc"]

    def test_validates_metadata_type(self):
        """Test that metadata must be KeyMetadata or None."""
        # Valid None
        context = AuthContext(api_key="test-key", metadata=None)
        assert context.metadata is None

        # Valid KeyMetadata
        metadata = KeyMetadata(
            key_id="valid-metadata",
            created_at=datetime.now(timezone.utc),
        )
        context = AuthContext(api_key="test-key", metadata=metadata)
        assert context.metadata == metadata

        # Invalid type
        with pytest.raises(ValidationError) as exc_info:
            AuthContext(api_key="test-key", metadata="invalid-metadata")

        error = exc_info.value.errors()[0]
        assert "metadata" in error["loc"]

    def test_metadata_defaults_to_none(self):
        """Test that metadata defaults to None."""
        context = AuthContext(api_key="default-test")

        assert context.metadata is None

    def test_serialization_to_dict(self):
        """Test serializing AuthContext to dictionary."""
        metadata = KeyMetadata(
            key_id="serialize-context",
            created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            requests_today=75,
        )

        context = AuthContext(api_key="serialize-api-key", metadata=metadata)

        data = context.model_dump()

        assert data["api_key"] == "serialize-api-key"
        assert isinstance(data["metadata"], dict)
        assert data["metadata"]["key_id"] == "serialize-context"
        assert data["metadata"]["requests_today"] == 75

    def test_serialization_with_none_metadata(self):
        """Test serializing AuthContext with None metadata."""
        context = AuthContext(api_key="none-metadata-key")

        data = context.model_dump()

        assert data["api_key"] == "none-metadata-key"
        assert data["metadata"] is None

    def test_json_serialization(self):
        """Test JSON serialization of AuthContext."""
        context = AuthContext(api_key="json-context-key")

        json_str = context.model_dump_json()
        assert "json-context-key" in json_str
        assert "null" in json_str  # metadata is None


class TestModelIntegration:
    """Test integration between KeyMetadata and AuthContext."""

    def test_nested_validation_success(self):
        """Test successful validation of nested KeyMetadata in AuthContext."""
        metadata_data = {
            "key_id": "integration-key",
            "created_at": datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "last_used": datetime(2025, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            "requests_today": 150,
        }

        context = AuthContext(
            api_key="integration-test",
            metadata=KeyMetadata(**metadata_data),
        )

        assert context.api_key == "integration-test"
        assert context.metadata.key_id == "integration-key"
        assert context.metadata.requests_today == 150

    def test_nested_validation_failure(self):
        """Test validation failure in nested KeyMetadata."""
        with pytest.raises(ValidationError) as exc_info:
            AuthContext(
                api_key="test-key",
                metadata=KeyMetadata(
                    key_id=None,  # Invalid: required field
                    created_at=datetime.now(timezone.utc),
                ),
            )

        # Should have validation error for key_id
        errors = exc_info.value.errors()
        assert any("key_id" in str(error["loc"]) for error in errors)

    def test_from_dict_construction(self):
        """Test creating models from dictionary data."""
        metadata_dict = {
            "key_id": "dict-key",
            "created_at": "2025-01-01T12:00:00+00:00",
            "last_used": None,
            "requests_today": 0,
        }

        context_dict = {
            "api_key": "dict-api-key",
            "metadata": metadata_dict,
        }

        # This tests Pydantic's ability to parse nested dictionaries
        context = AuthContext.model_validate(context_dict)

        assert context.api_key == "dict-api-key"
        assert context.metadata.key_id == "dict-key"
        assert context.metadata.last_used is None

    def test_partial_metadata_construction(self):
        """Test creating AuthContext with partial metadata."""
        context = AuthContext(
            api_key="partial-test",
            metadata=KeyMetadata(
                key_id="partial-key",
                created_at=datetime.now(timezone.utc),
                # last_used and requests_today use defaults
            ),
        )

        assert context.metadata.last_used is None
        assert context.metadata.requests_today == 0


class TestFieldDescriptions:
    """Test that field descriptions are properly set."""

    def test_keymetadata_field_descriptions(self):
        """Test KeyMetadata field descriptions."""
        fields = KeyMetadata.model_fields

        assert fields["key_id"].description == "Unique identifier for the API key"
        assert fields["created_at"].description == "When the key was created"
        assert fields["last_used"].description == "Last usage timestamp"
        assert fields["requests_today"].description == "Number of requests made today"

    def test_authcontext_field_descriptions(self):
        """Test AuthContext field descriptions."""
        fields = AuthContext.model_fields

        assert fields["api_key"].description == "The validated API key"
        assert fields["metadata"].description == "Key metadata if available"

    def test_field_requirements(self):
        """Test field requirement settings."""
        key_fields = KeyMetadata.model_fields
        auth_fields = AuthContext.model_fields

        # Required fields
        assert key_fields["key_id"].is_required()
        assert key_fields["created_at"].is_required()
        assert auth_fields["api_key"].is_required()

        # Optional fields
        assert not key_fields["last_used"].is_required()
        assert not key_fields["requests_today"].is_required()
        assert not auth_fields["metadata"].is_required()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
