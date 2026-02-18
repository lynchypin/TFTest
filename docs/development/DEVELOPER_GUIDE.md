# PagerDuty Demo Environment - Developer Guide

**For new developers starting work on this project**
**Last Updated:** February 18, 2026

---

## ⭐ IMPORTANT: Start Here

**Key documentation for new developers:**

| Document | Purpose |
|----------|---------|
| [NEXT_DEVELOPER_PROMPT.md](../NEXT_DEVELOPER_PROMPT.md) | **⭐ START HERE - Complete project context and handover** |
| [GOTCHAS_AND_WORKAROUNDS.md](../GOTCHAS_AND_WORKAROUNDS.md) | **⭐ READ THIS - Saves hours of debugging** |
| [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) | Master implementation plan with phases |
| [Lambda Implementation Guide](LAMBDA_LIFECYCLE_IMPLEMENTATION_GUIDE.md) | Architecture, API reference |

**February 18, 2026 Status:**
- ✅ 47/47 enabled scenarios E2E validated (`scripts/test_all_scenarios.py`) — 100% pass rate
- ✅ Demo Controller Lambda — self-contained scenario runner (trigger → ack → actions → resolve)
- ✅ Multi-message Slack conversations — phased messages from `CONVERSATION_LIBRARY`
- ✅ Slack health check — controller validates token at startup, logs errors
- ✅ Schedule rebalancing — all 6 users have 2-3 schedule assignments (Jim Beam reduced from 4)
- ✅ Incident resolution resilience — retry logic with error logging
- ✅ Both observer Slack accounts invited to channels
- ✅ Identity Team service name typo fixed
- ✅ Incident workflow Slack connection reference fixed
- ✅ Status Page API — rewritten Feb 14 to use correct PagerDuty Status Page API
- ✅ Jira Integration — 6 workflows create tickets automatically
- ✅ Datadog fallback — graceful degradation if trial expires
- ⚠️ Lambda Function URLs return 403 — use `aws lambda invoke` or API Gateway
- ⚠️ PagerDuty webhook deleted Feb 17 — controller does not use webhooks
- ⏳ 19 disabled scenarios — awaiting external integrations (ServiceNow, Grafana, UptimeRobot)
- ⏳ AIOps/EIM — requires add-on license
- ⏳ RBA interactive runbook content — needs creation

---

## Quick Start

```bash
# 1. Clone and enter the repo
cd /path/to/TFTest

# 2. Set up Terraform
export PAGERDUTY_TOKEN="your-api-token"
terraform init
terraform validate

# 3. Review the plan
terraform plan
```

---

## CRITICAL WORKAROUNDS AND GOTCHAS

> **READ THIS FIRST** - These are essential workarounds discovered during development that are not documented elsewhere. Failure to understand these will result in significant time lost debugging.

### 1. Incident Workflow Steps CANNOT Be Created via Terraform (CRITICAL)

**The Problem:** The PagerDuty Terraform provider can create workflow shells (name, description, team), but CANNOT populate workflow steps. The PagerDuty API's POST endpoint for creating workflows returns 404, and the Terraform provider does not support the `steps` argument.

**The Solution:** A two-phase deployment process:

**Phase 1: Terraform creates empty workflow shells**
```bash
terraform apply  # Creates workflows without steps
```

**Phase 2: Python script populates workflow steps via API PUT requests**
```bash
export PAGERDUTY_TOKEN=your_api_token  # MUST be an API key, not a user token
python scripts/populate_workflow_steps.py --apply
```

**CRITICAL DETAILS:**
- The `PAGERDUTY_TOKEN` MUST be a PagerDuty **API key** (starts with `u+` or similar), NOT a user OAuth token
- User tokens lack permissions to edit workflow steps via API
- The script uses `PUT /incident_workflows/{id}` which WORKS, unlike `POST /incident_workflows` which returns 404

**Script Location:** `scripts/populate_workflow_steps.py`

---

### 2. Workflow Action IDs Are NOT Documented (CRITICAL)

**The Problem:** PagerDuty workflow actions require fully-qualified action IDs that are not documented in PagerDuty's public API documentation. Using incorrect action IDs results in cryptic "Could not find actions" errors.

**The Correct Action IDs (discovered via API exploration):**

| Action | Action ID | Notes |
|--------|-----------|-------|
| Add Notes to Incident | `pagerduty.com:incident-workflows:add-notes-to-incident:1` | NOT `add-note:1` |
| Add Responders | `pagerduty.com:incident-workflows:add-responders:1` | |
| Send Status Update | `pagerduty.com:incident-workflows:send-status-update:5` | Note the version `:5` |
| Create Slack Channel | `pagerduty.com:slack:create-a-channel:4` | Slack-specific prefix |
| Send Slack Message | `pagerduty.com:slack:send-markdown-message:3` | |
| Archive Slack Channel | `pagerduty.com:slack:archive-channel:2` | |

**How to discover action IDs for your account:**
```bash
curl -s -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/incident_workflows/actions" | jq '.actions[] | {id, name}'
```

---

### 3. Workflow Action Input Field Names Are Case-Sensitive and Undocumented (CRITICAL)

**The Problem:** Workflow step inputs require EXACT field names. These names are NOT the same as what appears in the PagerDuty UI and are not documented.

**Correct Input Field Names for Slack Actions:**

| Action | Input Field Name | Value/Notes |
|--------|------------------|-------------|
| Create Slack Channel | `Workspace` | Slack workspace ID (e.g., `T0A9LN53CPQ`) |
| Create Slack Channel | `Channel Name` | Template string, e.g., `inc-{{incident.incident_number}}` |
| Create Slack Channel | `Channel visibility` | `Private` or `Public` |
| Create Slack Channel | `Pin incident` | `Yes` or `No` |
| Send Slack Message | `Workspace` | Slack workspace ID |
| Send Slack Message | `Channel` | `Incident Dedicated Channel` (literal string) |
| Send Slack Message | `Message` | Markdown message content |
| Send Slack Message | `Pinned message` | `Yes` or `No` |
| Archive Slack Channel | `Message` | Archive notification message |

**How to discover input field names:**
```bash
# Get all input fields for a specific action
curl -s -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/incident_workflows/actions" | \
  jq '.actions[] | select(.id == "pagerduty.com:slack:create-a-channel:4") | .inputs'
```

---

### 4. Slack Workspace ID Must Be Obtained from PagerDuty (CRITICAL)

**The Problem:** The Slack workspace ID required for workflow actions is NOT the same as your Slack workspace ID visible in Slack's admin. PagerDuty uses an internal reference.

