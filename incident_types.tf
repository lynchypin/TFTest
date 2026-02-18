############################################################
# incident_types.tf
# - Validates even with count=0 because required attrs exist
# - Creates two types when toggled on
# - Data lookups always available for triggers/refs
############################################################

locals {
  enable_types = var.enable_incident_automation && var.create_incident_types
}

# Base type lookup
data "pagerduty_incident_type" "base" {
  display_name = "Base Incident"
}

# Always-on data lookups (resolve if types exist via UI or TF)
data "pagerduty_incident_type" "major" {
  display_name = var.incident_type_major_display_name
}

data "pagerduty_incident_type" "security" {
  display_name = var.incident_type_security_display_name
}

# Create: Major Incident
resource "pagerduty_incident_type" "major" {
  count        = local.enable_types ? 1 : 0
  name         = var.incident_type_major_name
  display_name = var.incident_type_major_display_name
  description  = "Highest impact, cross-service incidents requiring mobilization"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}

# Create: Security Incident
resource "pagerduty_incident_type" "security" {
  count        = local.enable_types ? 1 : 0
  name         = var.incident_type_security_name
  display_name = var.incident_type_security_display_name
  description  = "Security events requiring incident response procedures"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}

# Create: Infrastructure Outage
resource "pagerduty_incident_type" "infrastructure" {
  count        = local.enable_types ? 1 : 0
  name         = "Infrastructure Outage"
  display_name = "Infrastructure Outage"
  description  = "Platform, network, or database infrastructure failures"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}

# Create: Customer Impacting
resource "pagerduty_incident_type" "customer_impacting" {
  count        = local.enable_types ? 1 : 0
  name         = "Customer Impacting"
  display_name = "Customer Impacting"
  description  = "Incidents with direct customer-facing impact"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}

# Create: Planned Maintenance
resource "pagerduty_incident_type" "maintenance" {
  count        = local.enable_types ? 1 : 0
  name         = "Planned Maintenance"
  display_name = "Planned Maintenance"
  description  = "Scheduled maintenance activities"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}

# Create: Third-Party/Vendor Issue
resource "pagerduty_incident_type" "vendor" {
  count        = local.enable_types ? 1 : 0
  name         = "Vendor Issue"
  display_name = "Third-Party/Vendor Issue"
  description  = "Incidents caused by third-party vendors or external dependencies"
  parent_type  = data.pagerduty_incident_type.base.id

  lifecycle {
    prevent_destroy = true
  }
}
