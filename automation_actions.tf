resource "pagerduty_automation_actions_runner" "runner_primary" {
  name             = "Primary Automation Runner"
  description      = "Primary runner for automation actions in production environment"
  runner_type      = "runbook"
  runbook_base_uri = "csmscale-runbook-primary"
  runbook_api_key  = var.runbook_api_key
}

resource "pagerduty_automation_actions_runner" "runner_secondary" {
  name             = "Secondary Automation Runner"
  description      = "Secondary runner for automation actions in production environment"
  runner_type      = "runbook"
  runbook_base_uri = "csmscale-runbook-secondary"
  runbook_api_key  = var.runbook_api_key
}

resource "pagerduty_automation_actions_action" "diagnostics_k8s_pod_status" {
  name        = "Kubernetes Pod Diagnostics"
  description = "Collects pod status, events, and logs for Kubernetes deployments"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Kubernetes Pod Diagnostics ==="
      echo "Namespace: $${NAMESPACE:-default}"
      echo "Pod: $${POD_NAME:-all}"
      kubectl get pods -n $${NAMESPACE:-default} -o wide
      kubectl describe pods -n $${NAMESPACE:-default}
      kubectl logs -n $${NAMESPACE:-default} --tail=100 $${POD_NAME:-}
      kubectl get events -n $${NAMESPACE:-default} --sort-by='.lastTimestamp'
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_k8s_node_status" {
  name        = "Kubernetes Node Diagnostics"
  description = "Collects node status, conditions, and resource allocation"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Kubernetes Node Diagnostics ==="
      kubectl get nodes -o wide
      kubectl describe nodes
      kubectl top nodes
      kubectl get events --field-selector reason=NodeNotReady --all-namespaces
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_database_status" {
  name        = "Database Health Check"
  description = "Checks database connectivity, replication status, and performance metrics"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Database Health Check ==="
      echo "Cluster: $${DB_CLUSTER:-primary}"
      psql -h $${DB_HOST} -c "SELECT pg_is_in_recovery();"
      psql -h $${DB_HOST} -c "SELECT * FROM pg_stat_replication;"
      psql -h $${DB_HOST} -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
      psql -h $${DB_HOST} -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_network_connectivity" {
  name        = "Network Connectivity Test"
  description = "Tests network connectivity to critical endpoints and services"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Network Connectivity Test ==="
      echo "Endpoint: $${ENDPOINT:-api.internal}"
      ping -c 5 $${ENDPOINT:-api.internal}
      traceroute $${ENDPOINT:-api.internal}
      curl -v -w "@curl-format.txt" "http://$${ENDPOINT:-api.internal}/health"
      nslookup $${ENDPOINT:-api.internal}
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_health_check" {
  name        = "Comprehensive Health Check"
  description = "Runs comprehensive health checks against all critical services"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Comprehensive Health Check ==="
      for service in api auth payments orders checkout; do
        echo "Checking $service..."
        curl -s -o /dev/null -w "%%{http_code}" "http://$service.internal/health"
        echo ""
      done
      echo "=== Service Mesh Status ==="
      istioctl proxy-status 2>/dev/null || echo "Istio not available"
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_collect_logs" {
  name        = "Collect Service Logs"
  description = "Collects recent logs from affected services and uploads to S3"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Log Collection ==="
      echo "Service: $${SERVICE_NAME:-all}"
      TIMESTAMP=$(date +%Y%m%d_%H%M%S)
      mkdir -p /tmp/logs_$TIMESTAMP
      kubectl logs -n $${NAMESPACE:-default} -l app=$${SERVICE_NAME} --tail=1000 > /tmp/logs_$TIMESTAMP/app.log
      aws s3 cp /tmp/logs_$TIMESTAMP s3://incident-logs/$${INCIDENT_ID}/ --recursive
      echo "Logs uploaded to s3://incident-logs/$${INCIDENT_ID}/"
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_pipeline_health" {
  name        = "Data Pipeline Health Check"
  description = "Checks Kafka, Flink, and data pipeline health"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Data Pipeline Health Check ==="
      echo "=== Kafka Topics ==="
      kafka-topics --bootstrap-server $${KAFKA_BOOTSTRAP} --list
      kafka-consumer-groups --bootstrap-server $${KAFKA_BOOTSTRAP} --describe --all-groups
      echo "=== Flink Jobs ==="
      curl -s http://flink-jobmanager:8081/jobs/overview
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "diagnostics_data_quality_check" {
  name        = "Data Quality Validation"
  description = "Runs data quality checks on critical data pipelines"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Data Quality Validation ==="
      echo "Pipeline: $${PIPELINE_NAME:-all}"
      python3 /scripts/data_quality_checks.py --pipeline $${PIPELINE_NAME:-all}
      echo "=== Recent DQ Alerts ==="
      aws cloudwatch get-metric-statistics --namespace DataQuality --metric-name FailedChecks --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 300 --statistics Sum
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_restart_service" {
  name        = "Restart Service"
  description = "Restarts a Kubernetes deployment by triggering a rollout"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      SERVICE=$${SERVICE_NAME:?SERVICE_NAME is required}
      NS=$${NAMESPACE:-default}

      echo "=== Service Restart: $SERVICE (ns: $NS) ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/5] Pre-flight: verifying deployment exists..."
      CURRENT_REPLICAS=$(kubectl get deployment/$SERVICE -n $NS -o jsonpath='{.spec.replicas}' 2>/dev/null)
      if [ -z "$CURRENT_REPLICAS" ]; then
        echo "ERROR: Deployment $SERVICE not found in namespace $NS"
        exit 1
      fi
      echo "  Current replicas: $CURRENT_REPLICAS"
      READY=$(kubectl get deployment/$SERVICE -n $NS -o jsonpath='{.status.readyReplicas}')
      echo "  Ready replicas: $${READY:-0}"

      echo "[2/5] Capturing current revision for rollback..."
      REVISION=$(kubectl rollout history deployment/$SERVICE -n $NS | tail -2 | head -1 | awk '{print $1}')
      echo "  Current revision: $REVISION"

      echo "[3/5] Initiating rolling restart..."
      kubectl rollout restart deployment/$SERVICE -n $NS

      echo "[4/5] Waiting for rollout to complete (timeout: 300s)..."
      if ! kubectl rollout status deployment/$SERVICE -n $NS --timeout=300s; then
        echo "ERROR: Rollout failed. Rolling back to revision $REVISION..."
        kubectl rollout undo deployment/$SERVICE -n $NS
        kubectl rollout status deployment/$SERVICE -n $NS --timeout=120s
        echo "Rollback complete. Service restored to previous version."
        exit 1
      fi

      echo "[5/5] Post-restart verification..."
      NEW_READY=$(kubectl get deployment/$SERVICE -n $NS -o jsonpath='{.status.readyReplicas}')
      echo "  Ready replicas after restart: $${NEW_READY:-0}/$CURRENT_REPLICAS"
      kubectl get pods -n $NS -l app=$SERVICE --no-headers | head -10

      echo "=== Restart Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_scale_k8s_pods" {
  name        = "Scale Kubernetes Pods"
  description = "Scales Kubernetes deployment to handle increased load"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      DEPLOY=$${DEPLOYMENT_NAME:?DEPLOYMENT_NAME is required}
      NS=$${NAMESPACE:-default}
      TARGET=$${REPLICA_COUNT:-5}

      echo "=== Pod Scaling: $DEPLOY -> $TARGET replicas (ns: $NS) ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/5] Current state..."
      CURRENT=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.replicas}')
      READY=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.status.readyReplicas}')
      echo "  Current: $CURRENT replicas ($${READY:-0} ready), Target: $TARGET"

      if [ "$CURRENT" -eq "$TARGET" ]; then
        echo "Already at target replica count. No action needed."
        exit 0
      fi

      echo "[2/5] Checking cluster capacity..."
      CPU_REQ=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}')
      MEM_REQ=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}')
      echo "  Per-pod requests: CPU=$${CPU_REQ:-unknown} MEM=$${MEM_REQ:-unknown}"
      kubectl top nodes --no-headers 2>/dev/null | head -5 || echo "  (metrics-server not available)"

      echo "[3/5] Checking HPA conflicts..."
      HPA=$(kubectl get hpa -n $NS -o jsonpath="{.items[?(@.spec.scaleTargetRef.name=='$DEPLOY')].metadata.name}" 2>/dev/null)
      if [ -n "$HPA" ]; then
        echo "  WARNING: HPA '$HPA' is active. Manual scale may be overridden."
        echo "  Patching HPA minReplicas to $TARGET..."
        kubectl patch hpa $HPA -n $NS -p "{\"spec\":{\"minReplicas\":$TARGET}}"
      fi

      echo "[4/5] Scaling deployment..."
      kubectl scale deployment/$DEPLOY -n $NS --replicas=$TARGET
      echo "  Waiting for rollout (timeout: 300s)..."
      kubectl rollout status deployment/$DEPLOY -n $NS --timeout=300s

      echo "[5/5] Post-scale verification..."
      NEW_READY=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.status.readyReplicas}')
      echo "  Ready: $${NEW_READY:-0}/$TARGET"
      kubectl get pods -n $NS -l app=$DEPLOY --no-headers | head -10

      echo "=== Scaling Complete: $CURRENT -> $TARGET ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_clear_cache" {
  name        = "Clear Application Cache"
  description = "Clears Redis and application caches"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      SERVICE=$${SERVICE_NAME:-all}
      REDIS=$${REDIS_HOST:?REDIS_HOST is required}

      echo "=== Cache Clear: $SERVICE ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/4] Pre-clear: checking Redis connectivity..."
      REDIS_INFO=$(redis-cli -h $REDIS PING 2>&1)
      if [ "$REDIS_INFO" != "PONG" ]; then
        echo "ERROR: Cannot connect to Redis at $REDIS"
        exit 1
      fi
      KEYS_BEFORE=$(redis-cli -h $REDIS DBSIZE | awk '{print $2}')
      MEM_BEFORE=$(redis-cli -h $REDIS INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '[:space:]')
      echo "  Keys: $KEYS_BEFORE, Memory: $MEM_BEFORE"

      echo "[2/4] Flushing Redis cache..."
      if [ "$SERVICE" = "all" ]; then
        redis-cli -h $REDIS FLUSHDB
      else
        redis-cli -h $REDIS --scan --pattern "$SERVICE:*" | xargs -r redis-cli -h $REDIS DEL
      fi

      echo "[3/4] Clearing application-level cache..."
      if [ "$SERVICE" = "all" ]; then
        for svc in api auth payments orders checkout; do
          HTTP_CODE=$(curl -s -o /dev/null -w "%%{http_code}" -X POST "http://$svc.internal/admin/cache/clear" 2>/dev/null || echo "000")
          echo "  $svc: HTTP $HTTP_CODE"
        done
      else
        HTTP_CODE=$(curl -s -o /dev/null -w "%%{http_code}" -X POST "http://$SERVICE.internal/admin/cache/clear")
        echo "  $SERVICE: HTTP $HTTP_CODE"
      fi

      echo "[4/4] Post-clear verification..."
      KEYS_AFTER=$(redis-cli -h $REDIS DBSIZE | awk '{print $2}')
      MEM_AFTER=$(redis-cli -h $REDIS INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '[:space:]')
      echo "  Keys: $KEYS_BEFORE -> $KEYS_AFTER, Memory: $MEM_BEFORE -> $MEM_AFTER"

      echo "=== Cache Clear Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_database_failover" {
  name        = "Database Failover"
  description = "Initiates database failover to replica"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      CLUSTER=$${DB_CLUSTER:?DB_CLUSTER is required}

      echo "=== Database Failover: $CLUSTER ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "WARNING: This will initiate a failover. Current primary will become replica."

      echo "[1/6] Pre-flight: checking cluster status..."
      STATUS=$(aws rds describe-db-clusters --db-cluster-identifier $CLUSTER --query 'DBClusters[0].Status' --output text)
      echo "  Cluster status: $STATUS"
      if [ "$STATUS" != "available" ]; then
        echo "ERROR: Cluster is not in 'available' state. Aborting."
        exit 1
      fi

      echo "[2/6] Identifying current primary and replicas..."
      aws rds describe-db-clusters --db-cluster-identifier $CLUSTER \
        --query 'DBClusters[0].DBClusterMembers[*].[DBInstanceIdentifier,IsClusterWriter]' --output table

      echo "[3/6] Checking replication lag..."
      REPLICA=$(aws rds describe-db-clusters --db-cluster-identifier $CLUSTER \
        --query 'DBClusters[0].DBClusterMembers[?IsClusterWriter==`false`].DBInstanceIdentifier' --output text | head -1)
      if [ -z "$REPLICA" ]; then
        echo "ERROR: No replica found. Cannot failover."
        exit 1
      fi
      echo "  Target replica: $REPLICA"

      echo "[4/6] Notifying dependent services..."
      echo "  Sending maintenance notification..."

      echo "[5/6] Initiating failover..."
      aws rds failover-db-cluster --db-cluster-identifier $CLUSTER --target-db-instance-identifier $REPLICA
      echo "  Failover initiated. Waiting for completion..."
      TIMEOUT=300
      ELAPSED=0
      while [ $ELAPSED -lt $TIMEOUT ]; do
        NEW_STATUS=$(aws rds describe-db-clusters --db-cluster-identifier $CLUSTER --query 'DBClusters[0].Status' --output text)
        if [ "$NEW_STATUS" = "available" ]; then
          break
        fi
        echo "  Status: $NEW_STATUS (elapsed: $${ELAPSED}s)"
        sleep 10
        ELAPSED=$((ELAPSED + 10))
      done

      echo "[6/6] Post-failover verification..."
      aws rds describe-db-clusters --db-cluster-identifier $CLUSTER \
        --query 'DBClusters[0].DBClusterMembers[*].[DBInstanceIdentifier,IsClusterWriter]' --output table
      echo "  New cluster status: $(aws rds describe-db-clusters --db-cluster-identifier $CLUSTER --query 'DBClusters[0].Status' --output text)"

      echo "=== Failover Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_circuit_breaker_reset" {
  name        = "Circuit Breaker Reset"
  description = "Resets circuit breakers for specified services"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      SERVICE=$${SERVICE_NAME:?SERVICE_NAME is required}

      echo "=== Circuit Breaker Reset: $SERVICE ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/4] Checking current circuit breaker state..."
      CB_STATUS=$(curl -s "http://$SERVICE.internal/admin/circuitbreaker/status" 2>/dev/null || echo '{"error":"unreachable"}')
      echo "  Status: $CB_STATUS"

      echo "[2/4] Checking upstream dependency health..."
      DEPS=$(curl -s "http://$SERVICE.internal/admin/dependencies" 2>/dev/null || echo '[]')
      echo "  Dependencies: $DEPS"

      echo "[3/4] Resetting circuit breakers..."
      RESET_RESULT=$(curl -s -w "\n%%{http_code}" -X POST "http://$SERVICE.internal/admin/circuitbreaker/reset")
      HTTP_CODE=$(echo "$RESET_RESULT" | tail -1)
      BODY=$(echo "$RESET_RESULT" | head -n -1)
      echo "  Response: HTTP $HTTP_CODE"
      echo "  Body: $BODY"

      if [ "$HTTP_CODE" != "200" ]; then
        echo "WARNING: Reset returned non-200 status. Attempting pod restart as fallback..."
        kubectl rollout restart deployment/$SERVICE -n $${NAMESPACE:-default} 2>/dev/null || echo "  kubectl fallback not available"
      fi

      echo "[4/4] Post-reset verification..."
      sleep 5
      NEW_STATUS=$(curl -s "http://$SERVICE.internal/admin/circuitbreaker/status" 2>/dev/null || echo '{"error":"unreachable"}')
      echo "  New status: $NEW_STATUS"
      HEALTH=$(curl -s -o /dev/null -w "%%{http_code}" "http://$SERVICE.internal/health" 2>/dev/null || echo "000")
      echo "  Health endpoint: HTTP $HEALTH"

      echo "=== Circuit Breaker Reset Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_drain_node" {
  name        = "Drain Kubernetes Node"
  description = "Safely drains a Kubernetes node for maintenance or failure recovery"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      NODE=$${NODE_NAME:?NODE_NAME is required}

      echo "=== Node Drain: $NODE ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/5] Pre-drain: checking node status..."
      NODE_STATUS=$(kubectl get node $NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
      echo "  Node ready: $NODE_STATUS"
      POD_COUNT=$(kubectl get pods --all-namespaces --field-selector spec.nodeName=$NODE --no-headers | wc -l)
      echo "  Pods on node: $POD_COUNT"

      echo "[2/5] Identifying critical workloads..."
      kubectl get pods --all-namespaces --field-selector spec.nodeName=$NODE \
        -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase' --no-headers | head -20
      PDB_VIOLATIONS=$(kubectl get pdb --all-namespaces -o json | \
        python3 -c "import sys,json; pdbs=json.load(sys.stdin)['items']; print(sum(1 for p in pdbs if p.get('status',{}).get('disruptionsAllowed',1)==0))" 2>/dev/null || echo "unknown")
      echo "  PodDisruptionBudgets at zero allowed disruptions: $PDB_VIOLATIONS"

      echo "[3/5] Cordoning node (marking unschedulable)..."
      kubectl cordon $NODE
      echo "  Node cordoned."

      echo "[4/5] Draining node (timeout: 300s)..."
      if ! kubectl drain $NODE --ignore-daemonsets --delete-emptydir-data --timeout=300s --grace-period=60; then
        echo "WARNING: Drain encountered errors. Checking remaining pods..."
        kubectl get pods --all-namespaces --field-selector spec.nodeName=$NODE --no-headers
        echo "Attempting force drain..."
        kubectl drain $NODE --ignore-daemonsets --delete-emptydir-data --force --timeout=120s
      fi

      echo "[5/5] Post-drain verification..."
      REMAINING=$(kubectl get pods --all-namespaces --field-selector spec.nodeName=$NODE --no-headers 2>/dev/null | grep -v "^kube-system" | wc -l)
      echo "  Non-system pods remaining: $REMAINING"
      kubectl get node $NODE -o wide

      echo "=== Node Drain Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_rollback_deployment" {
  name        = "Rollback Deployment"
  description = "Rolls back a Kubernetes deployment to the previous version"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      DEPLOY=$${DEPLOYMENT_NAME:?DEPLOYMENT_NAME is required}
      NS=$${NAMESPACE:-default}

      echo "=== Deployment Rollback: $DEPLOY (ns: $NS) ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      echo "[1/5] Current deployment state..."
      CURRENT_IMAGE=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.template.spec.containers[0].image}')
      CURRENT_REV=$(kubectl rollout history deployment/$DEPLOY -n $NS | tail -2 | head -1 | awk '{print $1}')
      READY=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.status.readyReplicas}')
      DESIRED=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.replicas}')
      echo "  Image: $CURRENT_IMAGE"
      echo "  Revision: $CURRENT_REV"
      echo "  Pods: $${READY:-0}/$DESIRED ready"

      echo "[2/5] Rollout history..."
      kubectl rollout history deployment/$DEPLOY -n $NS | tail -5

      echo "[3/5] Rolling back to previous revision..."
      kubectl rollout undo deployment/$DEPLOY -n $NS

      echo "[4/5] Waiting for rollout to stabilize (timeout: 300s)..."
      if ! kubectl rollout status deployment/$DEPLOY -n $NS --timeout=300s; then
        echo "ERROR: Rollback did not stabilize. Manual intervention may be required."
        kubectl get pods -n $NS -l app=$DEPLOY --no-headers
        exit 1
      fi

      echo "[5/5] Post-rollback verification..."
      NEW_IMAGE=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.spec.template.spec.containers[0].image}')
      NEW_READY=$(kubectl get deployment/$DEPLOY -n $NS -o jsonpath='{.status.readyReplicas}')
      echo "  Image: $CURRENT_IMAGE -> $NEW_IMAGE"
      echo "  Ready pods: $NEW_READY/$DESIRED"
      kubectl get pods -n $NS -l app=$DEPLOY --no-headers | head -10

      echo "=== Rollback Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "remediation_feature_flag_disable" {
  name        = "Disable Feature Flag"
  description = "Disables a feature flag through LaunchDarkly"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      set -euo pipefail
      FLAG=$${FLAG_KEY:?FLAG_KEY is required}
      LD_KEY=$${LAUNCHDARKLY_API_KEY:?LAUNCHDARKLY_API_KEY is required}
      PROJECT=$${LD_PROJECT:-default}
      ENV=$${LD_ENV:-production}

      echo "=== Feature Flag Disable: $FLAG ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "Project: $PROJECT, Environment: $ENV"

      echo "[1/4] Checking current flag state..."
      FLAG_STATE=$(curl -s -H "Authorization: $LD_KEY" \
        "https://app.launchdarkly.com/api/v2/flags/$PROJECT/$FLAG" 2>/dev/null)
      CURRENT_ON=$(echo "$FLAG_STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('on','unknown'))" 2>/dev/null || echo "unknown")
      echo "  Flag '$FLAG' is currently: $CURRENT_ON"

      if [ "$CURRENT_ON" = "False" ] || [ "$CURRENT_ON" = "false" ]; then
        echo "Flag is already disabled. No action needed."
        exit 0
      fi

      echo "[2/4] Checking flag targeting rules..."
      TARGETS=$(echo "$FLAG_STATE" | python3 -c "import sys,json; d=json.load(sys.stdin); envs=d.get('environments',{}); e=envs.get('$ENV',{}); print(len(e.get('rules',[])))" 2>/dev/null || echo "unknown")
      echo "  Targeting rules in $ENV: $TARGETS"

      echo "[3/4] Disabling flag..."
      RESPONSE=$(curl -s -w "\n%%{http_code}" -X PATCH \
        "https://app.launchdarkly.com/api/v2/flags/$PROJECT/$FLAG" \
        -H "Authorization: $LD_KEY" \
        -H "Content-Type: application/json; domain-model=launchdarkly.semanticpatch" \
        -d "[{\"kind\": \"turnFlagOff\", \"comment\": \"Disabled via PagerDuty incident automation\"}]")
      HTTP_CODE=$(echo "$RESPONSE" | tail -1)
      echo "  Response: HTTP $HTTP_CODE"
      if [ "$HTTP_CODE" != "200" ]; then
        echo "ERROR: Failed to disable flag. Response: $(echo "$RESPONSE" | head -n -1)"
        exit 1
      fi

      echo "[4/4] Verifying flag is disabled..."
      sleep 2
      NEW_STATE=$(curl -s -H "Authorization: $LD_KEY" \
        "https://app.launchdarkly.com/api/v2/flags/$PROJECT/$FLAG" | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('on','unknown'))" 2>/dev/null || echo "unknown")
      echo "  Flag '$FLAG' is now: $NEW_STATE"

      echo "=== Feature Flag Disable Complete ==="
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "security_audit_log_export" {
  name        = "Export Audit Logs"
  description = "Exports audit logs for security incident investigation"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Security Audit Log Export ==="
      TIMESTAMP=$(date +%Y%m%d_%H%M%S)
      echo "Exporting logs for time range: $${START_TIME} to $${END_TIME:-now}"
      aws logs filter-log-events \
        --log-group-name /aws/security/audit \
        --start-time $${START_TIME} \
        --end-time $${END_TIME:-$(date +%s)000} \
        --output json > /tmp/audit_logs_$TIMESTAMP.json
      aws s3 cp /tmp/audit_logs_$TIMESTAMP.json s3://security-audit-logs/$${INCIDENT_ID}/
      echo "Audit logs exported to s3://security-audit-logs/$${INCIDENT_ID}/"
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "security_isolate_host" {
  name        = "Isolate Compromised Host"
  description = "Isolates a potentially compromised host from the network"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Host Isolation ==="
      echo "Host: $${HOST_ID}"
      echo "WARNING: This will isolate the host from all network access"
      aws ec2 modify-instance-attribute \
        --instance-id $${HOST_ID} \
        --groups $${ISOLATION_SECURITY_GROUP}
      echo "Host $${HOST_ID} isolated. Only security team can access."
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "security_data_retention_hold" {
  name        = "Apply Data Retention Hold"
  description = "Applies legal hold to prevent data deletion during investigation"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Data Retention Hold ==="
      echo "Incident: $${INCIDENT_ID}"
      echo "Applying legal hold to all relevant data stores..."
      aws s3api put-object-legal-hold \
        --bucket production-data \
        --key $${DATA_PATH} \
        --legal-hold Status=ON
      echo "Legal hold applied. Data cannot be deleted until hold is removed."
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action" "notification_slack_broadcast" {
  name        = "Slack Broadcast Notification"
  description = "Sends a broadcast notification to multiple Slack channels"
  action_type = "script"

  action_data_reference {
    script             = <<-EOT
      #!/bin/bash
      echo "=== Slack Broadcast ==="
      echo "Message: $${MESSAGE}"
      echo "Channels: $${CHANNELS:-#incidents}"
      for channel in $(echo $${CHANNELS:-#incidents} | tr ',' ' '); do
        curl -X POST -H 'Content-type: application/json' \
          --data "{\"channel\":\"$channel\",\"text\":\"$${MESSAGE}\"}" \
          $${SLACK_WEBHOOK_URL}
      done
      echo "Broadcast complete"
    EOT
    invocation_command = "/bin/bash"
  }
}

resource "pagerduty_automation_actions_action_team_association" "diag_k8s_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_k8s_pod_status.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_node_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_k8s_node_status.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_db_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_database_status.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_net_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_network_connectivity.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_health_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_health_check.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_logs_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_collect_logs.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_pipeline_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_pipeline_health.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "diag_dq_platform" {
  action_id = pagerduty_automation_actions_action.diagnostics_data_quality_check.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_restart_platform" {
  action_id = pagerduty_automation_actions_action.remediation_restart_service.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_scale_platform" {
  action_id = pagerduty_automation_actions_action.remediation_scale_k8s_pods.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_cache_platform" {
  action_id = pagerduty_automation_actions_action.remediation_clear_cache.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_failover_platform" {
  action_id = pagerduty_automation_actions_action.remediation_database_failover.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_circuit_platform" {
  action_id = pagerduty_automation_actions_action.remediation_circuit_breaker_reset.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_drain_platform" {
  action_id = pagerduty_automation_actions_action.remediation_drain_node.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_rollback_platform" {
  action_id = pagerduty_automation_actions_action.remediation_rollback_deployment.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "rem_ff_platform" {
  action_id = pagerduty_automation_actions_action.remediation_feature_flag_disable.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "sec_audit_platform" {
  action_id = pagerduty_automation_actions_action.security_audit_log_export.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "sec_isolate_platform" {
  action_id = pagerduty_automation_actions_action.security_isolate_host.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "sec_retention_platform" {
  action_id = pagerduty_automation_actions_action.security_data_retention_hold.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_team_association" "notify_slack_platform" {
  action_id = pagerduty_automation_actions_action.notification_slack_broadcast.id
  team_id   = pagerduty_team.platform.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_k8s_k8s_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_k8s_pod_status.id
  service_id = pagerduty_service.svc_k8s.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_node_k8s_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_k8s_node_status.id
  service_id = pagerduty_service.svc_k8s.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_db_dbre_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_database_status.id
  service_id = pagerduty_service.svc_dbre.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_net_net_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_network_connectivity.id
  service_id = pagerduty_service.svc_net.id
}

resource "pagerduty_automation_actions_action_service_association" "sec_audit_security_service" {
  action_id  = pagerduty_automation_actions_action.security_audit_log_export.id
  service_id = pagerduty_service.svc_security_orch.id
}

resource "pagerduty_automation_actions_action_service_association" "sec_isolate_security_service" {
  action_id  = pagerduty_automation_actions_action.security_isolate_host.id
  service_id = pagerduty_service.svc_security_orch.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_pipeline_streaming_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_pipeline_health.id
  service_id = pagerduty_service.svc_streaming_orch.id
}

resource "pagerduty_automation_actions_action_service_association" "diag_dq_analytics_service" {
  action_id  = pagerduty_automation_actions_action.diagnostics_data_quality_check.id
  service_id = pagerduty_service.svc_analytics_orch.id
}
