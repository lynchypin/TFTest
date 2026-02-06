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

resource "aws_lambda_function_url" "orchestrator" {
  function_name      = aws_lambda_function.orchestrator.function_name
  authorization_type = "NONE"
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
      LOG_LEVEL             = "INFO"
      PAGERDUTY_ADMIN_TOKEN = var.pagerduty_admin_token
      PAGERDUTY_TOKEN       = var.pagerduty_admin_token
      SLACK_BOT_TOKEN       = var.slack_bot_token
      SLACK_CHANNEL         = var.slack_channel
      ROUTING_KEY_DBRE      = var.routing_key_dbre
      ROUTING_KEY_API       = var.routing_key_api
      ROUTING_KEY_K8S       = var.routing_key_k8s
      ROUTING_KEY_STREAMING = var.routing_key_streaming
      ACTION_DELAY_MIN      = "30"
      ACTION_DELAY_MAX      = "60"
      SCENARIOS_FILE        = "/var/task/scenarios.json"
    }
  }

  tags = local.tags
}

resource "aws_lambda_function_url" "demo_controller" {
  function_name      = aws_lambda_function.demo_controller.function_name
  authorization_type = "NONE"
}

resource "aws_cloudwatch_log_group" "demo_controller_logs" {
  name              = "/aws/lambda/demo-simulator-controller"
  retention_in_days = 7
  tags              = local.tags
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

resource "aws_lambda_function_url" "reset" {
  function_name      = aws_lambda_function.reset.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_function_url" "health_check" {
  function_name      = aws_lambda_function.health_check.function_name
  authorization_type = "NONE"
}

output "lambda_function_arn" {
  value = aws_lambda_function.orchestrator.arn
}

output "lambda_function_url" {
  value = aws_lambda_function_url.orchestrator.function_url
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

output "health_check_function_url" {
  value = aws_lambda_function_url.health_check.function_url
}

output "health_check_schedule_arn" {
  value = aws_cloudwatch_event_rule.health_check_schedule.arn
}

output "reset_function_arn" {
  value = aws_lambda_function.reset.arn
}

output "reset_function_url" {
  value       = aws_lambda_function_url.reset.function_url
  description = "URL to invoke demo reset. Use ?mode=quick or ?mode=full"
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

variable "rba_runner_token" {
  type      = string
  sensitive = true
  default   = "OFQxJ44WT15xGXhywkhXf8xP7mpi5m8L"
}

variable "rba_runner_id" {
  type    = string
  default = "4da17208-b265-40f6-a57f-88aa7275ce2b"
}

variable "rba_download_token" {
  type    = string
  default = "0e847bbb-7e2f-4e6d-ae0c-6618d853046a"
}

variable "rba_url" {
  type    = string
  default = "https://csmscale.runbook.pagerduty.cloud"
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "rba_runner" {
  name        = "rba-runner-sg"
  description = "Security group for RBA runner - outbound only"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(local.tags, {
    Name = "rba-runner-sg"
  })
}

resource "aws_iam_role" "rba_runner_role" {
  name = "rba-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "rba_runner_ssm" {
  role       = aws_iam_role.rba_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "rba_runner_profile" {
  name = "rba-runner-profile"
  role = aws_iam_role.rba_runner_role.name
}

resource "aws_instance" "rba_runner" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t2.micro"
  iam_instance_profile   = aws_iam_instance_profile.rba_runner_profile.name
  vpc_security_group_ids = [aws_security_group.rba_runner.id]

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -ex

    exec > /var/log/rba-runner-setup.log 2>&1

    echo "Starting RBA Runner setup..."

    yum update -y
    yum install -y java-17-amazon-corretto docker

    systemctl start docker
    systemctl enable docker

    mkdir -p /opt/rba-runner
    cd /opt/rba-runner

    cat > /opt/rba-runner/start-runner.sh << 'SCRIPT'
    #!/bin/bash
    docker run -d \
      --name rba-runner \
      --restart unless-stopped \
      -e RUNNER_RUNDECK_URL="${var.rba_url}" \
      -e RUNNER_RUNDECK_TOKEN="${var.rba_runner_token}" \
      -e RUNNER_ID="${var.rba_runner_id}" \
      rundeckpro/runner:latest
    SCRIPT
    chmod +x /opt/rba-runner/start-runner.sh

    docker pull rundeckpro/runner:latest

    docker run -d \
      --name rba-runner \
      --restart unless-stopped \
      -e RUNNER_RUNDECK_URL="${var.rba_url}" \
      -e RUNNER_RUNDECK_TOKEN="${var.rba_runner_token}" \
      -e RUNNER_ID="${var.rba_runner_id}" \
      rundeckpro/runner:latest

    echo "RBA Runner setup complete!"
  EOF
  )

  tags = merge(local.tags, {
    Name = "rba-cloud-runner"
  })

  lifecycle {
    create_before_destroy = true
  }
}

output "rba_runner_instance_id" {
  value = aws_instance.rba_runner.id
}

output "rba_runner_private_ip" {
  value = aws_instance.rba_runner.private_ip
}
