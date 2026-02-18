"""
Circuit Breaker pattern implementation.
Prevents cascading failures by short-circuiting calls to failing services.

States:
- CLOSED: Normal operation, requests flow through
- OPEN: Service is failing, requests are rejected immediately
- HALF_OPEN: Testing if service has recovered
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any
from functools import wraps

from app.observability.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AsyncCircuitBreaker:
    """
    Async-compatible circuit breaker with configurable thresholds.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning("circuit_breaker_open", name=self.name)
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. Service is temporarily unavailable."
            )

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_calls = 0
                    logger.info("circuit_breaker_closed", name=self.name)
            else:
                self._failure_count = max(0, self._failure_count - 1)

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("circuit_breaker_reopened", name=self.name)
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_tripped",
                    name=self.name,
                    failure_count=self._failure_count,
                )

    def reset(self):
        """Manually reset the circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is in OPEN state."""
    pass


# Global circuit breaker instance for the ranking service
_ranking_cb = AsyncCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
    name="ranking",
)


def ranking_circuit_breaker(func):
    """Decorator to wrap async functions with the ranking circuit breaker."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await _ranking_cb(func, *args, **kwargs)
    return wrapper
