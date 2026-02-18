resource "pagerduty_service" "services" {
  for_each = { for s in local.services : s.name => s }

  name                    = each.value.name
  description             = "${each.value.description}\n\nRunbook: ${each.value.runbook_url}"
  acknowledgement_timeout = 0
  auto_resolve_timeout    = 0
  alert_creation          = "create_alerts_and_incidents"

  # Team association now comes from the Escalation Policy
  escalation_policy = pagerduty_escalation_policy.eps[each.value.ep].id

  alert_grouping_parameters {
    type = lookup(each.value, "alert_grouping", "intelligent")
  }

  auto_pause_notifications_parameters {
    enabled = true
    timeout = 300
  }

  lifecycle {
    ignore_changes = [acknowledgement_timeout, auto_resolve_timeout]
  }
}