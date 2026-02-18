# PagerDuty Demo Environment - Gotchas and Workarounds

> **⚠️ ARCHIVED DOCUMENT**
> **This document is historical. For current gotchas documentation, see:**
> - `docs/GOTCHAS_AND_WORKAROUNDS.md` - Up-to-date gotchas document

This document captures non-obvious issues, workarounds, and lessons learned during development of this demo environment. It's intended to save future developers from re-discovering these pain points.

---

## Table of Contents
1. [PagerDuty API and Terraform](#pagerduty-api-and-terraform)
2. [Webhook Integration](#webhook-integration)
3. [Slack Integration](#slack-integration)
4. [Lambda and AWS](#lambda-and-aws)
5. [PagerDuty Workflow Creation](#pagerduty-workflow-creation)
6. [Event Types and Payloads](#event-types-and-payloads)

---

## PagerDuty API and Terraform

### Terraform Cannot Create Workflow Steps

**Problem**: The PagerDuty Terraform provider cannot create incident workflows WITH steps. You can only create empty workflow shells.

**Why**: The provider's `pagerduty_incident_workflow` resource doesn't support the `steps` attribute.

**Workaround**: Two-phase deployment:
1. Terraform creates empty workflow shells
2. Python script (`scripts/populate_workflow_steps.py`) populates steps via PagerDuty REST API

**Impact**: After every `terraform apply`, you must run the population script to add/update workflow steps.

---

### API Token Types Matter

**Problem**: Different PagerDuty operations require different token types.

| Operation | Token Type | How to Identify |
|-----------|-----------|-----------------|
| Most API operations | API Key (General Access) | Starts with `u+...` |
| Workflow creation via API | API User Token | Also starts with `u+...` but requires user-level access |
| Webhook signature verification | Webhook Signing Secret | Hex string from webhook subscription |

**Gotcha**: An API Key with admin scope may still return `403 User not permitted to create workflow` when creating workflows. You need an API User Token from a user with appropriate permissions.

**Location of tokens**: `aws/terraform.tfvars` and `docs/CREDENTIALS_REFERENCE.md`

---

## Webhook Integration

### Signature Verification - Raw Body Requirement

**Problem**: PagerDuty webhook signature verification requires the EXACT raw request body.

**Why**: HMAC-SHA256 is computed over the raw bytes. Any re-serialization (parsing JSON and re-dumping) changes the bytes.

**Correct Implementation**:
```python
raw_body = event.get('body', '')
if event.get('isBase64Encoded'):
    raw_body = base64.b64decode(raw_body).decode('utf-8')

computed = 'v1=' + hmac.new(
    secret.encode('utf-8'),
    raw_body.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

**Wrong**:
```python
# DO NOT DO THIS - changes the body
body_dict = json.loads(event['body'])
computed_body = json.dumps(body_dict)  # Different bytes!
```

---

### Generic Webhook Signing Secret Location

**Problem**: Hard to find where the webhook signing secret comes from.

**Location**: PagerDuty → Integrations → Generic Webhooks (V3) → [Your Subscription] → Signing Secret

**Note**: Each webhook subscription has its OWN signing secret. If you create a new subscription, you get a new secret.

---

### Event Type Prefix Mismatch

**Problem**: Webhook event types have inconsistent prefixes.

**Discovery**: The Lambda was checking for `workflow.completed` but PagerDuty sends `incident.workflow.completed`.

**Full event type mapping** (as implemented in handler.py):
```python
event_handlers = {
    'incident.triggered': on_incident_triggered,
    'incident.acknowledged': on_incident_acknowledged,
    'incident.resolved': on_incident_resolved,
    'incident.escalated': on_incident_escalated,
    'incident.workflow.completed': on_workflow_completed,  # NOT "workflow.completed"
    # ... etc
}
```

**Rule**: All incident-related webhooks start with `incident.` prefix.

---

## Slack Integration

### Lambda Cannot Create Slack Channels Directly

**Problem**: Attempting to create Slack channels from Lambda fails with `missing_scope` error.

**Why**: The Slack bot token used in this project lacks `channels:write` scope.

**Attempted Solution** (failed):
```python
def create_channel(self, name):
    resp = requests.post('https://slack.com/api/conversations.create',
        headers={'Authorization': f'Bearer {self.token}'},
        json={'name': name})
    # Returns: {"ok": false, "error": "missing_scope", "needed": "channels:write"}
```

**Working Solution**: Conference Bridge Approach
1. PagerDuty workflow creates channel (using PD's native Slack integration)
2. Workflow sets channel URL in incident's `conference_bridge.url` field
3. Lambda reads conference bridge URL on `incident.workflow.completed` event
4. Lambda extracts channel ID and invites users

**Why this works**: PagerDuty's Slack integration has the necessary permissions to create channels. Lambda only needs `channels:read`, `chat:write`, and `users:read`.

---

### Slack Channel URL Format

**Format**: `https://app.slack.com/client/{workspace_id}/{channel_id}`

**Example**: `https://app.slack.com/client/T0A9LN53CPQ/C0123456789`

**Extraction**:
```python
url = incident.get('conference_bridge', {}).get('url', '')
if 'slack.com/client/' in url:
    channel_id = url.split('/')[-1]
```

---

### Slack Workspace ID

**Current Workspace ID**: `T0A9LN53CPQ`

**Where it's used**: PagerDuty workflow "Create Incident Slack Channel" action configuration.

---

## Lambda and AWS

### Missing Environment Variables

**Problem**: Lambda fails silently or crashes when required environment variables are missing.

**Required Variables** (often overlooked):
| Variable | Purpose | Error if Missing |
|----------|---------|------------------|
| `SELF_LAMBDA_ARN` | EventBridge Scheduler target | Scheduler creation fails |
| `SCHEDULER_ROLE_ARN` | IAM role for Scheduler | Permission denied |
| `WEBHOOK_SECRET` | Signature verification | 401 Unauthorized |
| `DEMO_STATE_TABLE` | DynamoDB table name | Table not found |

**Tip**: Check `aws/demo_orchestrator.tf` for the full list of environment variables.

---

### Lambda Function URL vs API Gateway

**Lambda Function URL**:
- Format: `https://{function-url-id}.lambda-url.{region}.on.aws/`
- No path routing (all paths go to same handler)
- Simpler, but less flexible

**API Gateway**:
- Format: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/`
- Path-based routing
- More features (throttling, caching, etc.)

**This project uses**: Lambda Function URL (configured in `aws/demo_orchestrator.tf`)

---

### EventBridge Scheduler Permissions

**Problem**: Scheduled actions fail with permission errors.

**Required IAM Policy** for `SCHEDULER_ROLE_ARN`:
```json
{
  "Effect": "Allow",
  "Action": "lambda:InvokeFunction",
  "Resource": "<SELF_LAMBDA_ARN>"
}
```

**Trust Relationship**:
```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "scheduler.amazonaws.com"
  },
  "Action": "sts:AssumeRole"
}
```

---

## PagerDuty Workflow Creation

### Creating Workflows via API

**Problem**: Terraform can't create workflow steps, and the PagerDuty UI is tedious for complex workflows.

**Solution**: Use PagerDuty REST API directly.

**Endpoint**: `POST https://api.pagerduty.com/incident_workflows`

**Required Headers**:
```
Authorization: Token token={API_USER_TOKEN}
Content-Type: application/json
```

**Key Action IDs** (discovered via API exploration):
| Action | Action ID |
|--------|-----------|
| Create Incident Slack Channel | `pagerduty.com:slack:create-a-channel:4` |
| Add Conference Bridge | `pagerduty.com:incident-workflows:add-conference-bridge:1` |
| Create Jira Issue | `jira.com:incident-workflows:create-issue:1` |
| Send Status Update | `pagerduty.com:incident-workflows:send-status-update:2` |

**Finding Action IDs**: 
```bash
curl -s "https://api.pagerduty.com/incident_workflows/actions" \
  -H "Authorization: Token token=$PD_TOKEN" | jq '.actions[] | {name, id}'
```

---

### Workflow Trigger Types

**Available Trigger Types**:
1. **Manual** - User clicks "Run" in PD UI
2. **Conditional** - Fires when incident matches condition

**Gotcha**: Conditional triggers fire on incident **creation**, not acknowledgment. To trigger on acknowledgment, you must configure this in the PagerDuty UI (no API support for event-based triggers).

**API Trigger Creation**:
```bash
curl -X POST "https://api.pagerduty.com/incident_workflows/{workflow_id}/triggers" \
  -H "Authorization: Token token=$PD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": {
      "type": "conditional",
      "condition": {
        "expression": "incident.title matches part '\''[DEMO]'\''"
      }
    }
  }'
```

---

### Workflow Step Configuration

**Step Output Variables**: Workflow steps can output values that subsequent steps consume.

**Example**: Channel creation step outputs `Channel Link`, which conference bridge step uses:
```json
{
  "steps": [
    {
      "name": "Create Incident Slack Channel",
      "action_configuration": {
        "action_id": "pagerduty.com:slack:create-a-channel:4",
        "inputs": [
          {"name": "Channel Name", "value": "demo-{{incident.number}}-{{incident.title}}"},
          {"name": "Visibility", "value": "public"},
          {"name": "Workspace", "value": "T0A9LN53CPQ"}
        ]
      }
    },
    {
      "name": "Set Conference Bridge URL",
      "action_configuration": {
        "action_id": "pagerduty.com:incident-workflows:add-conference-bridge:1",
        "inputs": [
          {"name": "Conference URL", "value": "{{steps.Create Incident Slack Channel.Channel Link}}"}
        ]
      }
    }
  ]
}
```

---

## Event Types and Payloads

### Workflow Completion Event Structure

**Event Type**: `incident.workflow.completed`

**Payload Difference**: The incident data is nested differently than other webhook events.

**Normal incident event**:
```json
{
  "event": {
    "event_type": "incident.triggered",
    "data": {
      "id": "Q1234ABC",
      "title": "Incident Title",
      ...
    }
  }
}
```

**Workflow completion event**:
```json
{
  "event": {
    "event_type": "incident.workflow.completed",
    "data": {
      "incident": {
        "id": "Q1234ABC",
        "title": "Incident Title"
      },
      "workflow": {
        "id": "PUXIPNC",
        "name": "Demo Incident Channel Setup"
      }
    }
  }
}
```

**Extraction Code**:
```python
if event_type == 'incident.workflow.completed':
    incident_data = webhook_data.get('incident', {})
    incident_id = incident_data.get('id')
    title = incident_data.get('title')
else:
    incident_data = webhook_data
    incident_id = webhook_data.get('id')
    title = webhook_data.get('title')
```

---

### The [DEMO] Incident Filter

**Purpose**: Only process incidents intended for demo automation.

**Check**: Incident title must contain `[DEMO]` (case-sensitive).

**Bypass for Workflows**: The `[DEMO]` check is bypassed for `incident.workflow.completed` events because the workflow trigger already validated the condition.

```python
if '[DEMO]' not in title and event_type != 'incident.workflow.completed':
    print(f"Ignoring non-demo incident: {title}")
    return
```

---

## Quick Reference: Current Configuration

| Item | Value |
|------|-------|
| PagerDuty Subdomain | `pdt-losandes` |
| Slack Workspace ID | `T0A9LN53CPQ` |
| Demo Workflow ID | `PUXIPNC` |
| Demo Workflow Trigger ID | `7c33cc98-3c3a-4da2-9f6f-2211a706ca29` |
| Lambda Function | `demo-orchestrator` |
| DynamoDB Table | `demo-incident-state` |
| AWS Region | `eu-west-1` |

---

## Debugging Tips

### Enable Verbose Logging

In Lambda handler, use `print()` instead of `logger.info()` for CloudWatch visibility:
```python
print(f"DEBUG: event_type={event_type}, incident_id={incident_id}")
```

### Check Webhook Delivery

PagerDuty → Integrations → Generic Webhooks → [Subscription] → Recent Deliveries

### Test Webhook Locally

```bash
# Get a recent webhook payload
curl -s "https://api.pagerduty.com/webhooks/WEBHOOK_ID/records" \
  -H "Authorization: Token token=$PD_TOKEN" | jq '.records[0].body'
```

### Verify Workflow Execution

PagerDuty → Automation → Incident Workflows → [Workflow] → Run History

---

## Document Maintenance

**Last Updated**: 2026-02-07
**Author**: Documentation maintained by demo environment developers

When you discover a new gotcha or workaround, add it to this document to help future developers!
