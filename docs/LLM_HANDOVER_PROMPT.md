# LLM Developer Handover Prompt - PagerDuty Demo Simulator

> **Generated:** February 8, 2026
> **Last Updated:** February 18, 2026
> **Purpose:** Complete context for LLM developers taking over this project

---

## EXECUTIVE SUMMARY

You are taking over development of a **PagerDuty Demo Simulator** - a system designed to showcase PagerDuty's incident management capabilities in a realistic, automated fashion. The system creates fake but realistic-looking incidents, routes them through workflows, creates Slack channels, adds responders, and simulates the entire incident lifecycle.

**Current State (Feb 18, 2026):** The core automation is **WORKING AND DEPLOYED**. The `demo-simulator-controller` Lambda is the primary scenario execution engine. It can:
- Trigger PagerDuty events via Events API v2
- Create incidents routed to the correct service (via Global + Service Event Orchestration with cache variables)
- Acknowledge incidents as responders (with admin token)
- Discover Slack channels via conference_bridge polling
- Bot self-joins channels, invites observers + responders (one-by-one invite fix applied)
- Post phased investigation messages as impersonated users
- Resolve incidents after completing all action phases
- 51 of 51 enabled scenarios E2E validated (all passing via `scripts/test_all_scenarios.py`)

**All Lambda code is deployed.** AIOps, Status Page (API rewritten Feb 14), RBA action types are in production. Datadog integration has graceful fallback if trial expires. 7 Event Orchestration Cache Variables deployed (3 global, 4 service-level) for event source tracking, trigger counting, and pattern detection.

**Remaining Work:** Fix Terraform Lambda code detection, enable 19 disabled scenarios (pending external integrations), AIOps full configuration (requires add-on). See `docs/NEXT_DEVELOPER_PROMPT.md` for full details. Note: PagerDuty webhook subscription (PILGGJ0) was deleted Feb 17 — the controller does not use webhooks.

---

## PROJECT OVERVIEW

### What This System Does

1. **Triggers fake incidents** via multiple integrations (Datadog, Prometheus, CloudWatch, etc.)
2. **Routes events** through PagerDuty Event Orchestration to appropriate services
3. **Fires incident workflows** that create Slack channels, add notes, create Jira tickets
4. **Simulates responder activity** - acknowledgments, notes, status updates via AWS Lambda
5. **Auto-resolves incidents** after simulated investigation (2-10 minutes)

### Why It Exists

This is for **sales demos and training**. A PagerDuty Solutions Engineer (Conall) needs to demonstrate PagerDuty features to prospects. Instead of manually creating incidents and pretending to respond, this system automates everything so demos look realistic and professional.

### The Demo Owner

- **Name:** Conall Lynch
- **Email:** conall.lynch@pagerduty.com (work), conall@losandesgaa.ie (personal)
- **PagerDuty User ID:** PSLR7NC
- **Slack User IDs:** 
  - Work: `U0A9KAMT0BF`
  - Personal: `U0A9GBYT999`

---

## ARCHITECTURE

> **Note (February 12, 2026):** The diagram below shows the legacy webhook-driven architecture. The **current primary execution path** is the `demo-simulator-controller` Lambda, which runs scenarios end-to-end within a single invocation (no webhooks, no DynamoDB, no EventBridge Scheduler). See `docs/NEXT_DEVELOPER_PROMPT.md` for the current architecture.

