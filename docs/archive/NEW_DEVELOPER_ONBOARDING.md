# New Developer Onboarding: PagerDuty Demo Environment

You are working on a **PagerDuty Demo Environment** - a Terraform-managed system that simulates realistic incident management scenarios for PagerDuty Solutions Engineers to use in customer demonstrations.

---

## WHAT THIS PROJECT DOES

This project creates fake but realistic incidents in PagerDuty, complete with:
- Automated Slack conversations between simulated responders
- Incident lifecycle progression (trigger → acknowledge → investigate → resolve)
- Integration with Datadog, New Relic, and other observability tools
- Runbook Automation (RBA) job execution

**The goal:** Show prospects how PagerDuty handles real-world incidents without requiring actual production problems.

---

## ARCHITECTURE AT A GLANCE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HOW IT ALL CONNECTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   scenarios.json ──────► Lambda Functions ──────► PagerDuty                  │
│   (66 incident           (runs on schedule)       (creates incidents)        │
│    templates)                   │                       │                    │
│                                 │                       │                    │
│                                 ▼                       ▼                    │
│                            Slack API              Slack Channels             │
│                       (posts messages as          (incident-specific)        │
│                        fake responders)                                      │
│                                                                              │
│   Terraform ────────► PagerDuty Config                                       │
│   (*.tf files)        - 13 Services                                          │
│                       - 6 Escalation Policies                                │
│                       - 22 Incident Workflows                                │
│                       - Event Orchestration                                  │
│                       - Schedules                                            │
│                                                                              │
│   Datadog/NewRelic ──► Metrics ──► Monitor Alert ──► PagerDuty Event         │
│   (observability)                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## KEY DIRECTORIES

| Directory | Purpose |
|-----------|---------|
| `aws/` | Lambda function code (Python) |
| `aws/shared/` | Shared PagerDuty and Slack API clients |
| `aws/lambda-demo-orchestrator/` | Creates new incidents from scenarios |
| `aws/lambda-lifecycle/` | Progresses existing incidents (ack, notes, resolve) |
| `aws/lambda-demo-controller/` | Controlled demo mode (pause/play) |
| `configs/` | Configuration files |
| `docs/demo-scenarios/src/data/scenarios.json` | 66 incident scenario templates |
| `*.tf` | Terraform files defining PagerDuty resources |
| `scripts/` | Utility scripts for setup/testing |
| `docs/` | Documentation |

---

## THE SCENARIO SYSTEM

Every demo incident comes from `docs/demo-scenarios/src/data/scenarios.json`. Each scenario defines:

```json
{
  "id": "DB-001",
  "name": "Database Connection Pool Exhaustion",
  "target_service": "Database - Primary",
  "category": "database",
  "payload": {
    "summary": "Database connection pool exhausted - 0 connections available",
    "severity": "critical",
    "custom_details": {
      "environment": "production",
      "pd_service": "Database - Primary",
      "incident_type": "database_connectivity"
    }
  },
  "features_demonstrated": ["basic_routing", "escalation_policies", "slack_incident_channel"],
  "slack_messages": [
    {"role": "oncall", "message": "Looking into the connection pool issue now"},
    {"role": "responder", "message": "I see the pool is at 0/100 connections"}
  ]
}
```

**Key Fields:**
- `target_service`: Which PagerDuty service receives the incident
- `payload.custom_details.pd_service`: Metadata about the service (should match target_service)
- `features_demonstrated`: What PagerDuty features this scenario showcases
- `slack_messages`: Conversation to simulate in the incident channel

---

## YOUR PRIMARY TASK: FIX THE SCENARIO FLOW

There are **known issues** preventing scenarios from working correctly end-to-end. Your job is to fix them.

### ISSUE 1: 15 Missing PagerDuty Services

Many scenarios reference services that don't exist. When triggered, these fail silently or route to the wrong service.

**Missing Services:**
| Service Name | Used By |
|-------------|---------|
| Clinical Systems - EMR | HEALTH-001 through HEALTH-004 |
| Grid Operations Center | ENERGY-001 through ENERGY-004 |
| Mining Operations - Equipment | MINING-001 through MINING-003 |
| OT Operations - Factory Floor | MFG-001 through MFG-004 |
| Quality Control - Manufacturing | MFG-* scenarios |
| Payment Processing - Gateway | FINTECH-001 through FINTECH-003 |
| Retail Systems - POS | RETAIL-001, RETAIL-002 |

**Fix Options:**
1. **Add services to Terraform** (`services.tf`) - Preferred
2. **Update scenarios to use existing services** (`scenarios.json`)

