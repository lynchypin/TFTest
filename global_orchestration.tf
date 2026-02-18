resource "pagerduty_event_orchestration_global" "global" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id

  set {
    id = "start"

    rule {
      label = "Extract variables and route to triage"
      condition {
        expression = "event.summary matches regex '.*'"
      }
      actions {
        variable {
          name  = "hostname"
          path  = "event.custom_details.hostname"
          type  = "regex"
          value = "(.*)"
        }
        variable {
          name  = "environment"
          path  = "event.custom_details.env"
          type  = "regex"
          value = "(.*)"
        }
        annotate = "Event processed by global orchestration"
        route_to = "triage"
      }
    }
  }

  set {
    id = "triage"

    rule {
      label = "Security events - Critical priority"
      condition {
        expression = "event.class matches regex 'security.*' or event.summary matches part 'unauthorized' or event.summary matches part 'breach'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        severity = "critical"
        annotate = "SECURITY EVENT: Routed to SOC for immediate investigation"
      }
    }

    rule {
      label = "Critical severity in production - P1"
      condition {
        expression = "event.severity matches 'critical' and event.custom_details.env matches 'prod'"
      }
      actions {
        priority = data.pagerduty_priority.p1.id
        annotate = "P1 CRITICAL: Production critical event"
      }
    }

    rule {
      label = "Error severity in production - P2"
      condition {
        expression = "event.severity matches 'error' and event.custom_details.env matches 'prod'"
      }
      actions {
        priority = data.pagerduty_priority.p2.id
        annotate = "P2 ERROR: Production error event"
      }
    }

    rule {
      label = "Warning in production - P3"
      condition {
        expression = "event.severity matches 'warning' and event.custom_details.env matches 'prod'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "P3 WARNING: Production warning"
      }
    }

    rule {
      label = "Drop heartbeat OK events"
      condition {
        expression = "event.summary matches part 'heartbeat' and event.summary matches part 'OK'"
      }
      actions {
        drop_event = true
      }
    }

    rule {
      label = "Suppress info-level events"
      condition {
        expression = "event.severity matches 'info'"
      }
      actions {
        suppress = true
        annotate = "Info-level event suppressed"
      }
    }

    rule {
      label = "Non-production critical - P3"
      condition {
        expression = "event.severity matches 'critical' and event.custom_details.env matches regex 'staging|dev|test'"
      }
      actions {
        priority = data.pagerduty_priority.p3.id
        annotate = "Non-production critical event - Lower priority"
      }
    }

    rule {
      label = "Default handling"
      actions {
        annotate = "Standard processing - no priority override"
      }
    }
  }

  catch_all {
    actions {
      annotate = "Catch-all: Event did not match any orchestration rules"
    }
  }
}
