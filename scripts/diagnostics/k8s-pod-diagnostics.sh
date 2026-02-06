#!/bin/bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
POD_NAME="${POD_NAME:-}"
INCIDENT_ID="${INCIDENT_ID:-unknown}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
CLUSTER="${K8S_CLUSTER:-default}"

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Kubernetes Pod Diagnostics Script
Collects pod status, events, logs, and resource usage.

OPTIONS:
    -n, --namespace     Kubernetes namespace (default: default)
    -p, --pod           Specific pod name (optional)
    -i, --incident      PagerDuty incident ID
    -c, --cluster       Kubernetes cluster context
    -o, --output        Output format: text, json (default: text)
    -h, --help          Show this help message

EXAMPLES:
    $(basename "$0") -n production -i INC123
    $(basename "$0") -n default -p api-server-abc123 -i INC456
    $(basename "$0") --namespace kube-system --output json

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace) NAMESPACE="$2"; shift 2 ;;
        -p|--pod) POD_NAME="$2"; shift 2 ;;
        -i|--incident) INCIDENT_ID="$2"; shift 2 ;;
        -c|--cluster) CLUSTER="$2"; shift 2 ;;
        -o|--output) OUTPUT_FORMAT="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

json_output() {
    local section="$1"
    local data="$2"
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        echo "{\"section\": \"$section\", \"data\": \"$(echo "$data" | base64)\"}"
    else
        echo "=== $section ==="
        echo "$data"
        echo ""
    fi
}

log "Starting Kubernetes Pod Diagnostics"
log "Namespace: $NAMESPACE"
log "Incident ID: $INCIDENT_ID"
[ -n "$POD_NAME" ] && log "Pod: $POD_NAME"

if [ "$CLUSTER" != "default" ]; then
    log "Switching to cluster context: $CLUSTER"
    kubectl config use-context "$CLUSTER" 2>/dev/null || log "Warning: Could not switch context"
fi

echo ""
echo "=========================================="
echo "KUBERNETES POD DIAGNOSTICS"
echo "Incident: $INCIDENT_ID"
echo "Namespace: $NAMESPACE"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

if [ -n "$POD_NAME" ]; then
    POD_STATUS=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o wide 2>&1)
    POD_DESCRIBE=$(kubectl describe pod "$POD_NAME" -n "$NAMESPACE" 2>&1)
    POD_LOGS=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" --tail=100 2>&1 || echo "Unable to fetch logs")
else
    POD_STATUS=$(kubectl get pods -n "$NAMESPACE" -o wide 2>&1)
    POD_DESCRIBE=$(kubectl describe pods -n "$NAMESPACE" 2>&1 | head -500)
    POD_LOGS="(Multiple pods - logs not collected)"
fi

json_output "POD STATUS" "$POD_STATUS"
json_output "POD DESCRIPTION" "$POD_DESCRIBE"
json_output "POD LOGS" "$POD_LOGS"

EVENTS=$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' 2>&1 | tail -30)
json_output "RECENT EVENTS" "$EVENTS"

RESOURCE_USAGE=$(kubectl top pods -n "$NAMESPACE" 2>&1 || echo "Metrics server not available")
json_output "RESOURCE USAGE" "$RESOURCE_USAGE"

RESTART_PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{" restarts="}{range .status.containerStatuses[*]}{.restartCount}{" "}{end}{"\n"}{end}' 2>&1)
json_output "RESTART COUNTS" "$RESTART_PODS"

echo ""
echo "=========================================="
echo "Diagnostics complete"
echo "=========================================="