**To add a service via Terraform:**
```hcl
# In services.tf, add to the locals.services list
{
  name        = "Clinical Systems - EMR"
  description = "Healthcare EMR system"
  ep          = "default"  # Must match an escalation policy key
  runbook_url = "https://example.com/runbook"
}
```

Then run:
```bash
terraform plan
terraform apply
```

---

### ISSUE 2: 4 Scenarios Have Payload Mismatches

The `target_service` doesn't match `custom_details.pd_service`:

| Scenario | target_service | pd_service (wrong) |
|----------|---------------|-------------------|
| PRO-001 | Platform - Kubernetes/Platform | Platform - DBRE |
| DIGOPS-002 | Platform - Kubernetes/Platform | Platform - Network |
| EIM-001 | Platform - Kubernetes/Platform | Platform - DBRE |
| AUTO-003 | Platform - Kubernetes/Platform | Database - DBRE Team |

**Fix:** Edit `docs/demo-scenarios/src/data/scenarios.json` and make `pd_service` match `target_service`.

---

### ISSUE 3: Datadog → PagerDuty Integration Needs Verification

**The Flow:**
1. Lambda sends metrics to Datadog
2. Datadog monitor threshold exceeded
3. Datadog sends alert to PagerDuty
4. PagerDuty creates incident

**Recently Fixed (Feb 2026):** The Datadog integration was updated to use the correct Event Orchestration routing key: `R028NMN4RMUJEARZ18IJURLOU1VWQ779`

**To Test:**
```bash
# Trigger a high metric value
curl -X POST "https://api.datadoghq.com/api/v1/series" \
  -H "DD-API-KEY: $DATADOG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "series": [{
      "metric": "demo.api.response_time",
      "points": [['$(date +%s)', 500]],
      "type": "gauge"
    }]
  }'

# Wait 5 minutes for monitor to evaluate
# Check PagerDuty for new incident
```

---

### ISSUE 4: Lambda Code Changes Need Deployment

Recent code changes (Slack profile updates) are NOT deployed to AWS Lambda.

**Changed Files:**
- `aws/shared/clients.py`
- `aws/shared/__init__.py`
- `aws/lambda-demo-orchestrator/handler.py`
- `aws/lambda-package/handler.py`
- `aws/lambda-demo-controller/handler.py`

**To Deploy:**
```bash
cd aws
./deploy.sh  # Or use the Terraform AWS module
```

---

## CREDENTIALS YOU NEED

All credentials are in `terraform.tfvars` (not committed to git). You need:

| Variable | Purpose |
|----------|---------|
| `pagerduty_admin_token` | PagerDuty REST API token |
| `slack_bot_token` | Slack Bot OAuth token (xoxb-...) |
| `datadog_api_key` | Datadog API key |
| `datadog_app_key` | Datadog Application key |

**PagerDuty Site:** `pdt-losandes.pagerduty.com`

**Known Token Issue:** Token `u+vNaP7xtfSRRQr8TNnzdyvt5WUJ4xdA` returns 401 Unauthorized. Use the token from `terraform.tfvars` instead.

---

## THE 6 VALID DEMO USERS

Only these users exist in BOTH PagerDuty AND Slack. Use only these in schedules:

| Name | PagerDuty ID | Slack ID |
|------|-------------|----------|
| Jim Beam | PG6UTES | U0AA1LZSYHX |
| Jack Daniels | PR0E7IK | U0A9GC08EV9 |
| Jameson Casker | PCX6T22 | U0AA1LYLH2M |
| Jose Cuervo | PVOXRAP | U0A9LN3QVC6 |
| Ginny Tonic | PNRT76X | U0A9KANFCLV |
| Arthur Guinness | PYKISPC | U0A9SBF3MTN |

**Do NOT use:** James Murphy, Paddy Losty, Kaptin Morgan, Uisce Beatha (not in Slack)

---

## KEY CODE FILES

### `aws/shared/clients.py`
The central API client. Contains `PagerDutyClient` and `SlackClient` classes.

```python
# Trigger an incident
pd = PagerDutyClient()
pd.trigger_incident(
    routing_key="...",
    summary="[DEMO] Something broke",
    severity="critical",
    source="demo-simulator",
    dedup_key="unique-key-123"
)

# Post to Slack as a fake user
slack = SlackClient()
slack.post_message_as_user(
    channel_id="C123...",
    user_name="Jim Beam",
    user_avatar="https://...",
    message="I'm investigating now"
)
```

### `aws/lambda-demo-orchestrator/handler.py`
Runs every hour. Picks random scenarios and creates incidents.

