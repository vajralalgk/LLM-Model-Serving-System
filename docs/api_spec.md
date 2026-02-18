# API Specification

**Service:** LLM Ranking Service
**Author:** Gopi Krishna Vajrala
**Base URL:** `https://ranking-api.example.com`

---

## POST /rank

Rank candidate content titles based on user context and preferences.

### Request

```json
{
  "user_id": "string (required, 1-256 chars)",
  "context": {
    "location": "string",
    "device": "string",
    "time_of_day": "string",
    "...": "any additional context"
  },
  "candidate_titles": ["string (required, 1-500 items, each max 1000 chars)"],
  "model_version": "string (optional, e.g., 'v1', 'v2')"
}
```

### Response (200 OK)

```json
{
  "ranked_titles": ["string"],
  "ranked_items": [
    {
      "title": "string",
      "rank": 1,
      "score": 0.953421
    }
  ],
  "model_version": "v1",
  "request_id": "uuid",
  "latency_ms": 23.45,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Responses

| Code | Description |
|------|-------------|
| 400 | Invalid request body |
| 401 | Missing or invalid authentication |
| 413 | Request body too large (>1MB) |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (circuit breaker open) |
| 504 | Request timeout |

### Authentication

**API Key:**
```
X-API-Key: your-api-key
```

**JWT Bearer Token:**
```
Authorization: Bearer <jwt_token>
```

---

## GET /health

Liveness probe for Kubernetes.

**Response:** `{"status": "healthy"}`

## GET /ready

Readiness probe - confirms model is loaded.

**Response:** `{"status": "ready", "model_version": "v1", "batcher_queue_size": 0}`

## GET /version

Service and model version information.

## GET /metrics

Prometheus-compatible metrics endpoint.
