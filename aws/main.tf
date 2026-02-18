terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

variable "aws_access_key" {
  type      = string
  sensitive = true
}

variable "aws_secret_key" {
  type      = string
  sensitive = true
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "spawn_probability" {
  type        = number
  default     = 0.3
  description = "Probability of spawning an incident (0.0-1.0)"
}

variable "schedule_expression" {
  type        = string
  default     = "rate(1 hour)"
  description = "EventBridge schedule expression"
}

variable "demo_controller_schedule" {
  type        = string
  default     = "cron(0 13,15,17,19,21 ? * MON-FRI *)"
  description = "EventBridge cron for demo controller (default: every 2h from 9AM-5PM Chilean time, weekdays)"
}

variable "demo_controller_action_delay" {
  type        = number
  default     = 45
  description = "Delay in seconds between scenario phases when triggered by EventBridge"
}

variable "pagerduty_admin_token" {
  type      = string
  sensitive = true
}

variable "slack_bot_token" {
  type      = string
  sensitive = true
}

variable "slack_channel" {
  type    = string
  default = "C08CHCAGX3K"
}

variable "slack_team_id" {
  type    = string
  default = ""
}

variable "routing_key_dbre" {
  type      = string
  sensitive = true
}

variable "routing_key_api" {
  type      = string
  sensitive = true
}

variable "routing_key_k8s" {
  type      = string
  sensitive = true
}

variable "routing_key_streaming" {
  type      = string
  sensitive = true
}

variable "pagerduty_routing_key" {
  type      = string
  sensitive = true
}

variable "datadog_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "datadog_site" {
  type    = string
  default = "us5.datadoghq.com"
}

variable "newrelic_license_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "newrelic_account_id" {
  type    = string
  default = ""
}

variable "grafana_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

locals {
  function_name           = "demo-simulator-orchestrator"
  lifecycle_function_name = "demo-simulator-lifecycle"
  metrics_function_name   = "demo-simulator-metrics"
  notifier_function_name  = "demo-simulator-notifier"
  tags = {
    Project     = "pagerduty-demo"
    Environment = "demo"
    ManagedBy   = "terraform"
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-orchestrator"
  output_path = "${path.module}/lambda-orchestrator.zip"
}

data "archive_file" "metrics_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-metrics"
  output_path = "${path.module}/lambda-metrics.zip"
}

data "archive_file" "notifier_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-notifier"
  output_path = "${path.module}/lambda-notifier.zip"
}