### Technology Stack (Legacy Diagram — For Reference)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEMO SIMULATOR ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRIGGER SOURCES                    PAGERDUTY                    OUTPUTS    │
│  ┌──────────────┐                  ┌─────────────────┐        ┌──────────┐  │
│  │ Datadog      │──events──────────▶│ Event          │        │ Slack    │  │
│  │ (14 monitors)│                  │ Orchestration   │        │ Channels │  │
│  ├──────────────┤                  │ (12 rules)      │        └──────────┘  │
│  │ CloudWatch   │──events──────────▶│      │         │        ┌──────────┐  │
│  │ (SNS)        │                  │      ▼         │        │ Jira     │  │
│  ├──────────────┤                  │ ┌───────────┐  │        │ Tickets  │  │
│  │ Prometheus   │──events──────────▶│ │ Services  │  │        └──────────┘  │
│  │ (Grafana)    │                  │ │ (34)      │  │        ┌──────────┐  │
│  ├──────────────┤                  │ └─────┬─────┘  │        │ Status   │  │
│  │ New Relic    │──events──────────▶│       │        │        │ Updates  │  │
│  └──────────────┘                  │       ▼        │        └──────────┘  │
│                                    │ ┌───────────┐  │                      │
│                                    │ │ Workflows │  │                      │
│  AWS LAMBDA (us-east-1)           │ │ (25)      │  │                      │
│  ┌────────────────────────┐        │ └─────┬─────┘  │                      │
│  │ demo-simulator-        │        │       │        │                      │
│  │ controller (PRIMARY)   │        └───────┼────────┘                      │
│  │ (scenario runner)      │                │                               │
│  │                        │   polls PD API directly                        │
│  │ - Triggers events      │   (no webhooks needed)                         │
│  │ - Discovers channels   │                                                │
│  │ - Posts as users       │                                                │
│  │ - Resolves incidents   │                                                │
│  └────────────────────────┘                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Terraform (PagerDuty) | `/*.tf` (root) | Services, workflows, escalation policies |
| Terraform (AWS) | `/aws/*.tf` | Lambda, IAM, API Gateway |
| **Controller Lambda** | **`/aws/lambda-demo-controller/handler.py`** | **PRIMARY: Self-contained scenario runner** |
| Orchestrator Lambda | `/aws/lambda-demo-orchestrator/handler.py` | Legacy: webhook-driven handler |
| Shared Clients | `/aws/shared/clients.py` | PagerDuty, Slack API clients |
| E2E Tests | `/scripts/e2e_test.py` | Integration testing |
| Scenario Definitions | `/docs/demo-scenarios/src/data/scenarios.json` | 66 demo scenarios |

### AWS Region

**IMPORTANT:** All active Lambdas are in **us-east-1**. The primary Lambda is `demo-simulator-controller`. CloudWatch logs are at `/aws/lambda/demo-simulator-controller` in us-east-1. The legacy `demo-orchestrator` in eu-west-1 is DEPRECATED.

---

## RESOLVED ISSUES (February 9-10, 2026)

> **All critical blocking issues have been fixed.** This section documents the solutions for reference.

### Issue 1: Incidents Not Auto-Acknowledging - FIXED

**Root Causes & Solutions:**
1. **PagerDuty API token was `limited_user` role** - Upgraded to admin token (`YOUR_PAGERDUTY_TOKEN`)
2. **Scheduler role mismatch** - Lambda was configured to use `demo-scheduler-role` but the actual role is `demo-scheduler-invoke-role`

**Verified Working:** Incident #423, Q0LAK4XJZN2F4E acknowledged by Jim Beam automatically.

---

### Issue 2: Demo Owner Not Added to Slack Channels - FIXED

**Root Causes & Solutions:**
1. **Slack Enterprise Grid requires `team_id`** - Added `SLACK_TEAM_ID=T0A9LN53CPQ` to Lambda env vars
2. **Channel search pattern mismatch** - Changed from `inc-*` to `demo-*` pattern
3. **Bot token missing scopes** - Updated to working bot token

**Verified Working:** Observers successfully invited to Slack channels on incident acknowledgment.

---

### Issue 3: Events Routing to Default Service - PARTIAL

**Status:** All 47 enabled scenarios tested end-to-end and passing. 19 disabled scenarios awaiting external integrations.

**Current State:**
- 12 routing rules in Global Event Orchestration
- All enabled scenarios route correctly to their target services

---

### Issue 4: Scenarios Not End-to-End Tested - RESOLVED (Feb 14, 2026)

