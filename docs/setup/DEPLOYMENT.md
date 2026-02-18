# PagerDuty Demo Environment - Deployment Guide

**Version:** 1.0
**Last Updated:** February 2026
**Status:** Production

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Component Overview](#component-overview)
4. [Terraform Deployment (PagerDuty)](#terraform-deployment-pagerduty)
5. [AWS Lambda Deployment](#aws-lambda-deployment)
6. [RBA Runner Deployment](#rba-runner-deployment)
7. [Datadog Monitor Setup](#datadog-monitor-setup)
8. [GitHub Pages Deployment](#github-pages-deployment)
9. [Credential Management](#credential-management)
10. [Verification and Testing](#verification-and-testing)
11. [Troubleshooting](#troubleshooting)
12. [Cost Management](#cost-management)

---

## Overview

> **ZERO-COST POLICY:** All infrastructure MUST be free or effectively zero-cost. Only pay-per-use AWS services are permitted (Lambda, DynamoDB on-demand, API Gateway). Do NOT provision EC2 instances, NAT gateways, RDS, ELBs, or any always-on compute. If a feature needs a runner or compute, use PagerDuty's built-in Process Automation Cloud or Lambda functions instead.

This guide covers the complete deployment of the PagerDuty Demo Environment, which consists of:

1. **PagerDuty Infrastructure** - Services, teams, workflows, etc. (via Terraform)
2. **AWS Lambda Functions** - Traffic simulation and incident lifecycle management (pay-per-invocation, zero idle cost)
3. ~~**EC2-based RBA Runner**~~ - **REMOVED** — Violates zero-cost policy. Use PagerDuty Process Automation Cloud instead (see `GOTCHAS_AND_WORKAROUNDS.md` TODO-2)
4. **Datadog Monitors** - For Full Flow integration triggers
5. **GitHub Pages Dashboard** - For triggering demo scenarios (free via GitHub Pages)

**Architecture Summary:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEMO ENVIRONMENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GitHub Pages          AWS Lambda              PagerDuty Automation          │
│  ┌──────────┐         ┌──────────┐           ┌──────────────┐               │
│  │ Dashboard │         │Controller│           │ Process Auto │               │
│  │ (React)   │────────▶│ Lambda   │────────▶  │ (Cloud)      │               │
│  └──────────┘         └──────────┘           └──────────────┘               │
│       │                    │                        │                        │
│       ▼                    ▼                        ▼                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         PagerDuty                                    │    │
│  │  • 12 Services    • 22 Workflows    • Event Orchestration           │    │
│  │  • 5 Teams        • 8 RBA Jobs      • Slack/Jira Extensions         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Datadog                                      │    │
│  │  7 Monitors → @pagerduty-demo-simulator-alerts                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Accounts and Access

| Account | Purpose | Required Permissions |
|---------|---------|----------------------|
| AWS | Lambda, EC2, S3, EventBridge | Admin or specific IAM policies |
| PagerDuty | Demo environment services | Account Admin |
| Datadog | Monitors for Full Flow | API Key + App Key |
| GitHub | Dashboard hosting | Push access to repo |
| Slack | Notifications | Bot token with org-level access |

### Required Tools

```bash
# Local development machine
terraform >= 1.0
aws-cli >= 2.0
python >= 3.9
node >= 18
jq
curl
```

### Environment Variables Required

> **SECURITY NOTE:** Do not hardcode credentials in documentation or source code. Use `CREDENTIALS_REFERENCE.md` for the credential inventory. Actual values should be stored securely and passed via environment variables or AWS Secrets Manager.

```bash
# PagerDuty
export PAGERDUTY_TOKEN="<see CREDENTIALS_REFERENCE.md>"
export PAGERDUTY_FROM_EMAIL="clynch@pagerduty.com"

# AWS (use `aws configure` or IAM roles — do not hardcode)
export AWS_REGION="us-east-1"

# Datadog (trial expired Feb 14 — graceful fallback in place)
export DATADOG_API_KEY="<see CREDENTIALS_REFERENCE.md>"
export DATADOG_APP_KEY="<see CREDENTIALS_REFERENCE.md>"

# Slack
export SLACK_BOT_TOKEN="<see CREDENTIALS_REFERENCE.md>"
export SLACK_TEAM_ID="T0A9LN53CPQ"  # REQUIRED for Enterprise Grid
```

---

## Component Overview

### Components and Their Locations

| Component | Location | Deployment Method |
|-----------|----------|-------------------|
| PagerDuty Services/Teams | `*.tf` (root) | Terraform |
| Lambda Functions | `aws/lambda-*/` | AWS CLI / Terraform |
| Lambda Terraform | `aws/main.tf` | Terraform |
| RBA Runner | EC2 Instance | SSM / Manual |
| Dashboard | `docs/demo-scenarios/` | GitHub Pages |
| Datadog Monitors | `aws/setup_integrations.py` | Python Script |

---

## Terraform Deployment (PagerDuty)

### Step 1: Initialize Terraform

```bash
cd /path/to/TFTest
terraform init
```

### Step 2: Review Variables

Edit `terraform.tfvars` with your PagerDuty API token:
```hcl
pagerduty_token = "<your-pagerduty-api-token>"
```

### Step 3: Plan and Apply

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

**IMPORTANT — Terraform State Management During Apply:**

PagerDuty Terraform applies can fail partway through due to API constraints (open incidents blocking schedule destruction, duplicate resources, etc.). When this happens, the state file may have drifted. The procedures below were established during the February 18, 2026 deployment.

#### Resolving Open Incidents Blocking Schedule Changes

If `terraform apply` fails with:
> `Error: It is not possible to continue with the destruction of the Schedule "PXXXXXX", because it is being used by multiple Escalation Policies which have only one layer configured.`

This means PagerDuty won't destroy a schedule that has open incidents. Resolve all open incidents first:

```bash
export PD_TOKEN="<see CREDENTIALS_REFERENCE.md>"

# List open incidents
curl -s "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged&limit=100" \
  -H "Authorization: Token token=$PD_TOKEN" | python3 -c "
import sys,json
incs = json.load(sys.stdin).get('incidents', [])
print(f'{len(incs)} open incidents')
for i in incs:
    print(f'  {i[\"id\"]}: {i[\"status\"]} - {i[\"service\"][\"summary\"]}')"

# Resolve each open incident
curl -s -X PUT "https://api.pagerduty.com/incidents/<INCIDENT_ID>" \
  -H "Authorization: Token token=$PD_TOKEN" \
  -H "Content-Type: application/json" \
  -H "From: clynch@pagerduty.com" \
  -d '{"incident":{"type":"incident_reference","status":"resolved"}}'
```

Then re-run `terraform apply`.

#### Removing Orphaned State Entries

If a schedule or resource key was renamed in Terraform config (e.g., `"Manager/Major Incident 24x7"` → `"Schedule - Manager Escalation"`), Terraform will try to destroy the old key and create the new one. If the destroy fails but the state retains both entries, remove the stale one:

```bash
# List schedule entries in state
terraform state list | grep schedule

# Remove the orphaned old key (does NOT destroy the PD resource)
terraform state rm 'pagerduty_schedule.schedules["Old Key Name"]'
```

#### Handling Duplicate Workflow Triggers

If `terraform apply` fails with `400 Bad Request` when creating a workflow trigger, it likely already exists in PagerDuty but not in state. Options:

1. **Import it:** `terraform import pagerduty_incident_workflow_trigger.<name> <trigger_id>`
2. **Delete and recreate:** Use PagerDuty API to delete the existing trigger, then re-apply:
   ```bash
   curl -s -X DELETE "https://api.pagerduty.com/incident_workflows/triggers/<trigger_id>" \
     -H "Authorization: Token token=$PD_TOKEN"
   ```

#### Post-Apply Verification

After a successful apply, verify the resource count matches expectations:
```bash
terraform state list | wc -l
# Expected: ~212+ resources (includes 7 cache variables added Feb 18)
```

#### Cache Variables (Added February 18, 2026)

`terraform apply` automatically deploys 7 Event Orchestration Cache Variables defined in `cache_variables.tf`:

| Variable | Scope | Type | Service |
|----------|-------|------|---------|
| `recent_alert_source` | Global | `recent_value` | — |
| `critical_event_count` | Global | `trigger_event_count` | — |
| `recent_hostname` | Global | `recent_value` | — |
| `pod_restart_trigger_count` | Service | `trigger_event_count` | Platform K8s |
| `recent_failing_pod` | Service | `recent_value` | Platform K8s |
| `payment_failure_count` | Service | `trigger_event_count` | Payments Ops |
| `recent_slow_query_source` | Service | `recent_value` | Database Reliability |

**Provider Requirement:** PagerDuty Terraform provider **v3.22.0+** is required for cache variable resources. See `docs/GOTCHAS_AND_WORKAROUNDS.md` for cache variable gotchas.

### Step 4: Add Workflow Steps

There are two approaches to adding workflow steps:

**Option A: Manual via PagerDuty UI**
1. Navigate to **Automation → Incident Workflows** in PagerDuty
2. Click on each workflow created by Terraform
3. Use the visual builder to add the appropriate steps

**Option B: Via PagerDuty REST API (Recommended for complex workflows)**
For workflows with Slack channel creation or other integration steps, use the API directly:

```bash
# Example: Create "Demo Incident Channel Setup" workflow
python scripts/populate_workflow_steps.py
```

**Note:** The "Demo Incident Channel Setup" workflow (ID: `PUXIPNC`) was created entirely via API because it requires specific Slack integration steps that Terraform cannot manage.

See `docs/GOTCHAS_AND_WORKAROUNDS.md` for details on API-based workflow creation.

### Step 5: ~~Configure PagerDuty Webhooks~~ (OBSOLETE)

> **NOTE (Feb 17, 2026):** The PagerDuty Generic Webhook subscription (PILGGJ0) was deleted. The `demo-simulator-controller` Lambda does not use webhooks — it polls the PagerDuty API directly and runs the full incident lifecycle in a single invocation. If you ever need to re-enable webhooks for the orchestrator, point them at the API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com/webhook`

---

## AWS Lambda Deployment

### Step 1: Package Lambda Functions

```bash
cd aws

# Package each Lambda
for lambda in orchestrator lifecycle notifier metrics; do
  cd lambda-${lambda}
  pip install -r requirements.txt -t ../lambda-${lambda}-pkg/
  cp handler.py ../lambda-${lambda}-pkg/
  cd ../lambda-${lambda}-pkg
  zip -r ../lambda-${lambda}.zip .
  cd ..
done
```

### Step 2: Deploy via Terraform

```bash
cd aws
terraform init
terraform apply
```

Or manually via AWS CLI:

```bash
# Create Lambda function (example for orchestrator)
aws lambda create-function \
  --function-name demo-simulator-orchestrator \
  --runtime python3.11 \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda-orchestrator.zip \
  --role arn:aws:iam::127214181728:role/lambda-demo-role \
  --environment "Variables={PAGERDUTY_API_KEY=<your-token>,SLACK_BOT_TOKEN=<your-slack-token>}"
```

### Step 3: Create EventBridge Rules

```bash
# Orchestrator - every 15 minutes
aws events put-rule --name demo-orchestrator-schedule \
  --schedule-expression "rate(15 minutes)"

aws events put-targets --rule demo-orchestrator-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:127214181728:function:demo-simulator-orchestrator"

# Repeat for lifecycle (5 min), notifier (2 min), metrics (1 min)
```

### Step 4: Update Lambda Environment Variables

When updating credentials (e.g., Slack token), use this pattern:

```bash
# Get current config, modify, and update
aws lambda get-function-configuration --function-name demo-simulator-orchestrator \
  --query 'Environment' --output json | \
  jq '.Variables.SLACK_BOT_TOKEN = "xoxb-NEW-TOKEN"' > /tmp/env.json

aws lambda update-function-configuration \
  --function-name demo-simulator-orchestrator \
  --environment file:///tmp/env.json
```

**GOTCHA:** Do NOT pass large JSON directly on the command line - use `file://` to avoid shell limits.

### ~~Lambda Function URLs~~ — BROKEN (403 Forbidden)

> **WARNING (Feb 17, 2026):** All Lambda Function URLs on this AWS account return **403 Forbidden**, likely due to an account-level restriction (e.g., SCP or resource policy). Do NOT use Function URLs for invocation.

**Use these methods instead:**

| Function | Invocation Method |
|----------|-------------------|
| **`demo-simulator-controller`** | `aws lambda invoke --function-name demo-simulator-controller --payload '{"action":"run","scenario_id":"FREE-001"}' --cli-binary-format raw-in-base64-out --region us-east-1 out.json` |
| `demo-simulator-orchestrator-v2` | API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com` (supports `/health`, `/status`, `/trigger`, `/cleanup`) |
| `demo-simulator-health-check` | `aws lambda invoke --function-name demo-simulator-health-check --payload '{}' --region us-east-1 out.json` |
| `demo-simulator-reset` | `aws lambda invoke --function-name demo-simulator-reset --payload '{"mode":"quick"}' --cli-binary-format raw-in-base64-out --region us-east-1 out.json` |

### Demo Orchestrator Lambda - Webhook Handler (eu-west-1) — LEGACY, DO NOT USE

> **WARNING:** This is the V1 legacy Lambda. It is NOT actively used. The ACTIVE orchestrator is `demo-simulator-orchestrator-v2` in **us-east-1** (see next section). This section is preserved for historical reference only.

The **demo-orchestrator** Lambda was the original webhook handler. It has been superseded by V2 in us-east-1.

**Deployment:**
```bash
cd aws
terraform init
terraform apply  # Deploys demo-orchestrator Lambda + DynamoDB table
```

**Key Components:**
- **Function Name**: `demo-orchestrator`
- **Region**: `eu-west-1`
- **DynamoDB Table**: `demo-incident-state`
- **Trigger**: Lambda Function URL (receives PagerDuty webhooks)

**Required Environment Variables:**
| Variable | Description |
|----------|-------------|
| `PAGERDUTY_TOKEN` | API token for PagerDuty operations |
| `SLACK_BOT_TOKEN` | Slack bot token (channels:read, chat:write, users:read for user impersonation) |
| `DEMO_STATE_TABLE` | DynamoDB table name |
| `SELF_LAMBDA_ARN` | Lambda function ARN for EventBridge Scheduler |
| `SCHEDULER_ROLE_ARN` | IAM role ARN for Scheduler |
| `WEBHOOK_SECRET` | PagerDuty webhook signing secret |

**Webhook Events Handled:**
- `incident.triggered` - Records incident, schedules acknowledgment
- `incident.acknowledged` - Invites users to Slack channel
- `incident.resolved` - Cleanup
- `incident.workflow.completed` - Reads Slack channel URL from conference bridge

See `docs/DEVELOPER_HANDOVER.md` for detailed event handling flow.

### Demo Orchestrator V2 Lambda - ACTIVE (us-east-1)

> **IMPORTANT:** This is the ACTIVE demo orchestrator. The V1 in eu-west-1 is legacy.

**Function Name:** `demo-simulator-orchestrator-v2`
**Region:** `us-east-1`
**API Gateway:** `https://ynoioelti7.execute-api.us-east-1.amazonaws.com/webhook`

#### Code-Only Deployment (Quick Deploy)

When making code changes to `handler.py` without infrastructure changes:

```bash
cd aws/lambda-demo-orchestrator
rm -f ../handler.zip
zip -r ../handler.zip . -q
aws lambda update-function-code \
  --function-name demo-simulator-orchestrator-v2 \
  --zip-file fileb://../handler.zip \
  --region us-east-1
```

**Verify deployment:**
```bash
aws lambda get-function --function-name demo-simulator-orchestrator-v2 --region us-east-1 \
  --query 'Configuration.LastModified'
```

#### Required Environment Variables (Current as of Feb 17, 2026)

| Variable | Value | Notes |
|----------|-------|-------|
| `PAGERDUTY_TOKEN` | `<see CREDENTIALS_REFERENCE.md>` | MUST be admin role token |
| `PAGERDUTY_API_KEY` | `<same as PAGERDUTY_TOKEN>` | Code uses both variable names |
| `SLACK_BOT_TOKEN` | `<see CREDENTIALS_REFERENCE.md>` | Enterprise Grid bot token |
| `SLACK_TEAM_ID` | `T0A9LN53CPQ` | REQUIRED for Enterprise Grid |
| `SCHEDULER_ROLE_ARN` | `arn:aws:iam::127214181728:role/demo-scheduler-invoke-role` | For EventBridge Scheduler |
| `SELF_LAMBDA_ARN` | `arn:aws:lambda:us-east-1:127214181728:function:demo-simulator-orchestrator-v2` | Lambda ARN |
| `DEMO_STATE_TABLE` | `demo-incident-state` | DynamoDB table |
| `WEBHOOK_SECRET` | *(not needed)* | Webhook subscription deleted Feb 17 |

#### Update All Environment Variables

When updating multiple variables, get current config first:

```bash
aws lambda get-function-configuration \
  --function-name demo-simulator-orchestrator-v2 \
  --region us-east-1 \
  --query 'Environment.Variables' > /tmp/current_env.json

cat /tmp/current_env.json | jq '
  .PAGERDUTY_TOKEN = "<your-token>" |
  .SLACK_BOT_TOKEN = "<your-slack-token>" |
  .SLACK_TEAM_ID = "T0A9LN53CPQ" |
  .SCHEDULER_ROLE_ARN = "arn:aws:iam::127214181728:role/demo-scheduler-invoke-role"
' > /tmp/new_env.json

aws lambda update-function-configuration \
  --function-name demo-simulator-orchestrator-v2 \
  --environment "Variables=$(cat /tmp/new_env.json)" \
  --region us-east-1
```

#### View Recent Logs

```bash
aws logs tail /aws/lambda/demo-simulator-orchestrator-v2 \
  --since 5m \
  --region us-east-1

aws logs filter-log-events \
  --log-group-name "/aws/lambda/demo-simulator-orchestrator-v2" \
  --start-time $(( $(date +%s) * 1000 - 300000 )) \
  --region us-east-1 | grep -E "WEBHOOK|SLACK|ERROR|SCHEDULE"
```

#### GOTCHAS

1. **Slack Enterprise Grid:** All `conversations.list` API calls MUST include `team_id=T0A9LN53CPQ` parameter or you get empty results. The Lambda code reads this from `SLACK_TEAM_ID` env var.

2. **PagerDuty Admin Token:** The token MUST be admin-level to acknowledge incidents on behalf of other users. A `limited_user` token can only acknowledge incidents where that user is assigned.

3. **Scheduler Role:** The `SCHEDULER_ROLE_ARN` must point to `demo-scheduler-invoke-role` (not `demo-scheduler-role` which doesn't exist).

### Demo Controller Lambda

The **demo-simulator-controller** is the recommended Lambda for running controlled demos. It provides full orchestration of the demo flow with pause/play capability.

**Run a demo scenario:**
```bash
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run", "scenario_id": "PRO-001"}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json && cat out.json

# With faster action delays for testing (default: 15-30s, live demos: 30-60s):
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run", "scenario_id": "PRO-001", "action_delay": 5}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 \
  --cli-read-timeout 900 out.json && cat out.json
```

> **NOTE:** The controller runs synchronously for 2-12 minutes depending on action count and delays. Use `--invocation-type Event` for async invocation if you don't need the result inline. Use `--cli-read-timeout 900` for synchronous calls.

**List all available scenarios:**
```bash
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "list_scenarios"}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json && cat out.json
```

**Pause/Resume demo:**
```bash
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "pause"}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json

aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "resume"}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json
```

**Configuration:**
The demo controller uses these environment variables:
- `ACTION_DELAY_MIN`: Minimum delay between actions (default: 15 seconds)
- `ACTION_DELAY_MAX`: Maximum delay between actions (default: 30 seconds)
- `SCENARIOS_FILE`: Path to scenarios.json (default: /var/task/scenarios.json)

### Demo Reset Lambda

Reset the demo environment by resolving all `[DEMO]` incidents:

**Quick Reset:**
```bash
aws lambda invoke --function-name demo-simulator-reset \
  --payload '{"mode": "quick"}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json && cat out.json
```

**Full Reset** (resolve incidents + clear maintenance windows + optionally create samples):
```bash
aws lambda invoke --function-name demo-simulator-reset \
  --payload '{"mode": "full", "create_samples": true, "notify_slack": true}' \
  --cli-binary-format raw-in-base64-out --region us-east-1 out.json && cat out.json
```

### Integration Health Check Lambda

Check connectivity to all integrated services:

**Via API Gateway:**
```bash
curl -s "https://ynoioelti7.execute-api.us-east-1.amazonaws.com/health"
```

**Via direct invocation:**
```bash
aws lambda invoke --function-name demo-simulator-health-check \
  --payload '{}' --region us-east-1 out.json && cat out.json
```

The health check validates:
- PagerDuty API connectivity
- Datadog API connectivity
- Grafana Cloud connectivity
- Jira API connectivity

---

## RBA Runner Deployment

The RBA runner requires a special deployment process due to manual replica authentication. See `docs/setup/RBA_RUNNER_SETUP.md` for the full guide.

### Quick Summary

1. **Create Runner in PagerDuty UI** (Automation > Runners)
2. **Create Manual Replica via API:**
   ```bash
   curl -X POST "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/${RUNNER_ID}/replicas" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/json" \
     -o replica_response.json
   ```

3. **Download Custom JAR:**
   ```bash
   DOWNLOAD_TK=$(jq -r '.downloadTk' replica_response.json)
   curl -X GET "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/download/runner" \
     -H "Authorization: Bearer ${DOWNLOAD_TK}" \
     -o runner.jar
   ```

4. **Upload to S3:**
   ```bash
   aws s3 cp runner.jar s3://pagerduty-demo-runner-bucket/runner.jar
   ```

5. **Deploy on EC2:**
   ```bash
   aws ssm send-command --instance-ids i-03ab4fd5f509a8342 \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["aws s3 cp s3://pagerduty-demo-runner-bucket/runner.jar /opt/runner.jar","java -jar /opt/runner.jar &"]'
   ```

**CRITICAL:** Do NOT use the Docker container for manual replicas. It does not work.

---

## Datadog Monitor Setup

### Datadog Trial Expiry — Graceful Degradation

The Datadog account may be on a trial. If the API key expires or becomes invalid (403 errors), the demo continues to function:

- **`lambda-demo-orchestrator`**: Falls back to PagerDuty Events API v2 directly (incidents still fire).
- **`lambda-metrics-pkg`**: Returns `{'status': 'skipped'}` or `{'status': 'error'}` without crashing. Metrics/logs won't reach Datadog but nothing breaks.
- **`lambda-health-check`**: Reports Datadog as `SKIPPED` or `FAILED` in its health report.

To re-enable after obtaining a new key, update `DATADOG_API_KEY` on all three Lambdas and run the health check. See [Gotchas](../GOTCHAS_AND_WORKAROUNDS.md#datadog-trial-expiry) for details.

### Option 1: Automated Script

```bash
cd aws
python setup_integrations.py
```

### Option 2: Manual Creation

Create monitors in Datadog UI with these specifications:

| Monitor Name | Query | Threshold | Notification |
|--------------|-------|-----------|--------------|
| API Response Time High | `avg:demo.api.response_time{*}` | > 500 | @pagerduty-demo-simulator-alerts |
| Database Connections | `avg:demo.database.connections{*}` | > 90 | @pagerduty-demo-simulator-alerts |
| Error Rate High | `avg:demo.api.error_rate{*}` | > 5 | @pagerduty-demo-simulator-alerts |
| Memory Usage | `avg:demo.system.memory_usage{*}` | > 85 | @pagerduty-demo-simulator-alerts |
| Queue Depth | `avg:demo.queue.depth{*}` | > 1000 | @pagerduty-demo-simulator-alerts |

**IMPORTANT:** The `@pagerduty-demo-simulator-alerts` integration must be configured in Datadog > Integrations > PagerDuty.

---

## GitHub Pages Deployment

### Step 1: Build the Dashboard

```bash
cd docs/demo-scenarios
npm install
npm run build
```

### Step 2: Configure GitHub Pages

In GitHub Repository Settings:
- Go to Pages
- Source: "GitHub Actions" or "Deploy from branch"
- Branch: `main` or `gh-pages`
- Folder: `/docs/demo-scenarios/dist` (or root if using gh-pages branch)

### Step 3: Push to Deploy

```bash
git add .
git commit -m "Update dashboard"
git push origin main
```

The dashboard will be available at: https://lynchypin.github.io/TFTest/

---

## Credential Management

### Security Best Practices

1. **Never commit credentials** - Use environment variables or terraform.tfvars (gitignored)
2. **Rotate tokens periodically** - Especially Slack tokens after app reinstalls
3. **Use least privilege** - API keys should have minimum required permissions

### Credential Update Checklist

When updating a credential, update it in ALL locations:

| Credential | Locations to Update |
|------------|---------------------|
| Slack Bot Token | Lambda env vars (4), `docs/CREDENTIALS_REFERENCE.md` |
| PagerDuty API Key | `terraform.tfvars`, Lambda env vars, scripts |
| Datadog Keys | Lambda env vars, `setup_integrations.py` |
| AWS Keys | Local env, GitHub Secrets (if using Actions) |

### Quick Credential Update Commands

```bash
# Update Slack token across all Lambdas
for fn in demo-simulator-orchestrator demo-simulator-lifecycle demo-simulator-notifier demo-simulator-metrics; do
  aws lambda get-function-configuration --function-name "$fn" --query 'Environment' --output json | \
    jq '.Variables.SLACK_BOT_TOKEN = "NEW_TOKEN"' > /tmp/env.json
  aws lambda update-function-configuration --function-name "$fn" --environment file:///tmp/env.json
done
```

---

## Verification and Testing

### Verify Lambda Functions

```bash
# Check all Lambdas exist and are configured
for fn in demo-simulator-orchestrator demo-simulator-lifecycle demo-simulator-notifier demo-simulator-metrics; do
  echo "=== $fn ==="
  aws lambda get-function --function-name "$fn" --query 'Configuration.{State:State,Runtime:Runtime,LastModified:LastModified}' --output table
done
```

### Verify RBA Runner

```bash
# Check runner status via API
curl -s "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/c144f57c-b026-4174-88b9-d65b06a6d7cc/replicas" \
  -H "Authorization: Bearer ${RBA_API_TOKEN}" | jq '.[0].status'
# Expected: "Active"
```

### Verify Datadog Monitors

```bash
# List monitors with "demo" in name
curl -s "https://api.us5.datadoghq.com/api/v1/monitor?name=demo" \
  -H "DD-API-KEY: ${DATADOG_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" | jq '.[].name'
```

### Test End-to-End Flow

1. Open dashboard: https://lynchypin.github.io/TFTest/
2. Select a Datadog scenario (e.g., "API Response Time Spike")
3. Click "Trigger"
4. Verify in Datadog that metric was received
5. Wait for monitor to evaluate (~1 minute)
6. Verify incident created in PagerDuty

---

## Troubleshooting

### Lambda Function Errors

```bash
# View recent logs
aws logs tail /aws/lambda/demo-simulator-orchestrator --since 1h

# View specific invocation
aws logs filter-log-events --log-group-name /aws/lambda/demo-simulator-orchestrator \
  --filter-pattern "ERROR"
```

### RBA Runner Not Connecting

1. Check EC2 instance is running
2. Verify Java process: `ps aux | grep java`
3. Check logs: `tail -f /usr/bin/runner/logs/runner.log`
4. Verify outbound 443 connectivity

### Slack Notifications Failing

1. Verify token has correct scopes: `curl -H "Authorization: Bearer xoxb-..." https://slack.com/api/auth.test`
2. Check for `missing_scope` in Lambda logs
3. Ensure bot is installed at org level (not workspace)

### Datadog Monitors Not Triggering

1. Verify metric is being received: Check Metrics Explorer in Datadog
2. Check monitor evaluation window (default 1 minute)
3. Verify @pagerduty integration is configured

### Terraform Schedule Updates Failing with 403

If you see `403 Forbidden - Access Denied` when updating schedules:

1. The API token lacks schedule write permissions
2. **Workaround:** Update schedules via PagerDuty UI, or obtain an admin API token
3. The demo environment token `u+rRnDx15Dpsdsy8iM1Q` has read-only schedule access

### Schedule Users Not Appearing in Slack

If users in schedules are not being impersonated correctly in Slack:

1. Verify users exist in BOTH PagerDuty AND Slack
2. Only these 6 users are valid for schedules:
   - Jim Beam, Jameson Casker, Arthur Guinness, Jose Cuervo, Jack Daniels, Ginny Tonic
3. Current schedule assignments (as of Feb 18, 2026):
   - Jim Beam: App Team, IT Support + Primary
   - Jack Daniels: Platform, Business Ops, Manager Escalation + Primary
   - Jameson Casker: App, Data + Primary
   - Jose Cuervo: Platform, SecOps + Primary
   - Ginny Tonic: SecOps, IT Support, Manager Escalation + Primary
   - Arthur Guinness: Data, Business Ops, Manager Escalation + Primary
4. Users who are PagerDuty-only will cause issues:
   - James Murphy, Paddy Losty, Kaptin Morgan, Uisce Beatha
5. See `docs/development/DEVELOPER_GUIDE.md` for detailed user configuration

### Slack App Not Working for Some Users

Slack guest users CANNOT use the PagerDuty app - this is a Slack platform limitation:

1. Guest users cannot link PagerDuty accounts
2. Guest users cannot use `/pd` slash commands
3. All users in schedules must be full Slack members (not guests)

---

## Cost Management

### AWS Free Tier Eligibility

| Resource | Free Tier Limit | Current Usage | Status |
|----------|-----------------|---------------|--------|
| EC2 t2.micro | 750 hrs/month | ~720 hrs | FREE |
| Lambda | 1M requests/month | ~50K | FREE |
| S3 | 5 GB storage | ~300 MB | FREE |
| EventBridge | Unlimited scheduled rules | 4 rules | FREE |

### Monitoring Costs

```bash
# Check AWS costs (past 7 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -v-7d +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --output table
```

**Current Status (February 2026):** $0.00 - All resources within free tier.

---

## Recent Changes (February 6, 2026)

### Datadog-PagerDuty Integration Fix

The Datadog PagerDuty integration was updated to use the correct Event Orchestration routing key. This is required for Datadog monitor alerts to create PagerDuty incidents.

**Previous (Broken) Configuration:**
- Service name: `demo-simulator-alerts`
- Service key: Pointed to non-existent service

**Current (Working) Configuration:**
- Service name: `demo-simulator-alerts`
- Service key: `R028NMN4RMUJEARZ18IJURLOU1VWQ779` (Event Orchestration routing key)

**How to Verify:**
```bash
# Test the routing key directly
curl -s -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[TEST] Datadog Integration Test",
      "severity": "warning",
      "source": "datadog-test"
    }
  }'
# Expected: {"status":"success",...}
```

**Where to Update in Datadog:**
1. Go to Integrations → PagerDuty
2. Click on `demo-simulator-alerts` service
3. Update the Integration Key to the Event Orchestration routing key
4. Save

---

### Slack Profile Deployment

Both Conall Slack profiles have been added to the codebase but **require Lambda deployment** to take effect:

| Profile | Slack ID | Email |
|---------|----------|-------|
| Conall Lynch (Work) | `U0A9KAMT0BF` | clynch@pagerduty.com |
| Conall Personal | `U0A9GBYT999` | conalllynch88@gmail.com |

**Files Modified:**
- `aws/shared/clients.py`
- `aws/shared/__init__.py`
- `aws/lambda-demo-orchestrator/handler.py`
- `aws/lambda-package/handler.py`
- `aws/lambda-demo-controller/handler.py`

**Deployment Command:**
```bash
cd aws

# Option 1: Deploy all via Terraform
terraform apply

# Option 2: Manual deployment for specific Lambda
cd lambda-demo-controller
zip -r ../lambda-demo-controller.zip .
cd ..
aws lambda update-function-code \
  --function-name demo-simulator-controller \
  --zip-file fileb://lambda-demo-controller.zip

# Repeat for other modified Lambdas:
# - demo-simulator-orchestrator
# - demo-simulator-package (if applicable)
```

**Verification:**
1. Trigger a demo scenario
2. Wait for incident channel creation
3. Verify both Slack accounts are invited to the channel

---

### Known Issues (As of February 18, 2026)

**1. ~~PagerDuty REST API Token Returns 401~~** RESOLVED (Feb 10)
- Replaced with admin-level token. See `docs/CREDENTIALS_REFERENCE.md`.

**2. 15 PagerDuty Services Don't Exist**
Scenarios reference services not created in PagerDuty:
- Clinical Systems - EMR (Healthcare)
- Grid Operations Center (Energy)
- Mining Operations - Equipment (Mining)
- Payment Processing - Gateway (FinTech)
- See `docs/IMPLEMENTATION_PLAN.md` for current status

Resolution: Create services in `services.tf` or update scenarios to use existing services.

**3. Scenario Payload Mismatches**
4 scenarios have `target_service` different from `pd_service` in payload:
- PRO-001, DIGOPS-002, EIM-001, AUTO-003

See `docs/IMPLEMENTATION_PLAN.md` for current implementation priorities.

**4. Terraform State Backup Accumulation**
Terraform generates `.backup` files on every state change. These have been moved to `archive/terraform-state-backups/`. Periodically clean these up to avoid clutter.

---

## Document History

| Date | Changes |
|------|---------|
| February 18, 2026 | Added Terraform state management procedures (incident resolution, orphaned state, duplicate triggers) |
| February 18, 2026 | Updated known issues — API token issue marked resolved |
| February 18, 2026 | Archived obsolete credential files and 17 terraform state backups |
| February 17, 2026 | Marked webhook configuration as obsolete; documented Function URL 403 issue |
| February 6, 2026 | Added Datadog-PagerDuty integration fix documentation |
| February 6, 2026 | Added Slack profile deployment procedures |
| February 6, 2026 | Documented known issues (API token, missing services, payload mismatches) |
| February 2026 | Added troubleshooting for schedule permissions and Slack guest limitations |
| February 2026 | Added schedule user requirements documentation |
| February 2026 | Initial deployment guide created |
| February 2026 | Added RBA runner deployment procedures |
| February 2026 | Added credential management section |
| February 2026 | Added troubleshooting and verification steps |
