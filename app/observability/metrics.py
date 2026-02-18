"""
Prometheus metrics for monitoring the LLM Ranking Service.
Tracks latency percentiles, request rates, error rates, and batch performance.
"""

from prometheus_client import (
    Histogram,
    Counter,
    Gauge,
    Summary,
)


class PrometheusMetrics:
    """Centralized Prometheus metrics for the ranking service."""

    def __init__(self):
        # Request latency histogram with percentile buckets
        self.request_latency = Histogram(
            "ranking_request_latency_ms",
            "Request latency in milliseconds",
            buckets=[5, 10, 25, 50, 75, 100, 120, 150, 200, 500, 1000],
        )

        # Request counter by status
        self.request_count = Counter(
            "ranking_requests_total",
            "Total number of ranking requests",
            ["status"],
        )

        # Active requests gauge
        self.active_requests = Gauge(
            "ranking_active_requests",
            "Number of currently active requests",
        )

        # Batch metrics
        self.batch_size = Histogram(
            "ranking_batch_size",
            "Number of requests per batch",
            buckets=[1, 2, 4, 8, 16, 32, 64],
        )

        self.batch_latency = Histogram(
            "ranking_batch_latency_ms",
            "Batch processing latency in milliseconds",
            buckets=[5, 10, 20, 50, 100, 200],
        )

        # Model metrics
        self.model_inference_time = Histogram(
            "ranking_model_inference_ms",
            "Model inference time in milliseconds",
            buckets=[1, 5, 10, 25, 50, 100],
        )

        self.model_version_requests = Counter(
            "ranking_model_version_requests_total",
            "Requests per model version",
            ["version"],
        )

        # Queue depth
        self.queue_depth = Gauge(
            "ranking_queue_depth",
            "Number of requests waiting in the batch queue",
        )

        # Error metrics
        self.errors = Counter(
            "ranking_errors_total",
            "Total errors by type",
            ["error_type"],
        )

        # Circuit breaker state
        self.circuit_breaker_state = Gauge(
            "ranking_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)",
        )

    def record_request_latency(self, latency_ms: float):
        self.request_latency.observe(latency_ms)

    def increment_request_count(self, status: str = "success"):
        self.request_count.labels(status=status).inc()

    def record_batch_size(self, size: int):
        self.batch_size.observe(size)

    def record_batch_latency(self, latency_ms: float):
        self.batch_latency.observe(latency_ms)

    def record_error(self, error_type: str):
        self.errors.labels(error_type=error_type).inc()