**How to find the correct Slack Workspace ID:**
1. Go to PagerDuty UI → Automation → Incident Workflows
2. Create or edit a workflow with a "Create Slack Channel" step
3. Open browser Developer Tools (F12) → Network tab
4. Save the workflow and inspect the PUT request payload
5. The `Workspace` field value is your PagerDuty Slack workspace ID

**Current environment Slack Workspace ID:** `T0A9LN53CPQ`

---

### 5. Token Types Have Different Permissions

**The Problem:** Different PagerDuty token types have different API permissions. Using the wrong token type causes confusing permission errors.

| Token Type | Format | Workflow Edit | Notes |
|------------|--------|---------------|-------|
| API Key | `u+XXX...` | YES | Full API access, required for workflow steps |
| User OAuth Token | Varies | NO | Cannot edit workflow steps |
| Service Integration Key | Routing key | NO | Events API only |

**Always use an API key for workflow management scripts.**

---

### 6. Slack Guest Users CANNOT Use PagerDuty App (CRITICAL - PLATFORM LIMITATION)

**The Problem:** Slack guest accounts (single-channel or multi-channel guests) CANNOT interact with the PagerDuty Slack app. This is a fundamental Slack platform limitation, not a PagerDuty limitation.

**What Guest Users Cannot Do:**
- Link their PagerDuty account to Slack (the `/pd connect` command fails)
- Use PagerDuty slash commands (`/pd ack`, `/pd resolve`, etc.)
- Interact with PagerDuty message buttons in Slack
- Receive direct messages from PagerDuty via Slack

**Why This Happens:**
1. Slack apps must request `users:read` scope to access user information
2. Guest accounts are not visible via the `users:read` scope by default
3. Even if visible, guests cannot install or authorize workspace apps
4. This is a Slack design decision to limit guest capabilities

**Impact on Demo Environment:**
The Lambda-based incident lifecycle simulator (`aws/lambda-lifecycle/handler.py`) uses Slack's `chat:write.customize` feature to post messages **as if** they were from PagerDuty users. However:
- The bot can only post messages impersonating users by name/avatar
- The messages are NOT sent on behalf of the actual user
- Users in schedules who are guests cannot acknowledge/resolve incidents via Slack

**Workaround Implemented:**
1. All PagerDuty users who need to be impersonated in Slack must be **regular Slack members** (not guests)
2. The 6 users who exist in both PagerDuty AND Slack as full members are:
   - Jim Beam, Jameson Casker, Arthur Guiness, Jose Cuervo, Jack Daniels, Ginny Tonic
3. Schedules and escalation policies should only include these 6 users
4. Users who only exist in PagerDuty (James Murphy, Paddy Losty, Kaptin Morgan, Uisce Beatha) should be removed from schedules

**How to Check User Status:**
```bash
# List all Slack users and their type
curl -s "https://slack.com/api/users.list" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" | \
  jq '.members[] | select(.is_bot == false) | {name: .real_name, is_restricted: .is_restricted, is_ultra_restricted: .is_ultra_restricted}'
```

**Future Consideration:** If more users are needed, they must be upgraded from guest to full member in Slack.

---

### 7. Schedule Users Must Exist in Both PagerDuty AND Slack (CRITICAL)

**The Problem:** For the incident lifecycle simulation to work correctly, all users in on-call schedules MUST:
1. Exist as PagerDuty users
2. Exist as Slack users (NOT guests)
3. Have matching email addresses in both systems

**Why This Matters:**
The Lambda lifecycle simulator (`aws/lambda-lifecycle/handler.py`) performs these actions:
1. Fetches incidents from PagerDuty
2. Identifies responders (from escalation policy/schedule)
3. Posts Slack messages impersonating these responders
4. Acknowledges/resolves incidents as these users

If a user is in a schedule but NOT in Slack:
- The bot cannot impersonate them in Slack channels
- Messages may fail or use incorrect user references
- The demo looks incomplete/broken

**Current Valid Users for Schedules (February 2026):**
These 6 users exist in BOTH PagerDuty AND Slack as full members:

| PagerDuty User | Email | PagerDuty ID | Slack ID |
|----------------|-------|--------------|----------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U08CQAV8PEV |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U08CW1XJKD6 |
| Arthur Guiness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U08DF5S1MT9 |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U08CV6M0WHK |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U08CPGTNNGF |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U08D3BXNW3U |

**Users in PagerDuty but NOT in Slack (DO NOT USE IN SCHEDULES):**
| PagerDuty User | Email | Reason |
|----------------|-------|--------|
| James Murphy | jmurphy@losandesgaa.onmicrosoft.com | Not in Slack |
| Paddy Losty | plosty@losandesgaa.onmicrosoft.com | Not in Slack |
| Kaptin Morgan | kmorgan@losandesgaa.onmicrosoft.com | Not in Slack |
| Uisce Beatha | ubeatha@losandesgaa.onmicrosoft.com | Not in Slack |

**Terraform Configuration:**
In `data_lookups.tf`, only the 6 valid users should be in the `emails` local:
```hcl
locals {
  emails = [
    "jbeam@losandesgaa.onmicrosoft.com",
    "jcasker@losandesgaa.onmicrosoft.com",
    "aguiness@losandesgaa.onmicrosoft.com",
    "jcuervo@losandesgaa.onmicrosoft.com",
    "jdaniels@losandesgaa.onmicrosoft.com",
    "gtonic@losandesgaa.onmicrosoft.com",
  ]
}
```

---

### 8. PagerDuty API Token Permissions for Schedule Updates (CRITICAL)

**The Problem:** Not all PagerDuty API tokens have permission to update schedules. The demo environment API token may have read-only access to schedules.

**Error You'll See:**
```
Error: PUT API call to https://api.pagerduty.com/schedules/PXXXXXX failed 403 Forbidden.
Code: 2010, Errors: <nil>, Message: Access Denied
```

**Why This Happens:**
PagerDuty has granular API permissions. Some tokens are created with limited scopes:
- **Read-only tokens:** Can view schedules but not modify them
- **Admin tokens:** Full read/write access to all resources
- **Scoped tokens:** May have specific resource permissions

**How to Check Token Permissions:**
```bash
# Try to update a schedule (will fail if no permission)
curl -s -X PUT "https://api.pagerduty.com/schedules/YOUR_SCHEDULE_ID" \
  -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule": {"type": "schedule"}}' | jq
```

**Solution:**
1. **Option 1:** Get an admin API token from PagerDuty account settings
2. **Option 2:** Update schedules manually via PagerDuty UI
3. **Option 3:** Request elevated permissions for the existing token

