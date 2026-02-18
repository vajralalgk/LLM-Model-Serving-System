#!/usr/bin/env bash
# =============================================================================
# Rollback script - switches traffic back to previous deployment slot
# Author: Gopi Krishna Vajrala
# Usage: ./scripts/rollback.sh [blue|green]
# =============================================================================

set -euo pipefail

NAMESPACE="llm-serving"
TARGET_SLOT="${1:-blue}"

echo "================================================"
echo "  LLM Ranking Service - Rollback"
echo "  Rolling back to: ${TARGET_SLOT}"
echo "================================================"

# Verify target deployment is healthy
echo "[1/3] Verifying ${TARGET_SLOT} deployment health..."
READY=$(kubectl get deployment "ranking-service-${TARGET_SLOT}" \
  -n "${NAMESPACE}" \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

if [ "${READY}" -lt 1 ]; then
  echo "ERROR: ${TARGET_SLOT} deployment has no ready replicas!"
  exit 1
fi

echo "  ${READY} replicas ready in ${TARGET_SLOT}"

# Switch traffic
echo "[2/3] Switching traffic to ${TARGET_SLOT}..."
kubectl patch service ranking-service-live -n "${NAMESPACE}" \
  -p "{\"spec\":{\"selector\":{\"slot\":\"${TARGET_SLOT}\"}}}"

# Verify
echo "[3/3] Verifying traffic switch..."
CURRENT_SLOT=$(kubectl get service ranking-service-live \
  -n "${NAMESPACE}" \
  -o jsonpath='{.spec.selector.slot}')

if [ "${CURRENT_SLOT}" = "${TARGET_SLOT}" ]; then
  echo ""
  echo "✅ Rollback complete! Traffic now routed to: ${TARGET_SLOT}"
else
  echo "ERROR: Traffic switch verification failed!"
  exit 1
fi
