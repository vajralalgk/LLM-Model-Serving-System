"""
Retry mechanism with exponential backoff and jitter.
Handles transient failures gracefully.
"""

import asyncio
import random
from typing import Callable, Type, Tuple
from functools import wraps

from app.observability.logging import get_logger

logger = get_logger(__name__)


def async_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for async functions with exponential backoff retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential backoff
        jitter: Add randomized jitter to prevent thundering herd
        retryable_exceptions: Tuple of exception types that trigger retries
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e),
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        "retrying_operation",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=round(delay, 3),
                        error=str(e),
                    )

                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
