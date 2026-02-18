"""
Locust load testing script for the LLM Ranking Service.
Author: Gopi Krishna Vajrala

Usage:
    locust -f load_tests/locustfile.py --host http://localhost:8000

Targets:
    - p95 latency < 120ms
    - 5,000 RPS sustained
    - 0% error rate under normal load
"""

import random
import string

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Sample content titles for realistic load testing
SAMPLE_TITLES = [
    "Breaking News: AI Revolution in Healthcare",
    "Top 10 Machine Learning Frameworks in 2025",
    "How to Build Scalable Microservices",
    "Climate Change: Latest Scientific Findings",
    "Stock Market Analysis: Tech Sector Surge",
    "New Breakthrough in Quantum Computing",
    "Guide to Cloud-Native Architecture",
    "Sports Update: Championship Finals Results",
    "Travel Guide: Hidden Gems in Southeast Asia",
    "Healthy Recipes for Busy Professionals",
    "Understanding Large Language Models",
    "Cybersecurity Best Practices for Enterprises",
    "Remote Work: Productivity Tips and Tools",
    "Electric Vehicles: Market Trends 2025",
    "Space Exploration: Mars Mission Updates",
    "Blockchain Beyond Cryptocurrency",
    "Mental Health Awareness in the Workplace",
    "5G Technology: Impact on IoT",
    "Sustainable Fashion: Eco-Friendly Brands",
    "Artificial Intelligence in Education",
]

CONTEXTS = [
    {"location": "US", "device": "mobile", "time_of_day": "morning"},
    {"location": "UK", "device": "desktop", "time_of_day": "afternoon"},
    {"location": "IN", "device": "tablet", "time_of_day": "evening"},
    {"location": "JP", "device": "mobile", "time_of_day": "night"},
    {"location": "DE", "device": "desktop", "time_of_day": "morning"},
]

API_KEY = "test-api-key"


class RankingServiceUser(HttpUser):
    """Simulates a user making ranking requests."""

    wait_time = between(0.01, 0.05)  # High throughput simulation

    def on_start(self):
        self.user_id = f"user_{random.randint(1, 100000)}"

    @task(10)
    def rank_titles(self):
        """Standard ranking request with random candidates."""
        num_titles = random.randint(3, 15)
        titles = random.sample(SAMPLE_TITLES, min(num_titles, len(SAMPLE_TITLES)))
        context = random.choice(CONTEXTS)

        self.client.post(
            "/rank",
            json={
                "user_id": self.user_id,
                "context": context,
                "candidate_titles": titles,
            },
            headers={"X-API-Key": API_KEY},
            name="/rank",
        )

    @task(2)
    def rank_large_batch(self):
        """Ranking request with many candidates (stress test)."""
        titles = SAMPLE_TITLES.copy()
        # Add generated titles for larger batch
        for i in range(30):
            titles.append(f"Generated Article Title #{i}: {''.join(random.choices(string.ascii_lowercase, k=20))}")

        self.client.post(
            "/rank",
            json={
                "user_id": self.user_id,
                "context": random.choice(CONTEXTS),
                "candidate_titles": titles,
            },
            headers={"X-API-Key": API_KEY},
            name="/rank [large batch]",
        )

    @task(1)
    def health_check(self):
        """Periodic health check."""
        self.client.get("/health", name="/health")

    @task(1)
    def readiness_check(self):
        """Periodic readiness check."""
        self.client.get("/ready", name="/ready")


class HighThroughputUser(HttpUser):
    """High-throughput user for stress testing (5000 RPS target)."""

    wait_time = between(0.001, 0.01)

    def on_start(self):
        self.user_id = f"stress_user_{random.randint(1, 1000000)}"

    @task
    def rank_minimal(self):
        """Minimal ranking request for maximum throughput."""
        self.client.post(
            "/rank",
            json={
                "user_id": self.user_id,
                "context": {},
                "candidate_titles": random.sample(SAMPLE_TITLES, 5),
            },
            headers={"X-API-Key": API_KEY},
            name="/rank [stress]",
        )