**Current Token Status:**
The token `u+rRnDx15Dpsdsy8iM1Q` used in the demo environment does NOT have schedule write permissions. Schedule updates must be done:
- Via PagerDuty UI
- Or with an admin token

---

## System Architecture and End-to-End Data Flow

This section explains how all the components work together and how a demo scenario flows from trigger to resolution.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           DEMO SCENARIOS DASHBOARD                                       │
│                     https://lynchypin.github.io/TFTest/                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │  Scenario   │  │   Filter    │  │   Native    │  │  Trigger    │                     │
│  │   Library   │  │   System    │  │ Integration │  │   Button    │                     │
│  │  (66 total) │  │             │  │   Calls     │  │             │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┬──────┘                     │
└───────────────────────────────────────────────────────────┼─────────────────────────────┘
                                                            │
                    ┌───────────────────────────────────────┼───────────────────────────────┐
                    │              Events API v2            │                               │
                    │         (api.pagerduty.com)          ▼                               │
                    │  ┌─────────────────────────────────────────────────────────────────┐ │
                    │  │                   GLOBAL EVENT ORCHESTRATION                     │ │
                    │  │  • Enrichment (add severity, custom fields, priority)           │ │
                    │  │  • Routing (route to appropriate service based on payload)      │ │
                    │  │  • Classification (set incident type, add tags)                 │ │
                    │  └─────────────────────────────────────┬───────────────────────────┘ │
                    │                                        │                             │
                    │  ┌─────────────────────────────────────▼───────────────────────────┐ │
                    │  │                    SERVICE (receives incident)                   │ │
                    │  │  • Service Orchestration (service-specific enrichment)          │ │
                    │  │  • Alert Grouping (if AIOps enabled)                            │ │
                    │  │  • Incident Creation                                            │ │
                    │  └─────────────────────────────────────┬───────────────────────────┘ │
                    │                                        │                             │
                    │  ┌─────────────────────────────────────▼───────────────────────────┐ │
                    │  │               WORKFLOW TRIGGER (conditions evaluated)            │ │
                    │  │  • Priority-based: "incident.priority matches 'P1'"             │ │
                    │  │  • Service-based: "incident.service.id == 'PXXXXXX'"            │ │
                    │  │  • Type-based: Incident type is "Security Incident"             │ │
                    │  └─────────────────────────────────────┬───────────────────────────┘ │
                    │                                        │                             │
                    │  ┌─────────────────────────────────────▼───────────────────────────┐ │
                    │  │                  INCIDENT WORKFLOW EXECUTES                      │ │
                    │  │  Step 1: Create Slack Channel (per-incident)                    │ │
                    │  │  Step 2: Add Note (protocol activated message)                  │ │
                    │  │  Step 3: Post to Slack Channel (incident details)               │ │
                    │  │  Step 4: Add Responders (escalation policy)                     │ │
                    │  │  Step 5: Send Status Update (notify stakeholders)               │ │
                    │  └─────────────────────────────────────┬───────────────────────────┘ │
                    │                                        │                             │
                    └────────────────────────────────────────┼─────────────────────────────┘
                                                             │
┌────────────────────────────────────────────────────────────┼────────────────────────────┐
│                          SLACK WORKSPACE                   │                            │
│  ┌─────────────────────────────────────────────────────────▼──────────────────────────┐ │
│  │                    INCIDENT CHANNEL (auto-created)                                  │ │
│  │  #inc-1234-payment-service-outage                                                  │ │
│  │                                                                                     │ │
│  │  [BOT] Incident details posted, incident pinned                                    │ │
│  │  [Ginny Tonic] On it, pulling up dashboards now                                   │ │
│  │  [Jim Beam] Seeing elevated error rates around 14:32 UTC                          │ │
│  │  [Ginny Tonic] Found the issue - connection pool exhaustion                       │ │
│  │  [Jim Beam] Deploying fix now...                                                  │ │
│  │  [BOT] Incident resolved. Channel will be archived.                               │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                         │                                              │
│                        (Slack conversations simulated by                               │
│                         AWS Lambda lifecycle function)                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Scenario Execution Flow: Step-by-Step

Here is exactly what happens when a user triggers a scenario from the Demo Dashboard:

**1. User Clicks "Trigger" on Dashboard**
- Dashboard sends POST request to PagerDuty Events API v2
- Payload includes: `routing_key`, `event_action`, `payload` with summary, severity, source, custom_details

**2. Global Event Orchestration Processes Event**
- Matches event against rules in `global_orchestration.tf`
- Extracts/enriches: Sets priority based on severity, adds custom field values, sets incident type
- Routes to appropriate service based on `source` or `custom_details` fields

**3. Service Receives Alert, Creates Incident**
- Service-level orchestration applies additional transformations
- Alert grouping may correlate with existing incidents (if AIOps)
- New incident created with enriched data

**4. Workflow Triggers Fire**
- System evaluates all workflow triggers against the new incident
- Triggers based on priority, service, or incident type match
- Matched workflow begins execution

**5. Workflow Steps Execute**
- **Create Slack Channel:** New channel `#inc-{number}-{title}` created
- **Add Note:** Timeline note added with protocol/runbook info
- **Post to Channel:** Incident details posted to the new Slack channel
- **Add Responders:** Escalation policy or specific users paged
- **Send Status Update:** Stakeholders notified

**6. AWS Lambda Simulates Realistic Activity (Background)**
- `demo-simulator-lifecycle` Lambda runs every 30 minutes
- Fetches triggered/acknowledged incidents
- Posts realistic messages to Slack channels impersonating PagerDuty users
- Acknowledges incidents after delay, resolves after longer delay
- Messages include investigation findings, collaboration, and resolution details

**7. Incident Resolution**
- Incident marked resolved (manually or by Lambda)
- Resolution workflow may trigger (archives Slack channel, creates PIR ticket)

### Component Responsibilities

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Demo Dashboard** | Trigger scenarios, filter by plan/features | `docs/demo-scenarios/src/` |
| **Global Orchestration** | Route events, enrich with priority/type | `global_orchestration.tf` |
| **Services** | Receive incidents, define escalation | `services.tf`, `escalation_policies.tf` |
| **Workflows** | Automate response actions | `incident_workflows.tf`, `scripts/populate_workflow_steps.py` |
| **Workflow Triggers** | Determine when workflows fire | `incident_workflow_triggers.tf` |
| **Lambda Lifecycle** | Simulate realistic Slack conversations | `aws/lambda-lifecycle/handler.py` |
| **Lambda Metrics** | Generate background metrics | `aws/lambda-metrics/handler.py` |
| **Lambda Orchestrator** | Create background incidents | `aws/lambda-orchestrator/handler.py` |

