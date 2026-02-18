"""
Tests for the model server and ranking engine.
"""

import pytest
import numpy as np

from app.core.ranker import LightweightRanker, RankingEngine


class TestLightweightRanker:
    """Tests for the fallback lightweight ranker."""

    def test_encode_returns_embeddings(self):
        ranker = LightweightRanker()
        texts = ["Hello world", "Test text", "Another example"]
        embeddings = ranker.encode(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3
        assert embeddings.shape[1] == 128

    def test_embeddings_are_normalized(self):
        ranker = LightweightRanker()
        embeddings = ranker.encode(["Test text"])

        norm = np.linalg.norm(embeddings[0])
        assert abs(norm - 1.0) < 0.01 or norm == 0.0

    def test_similar_texts_have_similar_embeddings(self):
        ranker = LightweightRanker()
        embeddings = ranker.encode([
            "machine learning model",
            "machine learning algorithm",
            "cooking recipe pasta",
        ])

        # Similar texts should have higher cosine similarity
        sim_12 = np.dot(embeddings[0], embeddings[1])
        sim_13 = np.dot(embeddings[0], embeddings[2])
        assert sim_12 > sim_13

    def test_empty_text(self):
        ranker = LightweightRanker()
        embeddings = ranker.encode([""])
        assert embeddings.shape == (1, 128)


class TestRankingEngine:
    """Tests for the ranking engine."""

    def test_compute_scores(self):
        ranker = LightweightRanker()
        engine = RankingEngine(model=ranker)

        scores = engine.compute_scores(
            user_id="user_123",
            context={"location": "US"},
            candidate_titles=["Title A", "Title B", "Title C"],
        )

        assert len(scores) == 3
        assert all(0.0 <= s <= 1.0 for s in scores)

    def test_personalization_differs_by_user(self):
        ranker = LightweightRanker()
        engine = RankingEngine(model=ranker)

        titles = ["News", "Sports", "Weather"]

        scores_user1 = engine.compute_scores("user_1", {}, titles)
        scores_user2 = engine.compute_scores("user_2", {}, titles)

        # Different users should get different rankings (personalization)
        assert scores_user1 != scores_user2

    def test_deterministic_scores(self):
        ranker = LightweightRanker()
        engine = RankingEngine(model=ranker)

        titles = ["A", "B", "C"]
        scores1 = engine.compute_scores("user_1", {"ctx": "val"}, titles)
        scores2 = engine.compute_scores("user_1", {"ctx": "val"}, titles)

        # Same input should produce same output
        assert scores1 == scores2
