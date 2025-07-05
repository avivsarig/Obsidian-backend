import time
from unittest.mock import Mock, patch

import pytest

from app.src.core.util.retrier import Retrier


class TestRetrierInitialization:
    """Test Retrier initialization and parameter validation."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        retrier = Retrier()
        assert retrier.max_attempts == 5
        assert retrier.base_delay == 0.1
        assert retrier.max_delay == 5.0

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        retrier = Retrier(max_attempts=3, base_delay=0.5, max_delay=10.0)
        assert retrier.max_attempts == 3
        assert retrier.base_delay == 0.5
        assert retrier.max_delay == 10.0

    def test_invalid_max_attempts_zero(self):
        """Test that zero max_attempts raises ValueError."""
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            Retrier(max_attempts=0)

    def test_invalid_max_attempts_negative(self):
        """Test that negative max_attempts raises ValueError."""
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            Retrier(max_attempts=-1)

    def test_invalid_base_delay_negative(self):
        """Test that negative base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be non-negative"):
            Retrier(base_delay=-0.1)

    def test_invalid_max_delay_less_than_base(self):
        """Test that max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            Retrier(base_delay=1.0, max_delay=0.5)

    def test_valid_edge_cases(self):
        """Test valid edge cases for parameters."""
        # Zero base delay
        retrier1 = Retrier(base_delay=0.0, max_delay=0.0)
        assert retrier1.base_delay == 0.0
        assert retrier1.max_delay == 0.0

        # Equal base and max delay
        retrier2 = Retrier(base_delay=1.0, max_delay=1.0)
        assert retrier2.base_delay == 1.0
        assert retrier2.max_delay == 1.0

        # Single attempt
        retrier3 = Retrier(max_attempts=1)
        assert retrier3.max_attempts == 1


class TestRetrierSuccessScenarios:
    """Test successful operation scenarios."""

    def test_success_on_first_attempt(self):
        """Test operation succeeds on first attempt."""
        retrier = Retrier()
        operation = Mock(return_value="success")

        result = retrier.execute(operation)

        assert result == "success"
        operation.assert_called_once()

    def test_success_after_failures(self):
        """Test operation succeeds after some failures."""
        retrier = Retrier(max_attempts=3)
        operation = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            result = retrier.execute(operation)

            assert result == "success"
            assert operation.call_count == 3
            assert mock_sleep.call_count == 2  # 2 retries before success

    def test_returns_correct_value_type(self):
        """Test that the correct return type is preserved."""
        retrier = Retrier()

        # Test different return types
        str_op = Mock(return_value="string")
        int_op = Mock(return_value=42)
        dict_op = Mock(return_value={"key": "value"})

        assert retrier.execute(str_op) == "string"
        assert retrier.execute(int_op) == 42
        assert retrier.execute(dict_op) == {"key": "value"}


class TestRetrierFailureScenarios:
    """Test failure scenarios and exception handling."""

    def test_all_attempts_fail(self):
        """Test that original exception is raised when all attempts fail."""
        retrier = Retrier(max_attempts=3)
        original_error = ValueError("test error")
        operation = Mock(side_effect=original_error)

        with patch("app.src.core.util.retrier.time.sleep"), pytest.raises(
            ValueError, match="test error"
        ):
            retrier.execute(operation)

        assert operation.call_count == 3

    def test_different_exception_types(self):
        """Test handling of different exception types."""
        retrier = Retrier(max_attempts=2)

        # Test various exception types
        for exception_class in [ValueError, RuntimeError, KeyError, TypeError]:
            operation = Mock(side_effect=exception_class("test"))

            with patch("app.src.core.util.retrier.time.sleep"), pytest.raises(
                exception_class
            ):
                retrier.execute(operation)

    def test_last_exception_is_raised(self):
        """Test that the last exception is raised, not the first."""
        retrier = Retrier(max_attempts=3)
        operation = Mock(
            side_effect=[
                ValueError("first error"),
                RuntimeError("second error"),
                TypeError("last error"),
            ]
        )

        with patch("app.src.core.util.retrier.time.sleep"), pytest.raises(
            TypeError, match="last error"
        ):
            retrier.execute(operation)

    def test_runtime_error_on_no_captured_exception(self):
        """Test RuntimeError when no exception is captured (edge case)."""
        retrier = Retrier(max_attempts=1)

        # This is a contrived test for the edge case in the code
        # We'll test by mocking the internal state
        with patch.object(retrier, "max_attempts", 0):
            operation = Mock(return_value="success")

            with pytest.raises(
                RuntimeError,
                match="All retry attempts failed, but no exception was captured",
            ):
                retrier.execute(operation)


class TestRetrierDelayCalculation:
    """Test exponential backoff delay calculations."""

    def test_exponential_backoff_progression(self):
        """Test that delays follow exponential backoff pattern."""
        retrier = Retrier(max_attempts=5, base_delay=1.0, max_delay=100.0)
        operation = Mock(side_effect=RuntimeError("fail"))

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # Verify exponential progression: 1.0, 2.0, 4.0, 8.0
            expected_delays = [1.0, 2.0, 4.0, 8.0]
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays

    def test_max_delay_capping(self):
        """Test that delays are capped at max_delay."""
        retrier = Retrier(max_attempts=6, base_delay=1.0, max_delay=5.0)
        operation = Mock(side_effect=RuntimeError("fail"))

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # Delays should be: 1.0, 2.0, 4.0, 5.0 (capped), 5.0 (capped)
            expected_delays = [1.0, 2.0, 4.0, 5.0, 5.0]
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays

    def test_zero_base_delay(self):
        """Test behavior with zero base delay."""
        retrier = Retrier(max_attempts=3, base_delay=0.0, max_delay=1.0)
        operation = Mock(side_effect=RuntimeError("fail"))

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # All delays should be 0.0
            expected_delays = [0.0, 0.0]
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays

    def test_no_delay_on_last_attempt(self):
        """Test that no delay occurs after the last failed attempt."""
        retrier = Retrier(max_attempts=2)
        operation = Mock(side_effect=RuntimeError("fail"))

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # Only one delay should occur (after first failure, before second attempt)
            assert mock_sleep.call_count == 1

    def test_single_attempt_no_delay(self):
        """Test that no delay occurs with single attempt."""
        retrier = Retrier(max_attempts=1)
        operation = Mock(side_effect=RuntimeError("fail"))

        with patch("app.src.core.util.retrier.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # No delays should occur
            assert mock_sleep.call_count == 0


class TestRetrierLogging:
    """Test logging behavior during retries."""

    def test_debug_logging_on_retry(self):
        """Test that debug logs are generated during retries."""
        retrier = Retrier(max_attempts=3, base_delay=0.1)
        operation = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])

        with (
            patch("app.src.core.util.retrier.time.sleep"),
            patch("app.src.core.util.retrier.logger") as mock_logger,
        ):
            result = retrier.execute(operation)

            assert result == "success"
            assert mock_logger.debug.call_count == 2

            # Verify log messages
            calls = mock_logger.debug.call_args_list
            assert "Attempt 1 failed, retrying in 0.1 seconds" in str(calls[0])
            assert "Attempt 2 failed, retrying in 0.2 seconds" in str(calls[1])

    def test_no_logging_on_immediate_success(self):
        """Test that no debug logs are generated on immediate success."""
        retrier = Retrier()
        operation = Mock(return_value="success")

        with patch("app.src.core.util.retrier.logger") as mock_logger:
            retrier.execute(operation)

            mock_logger.debug.assert_not_called()

    def test_no_logging_on_final_failure(self):
        """Test that no debug log is generated for the final failure."""
        retrier = Retrier(max_attempts=2)
        operation = Mock(side_effect=RuntimeError("fail"))

        with (
            patch("app.src.core.util.retrier.time.sleep"),
            patch("app.src.core.util.retrier.logger") as mock_logger,
        ):
            with pytest.raises(RuntimeError):
                retrier.execute(operation)

            # Only one debug call (after first failure, not after final failure)
            assert mock_logger.debug.call_count == 1


class TestRetrierIntegration:
    """Integration tests with realistic scenarios."""

    def test_file_operation_simulation(self):
        """Test retrier with simulated file operation."""
        retrier = Retrier(max_attempts=3, base_delay=0.01)

        # Simulate file operation that fails twice then succeeds
        call_count = 0

        def file_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise OSError("File temporarily unavailable")
            return "file content"

        with patch("app.src.core.util.retrier.time.sleep"):
            result = retrier.execute(file_operation)

        assert result == "file content"
        assert call_count == 3

    def test_network_operation_simulation(self):
        """Test retrier with simulated network operation."""
        retrier = Retrier(max_attempts=4, base_delay=0.01)

        # Simulate network operation with various failures
        attempts = []

        def network_operation():
            attempt = len(attempts) + 1
            attempts.append(attempt)

            if attempt == 1:
                raise ConnectionError("Connection refused")
            elif attempt == 2:
                raise TimeoutError("Request timeout")
            elif attempt == 3:
                raise ValueError("Invalid response")
            else:
                return {"status": "success", "data": "response"}

        with patch("app.src.core.util.retrier.time.sleep"):
            result = retrier.execute(network_operation)

        assert result == {"status": "success", "data": "response"}
        assert len(attempts) == 4

    def test_mixed_success_failure_patterns(self):
        """Test various success/failure patterns."""
        patterns = [
            # (side_effects, expected_calls, should_succeed)
            (["success"], 1, True),
            ([Exception("fail"), "success"], 2, True),
            ([Exception("1"), Exception("2"), "success"], 3, True),
            ([Exception("1"), Exception("2"), Exception("3")], 3, False),
        ]

        for side_effects, expected_calls, should_succeed in patterns:
            retrier = Retrier(max_attempts=3, base_delay=0.01)
            operation = Mock(side_effect=side_effects)

            with patch("app.src.core.util.retrier.time.sleep"):
                if should_succeed:
                    result = retrier.execute(operation)
                    assert result == "success"
                else:
                    with pytest.raises(Exception, match=".*"):
                        retrier.execute(operation)

                assert operation.call_count == expected_calls


class TestRetrierPerformance:
    """Test performance and timing aspects."""

    def test_actual_delay_timing(self):
        """Test that actual delays approximately match expected delays."""
        retrier = Retrier(max_attempts=3, base_delay=0.01, max_delay=1.0)
        operation = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])

        start_time = time.time()
        result = retrier.execute(operation)
        end_time = time.time()

        # Should have slept approximately 0.01 + 0.02 = 0.03 seconds
        # Allow some margin for test execution overhead
        elapsed = end_time - start_time
        assert 0.025 <= elapsed <= 0.1  # Reasonable bounds for test timing
        assert result == "success"

    def test_operation_cleanup(self):
        """Test that operations are properly cleaned up."""
        retrier = Retrier(max_attempts=2)

        # Test with operation that creates and cleans up resources
        resources_created = []
        resources_cleaned = []

        def operation_with_cleanup():
            resource_id = len(resources_created)
            resources_created.append(resource_id)
            try:
                if len(resources_created) == 1:
                    raise Exception("First attempt fails")
                return "success"
            finally:
                resources_cleaned.append(resource_id)

        with patch("app.src.core.util.retrier.time.sleep"):
            result = retrier.execute(operation_with_cleanup)

        assert result == "success"
        assert len(resources_created) == 2
        assert len(resources_cleaned) == 2
        assert resources_created == resources_cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