### Scenario Categories and What They Demonstrate

| Category | Example Scenarios | PagerDuty Features Demonstrated |
|----------|-------------------|--------------------------------|
| **Infrastructure** | K8s node failure, DB connection exhaustion | Event Orchestration, Priority-based routing |
| **Security** | Credential stuffing, unauthorized access | Private Slack channels, SOC escalation |
| **Payments** | Payment gateway timeout, checkout errors | Revenue impact workflows, Finance notification |
| **Customer Impact** | SLA breach, customer-facing outage | Customer Success escalation, Status page updates |
| **Agent Scenarios** | SRE Agent investigation, Scribe post-mortem | PagerDuty Advance AI capabilities |
| **RBA Scenarios** | Auto-remediation, diagnostic collection | Runbook Automation, self-healing |

### Live Site Testing

**URL:** https://lynchypin.github.io/TFTest/

**To test the full flow:**
1. Open the Demo Dashboard
2. Click Settings (gear icon) and configure:
   - PagerDuty instance name
   - PagerDuty API key (for native integration triggers)
   - Default routing key
3. Filter scenarios by your desired criteria
4. Click "Trigger" on a scenario
5. Watch in PagerDuty:
   - Incident appears on service
   - Workflow triggers (check Automation → Incident Workflows → Activity)
   - Slack channel created (if Slack configured)
   - Responders paged
6. The lifecycle Lambda will simulate activity if deployed

---

## Project Overview

This repository contains a **PagerDuty demo environment** with:
- **Terraform configurations** for PagerDuty resources (orchestration, workflows, RBA, etc.)
- **Documentation** for the demo scenarios and implementation plans
- **Automation scripts** for diagnostics and remediation
- **Sample events** for testing

### What's Implemented

| Component | Count | Location |
|-----------|-------|----------|
| Services | 12 | `variables_and_locals.tf`, `services.tf` |
| Schedules | 5 | `variables_and_locals.tf`, `schedules.tf` |
| Escalation Policies | 5 | `variables_and_locals.tf`, `escalation_policies.tf` |
| Business Services | 6 | `business_services.tf` |
| Global Event Orchestration | 1 (20+ rules, 5 sets) | `global_orchestration.tf` |
| Service Orchestrations | 10 | `service_orchestrations.tf` |
| Incident Workflows | 22 | `incident_workflows.tf` |
| Workflow Triggers | 22+ | `incident_workflow_triggers.tf` |
| Automation Actions (RBA) | 22 (2 runners + 20 actions) | `automation_actions.tf` |
| Routing Rules | 13+ | `routing_rules.tf` |
| Custom Fields | 4+ | `custom_fields.tf` |
| Incident Types | 5+ | `incident_types.tf` |
| Demo Scenarios (Dashboard) | 66 | `docs/demo-scenarios/src/data/scenarios.json` |

---

## File Structure

```
TFTest/
├── *.tf                          # Terraform configurations
│   ├── main.tf                   # Provider configuration
│   ├── variables.tf              # Variables (PAGERDUTY_TOKEN)
│   ├── variables_and_locals.tf   # Team/schedule definitions
│   ├── data_lookups.tf           # User/team lookups
│   ├── global_orchestration.tf   # Global event orchestration
│   ├── routing_rules.tf          # Event router
│   ├── service_orchestrations.tf # Service-level orchestrations
│   ├── incident_workflows.tf     # 15 incident workflows
│   ├── incident_workflow_triggers.tf
│   ├── automation_actions.tf     # 20 RBA actions
│   ├── supporting_resources.tf   # Runners, priorities, etc.
│   ├── schedules.tf              # On-call schedules
│   ├── services.tf               # PagerDuty services
│   └── outputs.tf                # Terraform outputs
│
├── docs/                         # Documentation
│   ├── demo-scenarios/           # Demo Scenarios Dashboard (React app)
│   │   ├── src/                  # Source code
│   │   │   ├── components/       # React components
│   │   │   ├── data/             # scenarios.json
│   │   │   └── services/         # API integrations
│   │   ├── dist/                 # Production build (GitHub Pages)
│   │   └── package.json
│   ├── DEMO_ENVIRONMENT_PROPOSAL.md
│   ├── LICENSE_FILTERING.md
│   ├── EVENT_ORCHESTRATION.md
│   ├── INCIDENT_WORKFLOWS.md
│   └── RBA_DOCUMENTATION.md
│
├── events/                       # Test events
│   └── samples/                  # Sample JSON payloads
│
├── configs/                      # Integration configs
│
├── archive/                      # Archived files
│   ├── scripts/                  # Legacy shell scripts
│   ├── logs/                     # Terraform apply logs
│   ├── plans/                    # Terraform plan outputs
│   ├── conversations/            # Chat logs
│   └── docs/                     # Superseded documentation
│
├── DEVELOPER_GUIDE.md            # This file
├── MANUAL_SETUP_REQUIRED.md      # Manual PagerDuty UI steps
├── SECRETS.md                    # Credential reference
└── INCIDENT_WORKFLOW_AND_RBA_PLAN.md
```

---

## Key Users (Losandes Microsoft)

All personas map to these **10 actual PagerDuty users**:

| Email | Display Name |
|-------|--------------|
| `jbeam@losandesgaa.onmicrosoft.com` | Jim Beam |
| `jcasker@losandesgaa.onmicrosoft.com` | Jameson Casker |
| `aguiness@losandesgaa.onmicrosoft.com` | Arthur Guiness |
| `jcuervo@losandesgaa.onmicrosoft.com` | Jose Cuervo |
| `jmurphy@losandesgaa.onmicrosoft.com` | James Murphy |
| `plosty@losandesgaa.onmicrosoft.com` | Paddy Losty |
| `kmorgan@losandesgaa.onmicrosoft.com` | Kaptin Morgan |
| `ubeatha@losandesgaa.onmicrosoft.com` | Uisce Beatha |
| `jdaniels@losandesgaa.onmicrosoft.com` | Jack Daniels |
| `gtonic@losandesgaa.onmicrosoft.com` | Ginny Tonic |

These are defined in `data_lookups.tf` and referenced throughout.

---

## Teams

Defined in `data_lookups.tf` and `variables_and_locals.tf`:

| Team | Purpose |
|------|---------|
| Platform | Infrastructure/SRE |
| App | Application development |
| Support | Customer support |
| Corp IT | Corporate IT |
| SecOps | Security operations |