data "archive_file" "lifecycle_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-lifecycle"
  output_path = "${path.module}/lambda-lifecycle.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:PutParameter"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/demo-simulator/*"
      }
    ]
  })
}

resource "aws_lambda_function" "orchestrator" {
  function_name = local.function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL             = "INFO"
      PAGERDUTY_ADMIN_TOKEN = var.pagerduty_admin_token
      ROUTING_KEY_DBRE      = var.routing_key_dbre
      ROUTING_KEY_API       = var.routing_key_api
      ROUTING_KEY_K8S       = var.routing_key_k8s
      ROUTING_KEY_STREAMING = var.routing_key_streaming
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "lifecycle" {
  function_name = local.lifecycle_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 256

  filename         = data.archive_file.lifecycle_zip.output_path
  source_code_hash = data.archive_file.lifecycle_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL                      = "INFO"
      PAGERDUTY_ADMIN_TOKEN          = var.pagerduty_admin_token
      SLACK_BOT_TOKEN                = var.slack_bot_token
      SLACK_CHANNEL_ACTIVE_INCIDENTS = var.slack_channel
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "metrics" {
  function_name = local.metrics_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 256

  filename         = data.archive_file.metrics_zip.output_path
  source_code_hash = data.archive_file.metrics_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL             = "INFO"
      DATADOG_API_KEY       = var.datadog_api_key
      DATADOG_SITE          = var.datadog_site
      NEW_RELIC_LICENSE_KEY = var.newrelic_license_key
      NEW_RELIC_ACCOUNT_ID  = var.newrelic_account_id
      PAGERDUTY_ROUTING_KEY = var.pagerduty_routing_key
      SLACK_BOT_TOKEN       = var.slack_bot_token
      SLACK_CHANNEL         = var.slack_channel
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "notifier" {
  function_name = local.notifier_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 128

  filename         = data.archive_file.notifier_zip.output_path
  source_code_hash = data.archive_file.notifier_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL             = "INFO"
      PAGERDUTY_ADMIN_TOKEN = var.pagerduty_admin_token
      SLACK_BOT_TOKEN       = var.slack_bot_token
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 7

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "lifecycle_logs" {
  name              = "/aws/lambda/${local.lifecycle_function_name}"
  retention_in_days = 7

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "metrics_logs" {
  name              = "/aws/lambda/${local.metrics_function_name}"
  retention_in_days = 7

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "notifier_logs" {
  name              = "/aws/lambda/${local.notifier_function_name}"
  retention_in_days = 7

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${local.function_name}-schedule"
  description         = "Trigger demo-simulator orchestrator on schedule"
  schedule_expression = var.schedule_expression

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "lifecycle_schedule" {
  name                = "${local.lifecycle_function_name}-schedule"
  description         = "Process incident lifecycle (ack, notes, resolve)"
  schedule_expression = "rate(15 minutes)"

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "metrics_schedule" {
  name                = "${local.metrics_function_name}-schedule"
  description         = "Send metrics to Datadog and New Relic"
  schedule_expression = "rate(5 minutes)"

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "notifier_schedule" {
  name                = "${local.notifier_function_name}-schedule"
  description         = "Check for new demo scenario channels and notify conallP"
  schedule_expression = "rate(2 minutes)"

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "lambda"
  arn       = aws_lambda_function.orchestrator.arn

  input = jsonencode({
    probability = var.spawn_probability
  })
}

resource "aws_cloudwatch_event_target" "lifecycle" {
  rule      = aws_cloudwatch_event_rule.lifecycle_schedule.name
  target_id = "lifecycle"
  arn       = aws_lambda_function.lifecycle.arn
}

resource "aws_cloudwatch_event_target" "metrics" {
  rule      = aws_cloudwatch_event_rule.metrics_schedule.name
  target_id = "metrics"
  arn       = aws_lambda_function.metrics.arn

  input = jsonencode({
    spike_probability = 0.05
  })
}

resource "aws_cloudwatch_event_target" "notifier" {
  rule      = aws_cloudwatch_event_rule.notifier_schedule.name
  target_id = "notifier"
  arn       = aws_lambda_function.notifier.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orchestrator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

resource "aws_lambda_permission" "lifecycle_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lifecycle.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lifecycle_schedule.arn
}

resource "aws_lambda_permission" "metrics_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metrics.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.metrics_schedule.arn
}

resource "aws_lambda_permission" "notifier_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.notifier_schedule.arn
}

data "archive_file" "user_activity_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-user-activity"
  output_path = "${path.module}/lambda-user-activity.zip"
}

data "archive_file" "health_check_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-health-check"
  output_path = "${path.module}/lambda-health-check.zip"
}

data "archive_file" "reset_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-reset"
  output_path = "${path.module}/lambda-reset.zip"
}

variable "grafana_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "grafana_url" {
  type    = string
  default = "https://conalllynch88.grafana.net"
}

variable "newrelic_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "jira_email" {
  type    = string
  default = ""
}

variable "jira_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "jira_url" {
  type    = string
  default = "https://losandes.atlassian.net"
}

resource "aws_lambda_function" "user_activity" {
  function_name = "demo-simulator-user-activity"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 128

  filename         = data.archive_file.user_activity_zip.output_path
  source_code_hash = data.archive_file.user_activity_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL       = "INFO"
      PAGERDUTY_TOKEN = var.pagerduty_admin_token
      SLACK_BOT_TOKEN = var.slack_bot_token
      SLACK_CHANNEL   = var.slack_channel
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "health_check" {
  function_name = "demo-simulator-health-check"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 128

  filename         = data.archive_file.health_check_zip.output_path
  source_code_hash = data.archive_file.health_check_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL         = "INFO"
      PAGERDUTY_TOKEN   = var.pagerduty_admin_token
      DATADOG_API_KEY   = var.datadog_api_key
      DATADOG_SITE      = var.datadog_site
      NEW_RELIC_API_KEY = var.newrelic_api_key
      GRAFANA_TOKEN     = var.grafana_token
      GRAFANA_URL       = var.grafana_url
      SLACK_BOT_TOKEN   = var.slack_bot_token
      SLACK_CHANNEL     = var.slack_channel
      JIRA_EMAIL        = var.jira_email
      JIRA_TOKEN        = var.jira_token
      JIRA_URL          = var.jira_url
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "reset" {
  function_name = "demo-simulator-reset"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 120
  memory_size   = 256

  filename         = data.archive_file.reset_zip.output_path
  source_code_hash = data.archive_file.reset_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL             = "INFO"
      PAGERDUTY_TOKEN       = var.pagerduty_admin_token
      ADMIN_EMAIL           = "clynch@pagerduty.com"
      SLACK_BOT_TOKEN       = var.slack_bot_token
      SLACK_CHANNEL         = var.slack_channel
      PAGERDUTY_ROUTING_KEY = var.routing_key_k8s
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "user_activity_logs" {
  name              = "/aws/lambda/demo-simulator-user-activity"
  retention_in_days = 7
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "health_check_logs" {
  name              = "/aws/lambda/demo-simulator-health-check"
  retention_in_days = 7
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "reset_logs" {
  name              = "/aws/lambda/demo-simulator-reset"
  retention_in_days = 7
  tags              = local.tags
}

data "archive_file" "demo_controller_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-demo-controller"
  output_path = "${path.module}/lambda-demo-controller.zip"
}

resource "aws_lambda_function" "demo_controller" {
  function_name = "demo-simulator-controller"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 512

  filename         = data.archive_file.demo_controller_zip.output_path
  source_code_hash = data.archive_file.demo_controller_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL                    = "INFO"
      PAGERDUTY_ADMIN_TOKEN        = var.pagerduty_admin_token
      PAGERDUTY_TOKEN              = var.pagerduty_admin_token
      SLACK_BOT_TOKEN              = var.slack_bot_token
      SLACK_CHANNEL                = var.slack_channel
      SLACK_TEAM_ID                = var.slack_team_id
      ROUTING_KEY_DBRE             = var.routing_key_dbre
      ROUTING_KEY_API              = var.routing_key_api
      ROUTING_KEY_K8S              = var.routing_key_k8s
      ROUTING_KEY_STREAMING        = var.routing_key_streaming
      ACTION_DELAY_MIN             = "30"
      ACTION_DELAY_MAX             = "60"
      SCENARIOS_FILE               = "/var/task/scenarios.json"
      SSM_RECENT_SCENARIOS_PARAM   = aws_ssm_parameter.recent_scenarios.name
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "demo_controller_logs" {
  name              = "/aws/lambda/demo-simulator-controller"
  retention_in_days = 7
  tags              = local.tags
}

resource "aws_ssm_parameter" "recent_scenarios" {
  name  = "/demo-simulator/recent-scenarios"
  type  = "String"
  value = "[]"

  lifecycle {
    ignore_changes = [value]
  }

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "demo_controller_schedule" {
  name                = "demo-simulator-controller-daily"
  description         = "Run random demo scenario every 2h during Chilean business hours (9AM-5PM CLT)"
  schedule_expression = var.demo_controller_schedule

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "demo_controller" {
  rule      = aws_cloudwatch_event_rule.demo_controller_schedule.name
  target_id = "demo-controller"
  arn       = aws_lambda_function.demo_controller.arn

  input = jsonencode({
    action       = "run_random"
    action_delay = var.demo_controller_action_delay
  })
}

resource "aws_lambda_permission" "demo_controller_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.demo_controller.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.demo_controller_schedule.arn
}

resource "aws_cloudwatch_event_rule" "user_activity_schedule" {
  name                = "demo-simulator-user-activity-schedule"
  description         = "Simulate user activity on [DEMO] incidents (weekdays 9-17 UTC)"
  schedule_expression = "cron(0/15 9-17 ? * MON-FRI *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "health_check_schedule" {
  name                = "demo-simulator-health-check-schedule"
  description         = "Check integration health every 15 minutes"
  schedule_expression = "rate(15 minutes)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_target" "user_activity" {
  rule      = aws_cloudwatch_event_rule.user_activity_schedule.name
  target_id = "user-activity"
  arn       = aws_lambda_function.user_activity.arn

  input = jsonencode({
    num_actions = 1
  })
}

resource "aws_cloudwatch_event_target" "health_check" {
  rule      = aws_cloudwatch_event_rule.health_check_schedule.name
  target_id = "health-check"
  arn       = aws_lambda_function.health_check.arn

  input = jsonencode({
    post_to_slack = false
  })
}

resource "aws_lambda_permission" "user_activity_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_activity.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.user_activity_schedule.arn
}

resource "aws_lambda_permission" "health_check_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.health_check_schedule.arn
}

output "lambda_function_arn" {
  value = aws_lambda_function.orchestrator.arn
}

output "schedule_rule_arn" {
  value = aws_cloudwatch_event_rule.schedule.arn
}

output "lifecycle_function_arn" {
  value = aws_lambda_function.lifecycle.arn
}

output "lifecycle_schedule_arn" {
  value = aws_cloudwatch_event_rule.lifecycle_schedule.arn
}

output "metrics_function_arn" {
  value = aws_lambda_function.metrics.arn
}

output "metrics_schedule_arn" {
  value = aws_cloudwatch_event_rule.metrics_schedule.arn
}

output "notifier_function_arn" {
  value = aws_lambda_function.notifier.arn
}

output "notifier_schedule_arn" {
  value = aws_cloudwatch_event_rule.notifier_schedule.arn
}

output "user_activity_function_arn" {
  value = aws_lambda_function.user_activity.arn
}

output "user_activity_schedule_arn" {
  value = aws_cloudwatch_event_rule.user_activity_schedule.arn
}

output "health_check_function_arn" {
  value = aws_lambda_function.health_check.arn
}

output "health_check_schedule_arn" {
  value = aws_cloudwatch_event_rule.health_check_schedule.arn
}

output "reset_function_arn" {
  value = aws_lambda_function.reset.arn
}

resource "aws_sns_topic" "pagerduty_alerts" {
  name = "demo-simulator-pagerduty-alerts"
}

resource "aws_sns_topic_subscription" "pagerduty" {
  topic_arn = aws_sns_topic.pagerduty_alerts.arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/${var.routing_key_k8s}/enqueue"
}

resource "aws_cloudwatch_metric_alarm" "demo_api_latency" {
  alarm_name          = "demo-api-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "demo.api.response_time"
  namespace           = "DemoSimulator"
  period              = 60
  statistic           = "Average"
  threshold           = 500
  alarm_description   = "[DEMO] API response time exceeded threshold"

  alarm_actions = [aws_sns_topic.pagerduty_alerts.arn]
  ok_actions    = [aws_sns_topic.pagerduty_alerts.arn]

  dimensions = {
    Environment = "production"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Demo        = "true"
    Integration = "cloudwatch"
  }
}

resource "aws_cloudwatch_metric_alarm" "demo_error_rate" {
  alarm_name          = "demo-api-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "demo.api.error_rate"
  namespace           = "DemoSimulator"
  period              = 60
  statistic           = "Average"
  threshold           = 5
  alarm_description   = "[DEMO] API error rate exceeded threshold"

  alarm_actions = [aws_sns_topic.pagerduty_alerts.arn]
  ok_actions    = [aws_sns_topic.pagerduty_alerts.arn]

  dimensions = {
    Environment = "production"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Demo        = "true"
    Integration = "cloudwatch"
  }
}

resource "aws_cloudwatch_metric_alarm" "demo_db_connections" {
  alarm_name          = "demo-database-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "demo.database.connections"
  namespace           = "DemoSimulator"
  period              = 60
  statistic           = "Maximum"
  threshold           = 90
  alarm_description   = "[DEMO] Database connection pool nearing exhaustion"

  alarm_actions = [aws_sns_topic.pagerduty_alerts.arn]
  ok_actions    = [aws_sns_topic.pagerduty_alerts.arn]

  dimensions = {
    Environment = "production"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Demo        = "true"
    Integration = "cloudwatch"
  }
}

output "sns_topic_arn" {
  value = aws_sns_topic.pagerduty_alerts.arn
}

output "cloudwatch_alarm_api_latency" {
  value = aws_cloudwatch_metric_alarm.demo_api_latency.arn
}

output "cloudwatch_alarm_error_rate" {
  value = aws_cloudwatch_metric_alarm.demo_error_rate.arn
}

output "cloudwatch_alarm_db_connections" {
  value = aws_cloudwatch_metric_alarm.demo_db_connections.arn
}

resource "aws_cloudwatch_metric_alarm" "demo_controller_errors" {
  alarm_name          = "demo-controller-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "Demo controller Lambda errors detected — Slack operations may be failing"

  alarm_actions = [aws_sns_topic.pagerduty_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.demo_controller.function_name
  }

  treat_missing_data = "notBreaching"

  tags = local.tags
}

