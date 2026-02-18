"""
Tests for the circuit breaker implementation.
"""

import pytest
import asyncio

from app.resilience.circuit_breaker import AsyncCircuitBreaker, CircuitState, CircuitBreakerOpenError


@pytest.mark.asyncio
class TestAsyncCircuitBreaker:

    async def test_initial_state_is_closed(self):
        cb = AsyncCircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    async def test_opens_after_threshold_failures(self):
        cb = AsyncCircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def failing_func():
            raise ValueError("fail")

        for _ in range(3):
            with pytest.raises(ValueError):
                await cb(failing_func)

        assert cb.state == CircuitState.OPEN

    async def test_rejects_when_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, recovery_timeout=60)

        async def failing_func():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb(failing_func)

        with pytest.raises(CircuitBreakerOpenError):
            await cb(failing_func)

    async def test_success_reduces_failure_count(self):
        cb = AsyncCircuitBreaker(failure_threshold=3)

        async def success_func():
            return "ok"

        result = await cb(success_func)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    async def test_reset(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, recovery_timeout=60)

        async def failing_func():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb(failing_func)

        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
