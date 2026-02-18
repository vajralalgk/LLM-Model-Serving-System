#!/usr/bin/env bash
# =============================================================================
# Chaos Testing Script - Simulates failure scenarios under load
# Author: Gopi Krishna Vajrala
# Usage: ./scripts/chaos_test.sh
# =============================================================================

set -euo pipefail

NAMESPACE="llm-serving"

echo "================================================"
echo "  LLM Ranking Service - Chaos Testing"
echo "================================================"
echo ""

# Test 1: Pod Kill Under Load
echo "[Test 1] Pod Kill Under Load"
echo "  Starting load generator in background..."
# Start load in background (requires locust or curl loop)
for i in $(seq 1 100); do
  curl -s -X POST http://localhost:8000/rank \
    -H "Content-Type: application/json" \
    -H "X-API-Key: test-api-key" \
    -d '{"user_id":"chaos_user","context":{},"candidate_titles":["A","B","C"]}' \
    > /dev/null 2>&1 &
done

echo "  Killing a random pod..."
POD=$(kubectl get pods -n "${NAMESPACE}" -l app=ranking-service \
  -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "${POD}" -n "${NAMESPACE}" --grace-period=0 --force 2>/dev/null || true

echo "  Waiting for recovery..."
sleep 15

READY=$(kubectl get deployment ranking-service -n "${NAMESPACE}" \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
echo "  Ready replicas after recovery: ${READY}"
echo ""

# Test 2: Resource Pressure
echo "[Test 2] Simulating high memory pressure..."
kubectl set resources deployment/ranking-service \
  -n "${NAMESPACE}" \
  --limits=memory=256Mi 2>/dev/null || echo "  Skipped (deployment not found)"
sleep 10
kubectl set resources deployment/ranking-service \
  -n "${NAMESPACE}" \
  --limits=memory=4Gi 2>/dev/null || echo "  Skipped (deployment not found)"
echo ""

# Test 3: Network Partition Simulation
echo "[Test 3] Service endpoint verification under stress..."
for i in $(seq 1 50); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:8000/health 2>/dev/null || echo "000")
  if [ "${STATUS}" != "200" ]; then
    echo "  Health check returned ${STATUS} at iteration ${i}"
  fi
done
echo "  Stress health check complete"
echo ""

# Cleanup background jobs
wait 2>/dev/null || true

echo "================================================"
echo "  Chaos Testing Complete"
echo "================================================"
