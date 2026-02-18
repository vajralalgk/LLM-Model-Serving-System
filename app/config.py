"""
Centralized configuration management using pydantic-settings.
All settings are loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "llm-ranking-service"
    app_version: str = "1.0.0"
    app_env: str = "production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_workers: int = 4
    debug: bool = False

    # Model
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_version: str = "v1"
    model_cache_dir: str = "/app/models"
    model_device: str = "cpu"
    max_batch_size: int = 32
    batch_timeout_ms: int = 15

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    api_key: str = "change-me-in-production"
    rate_limit: str = "100/minute"

    # Redis
    redis_url: Optional[str] = None

    # Observability
    log_level: str = "INFO"
    enable_tracing: bool = False
    otlp_endpoint: str = "http://localhost:4317"
    prometheus_enabled: bool = True

    # Resilience
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    request_timeout_seconds: float = 5.0
    max_retries: int = 3

    # Request Limits
    max_request_size_bytes: int = 1_048_576  # 1MB
    max_candidate_titles: int = 500

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
