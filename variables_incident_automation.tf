terraform {
  required_version = ">= 1.4.0"
}

############################################################
# Master toggles and naming
############################################################
variable "enable_incident_automation" {
  type        = bool
  default     = false
  description = "Global toggle to enable incident automation resources"
}

variable "naming_prefix" {
  type        = string
  default     = "pd-demo"
  description = "Prefix for names of created resources"
}

############################################################
# Incident Types (optional creation)
############################################################
variable "create_incident_types" {
  type        = bool
  default     = false
  description = "Create Incident Types via Terraform. If false, types must already exist."
}

variable "incident_type_major_name" {
  type        = string
  default     = "Major Incident"
  description = "API name for the Major Incident type"
}

variable "incident_type_security_name" {
  type        = string
  default     = "Security Incident"
  description = "API name for the Security Incident type"
}

variable "incident_type_major_display_name" {
  type        = string
  default     = "Major Incident"
  description = "Display name for the Major Incident type"
}

variable "incident_type_security_display_name" {
  type        = string
  default     = "Security Incident"
  description = "Display name for the Security Incident type"
}

############################################################
# Workflow names
############################################################
variable "wf_major_name" {
  description = "Name for the Major Incident Auto-Mobilization workflow"
  type        = string
  default     = "LosAndes - Major Incident Auto-Mobilization"
}

variable "wf_security_name" {
  description = "Name for the Security Incident Response workflow"
  type        = string
  default     = "LosAndes - Security Incident Response"
}

############################################################
# Trigger service scoping (pass service names; IDs auto-resolved)
############################################################
variable "major_auto_mobilize_service_names" {
  description = "Services to subscribe Major Incident Auto-Mobilization trigger to (empty = all)"
  type        = list(string)
  default     = []
}

variable "security_ir_service_names" {
  description = "Services to subscribe Security IR trigger to (empty = all)"
  type        = list(string)
  default     = []
}

############################################################
# Optional Slack steps (native) – flags only (the ID already exists elsewhere)
############################################################
variable "enable_slack_actions" {
  description = "Enable Slack steps in workflows"
  type        = bool
  default     = false
}

variable "slack_channel_visibility" {
  description = "Slack channel visibility: public or private"
  type        = string
  default     = "public"
  validation {
    condition     = contains(["public", "private"], var.slack_channel_visibility)
    error_message = "slack_channel_visibility must be 'public' or 'private'."
  }
}

############################################################
# Optional Jira steps (native) – flags only (connection vars already exist elsewhere)
############################################################
variable "enable_jira_actions" {
  description = "Enable Jira issue creation steps in workflows"
  type        = bool
  default     = false
}
