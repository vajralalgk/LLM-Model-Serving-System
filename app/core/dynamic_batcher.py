"""
Dynamic Batching Engine - Combines multiple inference requests into single GPU forward passes.
Reduces GPU idle time and improves throughput without increasing latency.

Key features:
- Configurable batch window (10-20ms)
- Configurable max batch size
- Automatic de-batching of responses
- Backpressure handling
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from app.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BatchItem:
    """A single request waiting to be batched."""

    user_id: str
    context: Dict[str, Any]
    candidate_titles: List[str]
    model_version: str
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_event_loop().create_future())
    submitted_at: float = field(default_factory=time.perf_counter)


class DynamicBatcher:
    """
    Accumulates incoming requests and processes them in optimized batches.

    Flow:
    1. Request arrives -> added to queue with a Future
    2. Batch processor runs every `timeout_ms` or when queue reaches `max_batch_size`
    3. Batch is sent to ModelServer.predict_batch()
    4. Results are de-batched and delivered via Futures
    """

    def __init__(self, model_server, max_batch_size: int = 32, timeout_ms: int = 15):
        self.model_server = model_server
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._total_batches = 0
        self._total_items = 0

    async def start(self):
        """Start the batch processing loop."""
        self._running = True

        # Ensure model server engines are initialized
        await self.model_server.initialize()

        self._task = asyncio.create_task(self._batch_loop())
        logger.info(
            "dynamic_batcher_started",
            max_batch_size=self.max_batch_size,
            timeout_ms=self.timeout_ms,
        )

    async def stop(self):
        """Stop the batch processing loop gracefully."""
        self._running = False
        if self._task:
            # Process remaining items
            await self._drain_queue()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(
            "dynamic_batcher_stopped",
            total_batches=self._total_batches,
            total_items=self._total_items,
        )

    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    async def submit(
        self,
        user_id: str,
        context: Dict[str, Any],
        candidate_titles: List[str],
        model_version: str,
    ) -> List[float]:
        """
        Submit a ranking request for batched processing.
        Returns scores when the batch is processed.
        """
        loop = asyncio.get_event_loop()
        item = BatchItem(
            user_id=user_id,
            context=context,
            candidate_titles=candidate_titles,
            model_version=model_version,
            future=loop.create_future(),
        )

        await self._queue.put(item)

        # Wait for result
        return await item.future

    async def _batch_loop(self):
        """Main loop that collects and processes batches."""
        while self._running:
            try:
                batch = await self._collect_batch()
                if batch:
                    await self._process_batch(batch)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("batch_processing_error", error=str(e))
                await asyncio.sleep(0.01)

    async def _collect_batch(self) -> List[BatchItem]:
        """Collect items from the queue up to max_batch_size or timeout."""
        batch: List[BatchItem] = []

        try:
            # Wait for at least one item
            item = await asyncio.wait_for(
                self._queue.get(),
                timeout=self.timeout_ms / 1000.0,
            )
            batch.append(item)
        except asyncio.TimeoutError:
            return batch

        # Collect more items within the time window
        deadline = time.perf_counter() + (self.timeout_ms / 1000.0)

        while len(batch) < self.max_batch_size:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break

            try:
                item = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=remaining,
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break

        return batch

    async def _process_batch(self, batch: List[BatchItem]):
        """Process a collected batch and deliver results."""
        self._total_batches += 1
        self._total_items += len(batch)

        batch_start = time.perf_counter()

        try:
            # Build batch input for model server
            batch_input = [
                {
                    "user_id": item.user_id,
                    "context": item.context,
                    "candidate_titles": item.candidate_titles,
                    "model_version": item.model_version,
                }
                for item in batch
            ]

            # Execute batched inference
            results = await self.model_server.predict_batch(batch_input)

            # De-batch: deliver individual results via Futures
            for item, scores in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(scores)

            batch_time_ms = (time.perf_counter() - batch_start) * 1000
            logger.debug(
                "batch_processed",
                batch_size=len(batch),
                batch_time_ms=round(batch_time_ms, 2),
            )

        except Exception as e:
            # On error, fail all futures in the batch
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)
            logger.error("batch_processing_failed", batch_size=len(batch), error=str(e))

    async def _drain_queue(self):
        """Process remaining items in queue during shutdown."""
        remaining = []
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                remaining.append(item)
            except asyncio.QueueEmpty:
                break

        if remaining:
            logger.info("draining_queue", remaining_items=len(remaining))
            await self._process_batch(remaining)
