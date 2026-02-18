locals {
  ep_team_ids = {
    "EP - Customer-Facing Apps"            = [data.pagerduty_team.team_app.id]
    "EP - Platform Core"                   = [data.pagerduty_team.team_platform.id]
    "EP - Data Services"                   = [data.pagerduty_team.team_platform.id]
    "EP - IT and Internal Apps"            = [data.pagerduty_team.team_support.id]
    "EP - Security Monitoring (SOC)"       = [data.pagerduty_team.team_secops.id]
    "EP - Business Ops - Manual Operation" = [data.pagerduty_team.team_support.id]
  }
}

resource "pagerduty_escalation_policy" "eps" {
  for_each  = local.escalation_policies
  name      = each.key
  num_loops = 2

  teams = local.ep_team_ids[each.key]

  dynamic "rule" {
    for_each = each.value
    content {
      escalation_delay_in_minutes = rule.value.delay
      target {
        type = "schedule_reference"
        id   = pagerduty_schedule.schedules[rule.value.schedule].id
      }
    }
  }
}