**Status:** All 47 enabled scenarios validated end-to-end via `scripts/test_all_scenarios.py`. 19 disabled scenarios pending external integration setup.

**What's Validated:**
- Event → Service → Incident → Workflow → Slack channel → Lambda → Acknowledgment → Resolution
- All 47 enabled scenarios pass with 100% success rate

---

### Issue 5: Bot Posting as "Oauth APP" - FIXED (Feb 10, 2026)

**Root Cause:** The "Team assembled" message was using `slack.post_message()` which posts as the bot.

**Solution:** Changed to `slack.post_as_user()` with the first responder's identity:
```python
# Line 728 in handler.py
slack.post_as_user(first_responder['slack_id'], channel_id, "Team assembled for incident response...")
```

---

## DEBUGGING COMMANDS (us-east-1)

**Check controller logs (primary):**
```bash
aws logs tail /aws/lambda/demo-simulator-controller --since 30m --region us-east-1
```

**Search for specific scenario completion:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/demo-simulator-controller \
  --filter-pattern "DEMO FLOW" \
  --region us-east-1
```

**Check controller Lambda environment variables:**
```bash
aws lambda get-function-configuration \
  --function-name demo-simulator-controller \
  --region us-east-1 \
  --query 'Environment.Variables' | jq
```

**Run a quick test scenario:**
```bash
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run_scenario", "scenario_id": "FREE-001", "action_delay": 2}' \
  --cli-binary-format raw-in-base64-out /dev/stdout
```

**Legacy orchestrator logs (if needed):**
```bash
aws logs tail /aws/lambda/demo-simulator-orchestrator-v2 --since 30m --region us-east-1
```

---

## REMAINING WORK

### ~~Multi-Message Conversations~~ IMPLEMENTED (Feb 12, 2026)

The `demo-simulator-controller` Lambda now posts phased Slack messages during each action using `post_as_user()`. Each responder action generates a contextual message from the `CONVERSATION_LIBRARY` across the investigating → found_issue → working_fix → resolved phases.

### ~~Validate Remaining 60 Scenarios~~ COMPLETED (Feb 14, 2026)

All 47 enabled scenarios (of 66 total) have been E2E validated via `scripts/test_all_scenarios.py` with 100% pass rate. The remaining 19 scenarios are disabled (awaiting external integrations like ServiceNow, Grafana, UptimeRobot, etc.).

### ~~Webhook Signature Verification~~ OBSOLETE (Feb 17, 2026)

PagerDuty Generic Webhook subscription (PILGGJ0) was deleted on Feb 17, 2026. The `demo-simulator-controller` does not use webhooks — it polls the PagerDuty API directly. If webhooks are ever re-enabled, point them at the API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com/webhook`

---

## FILE STRUCTURE

```
/TFTest/
├── *.tf                           # PagerDuty Terraform resources
│   ├── services.tf                # 30+ services (12 via for_each + 20 individual)
│   ├── incident_workflows.tf      # 25 workflows
│   ├── incident_workflow_triggers.tf  # 38 triggers
│   ├── global_orchestration.tf    # Event routing rules (12 rules)
│   ├── escalation_policies.tf     # On-call schedules
│   └── ...
│
├── aws/
│   ├── main.tf                    # AWS infrastructure
│   ├── demo_orchestrator.tf       # Legacy orchestrator config
│   ├── lambda-demo-controller/
│   │   └── handler.py             # ** PRIMARY FILE - self-contained scenario runner **
│   ├── lambda-demo-orchestrator/
│   │   └── handler.py             # Legacy webhook handler (~2136 lines)
│   ├── shared/
│   │   ├── __init__.py
│   │   └── clients.py             # PagerDuty, Slack API clients (used by controller)
│   ├── lambda-lifecycle/          # Incident progression
│   ├── lambda-notifier/           # Slack notifications
│   └── ...
│
├── scripts/
│   ├── e2e_test.py                # Integration tests (validates webhook-driven flow)
│   ├── trigger_demo_incident.sh   # Manual incident trigger
│   ├── analyze_scenario_readiness.py  # Scenario status checker
│   └── ...
│
├── docs/
│   ├── NEXT_DEVELOPER_PROMPT.md   # ** START HERE **
│   ├── GOTCHAS_AND_WORKAROUNDS.md # ** READ THIS **
│   ├── demo-scenarios/src/data/scenarios.json  # 66 scenario definitions
│
└── datadog/
    └── *.tf                       # Datadog monitors
```