---

## What's Been Implemented

The **DEMO_ENVIRONMENT_PROPOSAL.md** and **COMPREHENSIVE_DEMO_ENVIRONMENT_SPECIFICATION.md** outline a "living demo environment". Here's current progress:

### Completed ✅
- **License Filtering UI**: Filter scenarios by PagerDuty plan (Free/Pro/Business/Enterprise) and add-ons
- **66 Demo Scenarios**: Available in the dashboard at https://lynchypin.github.io/TFTest/
  - Includes Agent scenarios (SRE, Scribe, Shift), Automation Actions, Runbook Automation
- **22 Incident Workflows**: Covering major incident, security, customer impact, payments, etc.
- **22 Automation Actions**: Diagnostic and remediation RBA jobs
- **Slack/Jira Integration**: Connected and working with workflows

### Remaining Work (See PROJECT_OVERVIEW.md for full details)

> **Note (Feb 18, 2026):** Most of the original HIGH PRIORITY items below have been completed by the `demo-simulator-controller` Lambda. The controller handles schedule user sync, conversation libraries, responder actions, Slack channel invites, and multi-phase conversations. See `NEXT_DEVELOPER_PROMPT.md` for the full "What's DONE and WORKING" list.

**~~HIGH PRIORITY - Lambda Lifecycle Simulation Enhancements:~~** ALL COMPLETED (Feb 11-18)

| Task | Status | Notes |
|------|--------|-------|
| Schedule User Sync | ✅ DONE | Schedules use only 6 valid PD+Slack users. Rebalanced Feb 18. |
| Add Responders Action | ✅ DONE | Controller selects 1-3 responders per scenario |
| Responder Action Logic | ✅ DONE | All responders perform actions; random resolver selection |
| Slack Channel Responders | ✅ DONE | Bot joins channel, invites observers + all responders |
| Conversation Libraries | ✅ DONE | `CONVERSATION_LIBRARY` in controller with scenario-specific messages |

**MEDIUM PRIORITY - Feature Demonstrations:** PARTIALLY DONE

| Task | Status | Notes |
|------|--------|-------|
| Status Updates | ✅ DONE | Controller posts status updates during incident |
| Automation Actions | ✅ DONE | Controller executes notes, custom fields, status updates |
| Workflow Triggers | ✅ DONE | Managed via `incident_workflow_triggers.tf` |
| Incident Types/Forms/Roles | ⏳ REMAINING | Requires AIOps/EIM add-on license |
| Tasks/Custom Fields | ✅ DONE | Controller updates custom fields per scenario |

**LOWER PRIORITY - Advanced Scenarios:**
- PagerDuty Advance scenarios (AI Status Updates, AI-Assisted PIR) — requires AIOps license
- PagerDuty Copilot scenarios — requires AIOps license

**LOWER PRIORITY - Enterprise Integrations:**
- Zoom conference bridge setup
- ServiceNow bidirectional integration (deferred — Jira sufficient)
- Salesforce customer context integration

**~~BLOCKED - Requires Admin Token or Manual Setup:~~** RESOLVED (Feb 10)
- ~~Schedule updates require PagerDuty UI~~ — Admin token now in use; Terraform manages schedules directly

---

## Terraform Commands

```bash
# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply changes (CAUTION: this modifies PagerDuty)
terraform apply

# Destroy resources
terraform destroy

# Format files
terraform fmt
```

---

## PagerDuty Integrations vs Extensions

Understanding the difference between Integrations and Extensions is critical for the demo environment:

### Integrations (Data INTO PagerDuty)

**Definition:** Tools that send events/data TO PagerDuty.

| Integration | Description | Data Flow |
|-------------|-------------|-----------|
| Datadog | Monitoring alerts | Datadog -> PagerDuty |
| New Relic | APM alerts | New Relic -> PagerDuty |
| Sentry | Error tracking | Sentry -> PagerDuty |
| Prometheus/Alertmanager | Metric alerts | Prometheus -> PagerDuty |
| AWS CloudWatch | AWS alerts | CloudWatch -> PagerDuty |
| Azure Monitor | Azure alerts | Azure -> PagerDuty |
| Splunk | Log-based alerts | Splunk -> PagerDuty |
| Custom Webhooks | API events | Any system -> PagerDuty |

### Extensions (Data OUT of PagerDuty)

**Definition:** Tools that are part of incident workflows OR receive data FROM PagerDuty about incidents.

| Extension | Description | Data Flow |
|-----------|-------------|-----------|
| Slack | ChatOps, channel creation, notifications | PagerDuty -> Slack |
| Microsoft Teams | ChatOps, channel creation, notifications | PagerDuty -> Teams |
| Jira | Ticket creation from incidents | PagerDuty -> Jira |
| ServiceNow | Incident sync, ticket creation | PagerDuty <-> ServiceNow |
| Zoom | Conference bridge creation | PagerDuty -> Zoom |
| Status Page | Automated status updates | PagerDuty -> Status Page |
| Email | Stakeholder notifications | PagerDuty -> Email |
| Webhooks (outbound) | Custom integrations | PagerDuty -> External systems |

### ChatOps Tools

ChatOps tools (Slack, Microsoft Teams) are **Extensions** because they:
- Receive incident data FROM PagerDuty
- Are used within Incident Workflows to create channels, post messages
- Enable bidirectional interaction (responders can take actions from chat)

**Configured in this environment:**
- Slack Workspace ID: `T0A9LN53CPQ`
- Used in workflows for: Channel creation, message posting, channel archiving

---

## Incident Workflow Creation Process

**IMPORTANT:** The PagerDuty Terraform provider creates workflow shells without steps. Steps are populated via the PagerDuty API or UI after `terraform apply`.

### Current Workflow Inventory (22 Total)

Defined in `incident_workflows.tf`:

