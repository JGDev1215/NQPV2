"""
Unit tests for core exception classes.

Tests the exception hierarchy and custom exception types.
"""

import pytest
from nasdaq_predictor.core.exceptions import (
    NQPException,
    DataFetchException,
    AnalysisException,
    DatabaseException,
    ValidationException,
    SchedulerException,
    CacheException,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_exceptions_inherit_from_nqp_exception(self):
        """Verify all custom exceptions inherit from NQPException."""
        exceptions = [
            DataFetchException,
            AnalysisException,
            DatabaseException,
            ValidationException,
            SchedulerException,
            CacheException,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, NQPException)

    def test_nqp_exception_inherits_from_exception(self):
        """Verify NQPException inherits from standard Exception."""
        assert issubclass(NQPException, Exception)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        msg = "Test error message"
        exc = DataFetchException(msg)
        assert str(exc) == msg

    def test_exception_raising_and_catching(self):
        """Test raising and catching specific exceptions."""
        with pytest.raises(DataFetchException):
            raise DataFetchException("Data fetch failed")

        with pytest.raises(ValidationException):
            raise ValidationException("Invalid input")

        with pytest.raises(AnalysisException):
            raise AnalysisException("Analysis failed")

    def test_catch_base_exception(self):
        """Test catching base NQPException catches all subclasses."""
        exceptions = [
            DataFetchException("fetch error"),
            ValidationException("validation error"),
            AnalysisException("analysis error"),
        ]

        for exc in exceptions:
            with pytest.raises(NQPException):
                raise exc

    def test_exception_with_cause(self):
        """Test exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise DatabaseException("Database operation failed") from e
        except DatabaseException as e:
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"

    def test_different_exceptions_not_caught_by_each_other(self):
        """Test that different exception types are distinct."""
        with pytest.raises(DataFetchException):
            raise DataFetchException("test")

        # ValidationException should not catch DataFetchException
        try:
            raise DataFetchException("test")
        except ValidationException:
            pytest.fail("DataFetchException was caught by ValidationException")
        except DataFetchException:
            pass  # Expected


class TestSpecificExceptions:
    """Test specific exception use cases."""

    def test_data_fetch_exception(self):
        """Test DataFetchException for API failures."""
        with pytest.raises(DataFetchException) as exc_info:
            raise DataFetchException("Yahoo Finance API timeout")

        assert "timeout" in str(exc_info.value).lower()

    def test_validation_exception(self):
        """Test ValidationException for input validation."""
        with pytest.raises(ValidationException) as exc_info:
            raise ValidationException("Invalid ticker: XYZ")

        assert "ticker" in str(exc_info.value).lower()

    def test_analysis_exception(self):
        """Test AnalysisException for calculation errors."""
        with pytest.raises(AnalysisException) as exc_info:
            raise AnalysisException("Insufficient data for signal calculation")

        assert "data" in str(exc_info.value).lower()

    def test_database_exception(self):
        """Test DatabaseException for DB errors."""
        with pytest.raises(DatabaseException) as exc_info:
            raise DatabaseException("Connection timeout")

        assert "connection" in str(exc_info.value).lower()

    def test_scheduler_exception(self):
        """Test SchedulerException for job errors."""
        with pytest.raises(SchedulerException) as exc_info:
            raise SchedulerException("Job execution failed")

        assert "job" in str(exc_info.value).lower()

    def test_cache_exception(self):
        """Test CacheException for cache errors."""
        with pytest.raises(CacheException) as exc_info:
            raise CacheException("Cache miss")

        assert "cache" in str(exc_info.value).lower()


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_exception_with_multiple_args(self):
        """Test exception with multiple arguments."""
        exc = ValidationException("Invalid", "ticker", "NQ=Z")
        # Exception should contain all args
        exc_str = str(exc)
        assert len(exc_str) > 0

    def test_exception_repr(self):
        """Test exception repr."""
        exc = DataFetchException("test error")
        repr_str = repr(exc)
        assert "test error" in repr_str

    def test_nested_exception_context(self):
        """Test exception context preservation."""
        try:
            try:
                raise RuntimeError("Inner error")
            except RuntimeError:
                raise ValidationException("Validation failed")
        except ValidationException as e:
            assert e.__context__ is not None
