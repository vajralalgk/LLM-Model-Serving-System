# =============================================================================
# Makefile for LLM Ranking Service
# Author: Gopi Krishna Vajrala
# =============================================================================

.PHONY: help install run test lint build push deploy clean load-test

APP_NAME := llm-ranking-service
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
DOCKER_REGISTRY ?= ghcr.io/your-org

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run development server
	APP_ENV=development uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run unit tests
	pytest tests/ -v --cov=app --cov-report=term-missing

test-ci: ## Run tests for CI (with JUnit output)
	pytest tests/ -v --cov=app --cov-report=xml --junitxml=test-results.xml

lint: ## Run linters
	ruff check app/ tests/
	mypy app/ --ignore-missing-imports

format: ## Format code
	ruff format app/ tests/

build: ## Build Docker image
	docker build -t $(APP_NAME):$(VERSION) -t $(APP_NAME):latest .

build-gpu: ## Build GPU Docker image
	docker build -f Dockerfile.gpu -t $(APP_NAME)-gpu:$(VERSION) -t $(APP_NAME)-gpu:latest .

push: build ## Push Docker image to registry
	docker tag $(APP_NAME):$(VERSION) $(DOCKER_REGISTRY)/$(APP_NAME):$(VERSION)
	docker push $(DOCKER_REGISTRY)/$(APP_NAME):$(VERSION)

up: ## Start local stack with Docker Compose
	docker-compose up -d --build

down: ## Stop local stack
	docker-compose down -v

deploy-blue: ## Deploy blue slot
	./scripts/deploy.sh blue $(VERSION)

deploy-green: ## Deploy green slot
	./scripts/deploy.sh green $(VERSION)

rollback: ## Rollback to blue slot
	./scripts/rollback.sh blue

load-test: ## Run Locust load test
	locust -f load_tests/locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 60s

load-test-k6: ## Run k6 load test
	k6 run load_tests/k6_test.js

chaos-test: ## Run chaos tests
	./scripts/chaos_test.sh

clean: ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov test-results.xml coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	docker-compose down -v --rmi local 2>/dev/null || true