| # | Workflow Name | Purpose |
|---|---------------|---------|
| 1 | Major Incident Full Mobilization | Comprehensive mobilization for major incidents |
| 2 | Security Incident Response (Confidential) | Security incidents with confidential handling |
| 3 | Customer Impact Communication | Incidents affecting external customers |
| 4 | Platform Infrastructure Degradation | Platform-wide infrastructure issues |
| 5 | Incident Closeout and PIR Scheduling | Post-incident review scheduling |
| 6 | Payments System Outage | Critical payment processing failures |
| 7 | Data Pipeline Alert | Critical data pipeline failures |
| 8 | Database Emergency Response | Critical database incident response |
| 9 | P1 Critical Response Protocol | Standard P1 incident response |
| 10 | Maintenance Window Incident | Incidents during planned maintenance |
| 11 | Data Breach Response | Critical data breach protocol |
| 12 | Identity/Authentication Crisis | Authentication system failure response |
| 13 | Escalation Timeout Handler | Automated handling when escalation times out |
| 14 | Run Comprehensive Diagnostics (Manual) | Manual trigger for full system diagnostics |
| 15 | Initiate Customer Communication (Manual) | Manual trigger for customer communication |
| 16 | Automated Service Health Check | Automated health check workflow |
| 17 | Incident Commander Handoff | IC shift change workflow |
| 18 | Third-Party Vendor Escalation | Escalation to third-party vendor support |
| 19 | Capacity Emergency Response | Infrastructure capacity crisis response |
| 20 | Compliance Incident Handler | Compliance-related incident workflow |
| 21 | Incident Resolution Cleanup | Post-resolution cleanup workflow |
| 22 | Standard Incident Response | Generic incident response workflow |

### Creating New Workflows

**Step 1: Add to `incident_workflows.tf`**
```hcl
resource "pagerduty_incident_workflow" "your_workflow" {
  name        = "Your Workflow Name"
  description = "Workflow description"
  team        = pagerduty_team.platform.id
}
```

**Step 2: Run Terraform**
```bash
terraform plan
terraform apply
```

**Step 3: Add Steps via PagerDuty UI**
1. Navigate to: Automation -> Incident Workflows
2. Find your workflow and click Edit
3. Add steps using the visual editor
4. Save and enable the workflow

### Available Workflow Actions

Actions available in workflows (use the fully qualified action ID):

| Action | Action ID Format | Description |
|--------|------------------|-------------|
| Create Slack Channel | `pagerduty.com:slack:create-a-channel:4` | Creates incident channel |
| Send Slack Message | `pagerduty.com:slack:send-markdown-message:3` | Posts to Slack |
| Add Responders | `pagerduty.add-responders` | Adds responders to incident |
| Add Note | `pagerduty.add-incident-note` | Adds internal note |
| Create Jira Issue | `pagerduty.create-jira-issue` | Creates Jira ticket |
| Run Automation Action | `pagerduty.run-automation-action` | Runs RBA job |
| Create Conference Bridge | `pagerduty.create-conference-bridge` | Creates Zoom meeting |
| Update Status Page | `pagerduty.post-to-status-page` | Posts status update |

### Script Reference

Workflow creation scripts are located in `scripts/`:
- `create_workflows_v2.sh` - Creates workflows via API
- `cleanup_workflows.sh` - Removes duplicate workflows

---

## Key References

| Document | Purpose |
|----------|---------|
| `docs/DEMO_ENVIRONMENT_PROPOSAL.md` | Main implementation plan |
| `docs/LICENSE_FILTERING.md` | Plan/add-on filtering spec |
| `docs/EVENT_ORCHESTRATION.md` | How orchestration works |
| `docs/INCIDENT_WORKFLOWS.md` | Workflow reference |
| `docs/RBA_DOCUMENTATION.md` | RBA actions reference |

---

## PagerDuty Plan Feature Matrix

| Feature | Free | Pro | Biz | Ent | +AIOps | +RBA |
|---------|------|-----|-----|-----|--------|------|
| Basic Routing | ✓ | ✓ | ✓ | ✓ | | |
| Incident Workflows | | 1 | ✓ | Full | | |
| Custom Fields | | | 15 | 30 | | |
| Global Orchestration | | | | | ✓ | |
| Alert Grouping | | | | | ✓ | |
| RBA Jobs | | | | | | ✓ |

Full details in `docs/LICENSE_FILTERING.md`.

---

## Next Steps for New Developer

1. **Read** `docs/DEMO_ENVIRONMENT_PROPOSAL.md` (main plan)
2. **Review** existing Terraform files to understand current state
3. **Run** `terraform validate` to confirm setup
4. **Try** the Demo Scenarios Dashboard at https://lynchypin.github.io/TFTest/

---

## Demo Scenarios Dashboard

A React-based web application for triggering PagerDuty demo scenarios.

**Live URL:** https://lynchypin.github.io/TFTest/

### Local Development

```bash
cd docs/demo-scenarios
npm install
npm run dev
```

### Features

- 66 pre-configured demo scenarios across industries (including Agent, RBA, and combined scenarios)
- Filter by integration, severity, team type, industry, PagerDuty features, and Agent type
- Dark mode support
- Native integration triggers (Sentry, Datadog, New Relic, etc.)
- Fallback to PagerDuty Events API v2

### Credential Configuration

All credentials are stored in browser localStorage and never transmitted except to their respective APIs.

1. Open the dashboard
2. Click the Settings gear icon
3. Configure PagerDuty credentials (instance, API key, routing keys)
4. Optionally configure external tool credentials (Sentry, Datadog, etc.)

### Deployment

The dashboard auto-deploys to GitHub Pages via the `.github/workflows/deploy-demo.yml` workflow on push to `main`.

Manual deployment:
```bash
cd docs/demo-scenarios
npm run build
# Output in dist/ - served via GitHub Pages
```

---

## Known Issues and Workarounds

### Terraform Provider Limitations

#### 1. Incident Workflow Creation (API 404)

**Issue:** The PagerDuty API returns 404 Not Found when attempting to create new incident workflows via POST request, even with valid payloads.

**Verified Behavior:**
- `GET /incident_workflows` - Works (lists existing workflows)
- `PUT /incident_workflows/{id}` - Works (updates existing workflows)
- `POST /incident_workflows` - Returns 404 (cannot create new workflows)

**Workaround:**
1. Create workflows manually in the PagerDuty UI (Automation → Incident Workflows)
2. Reference them in Terraform as data sources: `data "pagerduty_incident_workflow" "name" { name = "Workflow Name" }`
3. Workflow triggers CAN be created via Terraform

**Status:** Needs more research - see `incident_workflows.tf` for detailed notes.

#### 2. Global Orchestration "Duplicate Route" Errors

**Issue:** Terraform `pagerduty_event_orchestration_global` fails with error:
```
Error: PUT API call failed 400 Bad Request. Code: 0, Errors: map[route_to:[rules can't route to the same set/service: <set_name>]]
```

**Root Cause:** Multiple rules in a set cannot route to the same destination set. Each set should have unique routing targets.

**Workaround:** Simplify the orchestration structure to use a linear flow:
- `start` set: Initial enrichment/extraction → routes to `triage`
- `triage` set: Contains all classification rules with final routing to services
- Avoid creating complex multi-set structures where rules might route to the same set

