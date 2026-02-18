############################################################
# variables_comms.tf — Slack + Jira variables (no duplicates)
############################################################

# Slack (native Create Channel)
variable "slack_workspace_id" {
  type        = string
  default     = "E0A9LN3JFBQ"
  description = "Slack Team ID. PDT Los Andes workspace."
}

variable "slack_channel_private" {
  type        = bool
  default     = true
  description = "Create private incident channels when true."
}

variable "slack_pin_incident_link" {
  type        = bool
  default     = true
  description = "Pin the PagerDuty incident link in the created Slack channel."
}

# Do NOT declare slack_channel_prefix here if it already exists elsewhere.

# Jira Cloud (native Create Issue)
variable "jira_site_base_url" {
  type        = string
  default     = null
  description = "Base URL of the Jira Cloud site, e.g., https://example.atlassian.net"
}

variable "jira_account_name" {
  type        = string
  default     = "losandes"
  description = "PagerDuty Jira Cloud connected account display name."
}

variable "jira_issue_type" {
  type        = string
  default     = "Incident"
  description = "Issue type to create (e.g., Incident, Bug, Task)."
}

variable "jira_summary_template" {
  type        = string
  default     = "[INC-{{incident.number}}] {{incident.title}}"
  description = "Summary template for the Jira issue."
}

variable "jira_description_template" {
  type        = string
  default     = "Incident: {{incident.html_url}}\nService: {{incident.service.name}}\nPriority: {{incident.priority.name}}\nDescription: {{incident.description}}"
  description = "Description template for the Jira issue."
}

# Jeli Post-Incident Reviews
variable "jeli_connection_id" {
  type        = string
  default     = null
  description = "Jeli Workflow Integration connection ID. When set, enables automatic PIR creation workflows."
}
