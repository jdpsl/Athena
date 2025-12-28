"""Main error recovery orchestration."""

import logging
from typing import Any, Callable, Optional, TypeVar, Awaitable
from .classifier import ErrorClassifier, ErrorType
from .strategies import RetryStrategy, get_strategy_for_error_type

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorRecovery:
    """Intelligent error recovery with retry strategies."""

    def __init__(self, enable_recovery: bool = True):
        """Initialize error recovery.

        Args:
            enable_recovery: Whether to enable error recovery
        """
        self.enable_recovery = enable_recovery
        self.classifier = ErrorClassifier()

    async def execute_with_recovery(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        operation_name: str = "operation",
        custom_strategy: Optional[RetryStrategy] = None,
        **kwargs: Any,
    ) -> T:
        """Execute a function with automatic error recovery.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            operation_name: Name of operation for logging
            custom_strategy: Custom retry strategy (overrides default)
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            Exception: If all retry attempts fail
        """
        if not self.enable_recovery:
            # Recovery disabled, execute directly
            return await func(*args, **kwargs)

        last_error = None
        attempt = 0

        # Determine retry strategy (will be set after first error)
        strategy: Optional[RetryStrategy] = custom_strategy

        while True:
            attempt += 1

            try:
                # Execute the function
                logger.debug(f"Executing {operation_name} (attempt {attempt})")
                result = await func(*args, **kwargs)

                if attempt > 1:
                    logger.info(f"✓ {operation_name} succeeded after {attempt} attempts")

                return result

            except Exception as e:
                last_error = e
                error_message = str(e)
                error_type_obj = type(e)

                # Classify the error
                error_type = self.classifier.classify(error_message, error_type_obj)

                logger.debug(f"Error in {operation_name}: {error_type.value} - {error_message[:100]}")

                # Get strategy if not already set
                if strategy is None:
                    strategy = get_strategy_for_error_type(error_type)

                # Check if we should retry
                if not strategy.should_retry(attempt):
                    logger.warning(
                        f"✗ {operation_name} failed after {attempt} attempts: {error_message[:100]}"
                    )
                    # Get recovery hint
                    hint = self.classifier.get_recovery_hint(error_type, error_message)
                    if hint:
                        logger.info(f"Hint: {hint}")
                    raise last_error

                # Wait before retry
                if attempt > 1:
                    logger.info(
                        f"Retrying {operation_name} (attempt {attempt}/{strategy.max_attempts})"
                    )

                await strategy.wait(attempt)

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify an error.

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        return self.classifier.classify(str(error), type(error))

    def get_recovery_hint(self, error: Exception) -> Optional[str]:
        """Get a recovery hint for an error.

        Args:
            error: Exception to get hint for

        Returns:
            Recovery hint or None
        """
        error_type = self.classify_error(error)
        return self.classifier.get_recovery_hint(error_type, str(error))

    def is_retryable(self, error: Exception) -> bool:
        """Check if an error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error should be retried
        """
        error_type = self.classify_error(error)
        return self.classifier.is_retryable(error_type)


# Global instance for convenience
_default_recovery = ErrorRecovery()


async def with_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    operation_name: str = "operation",
    **kwargs: Any,
) -> T:
    """Convenience function for executing with retry.

    Args:
        func: Async function to execute
        *args: Positional arguments
        operation_name: Name for logging
        **kwargs: Keyword arguments

    Returns:
        Result from func
    """
    return await _default_recovery.execute_with_recovery(
        func, *args, operation_name=operation_name, **kwargs
    )
