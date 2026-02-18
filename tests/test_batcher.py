"""
Tests for the dynamic batching engine.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.core.dynamic_batcher import DynamicBatcher, BatchItem


@pytest.mark.asyncio
class TestDynamicBatcher:

    async def test_single_request(self):
        """Test that a single request is processed correctly."""
        mock_server = MagicMock()
        mock_server.initialize = AsyncMock()
        mock_server.predict_batch = AsyncMock(return_value=[[0.9, 0.8, 0.7]])

        batcher = DynamicBatcher(mock_server, max_batch_size=4, timeout_ms=50)
        await batcher.start()

        try:
            scores = await asyncio.wait_for(
                batcher.submit(
                    user_id="user_1",
                    context={"test": True},
                    candidate_titles=["A", "B", "C"],
                    model_version="v1",
                ),
                timeout=2.0,
            )

            assert scores == [0.9, 0.8, 0.7]
        finally:
            await batcher.stop()

    async def test_batch_collection(self):
        """Test that multiple concurrent requests are batched."""
        mock_server = MagicMock()
        mock_server.initialize = AsyncMock()
        mock_server.predict_batch = AsyncMock(
            return_value=[[0.9, 0.8], [0.7, 0.6]]
        )

        batcher = DynamicBatcher(mock_server, max_batch_size=4, timeout_ms=100)
        await batcher.start()

        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    batcher.submit("user_1", {}, ["A", "B"], "v1"),
                    batcher.submit("user_2", {}, ["C", "D"], "v1"),
                ),
                timeout=2.0,
            )

            assert len(results) == 2
        finally:
            await batcher.stop()

    async def test_queue_size(self):
        """Test queue size reporting."""
        mock_server = MagicMock()
        mock_server.initialize = AsyncMock()
        mock_server.predict_batch = AsyncMock(return_value=[])

        batcher = DynamicBatcher(mock_server, max_batch_size=4, timeout_ms=50)
        assert batcher.queue_size == 0
        assert not batcher.is_running()

        await batcher.start()
        assert batcher.is_running()
        await batcher.stop()