**Example Fix:**
```hcl
# BEFORE (causes error):
set { id = "start" rule { route_to = "enrichment" } rule { route_to = "enrichment" } }

# AFTER (works):
set { id = "start" rule { actions { extraction {...} } route_to = "triage" } }
```

#### 3. Global Orchestration "Invalid Extraction Target" Errors

**Issue:** Terraform fails with error:
```
Error: PUT API call failed 400 Bad Request. Code: 0, Errors: map[sets:[map[rules:[map[actions:map[extractions:[map[target:[invalid field]]]]]]]]]
```

**Root Cause:** Some extraction targets that work in the UI may not be valid via API. Known invalid targets include:
- `event.group` (in some contexts)
- `dedup_key` (must use specific action, not extraction)

**Workaround:**
1. Use only documented extraction targets: `event.summary`, `event.source`, `event.severity`, `event.component`, `event.class`
2. For deduplication, use the `dedup_key` action in the rule, not an extraction
3. For custom details, use `event.custom_details.<field_name>` format

#### 4. Workflow Trigger 400 Errors (Keyword Triggers)

**Issue:** Creating workflow triggers with certain condition patterns returns 400 Bad Request with no specific error message.

**Affected Patterns:**
- Multiple `matches part` conditions with OR logic for keywords
- Triggers that overlap significantly with other triggers on the same workflow

**Workaround:**
1. Remove or simplify keyword-based triggers
2. Use priority-based or service-based triggers instead of keyword triggers
3. If keyword matching is required, configure manually in the UI

**Removed Triggers (caused 400 errors):**
- `database_emergency_keyword_auto`
- `identity_crisis_keyword_auto`
- `data_pipeline_keyword_auto`

#### 5. Service Timeout "null" vs "0" Perpetual Drift

**Issue:** Services with `acknowledgement_timeout` and `auto_resolve_timeout` set to `null` in the API show up as needing changes to `0` on every terraform apply.

**Workaround:** Explicitly set timeouts to `0` in Terraform to match the "disabled" state:
```hcl
resource "pagerduty_service" "example" {
  acknowledgement_timeout = 0  # Disabled
  auto_resolve_timeout    = 0  # Disabled
}
```

#### 6. Incident Workflow Triggers Not Supported (OUTDATED)

**Issue:** Previously documented that triggers weren't supported.

**Update:** `pagerduty_incident_workflow_trigger` resource IS supported and works. Triggers can be:
- `type = "conditional"` - Automatic triggers based on conditions
- `type = "manual"` - Manual triggers available in the UI

**Working Example:**
```hcl
resource "pagerduty_incident_workflow_trigger" "example" {
  type                       = "conditional"
  workflow                   = data.pagerduty_incident_workflow.example.id
  services                   = [pagerduty_service.example.id]
  condition                  = "incident.priority matches 'P1'"
  subscribed_to_all_services = false
}
```

#### 7. Alert Grouping Settings Not Exposed

#### 4. OAuth Extensions Require Manual Setup

**Issue:** Slack, Jira, Microsoft Teams, ServiceNow, and Zoom integrations require OAuth browser flows.

**Workaround:** See `MANUAL_SETUP_REQUIRED.md` for step-by-step OAuth setup procedures.

#### 5. Salesforce OAuth Password Flow

**Issue:** Salesforce blocks the OAuth username-password flow by default, causing authentication failures even with valid credentials.

**Workaround:** Two settings must be enabled in Salesforce:
1. **Org-level setting:** Setup → OAuth and OpenID Connect Settings → Enable "Allow OAuth Username-Password Flows"
2. **Connected App setting:** After creating a Connected App, go to Manage Connected Apps → Edit Policies → Set "IP Relaxation" to "Relax IP restrictions"

**Note:** Changes may take 2-10 minutes to propagate after saving.

#### 6. PagerDuty Service Integrations via UI vs API

**Issue:** Adding integrations (like Datadog) to PagerDuty services via the UI sometimes doesn't persist, and the PagerDuty API integration creation can return empty results.

**Workaround:** For reliable integration setup:
1. Create the integration via PagerDuty API: `POST /services/{id}/integrations`
2. Use the vendor ID (e.g., Datadog vendor ID can be found via `GET /vendors?query=datadog`)
3. The integration key is returned in the API response

