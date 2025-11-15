"""
Unit tests for the Result type.

Tests the Ok/Err result type and its operations.
"""

import pytest
from nasdaq_predictor.core.result import Result, Ok, Err


class TestResultCreation:
    """Test Result creation."""

    def test_create_ok_result(self):
        """Test creating an Ok result."""
        result = Result.ok(42)
        assert result.is_ok()
        assert not result.is_err()

    def test_create_err_result(self):
        """Test creating an Err result."""
        result = Result.err("error message")
        assert result.is_err()
        assert not result.is_ok()

    def test_ok_result_type(self):
        """Test Ok result is instance of Ok."""
        result = Result.ok(100)
        assert isinstance(result, Ok)

    def test_err_result_type(self):
        """Test Err result is instance of Err."""
        result = Result.err("error")
        assert isinstance(result, Err)


class TestResultUnwrap:
    """Test unwrapping results."""

    def test_unwrap_ok_returns_value(self):
        """Test unwrap on Ok returns the value."""
        result = Result.ok(42)
        assert result.unwrap() == 42

    def test_unwrap_err_raises_exception(self):
        """Test unwrap on Err raises ValueError."""
        result = Result.err("error occurred")
        with pytest.raises(ValueError) as exc_info:
            result.unwrap()
        assert "error occurred" in str(exc_info.value)

    def test_unwrap_or_ok_returns_value(self):
        """Test unwrap_or on Ok returns the value, not default."""
        result = Result.ok(42)
        assert result.unwrap_or(100) == 42

    def test_unwrap_or_err_returns_default(self):
        """Test unwrap_or on Err returns default."""
        result = Result.err("error")
        assert result.unwrap_or(100) == 100

    def test_unwrap_or_else_ok_returns_value(self):
        """Test unwrap_or_else on Ok returns value."""
        result = Result.ok(42)
        assert result.unwrap_or_else(lambda e: 100) == 42

    def test_unwrap_or_else_err_calls_function(self):
        """Test unwrap_or_else on Err calls the function."""
        result = Result.err("error")
        value = result.unwrap_or_else(lambda e: f"handled: {e}")
        assert value == "handled: error"


class TestResultMap:
    """Test mapping operations."""

    def test_map_ok_applies_function(self):
        """Test map on Ok applies the function."""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 10

    def test_map_err_ignores_function(self):
        """Test map on Err ignores the function."""
        result = Result.err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_or(None) is None

    def test_map_chain(self):
        """Test chaining map operations."""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2).map(lambda x: x + 3)
        assert mapped.unwrap() == 13

    def test_map_err_ok_ignores_function(self):
        """Test map_err on Ok ignores the function."""
        result = Result.ok(42)
        mapped = result.map_err(lambda e: f"error: {e}")
        assert mapped.is_ok()
        assert mapped.unwrap() == 42

    def test_map_err_on_err_applies_function(self):
        """Test map_err on Err applies the function."""
        result = Result.err("original error")
        mapped = result.map_err(lambda e: f"wrapped: {e}")
        assert mapped.is_err()
        # Can't unwrap err, but can check error is wrapped
        assert "wrapped" in mapped.__dict__.get("error", "")

    def test_map_chain_with_error(self):
        """Test chaining maps stops at error."""
        result = Result.err("initial error")
        mapped = result.map(lambda x: x * 2).map(lambda x: x + 3)
        assert mapped.is_err()