---

## KEY FILES TO UNDERSTAND

### 1. `aws/lambda-demo-controller/handler.py` (~778 lines) — PRIMARY

This is the **current primary execution engine**. It runs complete demo scenarios within a single Lambda invocation (up to 15 minutes). Key functions:

| Function | Purpose |
|----------|---------|
| `lambda_handler` | Entry point — routes to `run`, `pause`, `resume`, `status`, `list_scenarios`, `reset` |
| `run_demo_flow` | Main orchestration — triggers event, polls for incident, acknowledges, runs phases, resolves |
| `trigger_pagerduty_event` | Sends event via PagerDuty Events API v2 with correct routing key |
| `poll_for_incident` | Polls PagerDuty API to find the created incident |
| `discover_slack_channel` | Polls incident conference_bridge for Slack channel URL |
| `execute_action_phase` | Runs phased actions (notes, status updates, custom fields, etc.) |
| `simulate_responder_conversation` | Posts phased messages from `CONVERSATION_LIBRARY` as impersonated users |

### 2. `aws/lambda-demo-orchestrator/handler.py` (~1206 lines) — LEGACY

This is the legacy webhook-driven handler, accessible via API Gateway. Still functional but not the primary path:

| Function | Purpose |
|----------|---------|
| `handle_api_request` | Routes API Gateway requests (`/health`, `/status`, `/trigger`, `/cleanup`) |
| `handle_trigger` | Triggers scenarios via external integrations or PagerDuty Events API |
| `handle_webhook` | Processes PagerDuty webhooks (webhook deleted Feb 17) |

### 3. `aws/lambda-demo-controller/shared/` (via `aws/shared/`)

API clients used by the controller:

| Class | Purpose |
|-------|---------|
| `PagerDutyClient` | Incidents, notes, status updates, responders, custom fields |
| `SlackClient` | Channels, messages, user profiles, invites, impersonation |
| `SlackNotifier` | Sends notifications to admin channels |

### 4. `aws/lambda-demo-controller/scenarios.json`

66 scenario definitions loaded at runtime. Each scenario has `id`, `name`, `severity`, `target_service`, `payload`, and metadata. 47 are enabled; 19 are disabled (awaiting external integrations).

### 5. `global_orchestration.tf`

Defines Event Orchestration routing rules. Routes events to correct PagerDuty services based on `class`, `component`, and source attributes.

---

## API CREDENTIALS

**CRITICAL: These are real credentials. Handle with care.**

### PagerDuty
```
Account: pdt-losandes.pagerduty.com
Admin API Key: u+rRnDx15Dpsdsy8iM1Q  (Terraform, read operations)
API User Token: YOUR_PAGERDUTY_TOKEN (Workflow operations, Lambda)
Events Routing Key: ed6b71f8718b4302d054db5f4cf7228f
Event Orchestration Key: R028NMN4RMUJEARZ18IJURLOU1VWQ779
```

### Slack
```
Workspace: Los Andes Demo (T0A9LN53CPQ)
Bot Token: xoxb-YOUR-SLACK-BOT-TOKEN
Bot Scopes: channels:read, chat:write, users:read, channels:join, groups:read, channels:manage
SLACK_TEAM_ID: T0A9LN53CPQ (REQUIRED for Enterprise Grid)
```

