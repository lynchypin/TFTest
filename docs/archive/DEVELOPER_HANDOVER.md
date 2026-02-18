# PagerDuty Demo Environment - Developer Handover

> **⚠️ ARCHIVED DOCUMENT**
> **This document is historical. For current handover documentation, see:**
> - `docs/NEXT_DEVELOPER_PROMPT.md` - Up-to-date handover document

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd TFTest

# Set environment variables
export PAGERDUTY_TOKEN="your-api-token"
export TF_VAR_pagerduty_token="$PAGERDUTY_TOKEN"

# Deploy Terraform resources
terraform init
terraform plan
terraform apply

# Populate workflow steps (REQUIRED after terraform apply)
python scripts/populate_workflow_steps.py

# Deploy Lambda Orchestrator (if using AWS)
cd aws && ./deploy.sh
```

---

## Project Overview

This project creates a comprehensive PagerDuty demo environment that showcases:
- Incident management end-to-end lifecycle
- Integrations with Slack, Jira, and monitoring tools
- Runbook Automation (RBA) capabilities
- Event Orchestration (global and service-level)
- Incident Workflows with automated actions
- Simulated user activity for realistic demos

---

## Directory Structure

```
TFTest/
├── docs/                          # Documentation
│   ├── CHANGELOG.md               # Running changelog
│   ├── DEVELOPER_HANDOVER.md      # This file
│   ├── ARCHITECTURE_BLUEPRINT.md  # Architecture with status
│   └── PROJECT_DESCRIPTION.md     # Detailed context
│
├── aws/                           # AWS Lambda Demo Orchestrator
│   └── lambda-package/
│       └── handler.py             # Main orchestrator code
│
├── scripts/                       # Utility scripts
│   └── populate_workflow_steps.py # Workflow step population
│
├── events/                        # Event samples
│   └── samples/                   # JSON event payloads
│
├── modules/                       # Terraform modules
│
├── configs/                       # Configuration files
│
├── datadog/                       # Datadog integration config
│
├── *.tf                           # Terraform resource definitions
│   ├── provider.tf                # Provider configuration
│   ├── services.tf                # PagerDuty services
│   ├── schedules.tf               # On-call schedules
│   ├── escalation_policies.tf     # Escalation policies
│   ├── incident_workflows.tf      # Workflow definitions (empty shells)
│   ├── incident_workflow_triggers.tf # Workflow triggers
│   ├── automation_actions.tf      # RBA automation actions
│   ├── global_orchestration.tf    # Global event orchestration
│   ├── service_orchestrations.tf  # Service event orchestrations
│   ├── integrations.tf            # Service integrations
│   └── business_services.tf       # Business service hierarchy
│
└── terraform.tfstate              # Terraform state (local)
```

---

## Key Components

### 1. Terraform Resources (205+ deployed)

| Resource Type | Count | File |
|--------------|-------|------|
| Services | 31 | `services.tf` |
| Teams | 6 | `data_teams.tf` (data sources) |
| Schedules | 8 | `schedules.tf` |
| Escalation Policies | 22 | `escalation_policies.tf` |
| Incident Workflows | 22 | `incident_workflows.tf` |
| Workflow Triggers | ~22 | `incident_workflow_triggers.tf` |
| Automation Actions | 20+ | `automation_actions.tf` |
| Service Orchestrations | 10+ | `service_orchestrations.tf` |
| Business Services | 12 | `business_services.tf` |

### 2. Lambda Demo Orchestrator (`aws/lambda-package/handler.py`)

**Purpose**: Simulates realistic incident response by:
- Receiving PagerDuty webhooks
- Populating Slack channels with responders
- Simulating acknowledgments, notes, status updates
- Managing incident lifecycle (trigger → acknowledge → resolve)

**Entry Point**: `lambda_handler(event, context)`

**Event Types Handled**:
| Source | Handler Function |
|--------|------------------|
| PagerDuty Webhook | `handle_webhook()` |
| EventBridge Scheduler | `handle_scheduled_action()` |
| API Gateway | `handle_api_request()` |

**Key Classes**:
- `DemoState` - DynamoDB state management
- `PagerDutyClient` - PagerDuty API wrapper
- `SlackClient` - Slack API wrapper

**API Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trigger` | POST | Trigger demo incident |
| `/pause` | POST | Pause demo automation |
| `/resume` | POST | Resume demo automation |
| `/cleanup` | POST | Resolve all demo incidents |
| `/status` | GET | Get demo state |
| `/integrations` | GET | Check integration status |
| `/health` | GET | Health check |

