# Architecture Design Document

**Project:** LLM Model Serving System - Real-Time Personalization Ranking Engine
**Author:** Gopi Krishna Vajrala
**Version:** 1.0.0

---

## 1. System Architecture

### High-Level Architecture

The system follows a layered microservice architecture optimized for real-time inference:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│           (Web Apps, Mobile Apps, Internal Services)             │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ingress / Load Balancer                     │
│              (NGINX Ingress Controller + TLS)                    │
│              Rate Limiting | SSL Termination                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                            │
│  ┌──────────┐  ┌───────────────┐  ┌─────────────────────────┐  │
│  │   Auth    │  │  Rate Limiter │  │  Request Validator      │  │
│  │  (JWT)    │  │  (SlowAPI)    │  │  (Size + Schema)        │  │
│  └──────────┘  └───────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Dynamic Batching Layer                         │
│                                                                   │
│  Incoming requests are queued and combined into optimal batches  │
│  Window: 10-20ms | Max batch: 32 | Async futures for response   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Model Serving Layer                            │
│                                                                   │
│  ┌──────────────────┐  ┌───────────────────────────────────┐   │
│  │  Model Registry   │  │       Ranking Engine              │   │
│  │  (Version Mgmt)   │  │  Semantic Similarity + Personalize│   │
│  │  Blue/Green Ready │  │  Cosine Sim + User Signal          │   │
│  └──────────────────┘  └───────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Resilience Layer                                │
│  ┌────────────────┐  ┌──────────┐  ┌───────────────────────┐   │
│  │ Circuit Breaker │  │  Retry   │  │  Timeout Enforcement  │   │
│  │ (3 states)      │  │ (Exp BO) │  │  (Configurable)       │   │
│  └────────────────┘  └──────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow for POST /rank

1. Client sends POST /rank with user_id, context, candidate_titles
2. Request passes through auth middleware (JWT/API key validation)
3. Rate limiter checks request budget
4. Request size validator ensures payload is within limits
5. Request is submitted to the Dynamic Batcher with an async Future
6. Batcher accumulates requests for 10-20ms or until batch is full
7. Batch is sent to Model Server for inference
8. Model Server encodes all texts in a single forward pass (GPU efficient)
9. Cosine similarity scores are computed
10. User-specific personalization is applied
11. Results are de-batched and returned via Futures
12. Response is serialized and returned to client

## 2. Component Design

### Dynamic Batching Engine
- **Purpose:** Maximize GPU utilization by combining multiple requests
- **Window:** Configurable 10-20ms collection window
- **Max Batch:** 32 requests (configurable)
- **Mechanism:** asyncio Queue + Future-based response delivery
- **Benefit:** 3-5x throughput improvement with minimal latency impact

### Model Registry
- **Purpose:** Manage multiple model versions simultaneously
- **Supports:** Blue/green deployment, canary routing
- **Hot Swap:** Switch active version without restart
- **Fallback:** Lightweight ranker when full models unavailable

### Circuit Breaker
- **States:** CLOSED → OPEN → HALF_OPEN → CLOSED
- **Threshold:** 5 consecutive failures triggers OPEN
- **Recovery:** 30s timeout before HALF_OPEN testing
- **Benefit:** Prevents cascade failures, fast-fails bad requests

## 3. Deployment Strategy

### Blue/Green Deployment
- Two identical deployments (blue + green) in Kubernetes
- Traffic switched instantly via Service selector patch
- Zero downtime during model updates
- Instant rollback capability

### Auto-Scaling
- HPA based on CPU (70%), Memory (80%), and custom RPS metrics
- Scale up: aggressive (4 pods/min or 100%/min)
- Scale down: conservative (1 pod/min, 5min stabilization)
- Min 3 replicas, Max 20 replicas

## 4. Observability

### Metrics (Prometheus)
- Request latency: p50, p95, p99
- Request rate (RPS) by status
- Error rate by type
- Batch size distribution
- Queue depth
- Circuit breaker state
- Model version traffic split

### Logging (Structured JSON)
- All logs in JSON format via structlog
- Request correlation IDs
- Performance timing in every log entry

### Tracing (OpenTelemetry)
- End-to-end distributed tracing
- Span for each processing stage
- Integration with Jaeger/Zipkin