### Jira
```
Instance: losandesgaa.atlassian.net
Email: conall@losandesgaa.ie
API Token: YOUR_JIRA_API_TOKEN... (see Lambda env vars)
Projects: COMP, DATA, DEMO, INFRA, KAN, LAX, PAY, PIR, SECOPS
```

### AWS
```
Region: us-east-1 (demo-simulator-orchestrator-v2, DynamoDB, EventBridge)
Legacy: eu-west-1 (demo-orchestrator V1 - DEPRECATED)
Profile: default (or use IAM role)
```

### Datadog
```
Site: us5.datadoghq.com
API Key: YOUR_DATADOG_API_KEY
App Key: YOUR_DATADOG_APP_KEY
```

---

## DEMO USERS (Fake Responders)

These are fake users in PagerDuty that simulate incident responders:

| Name | PagerDuty ID | Email | Slack ID |
|------|--------------|-------|----------|
| Jim Beam | PG6UTES | jbeam@losandesgaa.onmicrosoft.com | U0AA1LZSYHX |
| Jack Daniels | PR0E7IK | jdaniels@losandesgaa.onmicrosoft.com | U0A9GC08EV9 |
| Jameson Casker | PCX6T22 | jcasker@losandesgaa.onmicrosoft.com | U0AA1LYLH2M |
| Jose Cuervo | PVOXRAP | jcuervo@losandesgaa.onmicrosoft.com | U0A9LN3QVC6 |
| Ginny Tonic | PNRT76X | gtonic@losandesgaa.onmicrosoft.com | U0A9KANFCLV |
| Arthur Guinness | PYKISPC | aguiness@losandesgaa.onmicrosoft.com | U0A9SBF3MTN |

The full list is in `handler.py` at line ~50: `DEMO_USERS = [...]`

---

## COMMON COMMANDS

### Testing
```bash
# Run E2E tests (from project root)
python scripts/e2e_test.py

# Trigger a demo incident manually
./scripts/trigger_demo_incident.sh

# Analyze scenario readiness
python scripts/analyze_scenario_readiness.py
```

### Terraform
```bash
# PagerDuty resources (root directory)
terraform plan
terraform apply

# AWS resources
cd aws
terraform plan
terraform apply
```

### Lambda Deployment
```bash
cd aws/lambda-demo-orchestrator
zip -r ../handler.zip handler.py
aws lambda update-function-code \
  --function-name demo-simulator-orchestrator-v2 \
  --zip-file fileb://../handler.zip \
  --region us-east-1
```

### CloudWatch Logs (us-east-1)
```bash
# View recent Lambda logs
aws logs tail /aws/lambda/demo-simulator-orchestrator-v2 \
  --region us-east-1 --follow

# Search for specific events
aws logs filter-log-events \
  --log-group-name /aws/lambda/demo-simulator-orchestrator-v2 \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### PagerDuty API
```bash
# List incidents
curl -s -H "Authorization: Token token=YOUR_PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged" | jq

