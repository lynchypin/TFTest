data "archive_file" "demo_orchestrator" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-demo-orchestrator"
  output_path = "${path.module}/lambda-demo-orchestrator.zip"
}

resource "aws_dynamodb_table" "demo_state" {
  name         = "demo-incident-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "demo-incident-state"
    Environment = "demo"
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role" "demo_orchestrator" {
  name = "demo-orchestrator-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "demo_orchestrator_policy" {
  name = "demo-orchestrator-policy"
  role = aws_iam_role.demo_orchestrator.id

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
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.demo_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "scheduler:CreateSchedule",
          "scheduler:DeleteSchedule",
          "scheduler:GetSchedule"
        ]
        Resource = "arn:aws:scheduler:*:*:schedule/default/demo-*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = aws_iam_role.scheduler_role.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "PagerDutyDemo"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role" "scheduler_role" {
  name = "demo-scheduler-invoke-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_policy" {
  name = "scheduler-invoke-lambda"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.demo_orchestrator.arn
      }
    ]
  })
}

resource "aws_lambda_function" "demo_orchestrator" {
  filename         = data.archive_file.demo_orchestrator.output_path
  function_name    = "demo-simulator-orchestrator-v2"
  role             = aws_iam_role.demo_orchestrator.arn
  handler          = "handler.lambda_handler"
  source_code_hash = data.archive_file.demo_orchestrator.output_base64sha256
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      PAGERDUTY_TOKEN      = var.pagerduty_admin_token
      SLACK_BOT_TOKEN      = var.slack_bot_token
      DEMO_STATE_TABLE     = aws_dynamodb_table.demo_state.name
      SELF_LAMBDA_ARN      = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:demo-simulator-orchestrator-v2"
      SCHEDULER_ROLE_ARN   = aws_iam_role.scheduler_role.arn
      WEBHOOK_SECRET       = var.webhook_secret
      DATADOG_API_KEY      = var.datadog_api_key
      DATADOG_SITE         = var.datadog_site
      GRAFANA_API_KEY      = var.grafana_api_key
      GRAFANA_URL          = var.grafana_url
      NEWRELIC_API_KEY     = var.newrelic_api_key
      NEWRELIC_ACCOUNT_ID  = var.newrelic_account_id
      PAGERDUTY_ROUTING_KEY = var.pagerduty_routing_key
      CLOUDWATCH_NAMESPACE = "PagerDutyDemo"
    }
  }

  depends_on = [
    aws_iam_role_policy.demo_orchestrator_policy
  ]

  tags = {
    Name        = "demo-simulator-orchestrator-v2"
    Environment = "demo"
    ManagedBy   = "terraform"
  }
}

resource "aws_lambda_function_url" "demo_orchestrator" {
  function_name      = aws_lambda_function.demo_orchestrator.function_name
  authorization_type = "NONE"

  cors {
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    expose_headers    = ["*"]
    max_age           = 86400
    allow_credentials = false
  }
}

resource "aws_lambda_permission" "demo_orchestrator_url" {
  statement_id           = "AllowPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.demo_orchestrator.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

variable "webhook_secret" {
  description = "PagerDuty webhook signature secret"
  type        = string
  default     = ""
  sensitive   = true
}

output "demo_orchestrator_url" {
  description = "URL for the demo orchestrator Lambda"
  value       = aws_lambda_function_url.demo_orchestrator.function_url
}

output "demo_state_table" {
  description = "DynamoDB table for demo state"
  value       = aws_dynamodb_table.demo_state.name
}

resource "aws_apigatewayv2_api" "demo_orchestrator" {
  name          = "demo-orchestrator-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 86400
  }
}

resource "aws_apigatewayv2_stage" "demo_orchestrator" {
  api_id      = aws_apigatewayv2_api.demo_orchestrator.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "demo_orchestrator" {
  api_id                 = aws_apigatewayv2_api.demo_orchestrator.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.demo_orchestrator.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "demo_orchestrator_default" {
  api_id    = aws_apigatewayv2_api.demo_orchestrator.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.demo_orchestrator.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.demo_orchestrator.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.demo_orchestrator.execution_arn}/*/*"
}

output "demo_orchestrator_api_url" {
  description = "API Gateway URL for the demo orchestrator"
  value       = aws_apigatewayv2_stage.demo_orchestrator.invoke_url
}
