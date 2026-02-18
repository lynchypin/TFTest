# integrations.tf
#
# Direct API integrations (routing keys) for the Global Event Orchestration.
# LIMIT: 10 integrations per orchestration (PagerDuty limit)
# Keeping only FREE FOREVER tools (no time-limited trials)

# Core monitoring integrations
resource "pagerduty_event_orchestration_integration" "prometheus" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "Prometheus/Alertmanager"
}

resource "pagerduty_event_orchestration_integration" "new_relic" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "New Relic (Free Forever)"
}

resource "pagerduty_event_orchestration_integration" "sentry" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "Sentry"
}

resource "pagerduty_event_orchestration_integration" "uptime_robot" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "UptimeRobot"
}

resource "pagerduty_event_orchestration_integration" "github_actions" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "GitHub Actions"
}

resource "pagerduty_event_orchestration_integration" "grafana_cloud" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "Grafana Cloud"
}

resource "pagerduty_event_orchestration_integration" "aws_cloudwatch" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "AWS CloudWatch"
}

resource "pagerduty_event_orchestration_integration" "datadog" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "Datadog (Free Forever)"
}

resource "pagerduty_event_orchestration_integration" "splunk" {
  event_orchestration = pagerduty_event_orchestration.demo_orchestration.id
  label               = "Splunk"
}

# ============================================================================
# Outputs - Routing Keys
# ============================================================================
output "prometheus_routing_key" {
  value       = pagerduty_event_orchestration_integration.prometheus.parameters[0].routing_key
  description = "Routing key for Prometheus/Alertmanager"
  sensitive   = true
}

output "new_relic_routing_key" {
  value       = pagerduty_event_orchestration_integration.new_relic.parameters[0].routing_key
  description = "Routing key for New Relic"
  sensitive   = true
}

output "sentry_routing_key" {
  value       = pagerduty_event_orchestration_integration.sentry.parameters[0].routing_key
  description = "Routing key for Sentry"
  sensitive   = true
}

output "uptime_robot_routing_key" {
  value       = pagerduty_event_orchestration_integration.uptime_robot.parameters[0].routing_key
  description = "Routing key for UptimeRobot"
  sensitive   = true
}

output "github_actions_routing_key" {
  value       = pagerduty_event_orchestration_integration.github_actions.parameters[0].routing_key
  description = "Routing key for GitHub Actions"
  sensitive   = true
}

output "grafana_cloud_routing_key" {
  value       = pagerduty_event_orchestration_integration.grafana_cloud.parameters[0].routing_key
  description = "Routing key for Grafana Cloud"
  sensitive   = true
}

output "aws_cloudwatch_routing_key" {
  value       = pagerduty_event_orchestration_integration.aws_cloudwatch.parameters[0].routing_key
  description = "Routing key for AWS CloudWatch"
  sensitive   = true
}

output "datadog_routing_key" {
  value       = pagerduty_event_orchestration_integration.datadog.parameters[0].routing_key
  description = "Routing key for Datadog"
  sensitive   = true
}

output "splunk_routing_key" {
  value       = pagerduty_event_orchestration_integration.splunk.parameters[0].routing_key
  description = "Routing key for Splunk"
  sensitive   = true
}

# All routing keys as a map
output "all_routing_keys" {
  value = {
    prometheus     = pagerduty_event_orchestration_integration.prometheus.parameters[0].routing_key
    new_relic      = pagerduty_event_orchestration_integration.new_relic.parameters[0].routing_key
    sentry         = pagerduty_event_orchestration_integration.sentry.parameters[0].routing_key
    uptime_robot   = pagerduty_event_orchestration_integration.uptime_robot.parameters[0].routing_key
    github_actions = pagerduty_event_orchestration_integration.github_actions.parameters[0].routing_key
    grafana_cloud  = pagerduty_event_orchestration_integration.grafana_cloud.parameters[0].routing_key
    aws_cloudwatch = pagerduty_event_orchestration_integration.aws_cloudwatch.parameters[0].routing_key
    datadog        = pagerduty_event_orchestration_integration.datadog.parameters[0].routing_key
    splunk         = pagerduty_event_orchestration_integration.splunk.parameters[0].routing_key
  }
  description = "All orchestration routing keys"
  sensitive   = true
}