# Get webhooks
curl -s -H "Authorization: Token token=YOUR_PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/webhooks" | jq
```

---

## GOTCHAS (CRITICAL KNOWLEDGE)

### PagerDuty API

1. **API Token Role Matters:**
   - `limited_user` token can ONLY acknowledge incidents where that user is the assignee
   - `admin` token can acknowledge incidents on behalf of ANY user
   - Current working token: `YOUR_PAGERDUTY_TOKEN` (admin role)

2. **`From` Header Required:** PUT/POST requests need `From: user@pdt-losandes.pagerduty.com`

3. **Event Types Have Prefixes:** It's `incident.triggered`, NOT `triggered`

4. **Workflow Action IDs Have Versions:** `pagerduty.com:slack:create-a-channel:4` - the `:4` changes

### Slack API

1. **Enterprise Grid Requires `team_id`:** All `conversations.list` calls must include `team_id=T0A9LN53CPQ`

2. **Bot Can't Create Channels:** Use PagerDuty workflow action instead

3. **Must Join Before Posting:** Always `conversations.join` before `chat.postMessage`

4. **User Impersonation:** Use `slack.post_as_user(slack_id, channel_id, message)` to post as users

### Terraform

1. **Workflow Step Changes Require ID Changes:** Changing a workflow step often requires changing the workflow ID or Terraform gets confused

2. **Triggers Need Service Subscriptions:** A trigger with no services never fires

---

## INVESTIGATION CHECKLIST FOR DEBUGGING

When something doesn't work:

1. **Check Controller CloudWatch Logs (us-east-1):**
   ```bash
   aws logs tail /aws/lambda/demo-simulator-controller --region us-east-1 --since 30m
   ```

2. **Check API Gateway Health:**
   ```bash
   curl -s "https://ynoioelti7.execute-api.us-east-1.amazonaws.com/health"
   curl -s "https://ynoioelti7.execute-api.us-east-1.amazonaws.com/status"
   ```

3. **Check Lambda Environment Variables:**
   ```bash
   aws lambda get-function-configuration --function-name demo-simulator-controller \
     --region us-east-1 --query 'Environment.Variables' | python3 -m json.tool
   ```
   Key variables: `PAGERDUTY_TOKEN` (admin role), `PAGERDUTY_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID`, routing keys (`ROUTING_KEY_DBRE`, `ROUTING_KEY_K8S`, `ROUTING_KEY_API`)

4. **Test API Connectivity:**
   ```bash
   curl -s -H "Authorization: Token token=$PD_TOKEN" \
     "https://api.pagerduty.com/users/me" | python3 -m json.tool
   ```

5. **Check DynamoDB State (orchestrator only):**
   ```bash
   aws dynamodb scan --table-name demo-incident-state --region us-east-1
   ```

6. **Lambda Function URLs are BROKEN (403 Forbidden):**
   All Lambda Function URLs on this AWS account return 403. Always use `aws lambda invoke` or the API Gateway URL. Do NOT debug Function URL issues — it's an account-level restriction.

---

## RECOMMENDED FIRST STEPS

1. **Verify the pipeline works:**
   ```bash
   aws lambda invoke --function-name demo-simulator-controller \
     --payload '{"action": "list_scenarios"}' \
     --cli-binary-format raw-in-base64-out --region us-east-1 out.json && cat out.json
   ```

2. **Run a test scenario with fast delays:**
   ```bash
   aws lambda invoke --function-name demo-simulator-controller \
     --payload '{"action": "run", "scenario_id": "FREE-001", "action_delay": 5}' \
     --cli-binary-format raw-in-base64-out --region us-east-1 \
     --invocation-type Event /dev/null
   ```
   Then check status: `curl -s "https://ynoioelti7.execute-api.us-east-1.amazonaws.com/status"`

3. **Read the controller code:**
   Focus on `run_demo_flow()` in `aws/lambda-demo-controller/handler.py` — this is the complete pipeline.

4. **Read GOTCHAS_AND_WORKAROUNDS.md:**
   This document saves hours of debugging. Every gotcha was discovered the hard way.

5. **Check the scenarios:**
   Review `aws/lambda-demo-controller/scenarios.json` — scenarios with `"enabled": false` need external integration setup before they can be activated.

---

## WHAT SUCCESS LOOKS LIKE

When the controller runs a scenario, the flow is:

1. **T+0s:** Controller sends event via PagerDuty Events API v2
2. **T+5s:** Incident created on correct service via Event Orchestration routing
3. **T+8s:** PagerDuty workflow fires → Slack channel created, Jira ticket created
4. **T+12s:** Controller discovers Slack channel via conference_bridge polling
5. **T+15s:** Controller acknowledges incident as first responder
6. **T+15-20s:** Bot joins channel, invites observers + additional responders
7. **T+20s-5m:** Phased actions (notes, status updates, custom fields) with Slack conversation messages posted as impersonated users
8. **T+5-12m:** Incident resolved, resolution summary posted to Slack

Throughout, Slack channel shows realistic investigation conversation with messages appearing as different team members (from `CONVERSATION_LIBRARY` with 10 categories: database, kubernetes, api, security, network, automation, manufacturing, workflow, integration, general).

---

## REMAINING WORK — DETAILED CONTEXT

### 1. Enable 19 Disabled Scenarios

These scenarios are disabled because they depend on external integrations not yet configured:

| Integration | Scenarios Affected | Blocker |
|-------------|-------------------|---------|
| ServiceNow | IND-* (some), COMBO-* | ServiceNow dev instance needed + PagerDuty extension config |
| Grafana Cloud | DIGOPS-* (some) | Free tier may not support PagerDuty alerting |
| UptimeRobot | CSO-* | Free tier doesn't support PagerDuty integration |
| Splunk | DIGOPS-* (some) | No free-tier cloud option |
| Sentry | AUTO-* (some) | PagerDuty integration requires paid Sentry plan |

To enable a scenario: set `"enabled": true` in `scenarios.json`, verify the event orchestration routing rule exists in `global_orchestration.tf`, and deploy both the updated scenarios.json (to Lambda) and Terraform changes.

### 2. AIOps/EIM Features

Requires PagerDuty AIOps add-on license. Once licensed:
- Configure noise reduction rules
- Set up alert grouping
- Enable event correlation
- These features are already coded in the controller (`action_types` includes AIOps actions) but the PagerDuty account needs the license activated

### 3. RBA Interactive Runbook Content

The RBA runner infrastructure exists (EC2 `i-03ab4fd5f509a8342`, 8 jobs configured in PagerDuty). What's missing:
- Meaningful runbook job definitions (current jobs are stubs)
- The controller already has `run_automation` as an action type
- Need to create actual diagnostic/remediation scripts that the RBA runner executes
- See `docs/setup/RBA_RUNNER_SETUP.md` for runner deployment details

### 4. Terraform Lambda Code Detection

Terraform doesn't detect when Lambda handler code changes (it only tracks the zip hash). Current workaround: deploy Lambda code changes via `aws lambda update-function-code` CLI. A proper fix would use `source_code_hash` with the zip file hash in `aws/main.tf`.

### 5. Cost Awareness

The entire system runs on AWS Free Tier ($0.00 verified). Key considerations:
- Lambda: Always free (1M requests/month)
- DynamoDB: Always free (25 GB + 25 RCU/WCU)
- API Gateway HTTP API: Free for first 12 months, then $1/million requests
- EventBridge: Free for AWS service events
- Datadog: Trial expired — graceful fallback in place

---

## DOCUMENTATION REFERENCE

| Document | Purpose |
|----------|---------|
| `docs/README.md` | Project overview, quick start |
| `docs/NEXT_DEVELOPER_PROMPT.md` | Quick-start reference for new devs |
| `docs/GOTCHAS_AND_WORKAROUNDS.md` | API quirks, workarounds (ESSENTIAL) |
| `docs/IMPLEMENTATION_PLAN.md` | Phased implementation plan |
| `docs/PROJECT_DESCRIPTION.md` | Business context, design decisions, nuances |
| `docs/project/PROJECT_OVERVIEW.md` | Comprehensive project overview |
| `docs/setup/DEPLOYMENT.md` | Deployment procedures |
| `docs/CREDENTIALS_REFERENCE.md` | Credential inventory (no secrets in docs) |
| `docs/SCENARIO_FLOWS.md` | How each scenario type flows |
| `docs/ARCHITECTURE_BLUEPRINT.md` | Architecture and integration details |

---

## CONTACTS

- **Demo Owner:** Conall Lynch (conall.lynch@pagerduty.com)
- **PagerDuty Account:** pdt-losandes.pagerduty.com
- **Slack Workspace:** Los Andes Demo

---

*The core system is working and validated. Remaining work is primarily enabling additional scenarios and adding premium feature content.*