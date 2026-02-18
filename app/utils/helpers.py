"""
Utility functions for the LLM Ranking Service.
"""

import time
import uuid
from typing import Any
from datetime import datetime


def generate_request_id() -> str:
    """Generate a unique request identifier."""
    return str(uuid.uuid4())


def current_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.perf_counter()
        return (end - self.start_time) * 1000