### 3. Workflow Step Population Script

**Location**: `scripts/populate_workflow_steps.py`

**Purpose**: Adds steps to empty Terraform-created workflows via PagerDuty API.

**Why Needed**: PagerDuty Terraform provider cannot create workflows WITH steps.

**Usage**:
```bash
export PAGERDUTY_TOKEN="your-token"
python scripts/populate_workflow_steps.py
```

---

## Critical Workflows

### Incident Acknowledgment Flow

```
INCIDENT TRIGGERED
       │
       ▼
┌─────────────────────────────────────────────────────┐
│ Lambda receives webhook: incident.triggered         │
│ Creates DemoState in DynamoDB                       │
│ Schedules acknowledgment action (30-120s delay)    │
└─────────────────────────────────────────────────────┘
       │
       ▼ (EventBridge triggers Lambda)
┌─────────────────────────────────────────────────────┐
│ Lambda handles 'acknowledge' action                 │
│ Calls PD API: PUT /incidents/{id} status=ack       │
└─────────────────────────────────────────────────────┘
       │
       ▼ (PD sends webhook)
┌─────────────────────────────────────────────────────┐
│ Lambda receives: incident.acknowledged              │
│ Updates DemoState                                   │
│ Adds additional responders (if multi-responder)    │
│ Schedules next responder_action                    │
└─────────────────────────────────────────────────────┘
       │
       ▼ (Loop until all responders acted)
┌─────────────────────────────────────────────────────┐
│ Responders perform actions:                         │
│ - add_note, status_update, add_responder, etc.     │
│ Posts messages to Slack channel                    │
└─────────────────────────────────────────────────────┘
       │
       ▼ (All responders acted)
┌─────────────────────────────────────────────────────┐
│ Lambda schedules 'resolve' action (120-300s)       │
│ Resolves incident via PD API                       │
│ Posts resolution to Slack                          │
└─────────────────────────────────────────────────────┘
```

### Escalation Handling (NEW)

When primary responder doesn't acknowledge within timeout:
1. PagerDuty escalation policy activates
2. Incident escalates to next level
3. Lambda detects new assignee via webhook
4. Schedules acknowledgment for escalated responder
5. **Guarantee**: Incident ALWAYS gets acknowledged

### Demo Incident Slack Channel Setup Flow (via PagerDuty Workflow)

For `[DEMO]` incidents, Slack channels are created automatically by a PagerDuty workflow:

