# LLM Model Serving System - Real-Time Personalization Ranking Engine

**Author: Gopi Krishna Vajrala**

A production-grade, real-time personalization ranking system powered by Large Language Models (LLMs). Designed for sub-120ms p95 latency, 5,000+ RPS throughput, and 99.99% availability on Kubernetes.

---

## Architecture Overview

```
                    ┌──────────────────────────────────────────────────┐
                    │                  Kubernetes Cluster               │
                    │                                                    │
  Client ──────►   │  ┌─────────┐    ┌──────────────────────────┐     │
  POST /rank       │  │ Ingress │───►│   Ranking Service (Pods) │     │
                    │  │ (nginx) │    │  ┌────────────────────┐  │     │
                    │  └─────────┘    │  │   FastAPI + Auth   │  │     │
                    │                  │  ├────────────────────┤  │     │
                    │                  │  │  Dynamic Batcher   │  │     │
                    │                  │  │  (10-20ms window)  │  │     │
                    │                  │  ├────────────────────┤  │     │
                    │                  │  │   Model Server     │  │     │
                    │                  │  │  (LLM Inference)   │  │     │
                    │                  │  ├────────────────────┤  │     │
                    │                  │  │  Circuit Breaker   │  │     │
                    │                  │  │  + Rate Limiter    │  │     │
                    │                  │  └────────────────────┘  │     │
                    │                  └──────────────────────────┘     │
                    │                         │                          │
                    │              ┌──────────┼──────────┐             │
                    │              ▼          ▼          ▼             │
                    │         Prometheus   Grafana    Jaeger           │
                    │         (Metrics)  (Dashboards) (Tracing)       │
                    └──────────────────────────────────────────────────┘
```

## Features

| Category | Feature | Status |
|----------|---------|--------|
| **API** | POST /rank endpoint | ✅ |
| **API** | Model versioning (v1, v2...) | ✅ |
| **API** | Blue/Green zero-downtime deploy | ✅ |
| **Performance** | p95 latency < 120ms | ✅ |
| **Performance** | 5,000 RPS sustained | ✅ |
| **Performance** | Dynamic batching (10-20ms) | ✅ |
| **Performance** | Horizontal auto-scaling | ✅ |
| **Infra** | Docker containerized | ✅ |
| **Infra** | Kubernetes deployment | ✅ |
| **Infra** | GPU-enabled support | ✅ |
| **Infra** | HPA auto-scaling | ✅ |
| **Observability** | Prometheus metrics | ✅ |
| **Observability** | p50/p95/p99 latency tracking | ✅ |
| **Observability** | Grafana dashboards | ✅ |
| **Observability** | Structured JSON logging | ✅ |
| **Observability** | OpenTelemetry tracing | ✅ |
| **Resilience** | Circuit breaker | ✅ |
| **Resilience** | Retry with exponential backoff | ✅ |
| **Resilience** | Timeout enforcement | ✅ |
| **Resilience** | Graceful shutdown | ✅ |
| **Security** | JWT authentication | ✅ |
| **Security** | API key auth | ✅ |
| **Security** | Rate limiting | ✅ |
| **Security** | Input validation | ✅ |
| **Security** | Request size limits | ✅ |
| **Testing** | Unit tests | ✅ |
| **Testing** | Load tests (Locust + k6) | ✅ |
| **Testing** | Chaos testing | ✅ |

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Run development server
make run

# Run tests
make test
```

### Docker

```bash
# Build and start full stack
make up

# Stop
make down
```

### Kubernetes Deployment

```bash
# Deploy blue slot
make deploy-blue

# Switch to green (zero downtime)
make deploy-green

# Rollback
make rollback
```

## API Usage

### POST /rank

```bash
curl -X POST http://localhost:8000/rank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_id": "user_12345",
    "context": {
      "location": "US",
      "device": "mobile",
      "time_of_day": "morning"
    },
    "candidate_titles": [
      "Breaking News: AI Advances",
      "Sports Update: Championship",
      "Weather Forecast: Sunny Week"
    ]
  }'
```

**Response:**
```json
{
  "ranked_titles": [
    "Breaking News: AI Advances",
    "Weather Forecast: Sunny Week",
    "Sports Update: Championship"
  ],
  "ranked_items": [
    {"title": "Breaking News: AI Advances", "rank": 1, "score": 0.953421},
    {"title": "Weather Forecast: Sunny Week", "rank": 2, "score": 0.871234},
    {"title": "Sports Update: Championship", "rank": 3, "score": 0.756891}
  ],
  "model_version": "v1",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "latency_ms": 23.45,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Load Testing

```bash
# Locust (web UI at http://localhost:8089)
make load-test

# k6 (CLI-based)
make load-test-k6
```

## Project Structure

```
LLM-Model-Serving-System/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Centralized configuration
│   ├── api/
│   │   ├── routes/
│   │   │   ├── rank.py             # POST /rank endpoint
│   │   │   ├── health.py           # Liveness & readiness probes
│   │   │   └── metrics.py          # Prometheus metrics endpoint
│   │   ├── middleware/
│   │   │   ├── auth.py             # JWT & API key authentication
│   │   │   ├── rate_limiter.py     # Rate limiting
│   │   │   └── request_validator.py # Request size validation
│   │   └── schemas/
│   │       └── rank.py             # Pydantic request/response models
│   ├── core/
│   │   ├── model_server.py         # Model inference orchestrator
│   │   ├── dynamic_batcher.py      # Dynamic batching engine
│   │   ├── model_registry.py       # Model version management
│   │   └── ranker.py               # Ranking algorithms
│   ├── resilience/
│   │   ├── circuit_breaker.py      # Circuit breaker pattern
│   │   ├── retry.py                # Retry with exponential backoff
│   │   └── timeout.py              # Timeout enforcement
│   └── observability/
│       ├── logging.py              # Structured JSON logging
│       ├── metrics.py              # Prometheus metrics
│       └── tracing.py              # OpenTelemetry tracing
├── k8s/                            # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── blue-green/                 # Blue/Green deployment configs
│   └── monitoring/                 # Prometheus & Grafana configs
├── tests/                          # Unit & integration tests
├── load_tests/                     # Locust & k6 load tests
├── scripts/                        # Deploy, rollback, chaos scripts
├── Dockerfile                      # CPU production image
├── Dockerfile.gpu                  # GPU-enabled image
├── docker-compose.yml              # Local development stack
└── Makefile                        # Build automation
```

## License

MIT License - Gopi Krishna Vajrala
