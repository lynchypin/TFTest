# PagerDuty Demo Environment

A Terraform-managed PagerDuty demo environment showcasing the full platform across all pricing tiers, add-on products, and AI agents. Features automated incident lifecycle simulation with scenario-specific Slack conversations (user-impersonated), AIOps correlation, Event Orchestration Cache Variables, Status Page updates, Runbook Automation (RBA), and integrated ServiceNow/Jira ticketing. 51 of 70 scenarios are E2E validated as of February 18, 2026 (19 disabled pending external integrations) — see [remaining tasks](docs/NEXT_DEVELOPER_PROMPT.md).

## Project Vision

This environment provides PagerDuty Solutions Engineers with an **always-on demonstration environment** that showcases the platform without manual intervention. Key goals:

1. **Always-On Realism:** Continuously generates realistic incident activity — multi-responder conversations, escalations, status updates, automated remediation, AIOps correlation, and status page communication.
2. **Full Platform Coverage:** Demonstrates every major PagerDuty feature including AIOps/EIM, Incident Workflows, Automation Actions (RBA), Status Pages, Event Orchestration Cache Variables, ServiceNow integration, Service Dependencies, and Slack integration.
3. **Pause/Resume Control:** Presenters can pause the demo at any time. The system auto-detects `[DEMO]` prefix to only process demo incidents.
4. **Scenario Diversity:** 70 scenarios across 16 categories generate contextually appropriate technical conversations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DEMO ENVIRONMENT ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────┐     ┌─────────────────────────────────────────────────────────────┐   │
│   │   GitHub    │     │                    AWS Lambda Functions                      │   │
│   │   Pages     │     │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│   │  Dashboard  │────▶│  │ Orchestrator │  │  Controller  │  │ Health/Reset/    │   │   │
│   │  (React)    │     │  │ (webhooks)   │  │  (scenarios) │  │ Notify/Lifecycle │   │   │
│   └─────────────┘     │  └──────┬───────┘  └──────┬───────┘  └──────────────────┘   │   │
│         │             │         │                 │                                   │   │
│         │             └─────────┼─────────────────┼──────────────────────────────────┘   │
│         │                       │                 │                                       │
│         │                       ▼                 ▼                                       │
│         │             ┌─────────────────────────────────────────────────────────────┐   │
│         │             │                      PagerDuty                               │   │
│         └────────────▶│  • 30+ Services with dependency graph                       │   │
│                       │  • 25 Incident Workflows (auto-triggered)                    │   │
│                       │  • Global + Service Event Orchestration                      │   │
│                       │  • AIOps: Alert Grouping, Correlation, Suppression           │   │
│                       │  • 6 Active users with Slack mapping                        │   │
│                       │  • RBA Automation Jobs + EC2 Runner                          │   │
│                       │  • Status Page (programmatic updates via API)                │   │
│                       │  • ServiceNow (native PagerDuty extension)                   │   │
│                       └────────────────────────┬────────────────────────────────────┘   │
│                                                │                                        │
│         ┌──────────────────────┬───────────────┼───────────────┬────────────────┐       │
│         ▼                      ▼               ▼               ▼                ▼       │
│   ┌───────────┐        ┌────────────┐   ┌───────────┐  ┌────────────┐  ┌────────────┐ │
│   │   Slack   │        │  Datadog   │   │   Jira    │  │ Status Page│  │ ServiceNow │ │
│   │ Workspace │        │  Monitors  │   │  Tickets  │  │  Updates   │  │ (native)   │ │
│   └───────────┘        └────────────┘   └───────────┘  └────────────┘  └────────────┘ │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     RBA Runner (EC2) + Automation Actions                        │   │
│   │  • Executes runbooks triggered by incidents or Lambda                           │   │
│   │  • Diagnostic scripts, remediation, approval gates                              │   │
│   │  • Results posted to incident timeline                                          │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Automated Incident Lifecycle

The `demo-simulator-controller` Lambda is the primary scenario execution engine. It runs a complete incident lifecycle within a single invocation (up to 15 minutes).

### Invocation

```bash
# Quick test (2s delays, ~70s total)
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run_scenario", "scenario_id": "FREE-001", "action_delay": 2}' \
  --cli-binary-format raw-in-base64-out /dev/stdout

# Demo mode (30-60s delays, ~10min total)
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run_scenario", "scenario_id": "FREE-001"}' \
  --cli-binary-format raw-in-base64-out /dev/stdout
```

### Timeline

```
Time 0min      | TRIGGERED: Controller sends event via PagerDuty Events API v2
               |   ├─ Event routed to correct service via Event Orchestration
               |   └─ PD Workflow creates Slack channel + Jira ticket automatically
               |
Time ~10s      | ACKNOWLEDGED: Controller acknowledges as first responder
               |   ├─ Polls conference_bridge for Slack channel ID
               |   ├─ Bot joins channel, invites observers + responders
               |   └─ Posts initial investigation message (as user)
               |
Time 1-8min    | INVESTIGATION: Phased actions with 30-60s delays
               |   Phase 1 (investigating): sre_diagnostic, status_update, add_note
               |   Phase 2 (found_issue): update_custom_fields, reassign, add_note
               |   Phase 3 (working_fix): run_automation, trigger_workflow, shift_handoff
               |   Each action → PD API call + Slack message (user-impersonated)
               |
Time 8-12min   | RESOLVED: Incident resolved via PD API
               |   └─ "DEMO FLOW COMPLETED" logged with scenario ID
```