```
[DEMO] INCIDENT CREATED
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PagerDuty Conditional Trigger fires (title contains '[DEMO]')       │
│ Workflow ID: PUXIPNC                                                │
│ Trigger ID: 7c33cc98-3c3a-4da2-9f6f-2211a706ca29                   │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Workflow Step 1: "Create Incident Slack Channel"                    │
│ - Channel Name: demo-{incident_number}-{incident_title}             │
│ - Visibility: Public                                                │
│ - Output: Channel Link (Slack URL)                                  │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Workflow Step 2: "Add Conference Bridge"                            │
│ - Sets incident.conference_bridge.url = Channel Link                │
│ - This is the KEY mechanism to pass channel URL to Lambda           │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼ (PD sends webhook: incident.workflow.completed)
┌─────────────────────────────────────────────────────────────────────┐
│ Lambda receives: incident.workflow.completed                        │
│ - Fetches incident from PagerDuty API                               │
│ - Reads conference_bridge.url (contains Slack channel link)         │
│ - Extracts channel ID from URL                                      │
│ - Invites demo users to channel via Slack API                       │
│ - Posts welcome message                                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Why Conference Bridge Approach?**
- Lambda's Slack bot token lacks `channels:write` scope (cannot create channels directly)
- PagerDuty's native Slack integration CAN create channels
- Conference bridge URL is a standard incident field Lambda can read
- Avoids complex custom fields or notes parsing

**Key IDs and Configuration:**
| Item | Value |
|------|-------|
| Workflow ID | `PUXIPNC` |
| Trigger ID | `7c33cc98-3c3a-4da2-9f6f-2211a706ca29` |
| Slack Workspace ID | `T0A9LN53CPQ` |
| Channel Creation Action | `pagerduty.com:slack:create-a-channel:4` |
| Conference Bridge Action | `pagerduty.com:incident-workflows:add-conference-bridge:1` |

**Channel URL Format:** `https://app.slack.com/client/{workspace_id}/{channel_id}`

---

## Environment Variables

### Lambda Orchestrator
| Variable | Description | Required |
|----------|-------------|----------|
| `PAGERDUTY_TOKEN` | PagerDuty API token | Yes |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token | Yes |
| `DEMO_STATE_TABLE` | DynamoDB table name | Yes |
| `SELF_LAMBDA_ARN` | Lambda function ARN | Yes |
| `SCHEDULER_ROLE_ARN` | EventBridge Scheduler role | Yes |
| `WEBHOOK_SECRET` | PagerDuty webhook signing secret | No |
| `DATADOG_API_KEY` | Datadog API key | No |
| `GRAFANA_API_KEY` | Grafana API key | No |
| `NEWRELIC_API_KEY` | New Relic API key | No |

### Terraform
| Variable | Description | Required |
|----------|-------------|----------|
| `TF_VAR_pagerduty_token` | PagerDuty API token | Yes |
| `TF_VAR_pagerduty_subdomain` | PagerDuty subdomain | No |

---

## Integration Points

### Slack
- **How**: PagerDuty native Slack integration via incident workflows
- **Channel Creation**: Workflow "Demo Incident Channel Setup" (ID: `PUXIPNC`)
  - Triggered on `[DEMO]` incident creation
  - Creates public channel: `demo-{number}-{title}`
  - Stores channel URL in incident's `conference_bridge.url`
- **Lambda's Role**:
  - Receives `incident.workflow.completed` webhook
  - Reads channel URL from conference bridge
  - Invites demo users to channel
  - Posts simulated conversation messages
- **Required Scopes** (Slack Bot Token):
  - `channels:read` - Read channel info
  - `chat:write` - Post messages
  - `users:read` - Look up users by email
  - NOTE: `channels:write` is NOT required (channel creation via PagerDuty)

### Jira
- **How**: PagerDuty native Jira Cloud integration
- **What**: Workflows create tickets via `jira.com:incident-workflows:create-issue`
- **Projects Needed**: SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA

### Monitoring Tools
- **Datadog**: Sends metrics to trigger monitors → PagerDuty events
- **Grafana**: Creates annotations, triggers alerts
- **New Relic**: Sends custom events
- **CloudWatch**: Publishes metrics to trigger alarms

---

## Common Tasks

### Add New Service
1. Add to `services.tf`
2. Create escalation policy in `escalation_policies.tf`
3. Add service orchestration in `service_orchestrations.tf`
4. Run `terraform apply`

### Add New Workflow
1. Add workflow resource in `incident_workflows.tf`
2. Add trigger in `incident_workflow_triggers.tf`
3. Add step definitions in `scripts/populate_workflow_steps.py` WORKFLOW_STEPS dict
4. Run `terraform apply`
5. Run `python scripts/populate_workflow_steps.py`

