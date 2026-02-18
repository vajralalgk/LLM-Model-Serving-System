"""
Timeout enforcement for async operations.
Prevents requests from hanging indefinitely.
"""

import asyncio
from typing import TypeVar, Coroutine

T = TypeVar("T")


async def with_timeout(coro: Coroutine, timeout_seconds: float = 5.0) -> T:
    """
    Execute a coroutine with a timeout.
    Raises TimeoutError if the operation exceeds the specified duration.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Operation timed out after {timeout_seconds}s"
        )
