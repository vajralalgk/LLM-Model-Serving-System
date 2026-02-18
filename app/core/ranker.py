"""
Ranking Engine - Computes personalized relevance scores.
Supports both full LLM-based ranking and a lightweight fallback.
"""

import numpy as np
from typing import List, Dict, Any
import hashlib
import math


class LightweightRanker:
    """
    TF-IDF-inspired lightweight ranker that works without GPU.
    Used as a fallback when full models aren't available.
    Provides deterministic, user-personalized ranking.
    """

    def __init__(self):
        self._idf_cache: Dict[str, float] = {}

    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate pseudo-embeddings for a list of texts using character n-grams."""
        embeddings = []
        for text in texts:
            embedding = self._text_to_vector(text)
            embeddings.append(embedding)
        return np.array(embeddings)

    def _text_to_vector(self, text: str, dim: int = 128) -> np.ndarray:
        """Convert text to a fixed-dimension vector using hash-based features."""
        vector = np.zeros(dim)
        text_lower = text.lower()
        words = text_lower.split()

        # Word-level hashing for stable embeddings
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % dim
            vector[idx] += 1.0

            # Bigram features
            for i in range(len(word) - 1):
                bigram = word[i : i + 2]
                h2 = int(hashlib.md5(bigram.encode()).hexdigest(), 16)
                idx2 = h2 % dim
                vector[idx2] += 0.5

        # L2 normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector


class RankingEngine:
    """
    Core ranking engine that computes personalized relevance scores.
    Uses cosine similarity between user context embeddings and candidate title embeddings.
    """

    def __init__(self, model, device: str = "cpu"):
        self.model = model
        self.device = device

    def compute_scores(
        self,
        user_id: str,
        context: Dict[str, Any],
        candidate_titles: List[str],
    ) -> List[float]:
        """
        Compute relevance scores for each candidate title given user context.
        Returns a list of scores (higher = more relevant).
        """
        # Build user query from context
        context_text = self._build_context_text(user_id, context)

        # Encode context and candidates
        all_texts = [context_text] + candidate_titles

        if hasattr(self.model, "encode"):
            embeddings = self.model.encode(all_texts)
        else:
            raise ValueError("Model does not support encode method")

        context_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]

        # Compute cosine similarity scores
        scores = []
        for candidate_emb in candidate_embeddings:
            similarity = self._cosine_similarity(context_embedding, candidate_emb)
            # Normalize to [0, 1]
            score = (similarity + 1.0) / 2.0
            scores.append(float(score))

        # Add user-specific personalization signal
        scores = self._apply_personalization(scores, user_id, context)

        return scores

    def _build_context_text(self, user_id: str, context: Dict[str, Any]) -> str:
        """Build a natural language query from the user context."""
        parts = [f"user:{user_id}"]
        for key, value in sorted(context.items()):
            parts.append(f"{key}:{value}")
        return " ".join(parts)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def _apply_personalization(
        self,
        scores: List[float],
        user_id: str,
        context: Dict[str, Any],
    ) -> List[float]:
        """Apply user-specific personalization adjustments to scores."""
        # Deterministic user-specific bias using hash
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        user_seed = user_hash % 10000 / 10000.0

        personalized = []
        for i, score in enumerate(scores):
            # Small deterministic perturbation per user+position
            perturbation = math.sin(user_seed * (i + 1) * math.pi) * 0.02
            personalized.append(max(0.0, min(1.0, score + perturbation)))

        return personalized
