"""
Model Server - Orchestrates model inference for ranking requests.
Manages model lifecycle and provides the inference interface.
"""

import asyncio
from typing import Dict, Any, List, Optional

from app.core.model_registry import ModelRegistry
from app.core.ranker import RankingEngine
from app.observability.logging import get_logger

logger = get_logger(__name__)


class ModelServer:
    """
    High-level model server that:
    - Provides async inference interface
    - Manages model lifecycle
    - Supports version routing
    - Tracks inference metrics
    """

    def __init__(self, registry: ModelRegistry, settings):
        self.registry = registry
        self.settings = settings
        self._engines: Dict[str, RankingEngine] = {}
        self._ready = False
        self._inference_count = 0
        self._lock = asyncio.Lock()

    @property
    def current_version(self) -> str:
        return self.registry.active_version

    def is_ready(self) -> bool:
        return self._ready and len(self.registry.list_versions()) > 0

    async def initialize(self):
        """Initialize ranking engines for all loaded models."""
        for version in self.registry.list_versions():
            model_info = self.registry.get_model(version)
            self._engines[version] = RankingEngine(
                model=model_info.model,
                device=model_info.device,
            )
        self._ready = True
        logger.info("model_server_initialized", versions=self.registry.list_versions())

    def _ensure_engine(self, version: str) -> RankingEngine:
        """Get or create a ranking engine for a model version."""
        if version not in self._engines:
            model_info = self.registry.get_model(version)
            self._engines[version] = RankingEngine(
                model=model_info.model,
                device=model_info.device,
            )
        return self._engines[version]

    async def predict(
        self,
        user_id: str,
        context: Dict[str, Any],
        candidate_titles: List[str],
        model_version: Optional[str] = None,
    ) -> List[float]:
        """
        Run inference to compute ranking scores.
        Thread-safe and supports concurrent requests.
        """
        version = model_version or self.registry.active_version
        engine = self._ensure_engine(version)

        # Run compute in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            engine.compute_scores,
            user_id,
            context,
            candidate_titles,
        )

        self._inference_count += 1
        return scores

    async def predict_batch(
        self,
        batch: List[Dict[str, Any]],
    ) -> List[List[float]]:
        """
        Run batched inference for multiple requests.
        Combines inputs into single forward pass for GPU efficiency.
        """
        if not batch:
            return []

        # Group by model version
        version_groups: Dict[str, List] = {}
        for i, item in enumerate(batch):
            version = item.get("model_version") or self.registry.active_version
            if version not in version_groups:
                version_groups[version] = []
            version_groups[version].append((i, item))

        results = [None] * len(batch)

        for version, items in version_groups.items():
            engine = self._ensure_engine(version)

            # Combine all texts for batch encoding
            all_contexts = []
            all_candidates = []
            item_boundaries = []

            for idx, item in items:
                context_text = engine._build_context_text(item["user_id"], item["context"])
                all_contexts.append(context_text)
                all_candidates.extend(item["candidate_titles"])
                item_boundaries.append(len(item["candidate_titles"]))

            # Batch encode all texts at once
            all_texts = all_contexts + all_candidates
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                engine.model.encode,
                all_texts,
            )

            # Split embeddings back to individual requests
            context_embeddings = embeddings[: len(all_contexts)]
            candidate_embeddings = embeddings[len(all_contexts) :]

            offset = 0
            for i, (idx, item) in enumerate(items):
                num_candidates = item_boundaries[i]
                ctx_emb = context_embeddings[i]
                cand_embs = candidate_embeddings[offset : offset + num_candidates]
                offset += num_candidates

                # Compute scores
                scores = []
                for cand_emb in cand_embs:
                    sim = engine._cosine_similarity(ctx_emb, cand_emb)
                    scores.append(float((sim + 1.0) / 2.0))

                scores = engine._apply_personalization(scores, item["user_id"], item["context"])
                results[idx] = scores

        self._inference_count += len(batch)
        return results

    async def shutdown(self):
        """Clean up resources on shutdown."""
        self._ready = False
        self._engines.clear()
        logger.info("model_server_shutdown", total_inferences=self._inference_count)
