"""
Model Registry - Manages multiple model versions for blue/green and canary deployments.
Supports dynamic model loading, versioning, and hot-swapping.
"""

import os
import asyncio
from typing import Dict, List, Optional

from app.observability.logging import get_logger

logger = get_logger(__name__)


class ModelInfo:
    """Metadata and reference for a loaded model version."""

    def __init__(self, version: str, model, tokenizer=None, device: str = "cpu"):
        self.version = version
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.is_active = True
        self.request_count = 0


class ModelRegistry:
    """
    Manages model versions with support for:
    - Multiple concurrent model versions
    - Blue/green deployment (two active versions)
    - Canary routing (percentage-based traffic split)
    - Hot model reload without downtime
    """

    def __init__(self, settings):
        self.settings = settings
        self._models: Dict[str, ModelInfo] = {}
        self._active_version: str = settings.model_version
        self._lock = asyncio.Lock()

    async def load_models(self):
        """Load the default model on startup."""
        logger.info("loading_models", model_name=self.settings.model_name)

        try:
            model, tokenizer = await self._load_model(
                self.settings.model_name,
                self.settings.model_device,
            )

            self._models[self.settings.model_version] = ModelInfo(
                version=self.settings.model_version,
                model=model,
                tokenizer=tokenizer,
                device=self.settings.model_device,
            )

            logger.info(
                "model_loaded_successfully",
                version=self.settings.model_version,
                device=self.settings.model_device,
            )

        except Exception as e:
            logger.warning("model_load_failed_using_lightweight_fallback", error=str(e))
            # Fallback: load a lightweight embedding model for ranking
            await self._load_lightweight_model(self.settings.model_version)

    async def _load_model(self, model_name: str, device: str):
        """Load a sentence-transformer model for semantic ranking."""
        try:
            from sentence_transformers import SentenceTransformer

            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(model_name, device=device),
            )
            return model, None
        except ImportError:
            logger.warning("sentence_transformers_not_available")
            raise

    async def _load_lightweight_model(self, version: str):
        """Fallback lightweight model using TF-IDF-like scoring for ranking."""
        from app.core.ranker import LightweightRanker

        ranker = LightweightRanker()
        self._models[version] = ModelInfo(
            version=version,
            model=ranker,
            device="cpu",
        )
        logger.info("lightweight_model_loaded", version=version)

    def get_model(self, version: Optional[str] = None) -> ModelInfo:
        """Get a specific model version or the active one."""
        target_version = version or self._active_version
        model_info = self._models.get(target_version)

        if not model_info:
            raise ValueError(f"Model version '{target_version}' not found. Available: {self.list_versions()}")

        model_info.request_count += 1
        return model_info

    def list_versions(self) -> List[str]:
        """List all available model versions."""
        return list(self._models.keys())

    @property
    def active_version(self) -> str:
        return self._active_version

    async def switch_version(self, new_version: str):
        """Switch the active model version (blue/green deployment)."""
        async with self._lock:
            if new_version not in self._models:
                raise ValueError(f"Version '{new_version}' is not loaded")
            old_version = self._active_version
            self._active_version = new_version
            logger.info(
                "model_version_switched",
                from_version=old_version,
                to_version=new_version,
            )

    async def register_model(self, version: str, model, tokenizer=None, device: str = "cpu"):
        """Register a new model version dynamically."""
        async with self._lock:
            self._models[version] = ModelInfo(
                version=version,
                model=model,
                tokenizer=tokenizer,
                device=device,
            )
            logger.info("model_registered", version=version)

    async def unload_model(self, version: str):
        """Unload a model version to free resources."""
        async with self._lock:
            if version == self._active_version:
                raise ValueError("Cannot unload active model version")
            if version in self._models:
                del self._models[version]
                logger.info("model_unloaded", version=version)
