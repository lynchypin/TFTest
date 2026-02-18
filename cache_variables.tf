resource "pagerduty_event_orchestration_global_cache_variable" "recent_source" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  name                = "recent_alert_source"

  condition {
    expression = "event.source exists"
  }

  configuration {
    type        = "recent_value"
    source      = "event.source"
    regex       = "(.*)"
    ttl_seconds = 300
  }
}

resource "pagerduty_event_orchestration_global_cache_variable" "trigger_count_critical" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  name                = "critical_event_count"

  condition {
    expression = "event.severity matches 'critical'"
  }

  configuration {
    type        = "trigger_event_count"
    ttl_seconds = 600
  }
}

resource "pagerduty_event_orchestration_global_cache_variable" "recent_hostname" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  name                = "recent_hostname"

  condition {
    expression = "event.custom_details.hostname exists"
  }

  configuration {
    type        = "recent_value"
    source      = "event.custom_details.hostname"
    regex       = "(.*)"
    ttl_seconds = 600
  }
}

resource "pagerduty_event_orchestration_service_cache_variable" "k8s_pod_restart_count" {
  service = pagerduty_service.svc_k8s.id
  name    = "pod_restart_trigger_count"

  condition {
    expression = "event.summary matches part 'restart' or event.summary matches part 'CrashLoopBackOff'"
  }

  configuration {
    type        = "trigger_event_count"
    ttl_seconds = 300
  }
}

resource "pagerduty_event_orchestration_service_cache_variable" "k8s_recent_failing_pod" {
  service = pagerduty_service.svc_k8s.id
  name    = "recent_failing_pod"

  condition {
    expression = "event.severity matches 'critical' or event.severity matches 'error'"
  }

  configuration {
    type        = "recent_value"
    source      = "event.summary"
    regex       = "pod[/: ]+([\\w\\-]+)"
    ttl_seconds = 600
  }
}

resource "pagerduty_event_orchestration_service_cache_variable" "payments_failure_count" {
  service = pagerduty_service.svc_payments_orch.id
  name    = "payment_failure_count"

  condition {
    expression = "event.summary matches part 'payment' and (event.severity matches 'critical' or event.severity matches 'error')"
  }

  configuration {
    type        = "trigger_event_count"
    ttl_seconds = 300
  }
}

resource "pagerduty_event_orchestration_service_cache_variable" "dbre_recent_query" {
  service = pagerduty_service.svc_dbre.id
  name    = "recent_slow_query_source"

  condition {
    expression = "event.summary matches part 'slow query' or event.summary matches part 'replication lag'"
  }

  configuration {
    type        = "recent_value"
    source      = "event.custom_details.hostname"
    regex       = "(.*)"
    ttl_seconds = 600
  }
}