### `aws/lambda-lifecycle/handler.py`
Runs every 15 minutes. Processes existing incidents: acknowledges, posts messages, resolves.

### `services.tf`
Defines PagerDuty services. Add missing services here.

### `docs/demo-scenarios/src/data/scenarios.json`
The 66 scenario definitions. Fix payload mismatches here.

---

## TERRAFORM BASICS

The PagerDuty infrastructure is managed via Terraform.

```bash
# Initialize (first time)
terraform init

# See what will change
terraform plan

# Apply changes
terraform apply

# Get output values (like routing keys)
terraform output datadog_routing_key
```

**Key Terraform Files:**
| File | What It Creates |
|------|----------------|
| `services.tf` | PagerDuty services |
| `escalation_policies.tf` | Who gets paged |
| `schedules.tf` | On-call schedules |
| `incident_workflows.tf` | Automated incident workflows |
| `integrations.tf` | Event orchestration integrations |
| `global_orchestration.tf` | Event routing rules |

---

## ROUTING KEYS (CRITICAL)

There are TWO types of routing keys:

| Key | Value | Use For |
|-----|-------|---------|
| **Event Orchestration Key** | `R028NMN4RMUJEARZ18IJURLOU1VWQ779` | Datadog integration, external tools |
| **Service Integration Key** | `ed6b71f8718b4302d054db5f4cf7228f` | Direct API calls to specific service |

**Datadog MUST use the Event Orchestration key.** This was the root cause of a major integration issue.

---

## TESTING A SCENARIO END-TO-END

1. **Pick a scenario** from `scenarios.json` (e.g., `DB-001`)

2. **Verify the target service exists:**
```bash
curl -s -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/services" | jq '.services[].name'
```

3. **Trigger manually:**
```bash
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "dedup_key": "test-'$(date +%s)'",
    "payload": {
      "summary": "[DEMO] Database Connection Pool Exhaustion",
      "severity": "critical",
      "source": "demo-test",
      "custom_details": {
        "pd_service": "Database - Primary",
        "environment": "production"
      }
    }
  }'
```

4. **Check PagerDuty** for the incident

5. **Wait for lifecycle Lambda** (runs every 15 min) to progress it, OR manually acknowledge/resolve

---

## COMMON GOTCHAS

### 1. Workflow Steps Can't Be Created via Terraform
Terraform creates workflow shells only. Use `scripts/populate_workflow_steps.py` to add steps:
```bash
export PAGERDUTY_TOKEN=your_api_key
python scripts/populate_workflow_steps.py --apply
```

### 2. Slack Guest Users Can't Use PagerDuty
Slack guests cannot interact with PagerDuty. All demo users must be full Slack members.

### 3. Schedule Updates Return 403
The current API token lacks permission to update schedules. Need admin-level token.

### 4. Datadog Monitors Have Evaluation Periods
A single high metric won't trigger an alert. Metrics must exceed thresholds for the evaluation window (typically 5 minutes).

---

## DOCUMENTATION TO READ

| Doc | What It Contains |
|-----|------------------|
| `docs/development/REMAINING_WORK.md` | Full list of remaining tasks with context |
| `docs/development/DEVELOPER_GUIDE.md` | All the gotchas and workarounds |
| `docs/development/WORKAROUNDS.md` | Known issues and their solutions |
| `docs/setup/DEPLOYMENT.md` | How to deploy Lambda changes |
| `docs/CREDENTIALS_REFERENCE.md` | All API keys and tokens |

---

## YOUR CHECKLIST

- [ ] Get access to `terraform.tfvars` with credentials
- [ ] Run `terraform init` and `terraform plan` successfully
- [ ] Identify which scenarios are broken (missing services, payload mismatches)
- [ ] Decide: Create missing services OR update scenarios to use existing ones
- [ ] Make changes and test end-to-end
- [ ] Deploy Lambda changes if modified
- [ ] Verify Datadog → PagerDuty flow works
- [ ] Document any new gotchas you discover

---

## QUICK REFERENCE

**PagerDuty API:**
```bash
# List services
curl -s -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/services" | jq '.services[].name'

# List incidents
curl -s -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged"

# Trigger event
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{"routing_key":"...", "event_action":"trigger", ...}'
```

**Terraform:**
```bash
terraform init
terraform plan
terraform apply
terraform output
```

**Lambda Deployment:**
```bash
cd aws
./deploy.sh
```

---

Good luck! When in doubt, read `docs/development/REMAINING_WORK.md` - it has the most comprehensive context.