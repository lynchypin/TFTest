#!/bin/bash
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_TYPE="${DB_TYPE:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
INCIDENT_ID="${INCIDENT_ID:-unknown}"

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Database Health Check Script
Checks connectivity, replication, connections, and performance.

OPTIONS:
    -h, --host          Database hostname (default: localhost)
    -t, --type          Database type: postgres, mysql (default: postgres)
    -p, --port          Database port (default: 5432 for postgres, 3306 for mysql)
    -u, --user          Database user (default: postgres)
    -i, --incident      PagerDuty incident ID
    --help              Show this help message

EXAMPLES:
    $(basename "$0") -h db.example.com -t postgres -i INC123
    $(basename "$0") --host mysql.internal --type mysql -i INC456

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host) DB_HOST="$2"; shift 2 ;;
        -t|--type) DB_TYPE="$2"; shift 2 ;;
        -p|--port) DB_PORT="$2"; shift 2 ;;
        -u|--user) DB_USER="$2"; shift 2 ;;
        -i|--incident) INCIDENT_ID="$2"; shift 2 ;;
        --help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

echo "=========================================="
echo "DATABASE HEALTH CHECK"
echo "Host: $DB_HOST"
echo "Type: $DB_TYPE"
echo "Incident: $INCIDENT_ID"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

if [ "$DB_TYPE" = "postgres" ]; then
    [ "$DB_PORT" = "5432" ] || DB_PORT="${DB_PORT:-5432}"
    
    echo ""
    echo "=== CONNECTION TEST ==="
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -t 5; then
        echo "Status: CONNECTED"
    else
        echo "Status: FAILED"
        exit 1
    fi
    
    echo ""
    echo "=== REPLICATION STATUS ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            pg_is_in_recovery() as is_replica,
            CASE WHEN pg_is_in_recovery() THEN 
                pg_last_wal_receive_lsn()::text 
            ELSE 
                pg_current_wal_lsn()::text 
            END as current_lsn;
    " 2>/dev/null || echo "Unable to check replication status"
    
    echo ""
    echo "=== REPLICATION LAG ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            client_addr,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            pg_wal_lsn_diff(sent_lsn, replay_lsn) as replay_lag_bytes
        FROM pg_stat_replication;
    " 2>/dev/null || echo "No replication data (this may be a replica)"
    
    echo ""
    echo "=== CONNECTION STATISTICS ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            datname as database,
            count(*) as total_connections,
            count(*) FILTER (WHERE state = 'active') as active,
            count(*) FILTER (WHERE state = 'idle') as idle,
            count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
        FROM pg_stat_activity 
        WHERE datname IS NOT NULL
        GROUP BY datname
        ORDER BY total_connections DESC;
    " 2>/dev/null || echo "Unable to fetch connection stats"
    
    echo ""
    echo "=== DATABASE SIZES ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            datname as database,
            pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database 
        WHERE datistemplate = false
        ORDER BY pg_database_size(datname) DESC
        LIMIT 10;
    " 2>/dev/null || echo "Unable to fetch database sizes"
    
    echo ""
    echo "=== LONG RUNNING QUERIES (>30s) ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            pid,
            usename,
            datname,
            now() - query_start AS duration,
            state,
            LEFT(query, 100) as query_preview
        FROM pg_stat_activity 
        WHERE state = 'active' 
          AND query NOT ILIKE '%pg_stat_activity%'
          AND (now() - query_start) > interval '30 seconds'
        ORDER BY duration DESC
        LIMIT 10;
    " 2>/dev/null || echo "No long running queries"
    
    echo ""
    echo "=== LOCK WAITS ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "
        SELECT 
            blocked.pid AS blocked_pid,
            blocked.usename AS blocked_user,
            blocking.pid AS blocking_pid,
            blocking.usename AS blocking_user,
            blocked.query AS blocked_query
        FROM pg_catalog.pg_locks blocked_locks
        JOIN pg_catalog.pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
        JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
            AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
            AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
            AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
            AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
            AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
            AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
            AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
            AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
            AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
            AND blocking_locks.pid != blocked_locks.pid
        JOIN pg_catalog.pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
        WHERE NOT blocked_locks.granted
        LIMIT 10;
    " 2>/dev/null || echo "No lock waits detected"

elif [ "$DB_TYPE" = "mysql" ]; then
    [ "$DB_PORT" = "3306" ] || DB_PORT="${DB_PORT:-3306}"
    
    echo ""
    echo "=== CONNECTION TEST ==="
    if mysqladmin -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" ping 2>/dev/null; then
        echo "Status: CONNECTED"
    else
        echo "Status: FAILED"
        exit 1
    fi
    
    echo ""
    echo "=== REPLICATION STATUS ==="
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -e "SHOW SLAVE STATUS\G" 2>/dev/null || echo "Not a replica"
    
    echo ""
    echo "=== PROCESS LIST ==="
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -e "SHOW PROCESSLIST;" 2>/dev/null || echo "Unable to fetch process list"
    
    echo ""
    echo "=== INNODB STATUS ==="
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -e "SHOW ENGINE INNODB STATUS\G" 2>/dev/null | head -100 || echo "Unable to fetch InnoDB status"
fi

echo ""
echo "=========================================="
echo "Database health check complete"
echo "=========================================="
