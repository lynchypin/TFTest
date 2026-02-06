#!/bin/bash
# Los Andes PagerDuty Demo - Incident Trigger Script
# Triggers test incidents to demonstrate end-to-end workflows

set -e

# Service routing keys (from environment variables)
# Set these in your shell: export PD_ROUTING_KEY_PAYMENTS=xxx
get_routing_key() {
    case "$1" in
        payments) echo "${PD_ROUTING_KEY_PAYMENTS}" ;;
        database) echo "${PD_ROUTING_KEY_DATABASE}" ;;
        security) echo "${PD_ROUTING_KEY_SECURITY}" ;;
        networking) echo "${PD_ROUTING_KEY_NETWORKING}" ;;
        grafana) echo "${PD_ROUTING_KEY_GRAFANA}" ;;
        checkout) echo "${PD_ROUTING_KEY_CHECKOUT}" ;;
        orders) echo "${PD_ROUTING_KEY_ORDERS}" ;;
        identity) echo "${PD_ROUTING_KEY_IDENTITY}" ;;
        *) echo "" ;;
    esac
}

usage() {
    echo "Usage: $0 [service] [severity]"
    echo ""
    echo "Services: payments, database, security, networking, grafana, checkout, orders, identity"
    echo "Severity: critical, error, warning, info"
    echo ""
    echo "Examples:"
    echo "  $0 payments critical    # Trigger critical payment alert"
    echo "  $0 database error       # Trigger database error"
}

trigger_incident() {
    local routing_key="$1"
    local service="$2"
    local severity="$3"
    local dedup_key="demo-$(date +%s)"
    
    echo "Triggering $severity incident for $service..."
    
    response=$(curl -s -X POST "https://events.pagerduty.com/v2/enqueue" \
        -H "Content-Type: application/json" \
        -d "{
            \"routing_key\": \"$routing_key\",
            \"event_action\": \"trigger\",
            \"dedup_key\": \"$dedup_key\",
            \"payload\": {
                \"summary\": \"[DEMO] $service - Test incident triggered\",
                \"source\": \"los-andes-demo-script\",
                \"severity\": \"$severity\",
                \"custom_details\": {
                    \"environment\": \"demo\",
                    \"triggered_by\": \"validation_script\",
                    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
                }
            }
        }")
    
    status=$(echo "$response" | jq -r '.status // "error"')
    if [ "$status" = "success" ]; then
        echo "✓ Incident triggered successfully"
        echo "  Dedup Key: $dedup_key"
    else
        echo "✗ Failed: $response"
        return 1
    fi
}

# Main
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    usage
    exit 0
fi

SERVICE="${1:-payments}"
SEVERITY="${2:-warning}"

ROUTING_KEY=$(get_routing_key "$SERVICE")
if [ -z "$ROUTING_KEY" ]; then
    echo "Unknown service: $SERVICE"
    usage
    exit 1
fi

trigger_incident "$ROUTING_KEY" "$SERVICE" "$SEVERITY"
