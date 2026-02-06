#!/bin/bash
set -euo pipefail

DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-}"
NAMESPACE="${NAMESPACE:-default}"
REPLICA_COUNT="${REPLICA_COUNT:-}"
INCIDENT_ID="${INCIDENT_ID:-unknown}"
DRY_RUN="${DRY_RUN:-false}"
MAX_REPLICAS="${MAX_REPLICAS:-50}"

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Kubernetes Pod Scaling Script
Scales a deployment to handle load changes.

OPTIONS:
    -d, --deployment    Deployment name (required)
    -r, --replicas      Target replica count (required)
    -n, --namespace     Kubernetes namespace (default: default)
    -i, --incident      PagerDuty incident ID
    -m, --max           Maximum allowed replicas (default: 50)
    --dry-run           Show what would be done without executing
    -h, --help          Show this help message

EXAMPLES:
    $(basename "$0") -d api-server -r 10 -n production -i INC123
    $(basename "$0") --deployment checkout --replicas 5 --dry-run

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--deployment) DEPLOYMENT_NAME="$2"; shift 2 ;;
        -r|--replicas) REPLICA_COUNT="$2"; shift 2 ;;
        -n|--namespace) NAMESPACE="$2"; shift 2 ;;
        -i|--incident) INCIDENT_ID="$2"; shift 2 ;;
        -m|--max) MAX_REPLICAS="$2"; shift 2 ;;
        --dry-run) DRY_RUN="true"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$DEPLOYMENT_NAME" ] || [ -z "$REPLICA_COUNT" ]; then
    echo "ERROR: Deployment name and replica count are required"
    usage
fi

if [ "$REPLICA_COUNT" -gt "$MAX_REPLICAS" ]; then
    echo "ERROR: Requested replicas ($REPLICA_COUNT) exceeds maximum allowed ($MAX_REPLICAS)"
    exit 1
fi

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

echo "=========================================="
echo "POD SCALING"
echo "Deployment: $DEPLOYMENT_NAME"
echo "Target Replicas: $REPLICA_COUNT"
echo "Namespace: $NAMESPACE"
echo "Incident: $INCIDENT_ID"
echo "Dry Run: $DRY_RUN"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

echo ""
echo "=== CURRENT STATE ==="
kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o wide

CURRENT_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
READY_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' || echo "0")

log "Current spec replicas: $CURRENT_REPLICAS"
log "Current ready replicas: $READY_REPLICAS"
log "Target replicas: $REPLICA_COUNT"

if [ "$CURRENT_REPLICAS" = "$REPLICA_COUNT" ]; then
    log "Already at target replica count"
    echo ""
    echo "=========================================="
    echo "No scaling needed"
    echo "=========================================="
    exit 0
fi

SCALE_DIRECTION="up"
if [ "$REPLICA_COUNT" -lt "$CURRENT_REPLICAS" ]; then
    SCALE_DIRECTION="down"
fi
log "Scale direction: $SCALE_DIRECTION"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo "=== DRY RUN MODE ==="
    echo "Would execute: kubectl scale deployment/$DEPLOYMENT_NAME -n $NAMESPACE --replicas=$REPLICA_COUNT"
    echo "Scale direction: $SCALE_DIRECTION ($CURRENT_REPLICAS -> $REPLICA_COUNT)"
    echo ""
    echo "=========================================="
    echo "Dry run complete - no changes made"
    echo "=========================================="
    exit 0
fi

echo ""
echo "=== EXECUTING SCALE ==="
kubectl scale deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --replicas="$REPLICA_COUNT"
log "Scale command executed"

echo ""
echo "=== MONITORING SCALE ==="
log "Waiting for rollout..."

if kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=300s; then
    log "Scaling completed successfully"
    SCALE_STATUS="SUCCESS"
else
    log "WARNING: Scaling did not complete within timeout"
    SCALE_STATUS="TIMEOUT"
fi

echo ""
echo "=== FINAL STATE ==="
kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o wide
echo ""
kubectl get pods -n "$NAMESPACE" -l app="$DEPLOYMENT_NAME" -o wide

NEW_READY=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' || echo "0")

echo ""
echo "=========================================="
echo "Scaling complete"
echo "Status: $SCALE_STATUS"
echo "Direction: $SCALE_DIRECTION"
echo "Change: $CURRENT_REPLICAS -> $NEW_READY ready"
echo "=========================================="