### Responder Actions During Investigation

| Action | Probability | Description |
|--------|-------------|-------------|
| Post message | 100% | Scenario-specific investigation/progress messages |
| Escalate | 20% | Escalation to higher-level policy |
| Add responders | 15% | Additional responders via PagerDuty API |
| Post status update | 25% | Formal status update on incident |
| Snooze | 10% | Incident snoozed for 10 minutes |
| Reassign | 10% | Incident reassigned to another user |
| Trigger RBA | 10% | Automation Action triggered (invoke_rba) |
| AIOps correlate | varies | Fetches past/related incidents for correlation |
| Status Page update | varies | Updates status page component/incident |

### New Action Types (February 11, 2026)

| Action Type | Handler | Integration |
|-------------|---------|-------------|
| `aiops_correlate` | Fetches past incidents, finds related incidents | PagerDuty AIOps API |
| `status_page_update` | Creates/updates status page incidents and components | PagerDuty Status Page API |
| `invoke_rba` | Invokes automation actions or triggers incident workflows | PagerDuty Automation Actions API |

## Demo Users

### Active Users (PagerDuty + Slack) — USE IN SCHEDULES

Only these 6 users have both PagerDuty AND Slack accounts:

| User | Email | PD ID | Slack ID | Role |
|------|-------|-------|----------|------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U0AA1LZSYHX | Senior SRE, IC |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U0A9GC08EV9 | Platform Engineer |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U0AA1LYLH2M | SRE |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U0A9LN3QVC6 | SRE |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U0A9KANFCLV | SRE Lead, IC |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U0A9SBF3MTN | Platform Engineer |

### PagerDuty-Only Users — DO NOT USE IN SCHEDULES

| User | Email |
|------|-------|
| James Murphy | jmurphy@losandesgaa.onmicrosoft.com |
| Paddy Losty | plosty@losandesgaa.onmicrosoft.com |
| Kaptin Morgan | kmorgan@losandesgaa.onmicrosoft.com |
| Uisce Beatha | ubeatha@losandesgaa.onmicrosoft.com |

## Scenario Categories (70 Total)

| Prefix | Name | Count | Demonstrates |
|--------|------|-------|-------------|
| `IND` | Industry-Specific | 6 | Manufacturing, mining, retail, fintech, energy, telecom |
| `DIGOPS` | Digital Operations | 7 | Alert grouping, suppression, auto-pause, service graph |
| `SRE` | Site Reliability | 6 | SRE workflows and automation |
| `BUS` | Business Tier | 5 | Business features, ServiceNow integration (BUS-004) |
| `EIM` | Enterprise Incident Mgmt | 5 | Tasks, roles, types, priority, custom fields |
| `AIOPS` | AIOps Features | 8 | ML correlation, noise reduction, cache variables, event counting |
| `RBA` | Runbook Automation | 4 | Interactive runbooks, approval gates, self-service |
| `AA` | Automation Actions | 4 | Diagnostic scripts, remediation actions |
| `AUTO` | Auto-Remediation | 4 | Self-healing systems |
| `PRO` | Professional Tier | 3 | Slack coordination, Jira automation |
| `SCRIBE` | AI Scribe | 3 | Documentation AI |
| `SHIFT` | Scheduling | 3 | On-call management |
| `WF` | Workflows | 3 | Workflow automation |
| `FREE` | Free Tier | 2 | Entry-level demos |
| `COMBO` | Full Pipeline | 2 | End-to-end showcase (all features) |
| `CSO` | Status Page | 2 | Status communication to customers |

See [SCENARIO_FLOWS.md](docs/SCENARIO_FLOWS.md) for detailed flows.

## Project Structure

