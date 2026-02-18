#!/usr/bin/env bash
# =============================================================================
# Deployment script for LLM Ranking Service
# Author: Gopi Krishna Vajrala
# Usage: ./scripts/deploy.sh [blue|green] [image_tag]
# =============================================================================

set -euo pipefail

NAMESPACE="llm-serving"
SLOT="${1:-blue}"
IMAGE_TAG="${2:-latest}"
IMAGE_NAME="llm-ranking-service:${IMAGE_TAG}"

echo "================================================"
echo "  LLM Ranking Service - Deployment"
echo "  Slot: ${SLOT} | Image: ${IMAGE_NAME}"
echo "================================================"

# 1. Create namespace if not exists
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# 2. Apply configs
echo "[1/5] Applying configuration..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Deploy the target slot
echo "[2/5] Deploying ${SLOT} slot..."
kubectl apply -f "k8s/blue-green/deployment-${SLOT}.yaml"

# 4. Wait for rollout
echo "[3/5] Waiting for rollout..."
kubectl rollout status "deployment/ranking-service-${SLOT}" \
  -n "${NAMESPACE}" --timeout=300s

# 5. Run readiness check
echo "[4/5] Verifying readiness..."
POD=$(kubectl get pods -n "${NAMESPACE}" \
  -l "app=ranking-service,slot=${SLOT}" \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec "${POD}" -n "${NAMESPACE}" -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/ready').read())"

# 6. Switch traffic
echo "[5/5] Switching traffic to ${SLOT}..."
kubectl patch service ranking-service-live -n "${NAMESPACE}" \
  -p "{\"spec\":{\"selector\":{\"slot\":\"${SLOT}\"}}}"

echo ""
echo "✅ Deployment complete! Traffic now routed to: ${SLOT}"
echo "   Verify: kubectl get pods -n ${NAMESPACE} -l slot=${SLOT}"
