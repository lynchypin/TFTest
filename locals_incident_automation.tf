terraform {
  required_version = ">= 1.4.0"
}

locals {
  enable_resources = var.enable_incident_automation

  # Workflow display names
  wf_major_name    = var.wf_major_name
  wf_security_name = var.wf_security_name

  # Trigger conditions
  # Major = Priority P1 or P2
  major_auto_mobilize_condition = {
    operator = "or"
    subconditions = [
      { operator = "contains", parameter = { path = "incident.priority.name", value = "P1" } },
      { operator = "contains", parameter = { path = "incident.priority.name", value = "P2" } },
    ]
  }

  # Security IR = Incident Type equals "Security Incident"
  security_ir_condition = {
    operator = "and"
    subconditions = [
      { operator = "equals", parameter = { path = "incident.incident_type.name", value = "Security Incident" } },
    ]
  }
}
