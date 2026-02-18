resource "pagerduty_incident_custom_field" "affected_system" {
  name         = "affected_system"
  display_name = "Affected System"
  data_type    = "string"
  field_type   = "single_value"
  description  = "The primary system or component affected by this incident"
}

resource "pagerduty_incident_custom_field" "customer_tier" {
  name          = "customer_tier"
  display_name  = "Customer Tier"
  data_type     = "string"
  field_type    = "single_value"
  description   = "The tier of customers impacted (Enterprise, Business, Free, Internal)"
  default_value = "Internal"
}

resource "pagerduty_incident_custom_field" "region" {
  name          = "region"
  display_name  = "Affected Region"
  data_type     = "string"
  field_type    = "single_value"
  description   = "Geographic region affected by the incident (US-East, US-West, EU-West, APAC, Global)"
  default_value = "Global"
}

resource "pagerduty_incident_custom_field" "compliance_flag" {
  name          = "compliance_flag"
  display_name  = "Compliance Requirement"
  data_type     = "string"
  field_type    = "single_value"
  description   = "Compliance framework applicable to this incident (None, HIPAA, PCI-DSS, SOC2, GDPR)"
  default_value = "None"
}

resource "pagerduty_incident_custom_field" "incident_type" {
  name          = "incident_type"
  display_name  = "Incident Type"
  data_type     = "string"
  field_type    = "single_value"
  description   = "Category of incident for routing and reporting (Infrastructure, Application, Security, Database, Network, Third-Party)"
  default_value = "Application"
}

resource "pagerduty_incident_custom_field" "customer_impact_level" {
  name          = "customer_impact_level"
  display_name  = "Customer Impact Level"
  data_type     = "string"
  field_type    = "single_value"
  description   = "Severity of impact to customers (None, Minimal, Moderate, Significant, Critical)"
  default_value = "None"
}