class TestResultAndThen:
    """Test and_then (flatMap) operations."""

    def test_and_then_ok_calls_function(self):
        """Test and_then on Ok calls the function."""
        result = Result.ok(5)
        chained = result.and_then(lambda x: Result.ok(x * 2))
        assert chained.unwrap() == 10

    def test_and_then_err_ignores_function(self):
        """Test and_then on Err ignores the function."""
        result = Result.err("error")
        chained = result.and_then(lambda x: Result.ok(x * 2))
        assert chained.is_err()

    def test_and_then_can_convert_to_err(self):
        """Test and_then can convert Ok to Err."""
        result = Result.ok(0)
        chained = result.and_then(
            lambda x: Result.ok(10 / x) if x != 0 else Result.err("division by zero")
        )
        assert chained.is_err()

    def test_and_then_chain(self):
        """Test chaining and_then operations."""
        result = Result.ok(5)
        chained = (
            result.and_then(lambda x: Result.ok(x * 2))
            .and_then(lambda x: Result.ok(x + 3))
            .and_then(lambda x: Result.ok(x / 2))
        )
        assert chained.unwrap() == 6.5

    def test_and_then_stops_at_error(self):
        """Test chaining stops at first error."""
        result = Result.ok(5)
        chained = (
            result.and_then(lambda x: Result.ok(x * 2))
            .and_then(lambda x: Result.err("error in second"))
            .and_then(lambda x: Result.ok(x + 3))  # Should not execute
        )
        assert chained.is_err()


class TestResultComposition:
    """Test composing complex result operations."""

    def test_division_operation(self):
        """Test safe division using Result."""
        def safe_divide(a: int, b: int):
            return Result.ok(a / b) if b != 0 else Result.err("division by zero")

        result = safe_divide(10, 2)
        assert result.unwrap() == 5.0

        result = safe_divide(10, 0)
        assert result.is_err()
        assert result.unwrap_or(0) == 0

    def test_complex_computation(self):
        """Test complex computation with multiple steps."""
        result = (
            Result.ok(10)
            .map(lambda x: x * 2)  # 20
            .map(lambda x: x + 5)  # 25
            .and_then(lambda x: Result.ok(x / 5))  # 5.0
            .map(lambda x: int(x))  # 5
        )
        assert result.unwrap() == 5

    def test_validation_pipeline(self):
        """Test using Result for validation pipeline."""
        def validate_age(age: int):
            return Result.ok(age) if age >= 0 else Result.err("age cannot be negative")

        def validate_adult(age: int):
            return Result.ok(age) if age >= 18 else Result.err("must be adult")

        result = (
            validate_age(25)
            .and_then(validate_adult)
            .map(lambda x: f"Valid age: {x}")
        )
        assert result.unwrap() == "Valid age: 25"

        result = (
            validate_age(-5)
            .and_then(validate_adult)
        )
        assert result.is_err()


class TestResultRepr:
    """Test Result string representation."""

    def test_ok_repr(self):
        """Test Ok result repr."""
        result = Result.ok(42)
        assert "Ok" in repr(result)
        assert "42" in repr(result)

    def test_err_repr(self):
        """Test Err result repr."""
        result = Result.err("error message")
        assert "Err" in repr(result)
        assert "error message" in repr(result)

    def test_ok_with_string(self):
        """Test Ok result with string value."""
        result = Result.ok("success")
        assert result.unwrap() == "success"

    def test_err_with_dict(self):
        """Test Err result with dict value."""
        error = {"code": "VALIDATION_ERROR", "message": "Invalid input"}
        result = Result.err(error)
        assert result.is_err()
        assert result.unwrap_or({}).get("code") is None


class TestResultTypePreservation:
    """Test that Result preserves types correctly."""

    def test_ok_preserves_numeric_types(self):
        """Test Ok preserves numeric types."""
        ok_int = Result.ok(42)
        assert ok_int.unwrap() == 42
        assert isinstance(ok_int.unwrap(), int)

        ok_float = Result.ok(3.14)
        assert ok_float.unwrap() == 3.14
        assert isinstance(ok_float.unwrap(), float)

    def test_ok_preserves_complex_types(self):
        """Test Ok preserves complex types."""
        ok_list = Result.ok([1, 2, 3])
        assert ok_list.unwrap() == [1, 2, 3]

        ok_dict = Result.ok({"key": "value"})
        assert ok_dict.unwrap() == {"key": "value"}

        class CustomType:
            pass

        custom = CustomType()
        ok_custom = Result.ok(custom)
        assert ok_custom.unwrap() is custom