**Note**: For workflows with Slack channel creation, use the PagerDuty API directly
(see `docs/GOTCHAS_AND_WORKAROUNDS.md` for details on why).

### Add New Demo Scenario
1. Create event payload in `events/samples/`
2. Add routing rules in `global_orchestration.tf` if needed
3. Update Lambda's scenario handling if using special integration

### Pause Demo Mid-Demo
```bash
curl -X POST https://your-api-gateway/pause
```

### Cleanup All Demo Incidents
```bash
curl -X POST https://your-api-gateway/cleanup
```

---

## Troubleshooting

### Incident Not Triggering Workflow
1. Check workflow trigger conditions in PD UI (Automation → Incident Workflows)
2. Verify incident title contains `[DEMO]` (case-sensitive)
3. Check workflow is enabled (not disabled)
4. Review CloudWatch logs for `incident.workflow.completed` events

### Slack Channel Not Created (for [DEMO] incidents)
1. Verify PagerDuty Slack integration is active
2. Check workflow "Demo Incident Channel Setup" exists and is enabled
3. Verify Slack Workspace ID in workflow matches your workspace (`T0A9LN53CPQ`)
4. Check PagerDuty → Automation → Incident Workflows → Run History for errors
5. If workflow runs but channel not created, check Slack app permissions in PD

### Lambda Not Receiving `incident.workflow.completed` Events
1. Check PagerDuty → Integrations → Generic Webhooks subscription
2. Ensure "Workflow Completed" event type is enabled
3. Verify webhook URL points to Lambda Function URL
4. Check webhook signing secret matches `WEBHOOK_SECRET` env var

### Lambda Not Inviting Users to Slack Channel
1. Check CloudWatch logs for `ON_WORKFLOW_COMPLETED` entries
2. Verify `conference_bridge.url` is set on incident (check PD API)
3. Ensure Slack bot token has `users:read` and `chat:write` scopes
4. Check channel ID extraction from URL format

### Lambda Not Receiving Webhooks
1. Check PagerDuty → Integrations → Generic Webhooks
2. Verify Lambda function URL/API Gateway is correct
3. Check CloudWatch Logs for Lambda invocations
4. Verify webhook signature matches (check for "Signature mismatch" in logs)

### Simulated Actions Not Occurring
1. Check DynamoDB `demo-incident-state` table
2. Verify EventBridge Scheduler has correct IAM permissions
3. Check if demo is paused (`paused: true` in state)
4. Verify `SELF_LAMBDA_ARN` and `SCHEDULER_ROLE_ARN` environment variables are set

---

## Security Notes

- **API Tokens**: Never commit tokens to repository
- **Webhook Secret**: Use HMAC signature verification in production
- **IAM Roles**: Lambda needs minimal permissions (DynamoDB, Scheduler, Logs)
- **Slack Token**: Use Bot token, not User token

---

## Contact / Support

- **Project Owner**: Conall Lynch (clynch@pagerduty.com)
- **PD User ID**: PSLR7NC
- **Slack User ID**: U0A9KAMT0BF

---

## Related Documentation

- [NEXT_DEVELOPER_PROMPT.md](./NEXT_DEVELOPER_PROMPT.md) - **START HERE** if you're new to this project
- [CHANGELOG.md](./CHANGELOG.md) - What changed and when
- [ARCHITECTURE_BLUEPRINT.md](./ARCHITECTURE_BLUEPRINT.md) - System architecture
- [PROJECT_DESCRIPTION.md](./PROJECT_DESCRIPTION.md) - Detailed context
- [GOTCHAS_AND_WORKAROUNDS.md](./GOTCHAS_AND_WORKAROUNDS.md) - Known issues and solutions
- [CREDENTIALS_REFERENCE.md](./CREDENTIALS_REFERENCE.md) - API keys and tokens reference
