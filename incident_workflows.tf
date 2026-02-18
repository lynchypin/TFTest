# =============================================================================
# INCIDENT WORKFLOWS - PagerDuty Incident Workflow Configuration
# =============================================================================
#
# ARCHITECTURE:
# 1. Terraform creates empty workflows (no steps) - this works with the provider
# 2. After terraform apply, run scripts/populate_workflow_steps.py to add steps
# 3. Triggers are managed via Terraform in incident_workflow_triggers.tf
#
# This approach works around the Terraform provider limitation where creating
# workflows with steps fails. Empty workflows can be created, then populated.
# =============================================================================

# =============================================================================
# WORKFLOW RESOURCES - Created empty, steps added via API post-apply
# =============================================================================

resource "pagerduty_incident_workflow" "major_incident_mobilization" {
  name        = "Major Incident Full Mobilization"
  description = "Comprehensive mobilization for major incidents affecting multiple services - Slack channel, Zoom bridge, responders, diagnostics"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "security_incident_response" {
  name        = "Security Incident Response (Confidential)"
  description = "Specialized workflow for security incidents with confidential handling, SOC engagement, and audit log export"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "customer_impacting" {
  name        = "Customer Impact Communication"
  description = "Workflow for incidents affecting external customers - status page, customer success notification"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "platform_infrastructure" {
  name        = "Platform Infrastructure Degradation"
  description = "Response workflow for platform-wide infrastructure issues - multi-team coordination"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "incident_closeout" {
  name        = "Incident Closeout and PIR Scheduling"
  description = "Post-incident review scheduling and closeout procedures - Jira PIR ticket, timeline export"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "payments_outage" {
  name        = "Payments System Outage"
  description = "Critical response for payment processing failures - finance notification, compliance logging"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "data_pipeline_failure" {
  name        = "Data Pipeline Alert"
  description = "Response workflow for critical data pipeline failures - data team mobilization, upstream notification"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "database_emergency" {
  name        = "Database Emergency Response"
  description = "Critical database incident response - DBA escalation, backup verification, read replica failover"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "p1_critical" {
  name        = "P1 Critical Response Protocol"
  description = "Standard P1 incident response - immediate escalation, bridge creation, exec notification"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "maintenance_window" {
  name        = "Maintenance Window Incident"
  description = "Workflow for incidents during planned maintenance - suppressed notifications, change management link"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "data_breach_response" {
  name        = "Data Breach Response"
  description = "Critical data breach protocol - legal notification, evidence preservation, forensics initiation"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "identity_crisis" {
  name        = "Identity/Authentication Crisis"
  description = "Authentication system failure response - session management, user communication, SSO failover"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "escalation_timeout" {
  name        = "Escalation Timeout Handler"
  description = "Automated handling when escalation times out - manager notification, backup team engagement"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "manual_diagnostics" {
  name        = "Run Comprehensive Diagnostics (Manual)"
  description = "Manual trigger to run full system diagnostics - health checks, log aggregation, metric collection"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "manual_customer_comms" {
  name        = "Initiate Customer Communication (Manual)"
  description = "Manual trigger to initiate customer communication - status page update, email notification, Slack broadcast"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "service_health_check" {
  name        = "Automated Service Health Check"
  description = "Automated health check workflow - dependency verification, endpoint testing, latency measurement"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "incident_commander_handoff" {
  name        = "Incident Commander Handoff"
  description = "Workflow for IC shift change - context transfer, stakeholder notification, timeline sync"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "vendor_escalation" {
  name        = "Third-Party Vendor Escalation"
  description = "Escalation to third-party vendor support - case creation, SLA tracking, internal bridge"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "capacity_emergency" {
  name        = "Capacity Emergency Response"
  description = "Infrastructure capacity crisis response - auto-scaling trigger, traffic shedding, CDN activation"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "compliance_incident" {
  name        = "Compliance Incident Handler"
  description = "Compliance-related incident workflow - legal notification, audit trail, evidence collection"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "incident_resolution_cleanup" {
  name        = "Incident Resolution Cleanup"
  description = "Post-resolution cleanup workflow - archive Slack channel, close Jira tickets, update status page, generate timeline"
  team        = pagerduty_team.platform.id
}

resource "pagerduty_incident_workflow" "standard_incident_response" {
  name        = "Standard Incident Response"
  description = "Generic incident response workflow - Slack notification, Jira ticket creation, responder assignment"
  team        = pagerduty_team.platform.id
}

# =============================================================================
# OUTPUTS - Workflow IDs for use in triggers and API population script
# =============================================================================

output "workflow_ids" {
  description = "Map of workflow names to IDs for API population script"
  value = {
    major_incident_mobilization = pagerduty_incident_workflow.major_incident_mobilization.id
    security_incident_response  = pagerduty_incident_workflow.security_incident_response.id
    customer_impacting          = pagerduty_incident_workflow.customer_impacting.id
    platform_infrastructure     = pagerduty_incident_workflow.platform_infrastructure.id
    incident_closeout           = pagerduty_incident_workflow.incident_closeout.id
    payments_outage             = pagerduty_incident_workflow.payments_outage.id
    data_pipeline_failure       = pagerduty_incident_workflow.data_pipeline_failure.id
    database_emergency          = pagerduty_incident_workflow.database_emergency.id
    p1_critical                 = pagerduty_incident_workflow.p1_critical.id
    maintenance_window          = pagerduty_incident_workflow.maintenance_window.id
    data_breach_response        = pagerduty_incident_workflow.data_breach_response.id
    identity_crisis             = pagerduty_incident_workflow.identity_crisis.id
    escalation_timeout          = pagerduty_incident_workflow.escalation_timeout.id
    manual_diagnostics          = pagerduty_incident_workflow.manual_diagnostics.id
    manual_customer_comms       = pagerduty_incident_workflow.manual_customer_comms.id
    service_health_check        = pagerduty_incident_workflow.service_health_check.id
    incident_commander_handoff  = pagerduty_incident_workflow.incident_commander_handoff.id
    vendor_escalation           = pagerduty_incident_workflow.vendor_escalation.id
    capacity_emergency          = pagerduty_incident_workflow.capacity_emergency.id
    compliance_incident         = pagerduty_incident_workflow.compliance_incident.id
    incident_resolution_cleanup = pagerduty_incident_workflow.incident_resolution_cleanup.id
    standard_incident_response  = pagerduty_incident_workflow.standard_incident_response.id
  }
}