```
.
├── README.md
├── *.tf                                # Terraform: services, escalations, workflows, orchestration
├── cache_variables.tf                  # Event Orchestration Cache Variables (7 resources)
├── aws/
│   ├── main.tf, demo_orchestrator.tf   # AWS infrastructure as code
│   ├── deploy.sh                       # Lambda deployment script
│   ├── lambda-demo-orchestrator/       # Legacy: webhook-driven orchestrator
│   ├── lambda-demo-controller/         # PRIMARY: Self-contained scenario runner
│   ├── lambda-lifecycle/               # Incident lifecycle management
│   ├── lambda-package/                 # Feature-flagged demo package
│   ├── lambda-health-check/            # Integration health checks
│   ├── lambda-reset/                   # Demo environment reset
│   ├── lambda-notifier/                # Slack notifications
│   ├── shared/                         # Shared Python modules (clients.py)
│   └── archive/                        # Archived setup/test scripts
├── docs/
│   ├── NEXT_DEVELOPER_PROMPT.md        # START HERE for new developers
│   ├── ARCHITECTURE_BLUEPRINT.md       # System architecture and status
│   ├── GOTCHAS_AND_WORKAROUNDS.md      # Known issues and solutions (READ THIS)
│   ├── SCENARIO_FLOWS.md              # Scenario types, flows, readiness
│   ├── CREDENTIALS_REFERENCE.md       # All credentials
│   ├── setup/                          # Deployment and setup guides
│   ├── demo-scenarios/                 # React dashboard + scenarios.json
│   └── archive/                        # Historical documentation
├── scripts/
│   ├── e2e_test.py                     # End-to-end test suite
│   ├── test_all_scenarios.py           # Validate all 51 enabled scenarios
│   ├── analyze_scenario_readiness.py   # Scenario status checker
│   ├── status_page_manager.py          # Status Page incident management (rewritten Feb 14)
│   ├── populate_workflow_steps.py      # Workflow step population
│   ├── trigger_demo_incident.sh        # Manual test incident trigger
│   └── archive/                        # Archived one-time scripts
├── modules/                            # Reusable Terraform modules
├── configs/                            # Configuration files
├── archive/                            # Archived obsolete files
│   ├── tfplan-artifacts/               # Old Terraform plan files
│   ├── scripts-oneoff/                 # One-time analysis scripts and logs
│   ├── config-samples/                 # Sample config files
│   ├── terraform-state-backups/        # Historical state backups
│   └── credentials-obsolete/           # Old credential files
└── events/                             # Event payload examples
```

## Quick Start

### Prerequisites

- Terraform >= 1.0
- AWS CLI configured (us-east-1 region)
- PagerDuty account with admin API token
- Python 3.9+
- Slack workspace with bot token (`chat:write.customize` scope required)

### Deploy

```bash
# 1. Terraform (PagerDuty resources)
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply

# 2. AWS Lambda functions
cd aws
bash deploy.sh
```

### Verify

```bash
# Health check (via API Gateway — Lambda Function URLs return 403 on this account)
curl "https://ynoioelti7.execute-api.us-east-1.amazonaws.com/health"

# Or via direct Lambda invocation
aws lambda invoke --function-name demo-simulator-health-check --payload '{}' /tmp/health.json && cat /tmp/health.json

# Trigger test incident
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[DEMO] Test incident",
      "source": "manual-test",
      "severity": "critical",
      "class": "database",
      "component": "postgres"
    }
  }'
```

## Key Lambda Functions

| Function | Region | Trigger | Purpose |
|----------|--------|---------|---------|
| **`demo-simulator-controller`** | **us-east-1** | **Direct invocation** | **PRIMARY: Self-contained scenario runner — triggers events, discovers channels, runs actions** |
| `demo-simulator-orchestrator-v2` | us-east-1 | API Gateway | Legacy: event-driven handler (API: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com`) |
| `demo-simulator-lifecycle` | us-east-1 | EventBridge | Progresses incident states |
| `demo-simulator-health-check` | us-east-1 | EventBridge | Checks integration health |
| `demo-simulator-reset` | us-east-1 | Manual | Resets demo environment |

## Integrations Status

| Integration | Method | Status |
|-------------|--------|--------|
| Slack | Native app + Bot (chat:write.customize) | Working |
| Jira Cloud | OAuth + Workflows (6 projects) | Working |
| Datadog | API monitors (14) | Working (graceful fallback if trial expires — see [Gotchas](docs/GOTCHAS_AND_WORKAROUNDS.md#datadog-trial-expiry)) |
| ServiceNow | Native PagerDuty extension | Connected (no custom code needed) |
| Status Page | PagerDuty Status Page API | Working — API rewritten Feb 14 (see [Gotchas](docs/GOTCHAS_AND_WORKAROUNDS.md#status-page-api-rewrite)) |
| AIOps/EIM | PagerDuty AIOps API | Enabled, code ready |
| Cache Variables | Event Orchestration Cache Variables | 7 deployed (3 global, 4 service-level) |
| RBA/Rundeck | Automation Actions API + EC2 Runner | Runner exists, jobs configured |
| Grafana | Alert channels | Configured |
| New Relic | Workflow integration | Configured |

## Documentation

| Document | Purpose |
|----------|---------|
| [Next Developer Prompt](docs/NEXT_DEVELOPER_PROMPT.md) | **START HERE** — handover, context, remaining tasks |
| [Architecture Blueprint](docs/ARCHITECTURE_BLUEPRINT.md) | System architecture and component status |
| [Gotchas & Workarounds](docs/GOTCHAS_AND_WORKAROUNDS.md) | Known issues and solutions — **read before changing anything** |
| [Scenario Flows](docs/SCENARIO_FLOWS.md) | 70 scenario details, flows, readiness |
| [Credentials Reference](docs/CREDENTIALS_REFERENCE.md) | All credentials and where they're used |
| [Deployment Guide](docs/setup/DEPLOYMENT.md) | Full deployment procedures |
| [RBA Runner Setup](docs/setup/RBA_RUNNER_SETUP.md) | EC2 runner setup for automation demos |

## Support

For questions about this demo environment, contact the PagerDuty Solutions Engineering team.
Project owner: Conall Lynch (clynch@pagerduty.com)