**Alternative:** Configure bidirectional integrations from the external tool side (e.g., set up PagerDuty integration in Datadog's integrations page using PagerDuty API token).

#### 7. Bidirectional Integration Architecture

**Issue:** Full bidirectional integrations (Datadog, New Relic, Jira, etc.) require setup on BOTH sides.

**Configuration Pattern:**
| Tool | PagerDuty Side | External Tool Side |
|------|----------------|-------------------|
| Datadog | Add Datadog integration to service → Get routing key | Add PagerDuty tile → Enter API key |
| New Relic | Add New Relic integration to service → Get routing key | Create notification channel with PagerDuty |
| Jira Cloud | OAuth via Extensions page | OAuth from Jira marketplace app |
| Sentry | Add Sentry integration to service → Get routing key | Add PagerDuty integration in project settings |

### Integration vs Extension Architecture

Understanding this distinction is critical for troubleshooting:

| Aspect | Integrations (Inbound) | Extensions (Outbound) |
|--------|------------------------|----------------------|
| **Data Flow** | External → PagerDuty | PagerDuty → External |
| **Setup Method** | Routing keys, webhooks | OAuth, API tokens |
| **Terraform Support** | Full (Event Orchestration) | Partial (some extensions) |
| **Demo Behavior** | Simulated via Events API | Actually execute actions |

**Critical Implication:** When running demo scenarios:
- "Inbound integrations" (Datadog, Prometheus, etc.) are **simulated** - we send Events API payloads that *look like* they came from these tools
- "Outbound extensions" (Slack, Jira) are **real** - workflows actually create Slack channels, Jira tickets, etc.

### Event Orchestration Gotchas

#### 1. Rule Order Matters

Global orchestration rules are evaluated **top-to-bottom**. The first matching rule wins. Place specific rules before general catch-all rules.

#### 2. CEL Expression Syntax

PagerDuty uses CEL (Common Expression Language) for conditions. Common pitfalls:

```cel
// WRONG: Using == for regex match
event.summary == ".*critical.*"

// CORRECT: Using matches() for regex
event.summary matches "(?i).*critical.*"

// WRONG: Missing case-insensitive flag
event.summary matches "critical"

// CORRECT: Case-insensitive regex
event.summary matches "(?i)critical"
```

#### 3. Custom Field Extraction

To extract values into custom fields, use `set` actions in orchestration rules:
```hcl
set {
  key   = "pd-custom-field-12345"
  value = "event.custom_details.env"
}
```

The key must be the custom field's **ID**, not its display name.

### Workflow Step Limitations

#### 1. Step Actions via API

Workflow steps cannot be added via the PagerDuty API - only via the UI. The API only supports creating empty workflow shells.

#### 2. Conditional Logic

Workflows support conditions between steps, but complex branching (if/else/loops) requires Enterprise Incident Management tier.

#### 3. Action Input References

Workflow actions can reference incident data using mustache syntax:
- `{{incident.id}}` - Incident ID
- `{{incident.title}}` - Incident title
- `{{incident.urgency}}` - Incident urgency
- `{{incident.service.name}}` - Service name
- `{{incident.priority.name}}` - Priority name (P1, P2, etc.)

### RBA (Runbook Automation) Gotchas

#### 1. Runner Requirement

RBA jobs require a runner agent. This environment uses:
- Runner ID: `P9UFXPZ`
- Location: Process Automation instance

#### 2. Job Script Paths

Job scripts must exist on the runner. The paths in Terraform (`script { script_path = "..." }`) must match actual file locations on the runner.

#### 3. Environment Variables

RBA jobs can pass incident context via environment variables, but variable names must be explicitly defined in the job configuration.

### Demo Scenarios Dashboard Gotchas

The demo dashboard (`docs/demo-scenarios/`) has several implementation details developers should be aware of:

#### 1. Scenario ID Naming Convention

Two ID naming schemes exist in the dashboard:

| Scheme | Pattern | Examples | Use Case |
|--------|---------|----------|----------|
| Dashboard-style | `{TIER}-{NNN}` | `PRO-001`, `BUS-003`, `DIGOPS-005` | Original 46 scenarios |
| Spec-aligned | `{FEATURE}-{NNN}` | `SRE-001`, `SCRIBE-002`, `RBA-003` | Agent and RBA scenarios |

Both are valid. New scenarios should use spec-aligned IDs for consistency with the `COMPREHENSIVE_DEMO_ENVIRONMENT_SPECIFICATION.md`.

#### 2. Agent Type Filter (Derived Field)

The `agent_type` filter is a **derived filter** - it doesn't have a dedicated field in scenarios. Instead, it extracts agent types by pattern-matching two scenario fields:

```javascript
// In FilterPanel.jsx - getAvailableOptionsFromScenarios()
const tools = scenario.tags?.tool || [];
const features = scenario.tags?.features || [];
['sre', 'scribe', 'shift'].forEach(agentType => {
  if (tools.some(t => t === `pagerduty_agent_${agentType}`) ||
      features.some(f => f === `agent_${agentType}`)) {
    agentTypes.add(agentType);
  }
});
```

When adding new agent scenarios, ensure either:
- `tags.tool` includes `pagerduty_agent_{type}` (e.g., `pagerduty_agent_sre`)
- OR `tags.features` includes `agent_{type}` (e.g., `agent_sre`)

#### 3. Adding Scenarios to scenarios.json

The `scenarios.json` file structure is:
```json
{
  "scenarios": [...],    // Array of scenario objects
  "integrations": {...}, // Integration -> scenario mappings
  "filters": {...}       // Available filter options
}
```

When adding scenarios:
1. Add to the `scenarios` array (watch for proper comma placement)
2. Update `integrations` if using a new integration source
3. Update `filters` if introducing new filter values

**Common JSON errors**: Missing commas between array elements, trailing commas after last element.

#### 4. Filter Configuration Locations

Filters are defined in two places:
- `FilterPanel.jsx` - `FILTER_CONFIG` constant defines UI display and ordering
- `scenarios.json` - `filters` object defines available options

Keep these in sync when adding new filter categories.

#### 5. URL Query Parameters

Filters are persisted to URL query parameters for shareability. When adding new filter categories, update `App.jsx`:
```javascript
// Line ~27: Add to the URL parameter list
['industry', 'team_type', 'org_style', 'features', 'integration',
 'tool', 'tool_type', 'severity', 'agent_type'].forEach(key => {
```

---

## GitHub and Security

### GitHub Pages Hosting

**CRITICAL:** The GitHub repository hosts **ONLY** the Demo Scenarios Dashboard static files for GitHub Pages.

**What IS in the repository:**
- Terraform configuration files (no secrets)
- Documentation (Markdown files)
- Demo dashboard source code (React/JavaScript)
- Sample event payloads (no real data)

**What is NOT in the repository:**
- PagerDuty API tokens
- Integration keys/routing keys
- OAuth credentials
- terraform.tfvars with real values
- terraform.tfstate (contains resource IDs)

### Secret Management

All secrets are managed via:

1. **Environment Variables** (local development):
   ```bash
   export PAGERDUTY_TOKEN="your-token"
   ```

2. **terraform.tfvars** (local file, gitignored):
   ```hcl
   pagerduty_token = "your-token"
   slack_connection_id = "actual-id"
   ```

3. **Browser localStorage** (demo dashboard):
   - Credentials never leave the browser except to their respective APIs
   - Never transmitted to GitHub or any backend

### Pre-Commit Checklist

Before committing any changes:

1. **Check for secrets:**
   ```bash
   grep -r "PAGERDUTY_TOKEN\|api_key\|token=" --include="*.tf" --include="*.json" --include="*.js"
   ```

2. **Verify .gitignore:**
   ```
   terraform.tfvars
   terraform.tfstate
   terraform.tfstate.backup
   *.tfvars
   .env
   ```

3. **Review terraform.tfvars.example:**
   - Should contain only placeholder values
   - Never real tokens or IDs

4. **Check demo dashboard:**
   - `docs/demo-scenarios/src/` should not hardcode any credentials
   - All API calls should use localStorage-sourced credentials

### Sensitive Files Reference

| File | Contains | Git Status |
|------|----------|------------|
| `terraform.tfvars` | Real API tokens | **GITIGNORED** |
| `terraform.tfstate` | Resource IDs | **GITIGNORED** |
| `SECRETS.md` | Credential documentation | In repo (no actual secrets) |
| `terraform.tfvars.example` | Placeholder values | In repo |

---

## Questions?

The codebase is self-documenting through:
- Terraform resource comments
- Markdown documentation in `docs/`
- Sample events in `events/samples/`
- Dashboard source code in `docs/demo-scenarios/src/`

All Terraform configurations are valid and ready for `terraform apply`.