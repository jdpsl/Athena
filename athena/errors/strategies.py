"""Retry strategies for error recovery."""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RetryStrategy(ABC):
    """Base class for retry strategies."""

    def __init__(self, max_attempts: int = 3):
        """Initialize retry strategy.

        Args:
            max_attempts: Maximum number of retry attempts
        """
        self.max_attempts = max_attempts

    @abstractmethod
    async def wait(self, attempt: int) -> None:
        """Wait before the next retry attempt.

        Args:
            attempt: Current attempt number (1-indexed)
        """
        pass

    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            True if we should retry
        """
        return attempt < self.max_attempts


class NoRetry(RetryStrategy):
    """No retry strategy - fail immediately."""

    def __init__(self):
        """Initialize no-retry strategy."""
        super().__init__(max_attempts=1)

    async def wait(self, attempt: int) -> None:
        """No waiting needed."""
        pass


class LinearBackoff(RetryStrategy):
    """Linear backoff - wait increases linearly."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        """Initialize linear backoff strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def wait(self, attempt: int) -> None:
        """Wait with linear backoff.

        Args:
            attempt: Current attempt number (1-indexed)
        """
        delay = min(self.base_delay * attempt, self.max_delay)
        logger.debug(f"Linear backoff: waiting {delay:.2f}s before retry {attempt}")
        await asyncio.sleep(delay)


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff with jitter - wait increases exponentially."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        """Initialize exponential backoff strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to prevent thundering herd
        """
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    async def wait(self, attempt: int) -> None:
        """Wait with exponential backoff.

        Args:
            attempt: Current attempt number (1-indexed)
        """
        # Exponential: 2^attempt * base_delay
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)

        # Add jitter (random 0-50% of delay)
        if self.jitter:
            jitter_amount = delay * 0.5 * random.random()
            delay += jitter_amount

        logger.debug(f"Exponential backoff: waiting {delay:.2f}s before retry {attempt}")
        await asyncio.sleep(delay)


class RateLimitBackoff(RetryStrategy):
    """Special backoff for rate limit errors - longer waits."""

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 5.0,
        max_delay: float = 120.0
    ):
        """Initialize rate limit backoff strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds (higher than normal)
            max_delay: Maximum delay in seconds
        """
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def wait(self, attempt: int) -> None:
        """Wait with rate limit backoff.

        Args:
            attempt: Current attempt number (1-indexed)
        """
        # Aggressive exponential backoff for rate limits
        delay = min(self.base_delay * (3 ** (attempt - 1)), self.max_delay)
        logger.info(f"Rate limit: waiting {delay:.2f}s before retry {attempt}")
        await asyncio.sleep(delay)


def get_strategy_for_error_type(error_type: str) -> RetryStrategy:
    """Get appropriate retry strategy for error type.

    Args:
        error_type: Type of error (from ErrorType enum)

    Returns:
        Appropriate retry strategy
    """
    from .classifier import ErrorType

    strategies = {
        ErrorType.NETWORK: ExponentialBackoff(max_attempts=3, base_delay=1.0, max_delay=10.0),
        ErrorType.TIMEOUT: ExponentialBackoff(max_attempts=3, base_delay=2.0, max_delay=15.0),
        ErrorType.RATE_LIMIT: RateLimitBackoff(max_attempts=5, base_delay=5.0, max_delay=120.0),
        ErrorType.FILE_NOT_FOUND: NoRetry(),
        ErrorType.PERMISSION: NoRetry(),
        ErrorType.SYNTAX: NoRetry(),
        ErrorType.VALIDATION: NoRetry(),
        ErrorType.UNKNOWN: LinearBackoff(max_attempts=2, base_delay=1.0),
    }

    # Convert string to ErrorType if needed
    if isinstance(error_type, str):
        try:
            error_type = ErrorType(error_type)
        except ValueError:
            error_type = ErrorType.UNKNOWN

    return strategies.get(error_type, NoRetry())
