"""
Word Document Generator for LLM Model Serving System
Author: Gopi Krishna Vajrala

Generates a comprehensive project documentation in Word format.

Usage: python scripts/generate_doc.py
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
import os


def set_heading_style(doc):
    """Configure custom heading styles."""
    style = doc.styles["Heading 1"]
    font = style.font
    font.size = Pt(24)
    font.color.rgb = RGBColor(0x1B, 0x2A, 0x4A)
    font.bold = True

    style = doc.styles["Heading 2"]
    font = style.font
    font.size = Pt(18)
    font.color.rgb = RGBColor(0x2E, 0x86, 0xDE)
    font.bold = True

    style = doc.styles["Heading 3"]
    font = style.font
    font.size = Pt(14)
    font.color.rgb = RGBColor(0x34, 0x49, 0x5E)
    font.bold = True


def add_table(doc, headers, rows):
    """Add a formatted table to the document."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)

    # Data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_data in enumerate(row_data):
            table.rows[row_idx + 1].cells[col_idx].text = str(cell_data)

    doc.add_paragraph()


def create_document():
    doc = Document()
    set_heading_style(doc)

    # ===== TITLE PAGE =====
    doc.add_paragraph()
    doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Real-Time LLM Model Serving System")
    run.font.size = Pt(32)
    run.font.color.rgb = RGBColor(0x1B, 0x2A, 0x4A)
    run.bold = True

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Production-Grade Personalization Ranking Engine")
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x2E, 0x86, 0xDE)

    doc.add_paragraph()

    # Accent line
    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run("_" * 60)
    run.font.color.rgb = RGBColor(0x2E, 0x86, 0xDE)

    doc.add_paragraph()

    info_items = [
        ("Author:", "Gopi Krishna Vajrala"),
        ("Version:", "1.0.0"),
        ("Date:", "2025"),
        ("Document Type:", "Technical Design Document"),
    ]

    for label, value in info_items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run1 = p.add_run(f"{label} ")
        run1.bold = True
        run1.font.size = Pt(12)
        run2 = p.add_run(value)
        run2.font.size = Pt(12)

    doc.add_page_break()

    # ===== TABLE OF CONTENTS =====
    doc.add_heading("Table of Contents", level=1)
    toc_items = [
        "1. Executive Summary",
        "2. Business Objective",
        "3. System Architecture",
        "4. Functional Requirements",
        "5. Performance Engineering",
        "6. Infrastructure Design",
        "7. Dynamic Batching",
        "8. Observability & Monitoring",
        "9. Reliability & Resilience",
        "10. Security & Governance",
        "11. Deployment Strategy",
        "12. Testing Strategy",
        "13. API Specification",
        "14. Technology Stack",
        "15. Project Structure",
        "16. Future Roadmap",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(4)

    doc.add_page_break()

    # ===== 1. EXECUTIVE SUMMARY =====
    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph(
        "This document describes the architecture and implementation of a production-grade, "
        "real-time personalization ranking system powered by Large Language Models (LLMs). "
        "The system is designed to serve user-specific ranked content with sub-120ms p95 latency, "
        "handle 5,000 requests per second, and achieve 99.99% availability in a Kubernetes-based "
        "distributed environment."
    )
    doc.add_paragraph(
        "The system leverages semantic embeddings from transformer models to compute personalized "
        "relevance scores for candidate content titles. A dynamic batching engine optimizes GPU "
        "utilization by combining multiple inference requests into single forward passes. "
        "Comprehensive resilience patterns (circuit breakers, retries, timeouts) ensure the system "
        "gracefully handles partial failures. The entire stack is containerized and deployable on "
        "any Kubernetes cluster with blue/green zero-downtime deployment support."
    )

    # ===== 2. BUSINESS OBJECTIVE =====
    doc.add_heading("2. Business Objective", level=1)
    doc.add_paragraph(
        "Build a production-grade, real-time personalization ranking system that:"
    )
    objectives = [
        "Serves user-specific ranked content in under 120ms p95 latency",
        "Handles 5,000 requests per second sustained throughput",
        "Achieves 99.99% availability (less than 52 minutes downtime per year)",
        "Supports model versioning with blue/green deployment",
        "Runs on Kubernetes with GPU-enabled node pools",
        "Provides full observability through Prometheus, Grafana, and OpenTelemetry",
    ]
    for obj in objectives:
        doc.add_paragraph(obj, style="List Bullet")

    # ===== 3. SYSTEM ARCHITECTURE =====
    doc.add_heading("3. System Architecture", level=1)

    doc.add_heading("3.1 High-Level Architecture", level=2)
    doc.add_paragraph(
        "The system follows a layered microservice architecture optimized for real-time ML inference:"
    )

    layers = [
        ("Client Layer", "Web applications, mobile apps, and internal services communicate via REST API."),
        ("Ingress Layer", "NGINX Ingress Controller handles TLS termination, rate limiting, and load balancing."),
        ("API Gateway", "FastAPI application with JWT authentication, rate limiting, and request validation."),
        ("Dynamic Batching", "Accumulates requests in a 10-20ms window and batches them for efficient GPU processing."),
        ("Model Serving", "Sentence-transformer models compute semantic embeddings and cosine similarity scores."),
        ("Resilience", "Circuit breakers, retries, and timeouts protect against cascading failures."),
        ("Observability", "Prometheus metrics, structured logging, and distributed tracing provide full visibility."),
    ]

    add_table(doc, ["Layer", "Description"], layers)

    doc.add_heading("3.2 Request Flow", level=2)
    flow_steps = [
        "Client sends POST /rank with user_id, context, and candidate_titles",
        "Request passes through Ingress (TLS, rate limit, load balance)",
        "JWT/API key authentication validates the caller",
        "Request size and schema validation ensures payload integrity",
        "Dynamic Batcher queues the request with an async Future",
        "Batcher collects requests for 10-20ms or until batch is full (max 32)",
        "Batch is sent to Model Server for vectorized inference",
        "All texts are encoded in a single forward pass (GPU efficient)",
        "Cosine similarity scores are computed between user context and candidates",
        "User-specific personalization adjustments are applied",
        "Results are de-batched and returned via individual Futures",
        "Client receives ranked titles with scores, model version, and latency info",
    ]
    for i, step in enumerate(flow_steps, 1):
        doc.add_paragraph(f"{i}. {step}")

    # ===== 4. FUNCTIONAL REQUIREMENTS =====
    doc.add_heading("4. Functional Requirements", level=1)

    doc.add_heading("4.1 API Endpoint", level=2)
    doc.add_paragraph("Primary endpoint: POST /rank")

    add_table(doc, ["Field", "Type", "Required", "Description"], [
        ("user_id", "string", "Yes", "Unique user identifier (1-256 chars)"),
        ("context", "object", "No", "User context for personalization"),
        ("candidate_titles", "string[]", "Yes", "Content titles to rank (1-500 items)"),
        ("model_version", "string", "No", "Specific model version to use"),
    ])

    doc.add_heading("4.2 Response Format", level=2)
    add_table(doc, ["Field", "Type", "Description"], [
        ("ranked_titles", "string[]", "Titles sorted by relevance (most relevant first)"),
        ("ranked_items", "object[]", "Detailed ranking with title, rank, and score"),
        ("model_version", "string", "Model version used for this request"),
        ("request_id", "string", "Unique request ID for tracing"),
        ("latency_ms", "float", "Server-side processing time in milliseconds"),
        ("timestamp", "datetime", "UTC timestamp of the response"),
    ])

    doc.add_heading("4.3 Model Versioning", level=2)
    doc.add_paragraph(
        "The system supports multiple model versions simultaneously. "
        "Clients can request a specific version or use the default active version. "
        "Model versions can be switched at runtime via the Model Registry without restart."
    )

    # ===== 5. PERFORMANCE ENGINEERING =====
    doc.add_heading("5. Performance Engineering", level=1)

    add_table(doc, ["Metric", "Target", "Implementation"], [
        ("p95 Latency", "< 120ms", "Dynamic batching, ORJson serialization, async I/O"),
        ("Throughput", "5,000 RPS", "Horizontal scaling, connection pooling, batch inference"),
        ("Availability", "99.99%", "3+ replicas, circuit breakers, graceful degradation"),
        ("Scale-up Time", "< 60s", "Aggressive HPA: 4 pods/min or 100%/min"),
        ("Scale-down Time", "5 min", "Conservative: 1 pod/min, 5min stabilization window"),
    ])

    doc.add_heading("5.1 Dynamic Batching", level=2)
    doc.add_paragraph(
        "The Dynamic Batcher is the key performance innovation. Instead of processing each "
        "request individually, it accumulates incoming requests in a configurable time window "
        "(10-20ms) and combines them into a single batch for GPU inference. This provides:"
    )
    benefits = [
        "3-5x throughput improvement by reducing GPU idle time",
        "Amortized model loading overhead across multiple requests",
        "Minimal latency impact (only 10-20ms of additional queuing time)",
        "Automatic de-batching delivers individual responses via async Futures",
    ]
    for b in benefits:
        doc.add_paragraph(b, style="List Bullet")

    # ===== 6. INFRASTRUCTURE DESIGN =====
    doc.add_heading("6. Infrastructure Design", level=1)

    doc.add_heading("6.1 Docker", level=2)
    doc.add_paragraph(
        "The application uses multi-stage Docker builds for minimal production images. "
        "A separate GPU-enabled Dockerfile (Dockerfile.gpu) is provided for NVIDIA CUDA support. "
        "All containers run as non-root users for security."
    )

    doc.add_heading("6.2 Kubernetes", level=2)
    add_table(doc, ["Resource", "Configuration"], [
        ("Namespace", "llm-serving (isolated)"),
        ("Deployment", "3 replicas, RollingUpdate strategy"),
        ("Service", "ClusterIP (internal)"),
        ("Ingress", "NGINX with TLS, rate limiting"),
        ("HPA", "3-20 replicas, CPU/Memory/RPS triggers"),
        ("ConfigMap", "Application configuration"),
        ("Secret", "JWT keys, API keys"),
        ("Probes", "Startup + Liveness + Readiness"),
    ])

    # ===== 7. DYNAMIC BATCHING =====
    doc.add_heading("7. Advanced Model Serving - Dynamic Batching", level=1)
    doc.add_paragraph(
        "The Dynamic Batching Engine is the most critical performance component. "
        "It transforms individual request processing into batch processing, enabling "
        "efficient GPU utilization."
    )

    doc.add_heading("7.1 How It Works", level=2)
    steps = [
        "Request arrives at POST /rank and is submitted to the batcher with an asyncio.Future",
        "Batcher maintains an asyncio.Queue for incoming requests",
        "A background task continuously collects items from the queue",
        "Collection stops when: batch reaches max_size (32) OR timeout expires (15ms)",
        "Collected batch is sent to ModelServer.predict_batch() for vectorized inference",
        "All texts (contexts + candidates) are encoded in a single model.encode() call",
        "Cosine similarity scores are computed for each request",
        "Results are de-batched: each request's Future is resolved with its specific scores",
        "Original callers receive their results via awaited Futures",
    ]
    for i, step in enumerate(steps, 1):
        doc.add_paragraph(f"{i}. {step}")

    doc.add_heading("7.2 Configuration", level=2)
    add_table(doc, ["Parameter", "Default", "Description"], [
        ("max_batch_size", "32", "Maximum requests per batch"),
        ("batch_timeout_ms", "15", "Maximum wait time before processing"),
        ("queue_type", "asyncio.Queue", "Unbounded async queue"),
    ])

    # ===== 8. OBSERVABILITY =====
    doc.add_heading("8. Observability & Monitoring", level=1)

    doc.add_heading("8.1 Prometheus Metrics", level=2)
    add_table(doc, ["Metric", "Type", "Description"], [
        ("ranking_request_latency_ms", "Histogram", "Request latency distribution"),
        ("ranking_requests_total", "Counter", "Total requests by status"),
        ("ranking_active_requests", "Gauge", "Currently active requests"),
        ("ranking_batch_size", "Histogram", "Batch size distribution"),
        ("ranking_batch_latency_ms", "Histogram", "Batch processing latency"),
        ("ranking_queue_depth", "Gauge", "Batcher queue depth"),
        ("ranking_errors_total", "Counter", "Errors by type"),
        ("ranking_circuit_breaker_state", "Gauge", "Circuit breaker state (0/1/2)"),
    ])

    doc.add_heading("8.2 Structured Logging", level=2)
    doc.add_paragraph(
        "All application logs are emitted in JSON format using structlog. "
        "Each log entry includes timestamp, log level, component name, and contextual fields. "
        "Request correlation IDs enable end-to-end tracing across log entries."
    )

    doc.add_heading("8.3 Distributed Tracing", level=2)
    doc.add_paragraph(
        "OpenTelemetry instrumentation provides distributed tracing across the entire "
        "request lifecycle. Traces are exported via OTLP to Jaeger or any compatible backend."
    )

    # ===== 9. RESILIENCE =====
    doc.add_heading("9. Reliability & Resilience", level=1)

    doc.add_heading("9.1 Circuit Breaker", level=2)
    doc.add_paragraph(
        "The circuit breaker prevents cascading failures by monitoring failure rates "
        "and short-circuiting requests when a threshold is exceeded."
    )
    add_table(doc, ["State", "Behavior", "Transition"], [
        ("CLOSED", "Normal operation - requests flow through", "Opens after 5 consecutive failures"),
        ("OPEN", "Fast-fail - rejects immediately", "Transitions to HALF_OPEN after 30s"),
        ("HALF_OPEN", "Testing - allows limited requests", "Closes after 3 successes, reopens on failure"),
    ])

    doc.add_heading("9.2 Retry Mechanism", level=2)
    doc.add_paragraph(
        "Exponential backoff with jitter handles transient failures. "
        "Maximum 3 retries with delays: ~100ms, ~200ms, ~400ms (with random jitter to prevent thundering herd)."
    )

    doc.add_heading("9.3 Timeout Enforcement", level=2)
    doc.add_paragraph(
        "All inference operations are wrapped with configurable timeouts (default: 5 seconds). "
        "This prevents requests from hanging indefinitely and ensures SLA compliance."
    )

    doc.add_heading("9.4 Graceful Shutdown", level=2)
    doc.add_paragraph(
        "On SIGTERM, the application: (1) stops accepting new requests, "
        "(2) drains the batcher queue, (3) completes in-flight requests, "
        "(4) cleanly shuts down model server resources. "
        "Kubernetes terminationGracePeriodSeconds is set to 30s."
    )

    # ===== 10. SECURITY =====
    doc.add_heading("10. Security & Governance", level=1)

    add_table(doc, ["Control", "Implementation", "Details"], [
        ("Authentication", "JWT + API Key", "Bearer tokens or X-API-Key header"),
        ("Rate Limiting", "SlowAPI", "100 req/min per IP (configurable)"),
        ("Input Validation", "Pydantic v2", "Strict schema validation on all inputs"),
        ("Size Limits", "Middleware", "1MB max request body"),
        ("Container Security", "Non-root user", "appuser with minimal permissions"),
        ("TLS/SSL", "Ingress", "NGINX handles TLS termination"),
        ("Secrets", "K8s Secrets", "JWT keys and API keys stored securely"),
        ("Audit Logging", "Structured logs", "All requests logged with correlation IDs"),
    ])

    # ===== 11. DEPLOYMENT =====
    doc.add_heading("11. Deployment Strategy", level=1)

    doc.add_heading("11.1 Blue/Green Deployment", level=2)
    doc.add_paragraph(
        "Two identical Kubernetes Deployments (blue and green) run simultaneously. "
        "A Kubernetes Service selector determines which slot receives live traffic. "
        "Deployments are switched by patching the Service selector, enabling instant traffic cutover "
        "and zero-downtime model updates. Rollback is achieved by patching back to the previous slot."
    )

    doc.add_heading("11.2 Auto-Scaling", level=2)
    doc.add_paragraph(
        "Horizontal Pod Autoscaler (HPA) scales based on CPU utilization (70%), "
        "memory utilization (80%), and custom RPS metrics. Scale-up is aggressive "
        "(4 pods per minute) while scale-down is conservative (1 pod per minute with 5-minute stabilization)."
    )

    # ===== 12. TESTING =====
    doc.add_heading("12. Testing Strategy", level=1)

    add_table(doc, ["Test Type", "Tool", "Scope"], [
        ("Unit Tests", "pytest", "Individual components, schemas, engines"),
        ("Integration Tests", "pytest + httpx", "Full API request pipeline"),
        ("Load Tests", "Locust", "Throughput and latency under sustained load"),
        ("Performance Tests", "k6", "p95/p99 latency thresholds validation"),
        ("Chaos Tests", "Custom scripts", "Pod kill, resource pressure, network partition"),
    ])

    # ===== 13. API SPEC =====
    doc.add_heading("13. API Specification", level=1)
    doc.add_paragraph("See docs/api_spec.md for full OpenAPI specification.")

    add_table(doc, ["Endpoint", "Method", "Auth", "Description"], [
        ("/rank", "POST", "Required", "Rank candidate titles for a user"),
        ("/health", "GET", "None", "Liveness probe"),
        ("/ready", "GET", "None", "Readiness probe"),
        ("/version", "GET", "None", "Service version info"),
        ("/metrics", "GET", "None", "Prometheus metrics"),
    ])

    # ===== 14. TECH STACK =====
    doc.add_heading("14. Technology Stack", level=1)

    add_table(doc, ["Category", "Technology", "Purpose"], [
        ("Framework", "FastAPI + Uvicorn", "High-performance async web framework"),
        ("ML", "PyTorch + Sentence-Transformers", "Semantic embedding and inference"),
        ("Auth", "python-jose (JWT)", "Token-based authentication"),
        ("Rate Limiting", "SlowAPI", "Request rate limiting"),
        ("Metrics", "prometheus-client", "Prometheus-compatible metrics"),
        ("Logging", "structlog", "Structured JSON logging"),
        ("Tracing", "OpenTelemetry", "Distributed tracing"),
        ("Container", "Docker", "Application containerization"),
        ("Orchestration", "Kubernetes", "Container orchestration"),
        ("Load Testing", "Locust + k6", "Performance validation"),
    ])

    # ===== 15. PROJECT STRUCTURE =====
    doc.add_heading("15. Project Structure", level=1)

    structure = [
        ("app/main.py", "FastAPI application entry point and lifecycle management"),
        ("app/config.py", "Centralized configuration via environment variables"),
        ("app/api/routes/rank.py", "POST /rank endpoint implementation"),
        ("app/api/middleware/auth.py", "JWT and API key authentication"),
        ("app/core/dynamic_batcher.py", "Dynamic batching engine"),
        ("app/core/model_server.py", "Model inference orchestrator"),
        ("app/core/model_registry.py", "Model version management"),
        ("app/core/ranker.py", "Ranking algorithms (full + lightweight)"),
        ("app/resilience/", "Circuit breaker, retry, timeout patterns"),
        ("app/observability/", "Metrics, logging, tracing"),
        ("k8s/", "Kubernetes deployment manifests"),
        ("tests/", "Unit and integration tests"),
        ("load_tests/", "Locust and k6 load test scripts"),
        ("scripts/", "Deploy, rollback, and chaos test scripts"),
    ]
    add_table(doc, ["Path", "Description"], structure)

    # ===== 16. ROADMAP =====
    doc.add_heading("16. Future Roadmap", level=1)

    add_table(doc, ["Phase", "Feature", "Timeline"], [
        ("Phase 2", "Multi-region deployment", "Q2 2025"),
        ("Phase 2", "Canary deployment with A/B testing", "Q2 2025"),
        ("Phase 2", "Token streaming support", "Q2 2025"),
        ("Phase 3", "Cost-aware model routing", "Q3 2025"),
        ("Phase 3", "Shadow traffic testing", "Q3 2025"),
        ("Phase 3", "Online learning from feedback", "Q3 2025"),
        ("Phase 4", "Multi-cloud deployment", "Q4 2025"),
        ("Phase 4", "Edge deployment", "Q4 2025"),
        ("Phase 4", "50K+ RPS with GPU cluster", "Q1 2026"),
    ])

    doc.add_paragraph()
    doc.add_paragraph()

    # Footer
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("Document prepared by Gopi Krishna Vajrala")
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x95, 0x95, 0x95)

    # Save
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "LLM_Ranking_Service_Documentation.docx")
    doc.save(output_path)
    print(f"Document saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    create_document()
