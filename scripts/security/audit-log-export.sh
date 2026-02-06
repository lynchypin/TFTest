#!/bin/bash
set -euo pipefail

LOG_GROUP="${LOG_GROUP:-/aws/security/audit}"
START_TIME="${START_TIME:-}"
END_TIME="${END_TIME:-}"
INCIDENT_ID="${INCIDENT_ID:-unknown}"
S3_BUCKET="${S3_BUCKET:-security-audit-logs}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp}"
FILTER_PATTERN="${FILTER_PATTERN:-}"

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Security Audit Log Export Script
Exports CloudWatch logs for security incident investigation.

OPTIONS:
    -g, --log-group     CloudWatch log group (default: /aws/security/audit)
    -s, --start         Start time (ISO 8601 or epoch ms, required)
    -e, --end           End time (ISO 8601 or epoch ms, default: now)
    -i, --incident      PagerDuty incident ID (required)
    -b, --bucket        S3 bucket for upload (default: security-audit-logs)
    -o, --output        Local output directory (default: /tmp)
    -f, --filter        CloudWatch filter pattern (optional)
    -h, --help          Show this help message

EXAMPLES:
    $(basename "$0") -s "2024-01-01T00:00:00Z" -i INC123
    $(basename "$0") --start 1704067200000 --end 1704153600000 -i INC456
    $(basename "$0") -g /aws/app/api -s "1 hour ago" -i INC789

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--log-group) LOG_GROUP="$2"; shift 2 ;;
        -s|--start) START_TIME="$2"; shift 2 ;;
        -e|--end) END_TIME="$2"; shift 2 ;;
        -i|--incident) INCIDENT_ID="$2"; shift 2 ;;
        -b|--bucket) S3_BUCKET="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -f|--filter) FILTER_PATTERN="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$START_TIME" ] || [ -z "$INCIDENT_ID" ]; then
    echo "ERROR: Start time and incident ID are required"
    usage
fi

parse_time() {
    local input="$1"
    if [[ "$input" =~ ^[0-9]+$ ]]; then
        echo "$input"
    elif [[ "$input" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2} ]]; then
        date -d "$input" +%s000 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$input" +%s000 2>/dev/null
    elif [[ "$input" =~ "ago" ]]; then
        date -d "$input" +%s000 2>/dev/null || echo ""
    else
        echo ""
    fi
}

START_MS=$(parse_time "$START_TIME")
if [ -z "$START_MS" ]; then
    echo "ERROR: Could not parse start time: $START_TIME"
    exit 1
fi

if [ -n "$END_TIME" ]; then
    END_MS=$(parse_time "$END_TIME")
else
    END_MS=$(date +%s000)
fi

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/audit_logs_${INCIDENT_ID}_${TIMESTAMP}.json"
SUMMARY_FILE="${OUTPUT_DIR}/audit_summary_${INCIDENT_ID}_${TIMESTAMP}.txt"

echo "=========================================="
echo "SECURITY AUDIT LOG EXPORT"
echo "Incident: $INCIDENT_ID"
echo "Log Group: $LOG_GROUP"
echo "Start Time: $START_TIME ($START_MS)"
echo "End Time: ${END_TIME:-now} ($END_MS)"
echo "Output: $OUTPUT_FILE"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

echo ""
echo "=== VERIFYING LOG GROUP ==="
if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text | grep -q "$LOG_GROUP"; then
    log "Log group found: $LOG_GROUP"
else
    log "WARNING: Log group may not exist or is inaccessible"
fi

echo ""
echo "=== EXPORTING LOGS ==="
log "Fetching logs from CloudWatch..."

FILTER_ARGS=""
if [ -n "$FILTER_PATTERN" ]; then
    FILTER_ARGS="--filter-pattern \"$FILTER_PATTERN\""
    log "Using filter pattern: $FILTER_PATTERN"
fi

aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --start-time "$START_MS" \
    --end-time "$END_MS" \
    $FILTER_ARGS \
    --output json > "$OUTPUT_FILE" 2>/dev/null || {
        log "ERROR: Failed to export logs"
        exit 1
    }

EVENT_COUNT=$(jq '.events | length' "$OUTPUT_FILE")
log "Exported $EVENT_COUNT log events"

echo ""
echo "=== GENERATING SUMMARY ==="
{
    echo "Security Audit Log Export Summary"
    echo "================================="
    echo ""
    echo "Incident ID: $INCIDENT_ID"
    echo "Log Group: $LOG_GROUP"
    echo "Time Range: $START_TIME to ${END_TIME:-now}"
    echo "Total Events: $EVENT_COUNT"
    echo "Export Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "Event Types:"
    jq -r '.events[].message' "$OUTPUT_FILE" | grep -oE '"eventType":\s*"[^"]+"' | sort | uniq -c | sort -rn | head -20
    echo ""
    echo "Top Source IPs:"
    jq -r '.events[].message' "$OUTPUT_FILE" | grep -oE '"sourceIPAddress":\s*"[^"]+"' | sort | uniq -c | sort -rn | head -10
    echo ""
    echo "User Agents:"
    jq -r '.events[].message' "$OUTPUT_FILE" | grep -oE '"userAgent":\s*"[^"]+"' | sort | uniq -c | sort -rn | head -10
} > "$SUMMARY_FILE" 2>/dev/null || log "Summary generation partially failed"

echo ""
echo "=== UPLOADING TO S3 ==="
S3_PATH="s3://${S3_BUCKET}/incidents/${INCIDENT_ID}/"

aws s3 cp "$OUTPUT_FILE" "${S3_PATH}" && log "Uploaded: $(basename "$OUTPUT_FILE")"
aws s3 cp "$SUMMARY_FILE" "${S3_PATH}" && log "Uploaded: $(basename "$SUMMARY_FILE")"

echo ""
echo "=== APPLYING LEGAL HOLD ==="
aws s3api put-object-legal-hold \
    --bucket "$S3_BUCKET" \
    --key "incidents/${INCIDENT_ID}/$(basename "$OUTPUT_FILE")" \
    --legal-hold Status=ON 2>/dev/null && log "Legal hold applied" || log "WARNING: Could not apply legal hold"

echo ""
echo "=== CLEANUP ==="
rm -f "$OUTPUT_FILE" "$SUMMARY_FILE"
log "Local files cleaned up"

echo ""
echo "=========================================="
echo "Audit log export complete"
echo "Location: ${S3_PATH}"
echo "Events exported: $EVENT_COUNT"
echo "=========================================="
