variable "slack_connection_id" {
  description = "Slack connection ID for workflow integrations"
  type        = string
  default     = "SLACK_CONN_ID"
}

variable "legal_user_id" {
  description = "PagerDuty user ID for legal team contact"
  type        = string
  default     = "PLACEHOLDER_LEGAL_USER"
}

variable "dpo_user_id" {
  description = "PagerDuty user ID for Data Protection Officer"
  type        = string
  default     = "PLACEHOLDER_DPO_USER"
}

variable "ciso_user_id" {
  description = "PagerDuty user ID for Chief Information Security Officer"
  type        = string
  default     = "PLACEHOLDER_CISO_USER"
}

variable "finance_oncall_user_id" {
  description = "PagerDuty user ID for finance on-call contact"
  type        = string
  default     = "PLACEHOLDER_FINANCE_USER"
}

variable "customer_success_lead_id" {
  description = "PagerDuty user ID for customer success lead"
  type        = string
  default     = "PLACEHOLDER_CS_LEAD"
}

variable "primary_oncall_user_id" {
  description = "PagerDuty user ID for primary on-call"
  type        = string
  default     = "PLACEHOLDER_ONCALL_USER"
}

variable "siem_webhook_url" {
  description = "Webhook URL for SIEM integration"
  type        = string
  default     = "https://siem.company.com/webhook/pagerduty"
}

variable "siem_api_token" {
  description = "API token for SIEM authentication"
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER_SIEM_TOKEN"
}

variable "pagerduty_api_key" {
  description = "PagerDuty API key for automation actions"
  type        = string
  sensitive   = true
  default     = ""
}

variable "runbook_api_key" {
  description = "API key for PagerDuty Automation Actions runners"
  type        = string
  sensitive   = true
}
