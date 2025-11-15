"""
Result type for functional error handling.

Implements Rust-style Result<T, E> pattern for better error handling without exceptions.
Allows operations to fail gracefully and compose error handling.

Example:
    >>> result = Result.ok(100.0)
    >>> result.map(lambda x: x * 1.05).unwrap_or(0.0)
    105.0

    >>> result = Result.err("Failed to fetch data")
    >>> result.map(lambda x: x * 2).unwrap_or(0.0)
    0.0
"""

from typing import TypeVar, Generic, Union, Callable, Optional

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T, E]):
    """Result type representing either success (Ok) or failure (Err).

    This pattern eliminates the need for exceptions in many cases and provides
    a composable way to handle errors.
    """

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        """Create a successful Result with a value.

        Args:
            value: The success value.

        Returns:
            An Ok instance wrapping the value.
        """
        return Ok(value)

    @staticmethod
    def err(error: E) -> "Result[T, E]":
        """Create a failed Result with an error.

        Args:
            error: The error value.

        Returns:
            An Err instance wrapping the error.
        """
        return Err(error)

    def is_ok(self) -> bool:
        """Check if this Result is Ok.

        Returns:
            True if this is an Ok result, False otherwise.
        """
        raise NotImplementedError

    def is_err(self) -> bool:
        """Check if this Result is Err.

        Returns:
            True if this is an Err result, False otherwise.
        """
        raise NotImplementedError

    def unwrap(self) -> T:
        """Extract the value from Ok or raise an exception.

        Returns:
            The wrapped value if Ok.

        Raises:
            ValueError: If this is an Err result.
        """
        raise NotImplementedError

    def unwrap_or(self, default: T) -> T:
        """Extract the value from Ok or return a default.

        Args:
            default: The default value to return on Err.

        Returns:
            The wrapped value if Ok, or the default if Err.
        """
        raise NotImplementedError

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        """Extract the value from Ok or compute a default.

        Args:
            fn: Function to call with error to compute default.

        Returns:
            The wrapped value if Ok, or result of fn if Err.
        """
        raise NotImplementedError

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        """Apply a function to the value if Ok.

        Args:
            fn: Function to apply to the value.

        Returns:
            A new Result with the mapped value, or self if Err.
        """
        raise NotImplementedError

    def map_err(self, fn: Callable[[E], F]) -> "Result[T, F]":
        """Apply a function to the error if Err.

        Args:
            fn: Function to apply to the error.

        Returns:
            A new Result with the mapped error, or self if Ok.
        """
        raise NotImplementedError

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Chain operations that return Results.

        Args:
            fn: Function that takes a value and returns a Result.

        Returns:
            The result of fn if Ok, or self if Err.
        """
        raise NotImplementedError


class Ok(Result[T, E]):
    """A successful Result containing a value."""

    def __init__(self, value: T):
        """Initialize Ok with a value.

        Args:
            value: The success value to wrap.
        """
        self.value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        return Ok(fn(self.value))

    def map_err(self, fn: Callable[[E], F]) -> "Result[T, F]":
        return Ok(self.value)

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return fn(self.value)

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


class Err(Result[T, E]):
    """A failed Result containing an error."""

    def __init__(self, error: E):
        """Initialize Err with an error.

        Args:
            error: The error value to wrap.
        """
        self.error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on an Err value: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        return fn(self.error)

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        return Err(self.error)

    def map_err(self, fn: Callable[[E], F]) -> "Result[T, F]":
        return Err(fn(self.error))

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return Err(self.error)

    def __repr__(self) -> str:
        return f"Err({self.error!r})"
