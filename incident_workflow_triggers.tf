# =============================================================================
# INCIDENT WORKFLOW TRIGGERS
# =============================================================================
# Triggers define when workflows run. Each trigger can be:
# - Manual: Run by user from incident UI
# - Conditional: Auto-run when incident matches conditions
#
# CRITICAL: subscribed_to_all_services must be true for conditional triggers
# to fire on any incident. Otherwise specify specific services.
# =============================================================================

# Demo Incident Channel Setup - triggers on [DEMO] in title
resource "pagerduty_incident_workflow_trigger" "demo_channel_setup" {
  type      = "conditional"
  workflow  = "PUXIPNC"
  condition = "incident.title matches part '[DEMO]'"

  subscribed_to_all_services = true
}

# Standard Incident Response - could be manual or conditional
resource "pagerduty_incident_workflow_trigger" "standard_response" {
  type      = "conditional"
  workflow  = pagerduty_incident_workflow.standard_incident_response.id
  condition = "incident.urgency matches 'high'"

  subscribed_to_all_services = true
}

# Major Incident Mobilization - P1/P2 incidents
resource "pagerduty_incident_workflow_trigger" "major_incident" {
  type      = "conditional"
  workflow  = pagerduty_incident_workflow.major_incident_mobilization.id
  condition = "incident.priority.name matches part 'P1' or incident.priority.name matches part 'P2'"

  subscribed_to_all_services = true
}

# Security Incident Response
resource "pagerduty_incident_workflow_trigger" "security_response" {
  type      = "conditional"
  workflow  = pagerduty_incident_workflow.security_incident_response.id
  condition = "incident.title matches part '[SECURITY]' or incident.title matches part 'security'"

  subscribed_to_all_services = true
}
