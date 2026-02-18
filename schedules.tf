resource "pagerduty_schedule" "schedules" {
  for_each = local.schedules

  name        = each.key
  time_zone   = each.value.time_zone
  teams       = [data.pagerduty_team.by_name[each.value.team].id]
  description = "Managed by Terraform"

  layer {
    name = "Primary"
    # Both are required by the current provider
    start                        = var.rotation_start
    rotation_virtual_start       = var.rotation_start
    rotation_turn_length_seconds = each.value.rotation_days * 24 * 60 * 60

    users = [
      for email in each.value.members :
      data.pagerduty_user.by_email[email].id
    ]

    # Weekly business-hours restrictions Mon–Fri (09:00–17:00 = 8h)
    dynamic "restriction" {
      for_each = each.value.business_hours == null ? [] : toset(each.value.business_hours.days)
      content {
        type              = "weekly_restriction"
        start_day_of_week = restriction.value
        start_time_of_day = each.value.business_hours.start_time
        duration_seconds  = each.value.business_hours.duration_seconds
      }
    }
  }
}
