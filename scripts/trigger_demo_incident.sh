#!/bin/bash
# Los Andes PagerDuty Demo - Incident Trigger Script
# Triggers test incidents to demonstrate end-to-end workflows

set -e

# Service routing keys (from Events API v2 integrations)
get_routing_key() {
    case "$1" in
        payments) echo "b56d9bd924ea4404c0a189c12faef4d4" ;;
        database) echo "ed6b71f8718b4302d054db5f4cf7228f" ;;
        security) echo "6f1b5676a9cb4d0bd061e4c1c9f5f82b" ;;
        networking) echo "e79d36284bbd4406c0e636bb2eba9932" ;;
        grafana) echo "97ad8b11bc164707d088b9d76b33d621" ;;
        checkout) echo "7d6b339366c34b00d0a18788e22aa911" ;;
        orders) echo "d70bbf9c8f104703c06b04fc241c0d20" ;;
        identity) echo "615cd96aae294a09c0a1323eae9e83ad" ;;
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
