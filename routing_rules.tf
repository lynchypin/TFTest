resource "pagerduty_event_orchestration" "demo_orchestration" {
  name = "Demo Global Event Orchestration"
  team = pagerduty_team.platform.id
}

resource "pagerduty_event_orchestration_router" "router" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id

  set {
    id = "start"

    rule {
      label = "Dynamic routing by service name in payload"
      actions {
        dynamic_route_to {
          lookup_by = "service_name"
          regex     = "(\\S+)"
          source    = "event.custom_details.service_name"
        }
      }
    }

    rule {
      label = "Security events to Security Monitoring service"
      condition {
        expression = "event.class matches regex 'security.*' or event.custom_details.security_classification exists"
      }
      actions {
        route_to = pagerduty_service.svc_security.id
      }
    }

    rule {
      label = "Kubernetes, container and infrastructure events to Platform K8s"
      condition {
        expression = "event.source matches regex 'kubernetes|k8s|container|docker|prometheus' or event.component matches part 'pod' or event.component matches part 'node' or (event.source matches 'prometheus' and event.severity matches 'critical')"
      }
      actions {
        route_to = pagerduty_service.svc_k8s.id
      }
    }

    rule {
      label = "Database events to Platform DBRE"
      condition {
        expression = "event.component matches regex 'mysql|postgres|redis|mongodb|cassandra' or event.class matches part 'database'"
      }
      actions {
        route_to = pagerduty_service.svc_dbre.id
      }
    }

    rule {
      label = "Network and connectivity events to Platform Network"
      condition {
        expression = "event.class matches regex 'network.*' or event.summary matches part 'connectivity' or event.summary matches part 'latency' or event.summary matches part 'packet loss'"
      }
      actions {
        route_to = pagerduty_service.svc_net.id
      }
    }

    rule {
      label = "Payment processing events to Payments Ops"
      condition {
        expression = "event.custom_details.domain matches 'payments' or event.class matches part 'payment' or event.summary matches part 'transaction'"
      }
      actions {
        route_to = pagerduty_service.svc_payments.id
      }
    }

    rule {
      label = "Checkout and cart events to App Checkout"
      condition {
        expression = "event.custom_details.service matches regex 'checkout|cart' or event.class matches part 'checkout'"
      }
      actions {
        route_to = pagerduty_service.svc_checkout.id
      }
    }

    rule {
      label = "Order and fulfillment events to App Orders"
      condition {
        expression = "event.custom_details.service matches regex 'order|fulfillment|inventory' or event.class matches part 'order'"
      }
      actions {
        route_to = pagerduty_service.svc_orders.id
      }
    }

    rule {
      label = "Identity and authentication events to App Identity"
      condition {
        expression = "event.custom_details.service matches regex 'identity|auth|sso|login' or event.class matches part 'authentication'"
      }
      actions {
        route_to = pagerduty_service.svc_identity.id
      }
    }

    rule {
      label = "Streaming and Kafka events to Data Streaming"
      condition {
        expression = "event.custom_details.service matches regex 'streaming|kafka|kinesis|pubsub' or event.class matches part 'pipeline'"
      }
      actions {
        route_to = pagerduty_service.svc_streaming.id
      }
    }

    rule {
      label = "Analytics and data warehouse events to Data Analytics"
      condition {
        expression = "event.custom_details.service matches regex 'analytics|warehouse|bigquery|snowflake|redshift' or event.class matches part 'etl'"
      }
      actions {
        route_to = pagerduty_service.svc_analytics.id
      }
    }

    rule {
      label = "Manufacturing and factory events"
      condition {
        expression = "event.custom_details.service matches regex 'factory|manufacturing|scada|plc' or event.class matches regex 'ot|manufacturing'"
      }
      actions {
        route_to = pagerduty_service.services["OT Operations - Factory Floor"].id
      }
    }

    rule {
      label = "Clinical and healthcare events"
      condition {
        expression = "event.custom_details.service matches regex 'clinical|emr|ehr|healthcare' or event.class matches part 'clinical'"
      }
      actions {
        route_to = pagerduty_service.services["Clinical Systems - EMR"].id
      }
    }

    rule {
      label = "CI/CD pipeline and deployment events"
      condition {
        expression = "event.custom_details.service matches regex 'cicd|ci/cd|pipeline|jenkins|github.actions' or event.class matches part 'deployment'"
      }
      actions {
        route_to = pagerduty_service.services["DevOps - CI/CD Platform"].id
      }
    }

    rule {
      label = "Energy grid operations events"
      condition {
        expression = "event.custom_details.service matches regex 'grid|energy|power|substation' or event.class matches part 'grid'"
      }
      actions {
        route_to = pagerduty_service.services["Grid Operations Center"].id
      }
    }

    rule {
      label = "Mining operations events"
      condition {
        expression = "event.custom_details.service matches regex 'mining|excavat|drill' or event.class matches part 'mining'"
      }
      actions {
        route_to = pagerduty_service.services["Mining Operations - Equipment"].id
      }
    }

    rule {
      label = "Telecom network operations events"
      condition {
        expression = "event.custom_details.service matches regex 'telecom|core.network|noc' or event.class matches regex 'telecom|noc'"
      }
      actions {
        route_to = pagerduty_service.services["Network Operations - Core"].id
      }
    }

    rule {
      label = "Quality control events"
      condition {
        expression = "event.custom_details.service matches regex 'quality.control|qc|defect' or event.class matches part 'quality'"
      }
      actions {
        route_to = pagerduty_service.services["Quality Control - Manufacturing"].id
      }
    }

    rule {
      label = "Retail POS events"
      condition {
        expression = "event.custom_details.service matches regex 'retail|pos|point.of.sale' or event.class matches part 'retail'"
      }
      actions {
        route_to = pagerduty_service.services["Retail Systems - POS"].id
      }
    }

    rule {
      label = "Safety operations events"
      condition {
        expression = "event.custom_details.service matches regex 'safety|compliance|environmental' or event.class matches part 'safety'"
      }
      actions {
        route_to = pagerduty_service.services["Safety Operations"].id
      }
    }

    rule {
      label = "Low priority warnings to Low Priority service"
      condition {
        expression = "event.severity matches 'warning' and event.custom_details.priority_override matches 'low'"
      }
      actions {
        route_to = pagerduty_service.svc_low_priority.id
      }
    }
  }

  catch_all {
    actions {
      route_to = pagerduty_service.svc_default.id
    }
  }
}

resource "pagerduty_service" "svc_security" {
  name                    = "Security Monitoring"
  escalation_policy       = pagerduty_escalation_policy.ep_soc.id
  alert_creation          = "create_alerts_and_incidents"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600

  incident_urgency_rule {
    type    = "constant"
    urgency = "high"
  }
}

resource "pagerduty_service" "svc_payments" {
  name                    = "Payments Routing"
  escalation_policy       = pagerduty_escalation_policy.ep_payments.id
  alert_creation          = "create_alerts_and_incidents"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600

  incident_urgency_rule {
    type    = "constant"
    urgency = "high"
  }
}

resource "pagerduty_service" "svc_low_priority" {
  name                    = "Low Priority Alerts"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  alert_creation          = "create_alerts_and_incidents"
  auto_resolve_timeout    = 86400
  acknowledgement_timeout = 1800

  incident_urgency_rule {
    type    = "constant"
    urgency = "low"
  }
}

resource "pagerduty_service" "svc_default" {
  name                    = "Default Service - Unrouted Events"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  alert_creation          = "create_alerts_and_incidents"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 900

  incident_urgency_rule {
    type    = "constant"
    urgency = "low"
  }
}
