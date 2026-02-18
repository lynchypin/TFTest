resource "pagerduty_event_orchestration_service" "svc_k8s" {
  service                                = pagerduty_service.svc_k8s.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract Kubernetes context variables"
      condition {
        expression = "event.summary matches regex '.*'"
      }
      actions {
        variable {
          name  = "pod_name"
          path  = "event.summary"
          type  = "regex"
          value = "pod[/: ]+([\\w\\-]+)"
        }
        variable {
          name  = "namespace"
          path  = "event.summary"
          type  = "regex"
          value = "namespace[/: ]+([\\w\\-]+)"
        }
        variable {
          name  = "cluster"
          path  = "event.custom_details"
          type  = "regex"
          value = "cluster[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "node_name"
          path  = "event.summary"
          type  = "regex"
          value = "node[/: ]+([\\w\\-\\.]+)"
        }
        extraction {
          target   = "event.group"
          template = "k8s:{{variables.cluster}}:{{variables.namespace}}"
        }
        route_to = "severity-triage"
      }
    }
  }

  set {
    id = "severity-triage"

    rule {
      label = "Critical K8s events - immediate response"
      condition {
        expression = "event.severity matches 'critical'"
      }
      actions {
        route_to = "critical-path"
      }
    }

    rule {
      label = "Pod crash and OOM events"
      condition {
        expression = "event.summary matches part 'CrashLoopBackOff' or event.summary matches part 'OOMKilled' or event.summary matches part 'Error'"
      }
      actions {
        route_to = "pod-failures"
      }
    }

    rule {
      label = "Node-level issues"
      condition {
        expression = "event.summary matches part 'NodeNotReady' or event.summary matches part 'Cordoned' or event.summary matches part 'DiskPressure' or event.summary matches part 'MemoryPressure'"
      }
      actions {
        route_to = "node-issues"
      }
    }

    rule {
      label = "Resource threshold alerts"
      condition {
        expression = "event.summary matches part 'CPU' or event.summary matches part 'Memory' or event.summary matches part 'quota'"
      }
      actions {
        route_to = "resource-alerts"
      }
    }

    rule {
      label = "Default K8s processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "K8s event - standard processing"
      }
    }
  }

  set {
    id = "critical-path"

    rule {
      label = "Critical production K8s event"
      condition {
        expression = "event.custom_details.env matches 'prod'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "P1 CRITICAL: Production Kubernetes issue - Auto-diagnostics triggered"
        extraction {
          target   = "event.custom_details.runbook"
          template = "https://runbooks.company.com/k8s/critical"
        }
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_k8s_pod_status.id
        }
      }
    }

    rule {
      label = "Critical non-production K8s event"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "P2 CRITICAL: Non-production Kubernetes issue"
      }
    }
  }

  set {
    id = "pod-failures"

    rule {
      label = "CrashLoopBackOff with high restart count"
      condition {
        expression = "event.summary matches part 'CrashLoopBackOff'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Pod in CrashLoopBackOff - investigate container logs"
        extraction {
          target   = "event.custom_details.failure_type"
          template = "crash-loop"
        }
        extraction {
          target   = "event.group"
          template = "k8s:pod-crash:{{variables.namespace}}:{{variables.pod_name}}"
        }
      }
    }

    rule {
      label = "OOMKilled events"
      condition {
        expression = "event.summary matches part 'OOMKilled'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Pod OOMKilled - review memory limits and usage"
        extraction {
          target   = "event.custom_details.failure_type"
          template = "oom-killed"
        }
      }
    }

    rule {
      label = "Generic pod errors"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Pod error detected"
      }
    }
  }

  set {
    id = "node-issues"

    rule {
      label = "Node not ready - high priority"
      condition {
        expression = "event.summary matches part 'NodeNotReady'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Node not ready - workloads may be affected"
        extraction {
          target   = "event.custom_details.node"
          template = "{{variables.node_name}}"
        }
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_k8s_pod_status.id
        }
      }
    }

    rule {
      label = "Node pressure conditions"
      condition {
        expression = "event.summary matches part 'Pressure'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Node under pressure - monitor for degradation"
      }
    }

    rule {
      label = "Node cordoned"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Node cordoned - planned or manual intervention"
      }
    }
  }

  set {
    id = "resource-alerts"

    rule {
      label = "High CPU utilization"
      condition {
        expression = "event.summary matches part 'CPU' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "High CPU utilization detected"
        extraction {
          target   = "event.custom_details.resource_type"
          template = "cpu"
        }
      }
    }

    rule {
      label = "Resource quota warnings"
      actions {
        priority = data.pagerduty_priority.p3.id
        suppress = false
        annotate = "Resource utilization warning"
      }
    }
  }

  catch_all {
    actions {
      suppress = false
      annotate = "K8s event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_dbre" {
  service                                = pagerduty_service.svc_dbre.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract database context"
      condition {
        expression = "event.summary matches regex '.*'"
      }
      actions {
        variable {
          name  = "db_cluster"
          path  = "event.custom_details"
          type  = "regex"
          value = "cluster[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "db_type"
          path  = "event.component"
          type  = "regex"
          value = "(mysql|postgres|redis|mongodb)"
        }
        variable {
          name  = "replica_name"
          path  = "event.summary"
          type  = "regex"
          value = "replica[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "db:{{variables.db_type}}:{{variables.db_cluster}}"
        }
        route_to = "db-triage"
      }
    }
  }

  set {
    id = "db-triage"

    rule {
      label = "Failover and replication critical"
      condition {
        expression = "event.summary matches part 'failover' or event.summary matches part 'replication failed' or event.summary matches part 'primary down'"
      }
      actions {
        route_to = "failover-detection"
      }
    }

    rule {
      label = "Replication lag alerts"
      condition {
        expression = "event.summary matches part 'replication lag' or event.summary matches part 'slave lag'"
      }
      actions {
        route_to = "replication-lag"
      }
    }

    rule {
      label = "Connection issues"
      condition {
        expression = "event.summary matches part 'connection' or event.summary matches part 'pool exhausted' or event.summary matches part 'max_connections'"
      }
      actions {
        route_to = "connection-issues"
      }
    }

    rule {
      label = "Disk space alerts"
      condition {
        expression = "event.summary matches part 'disk' or event.summary matches part 'storage'"
      }
      actions {
        route_to = "disk-space"
      }
    }

    rule {
      label = "Default database processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Database event - standard processing"
      }
    }
  }

  set {
    id = "failover-detection"

    rule {
      label = "Primary database down - critical"
      condition {
        expression = "event.summary matches part 'primary down' or event.summary matches part 'master down'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Primary database down - Failover may be required"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_database_status.id
        }
      }
    }

    rule {
      label = "Automatic failover triggered"
      condition {
        expression = "event.summary matches part 'failover triggered' or event.summary matches part 'failover complete'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Database failover in progress or completed - verify application connectivity"
      }
    }

    rule {
      label = "Replication failure"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Replication failure detected - investigate immediately"
      }
    }
  }

  set {
    id = "replication-lag"

    rule {
      label = "Critical replication lag (>60s)"
      condition {
        expression = "event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Critical replication lag - data consistency at risk"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_database_status.id
        }
      }
    }

    rule {
      label = "Warning replication lag"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Replication lag detected - monitor closely"
      }
    }
  }

  set {
    id = "connection-issues"

    rule {
      label = "Connection pool exhausted"
      condition {
        expression = "event.summary matches part 'pool exhausted' or event.summary matches part 'no available connections'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Connection pool exhausted - applications may be failing"
        extraction {
          target   = "event.custom_details.issue_type"
          template = "connection-pool-exhausted"
        }
      }
    }

    rule {
      label = "Max connections reached"
      condition {
        expression = "event.summary matches part 'max_connections'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Approaching max connections limit"
      }
    }

    rule {
      label = "Connection timeout"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Database connection issues detected"
      }
    }
  }

  set {
    id = "disk-space"

    rule {
      label = "Critical disk space (<10%)"
      condition {
        expression = "event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Database disk space critically low"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_database_status.id
        }
      }
    }

    rule {
      label = "Warning disk space"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Database disk space warning - plan expansion"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Database event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_net" {
  service                                = pagerduty_service.svc_net.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract network context"
      actions {
        variable {
          name  = "endpoint"
          path  = "event.custom_details"
          type  = "regex"
          value = "endpoint[=: ]+[\"']?([\\w\\-\\.:]+)"
        }
        variable {
          name  = "source_ip"
          path  = "event.summary"
          type  = "regex"
          value = "(\\d+\\.\\d+\\.\\d+\\.\\d+)"
        }
        extraction {
          target   = "event.group"
          template = "net:{{variables.endpoint}}"
        }
        route_to = "net-triage"
      }
    }
  }

  set {
    id = "net-triage"

    rule {
      label = "Complete connectivity loss"
      condition {
        expression = "event.summary matches part 'unreachable' or event.summary matches part 'connection refused' or event.summary matches part '100% packet loss'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Complete connectivity loss detected"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_network_connectivity.id
        }
      }
    }

    rule {
      label = "High latency"
      condition {
        expression = "event.summary matches part 'latency' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "High network latency detected"
      }
    }

    rule {
      label = "Packet loss"
      condition {
        expression = "event.summary matches part 'packet loss'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Network packet loss detected"
      }
    }

    rule {
      label = "DNS issues"
      condition {
        expression = "event.summary matches part 'DNS' or event.summary matches part 'resolution'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "DNS resolution issues detected"
      }
    }

    rule {
      label = "Default network processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Network event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Network event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_security_orch" {
  service                                = pagerduty_service.svc_security.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract security context"
      actions {
        variable {
          name  = "threat_type"
          path  = "event.class"
          type  = "regex"
          value = "security[\\./]([\\w\\-]+)"
        }
        variable {
          name  = "source_ip"
          path  = "event.summary"
          type  = "regex"
          value = "(\\d+\\.\\d+\\.\\d+\\.\\d+)"
        }
        extraction {
          target   = "event.group"
          template = "security:{{variables.threat_type}}"
        }
        route_to = "security-triage"
      }
    }
  }

  set {
    id = "security-triage"

    rule {
      label = "Active breach or intrusion"
      condition {
        expression = "event.summary matches part 'breach' or event.summary matches part 'intrusion' or event.summary matches part 'compromised'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "SECURITY CRITICAL: Active breach detected - Initiate incident response"
        extraction {
          target   = "event.custom_details.security_level"
          template = "critical"
        }
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.security_audit_log_export.id
        }
      }
    }

    rule {
      label = "Unauthorized access attempt"
      condition {
        expression = "event.summary matches part 'unauthorized' or event.summary matches part 'brute force' or event.summary matches part 'failed login'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Security alert: Unauthorized access attempt detected"
        extraction {
          target   = "event.custom_details.security_level"
          template = "high"
        }
      }
    }

    rule {
      label = "Compliance and audit events"
      condition {
        expression = "event.class matches part 'compliance' or event.class matches part 'audit'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Compliance/Audit event logged"
      }
    }

    rule {
      label = "Default security processing"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Security event - review required"
      }
    }
  }

  catch_all {
    actions {
      priority = data.pagerduty_priority.p2.id
      annotate = "Security event - unclassified"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_payments_orch" {
  service                                = pagerduty_service.svc_payments.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract payment context"
      actions {
        variable {
          name  = "transaction_id"
          path  = "event.custom_details"
          type  = "regex"
          value = "transaction[_-]?id[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "payment_provider"
          path  = "event.custom_details"
          type  = "regex"
          value = "provider[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "error_code"
          path  = "event.custom_details"
          type  = "regex"
          value = "error[_-]?code[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "payments:{{variables.payment_provider}}"
        }
        route_to = "payments-triage"
      }
    }
  }

  set {
    id = "payments-triage"

    rule {
      label = "Payment gateway down"
      condition {
        expression = "event.summary matches part 'gateway down' or event.summary matches part 'provider unavailable' or event.summary matches part 'payment system down'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Payment gateway down - Revenue impact in progress"
        extraction {
          target   = "event.custom_details.revenue_impact"
          template = "true"
        }
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_health_check.id
        }
      }
    }

    rule {
      label = "High transaction failure rate"
      condition {
        expression = "event.summary matches part 'failure rate' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "High payment transaction failure rate"
      }
    }

    rule {
      label = "Fraud detection alert"
      condition {
        expression = "event.summary matches part 'fraud' or event.summary matches part 'suspicious transaction'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "FRAUD ALERT: Suspicious payment activity detected"
        extraction {
          target   = "event.custom_details.fraud_flag"
          template = "true"
        }
      }
    }

    rule {
      label = "Provider-specific errors"
      condition {
        expression = "event.custom_details.error_code exists"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Payment provider error: {{variables.error_code}}"
      }
    }

    rule {
      label = "Default payment processing"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Payment event - review required"
      }
    }
  }

  catch_all {
    actions {
      priority = data.pagerduty_priority.p2.id
      annotate = "Payment event - unclassified"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_orders_orch" {
  service                                = pagerduty_service.svc_orders.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract order context"
      actions {
        variable {
          name  = "order_id"
          path  = "event.custom_details"
          type  = "regex"
          value = "order[_-]?id[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "orders:{{event.class}}"
        }
        route_to = "orders-triage"
      }
    }
  }

  set {
    id = "orders-triage"

    rule {
      label = "Order processing failure"
      condition {
        expression = "event.summary matches part 'order failed' or event.summary matches part 'processing error'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Order processing failure detected"
      }
    }

    rule {
      label = "Inventory issues"
      condition {
        expression = "event.summary matches part 'out of stock' or event.summary matches part 'inventory'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Inventory alert"
      }
    }

    rule {
      label = "Fulfillment delays"
      condition {
        expression = "event.summary matches part 'fulfillment' or event.summary matches part 'shipping delay'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Fulfillment issue detected"
      }
    }

    rule {
      label = "Default orders processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Orders event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Orders event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_checkout_orch" {
  service                                = pagerduty_service.svc_checkout.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract checkout context"
      actions {
        variable {
          name  = "session_id"
          path  = "event.custom_details"
          type  = "regex"
          value = "session[_-]?id[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "checkout:{{event.class}}"
        }
        route_to = "checkout-triage"
      }
    }
  }

  set {
    id = "checkout-triage"

    rule {
      label = "Checkout flow broken"
      condition {
        expression = "event.summary matches part 'checkout failed' or event.summary matches part 'checkout error' or event.summary matches part 'cart error'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Checkout flow broken - Revenue impact"
      }
    }

    rule {
      label = "High cart abandonment rate"
      condition {
        expression = "event.summary matches part 'abandonment' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "High cart abandonment rate detected"
        suppress = true
      }
    }

    rule {
      label = "Payment integration issue"
      condition {
        expression = "event.summary matches part 'payment' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Payment integration issue in checkout"
      }
    }

    rule {
      label = "Default checkout processing"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Checkout event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Checkout event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_identity_orch" {
  service                                = pagerduty_service.svc_identity.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract identity context"
      actions {
        variable {
          name  = "user_id"
          path  = "event.custom_details"
          type  = "regex"
          value = "user[_-]?id[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "auth_provider"
          path  = "event.custom_details"
          type  = "regex"
          value = "provider[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "identity:{{variables.auth_provider}}"
        }
        route_to = "identity-triage"
      }
    }
  }

  set {
    id = "identity-triage"

    rule {
      label = "Authentication system down"
      condition {
        expression = "event.summary matches part 'auth down' or event.summary matches part 'login unavailable' or event.summary matches part 'SSO down'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Authentication system down - All users affected"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_health_check.id
        }
      }
    }

    rule {
      label = "High authentication failure rate"
      condition {
        expression = "event.summary matches part 'auth failure' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "High authentication failure rate"
      }
    }

    rule {
      label = "Session management issues"
      condition {
        expression = "event.summary matches part 'session' or event.summary matches part 'token'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Session/token management issue"
      }
    }

    rule {
      label = "Default identity processing"
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Identity event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Identity event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_streaming_orch" {
  service                                = pagerduty_service.svc_streaming.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract streaming context"
      actions {
        variable {
          name  = "topic"
          path  = "event.custom_details"
          type  = "regex"
          value = "topic[=: ]+[\"']?([\\w\\-\\.]+)"
        }
        variable {
          name  = "consumer_group"
          path  = "event.custom_details"
          type  = "regex"
          value = "consumer[_-]?group[=: ]+[\"']?([\\w\\-]+)"
        }
        extraction {
          target   = "event.group"
          template = "streaming:{{variables.topic}}"
        }
        route_to = "streaming-triage"
      }
    }
  }

  set {
    id = "streaming-triage"

    rule {
      label = "Kafka/Pipeline down"
      condition {
        expression = "event.summary matches part 'broker down' or event.summary matches part 'pipeline down' or event.summary matches part 'cluster unavailable'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "CRITICAL: Streaming infrastructure down"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_pipeline_health.id
        }
      }
    }

    rule {
      label = "High consumer lag"
      condition {
        expression = "event.summary matches part 'consumer lag' and event.severity matches 'critical'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "Critical consumer lag - data processing delayed"
      }
    }

    rule {
      label = "Producer failures"
      condition {
        expression = "event.summary matches part 'producer' and event.summary matches part 'error'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Producer sending failures detected"
      }
    }

    rule {
      label = "Default streaming processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Streaming event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Streaming event - no specific rule matched"
    }
  }
}

