# variables_jira.tf
variable "jira_project_key" {
  description = "Jira project key (e.g., KAN)"
  type        = string
  default     = "KAN"
}
