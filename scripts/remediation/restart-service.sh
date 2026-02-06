#!/bin/bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-}"
NAMESPACE="${NAMESPACE:-default}"
INCIDENT_ID="${INCIDENT_ID:-unknown}"
TIMEOUT="${TIMEOUT:-300}"
DRY_RUN="${DRY_RUN:-false}"

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Service Restart Script
Safely restarts a Kubernetes deployment with health monitoring.

OPTIONS:
    -s, --service       Service/deployment name (required)
    -n, --namespace     Kubernetes namespace (default: default)
    -i, --incident      PagerDuty incident ID
    -t, --timeout       Rollout timeout in seconds (default: 300)
    --dry-run           Show what would be done without executing
    -h, --help          Show this help message

EXAMPLES:
    $(basename "$0") -s api-server -n production -i INC123
    $(basename "$0") --service checkout --namespace default --dry-run

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service) SERVICE_NAME="$2"; shift 2 ;;
        -n|--namespace) NAMESPACE="$2"; shift 2 ;;
        -i|--incident) INCIDENT_ID="$2"; shift 2 ;;
        -t|--timeout) TIMEOUT="$2"; shift 2 ;;
        --dry-run) DRY_RUN="true"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$SERVICE_NAME" ]; then
    echo "ERROR: Service name is required"
    usage
fi

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

echo "=========================================="
echo "SERVICE RESTART"
echo "Service: $SERVICE_NAME"
echo "Namespace: $NAMESPACE"
echo "Incident: $INCIDENT_ID"
echo "Timeout: ${TIMEOUT}s"
echo "Dry Run: $DRY_RUN"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

echo ""
echo "=== PRE-RESTART STATUS ==="
kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o wide
echo ""
kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME" -o wide

CURRENT_REPLICAS=$(kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
log "Current ready replicas: $CURRENT_REPLICAS"

CURRENT_IMAGE=$(kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown")
log "Current image: $CURRENT_IMAGE"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo "=== DRY RUN MODE ==="
    echo "Would execute: kubectl rollout restart deployment/$SERVICE_NAME -n $NAMESPACE"
    echo "Would wait for rollout with timeout: ${TIMEOUT}s"
    echo ""
    echo "=========================================="
    echo "Dry run complete - no changes made"
    echo "=========================================="
    exit 0
fi

echo ""
echo "=== INITIATING RESTART ==="
log "Executing rollout restart..."
kubectl rollout restart deployment/"$SERVICE_NAME" -n "$NAMESPACE"

echo ""
echo "=== MONITORING ROLLOUT ==="
log "Waiting for rollout to complete (timeout: ${TIMEOUT}s)..."

if kubectl rollout status deployment/"$SERVICE_NAME" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
    log "Rollout completed successfully"
    ROLLOUT_STATUS="SUCCESS"
else
    log "WARNING: Rollout did not complete within ${TIMEOUT}s"
    ROLLOUT_STATUS="TIMEOUT"
fi

echo ""
echo "=== POST-RESTART STATUS ==="
kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o wide
echo ""
kubectl get pods -n "$NAMESPACE" -l app="$SERVICE_NAME" -o wide

NEW_REPLICAS=$(kubectl get deployment "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
log "New ready replicas: $NEW_REPLICAS"

echo ""
echo "=== RECENT EVENTS ==="
kubectl get events -n "$NAMESPACE" --field-selector involvedObject.name="$SERVICE_NAME" --sort-by='.lastTimestamp' | tail -10

echo ""
echo "=========================================="
echo "Service restart complete"
echo "Status: $ROLLOUT_STATUS"
echo "Replicas: $CURRENT_REPLICAS -> $NEW_REPLICAS"
echo "=========================================="

if [ "$ROLLOUT_STATUS" != "SUCCESS" ]; then
    exit 1
fi