resource "pagerduty_event_orchestration_service" "svc_analytics_orch" {
  service                                = pagerduty_service.svc_analytics.id
  enable_event_orchestration_for_service = true

  set {
    id = "start"

    rule {
      label = "Extract analytics context"
      actions {
        variable {
          name  = "pipeline_name"
          path  = "event.custom_details"
          type  = "regex"
          value = "pipeline[=: ]+[\"']?([\\w\\-]+)"
        }
        variable {
          name  = "dataset"
          path  = "event.custom_details"
          type  = "regex"
          value = "dataset[=: ]+[\"']?([\\w\\-\\.]+)"
        }
        extraction {
          target   = "event.group"
          template = "analytics:{{variables.pipeline_name}}"
        }
        route_to = "analytics-triage"
      }
    }
  }

  set {
    id = "analytics-triage"

    rule {
      label = "ETL/Pipeline failure"
      condition {
        expression = "event.summary matches part 'ETL failed' or event.summary matches part 'pipeline failed' or event.summary matches part 'job failed'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Data pipeline/ETL failure"
        pagerduty_automation_action {
          action_id = pagerduty_automation_actions_action.diagnostics_pipeline_health.id
        }
      }
    }

    rule {
      label = "Data quality issues"
      condition {
        expression = "event.summary matches part 'data quality' or event.summary matches part 'validation failed'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "Data quality issue detected"
      }
    }

    rule {
      label = "Query performance"
      condition {
        expression = "event.summary matches part 'slow query' or event.summary matches part 'query timeout'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Query performance degradation"
      }
    }

    rule {
      label = "Default analytics processing"
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Analytics event - standard processing"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Analytics event - no specific rule matched"
    }
  }
}
