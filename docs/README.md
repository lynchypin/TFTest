# PagerDuty Demo Environment Documentation

**Last Updated:** February 17, 2026

This directory contains all documentation for the PagerDuty Demo Environment project.

---

## Quick Navigation

| Document | Description |
|----------|-------------|
| [NEXT_DEVELOPER_PROMPT.md](NEXT_DEVELOPER_PROMPT.md) | **START HERE** - Complete context for new developers |
| [LLM_HANDOVER_PROMPT.md](LLM_HANDOVER_PROMPT.md) | Full LLM developer handover with remaining work details |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Master implementation plan with phases |
| [GOTCHAS_AND_WORKAROUNDS.md](GOTCHAS_AND_WORKAROUNDS.md) | **READ THIS** - Saves hours of debugging |
| [SCENARIO_FLOWS.md](SCENARIO_FLOWS.md) | How each scenario type works |
| [E2E_TEST_DOCUMENTATION.md](E2E_TEST_DOCUMENTATION.md) | End-to-end test suite documentation |
| [CREDENTIALS_REFERENCE.md](CREDENTIALS_REFERENCE.md) | Credential inventory (no secrets stored here) |
| [project/PROJECT_OVERVIEW.md](project/PROJECT_OVERVIEW.md) | Comprehensive project overview |

---

## Current Implementation Status (February 17, 2026)

| Component | Count | Status |
|-----------|-------|--------|
| PagerDuty Services | 34 | Deployed |
| Incident Workflows | 25 | All with steps |
| Workflow Triggers | 38 | Active (orphaned removed) |
| Jira Integration | 6 workflows | Auto-create tickets |
| E2E Test Suite | 7 tests | All passing |
| Demo Scenarios | 70 | 51 enabled + E2E validated, 19 disabled (pending external integrations) |
| Lambda Functions | 9 | Running — Controller is PRIMARY execution path |
| Datadog Monitors | 14 | Active (trial may be expired — graceful degradation in place) |
| Slack Integration | - | User impersonation enabled, Enterprise Grid `team_id` configured |
| Event Orchestration | 34+ rules | Routes all 51 enabled scenarios correctly |
| Cache Variables | 7 | 3 global + 4 service-level (event tracking, trigger counting) |

### ALL CRITICAL BLOCKERS RESOLVED

All blockers identified in Feb 7-10 have been resolved:

1. ~~**Incidents not being auto-acknowledged**~~ FIXED (Feb 10) — Admin token + responder roles
2. ~~**Demo owner not added to Slack channels**~~ FIXED (Feb 14) — One-by-one invite with error handling
3. ~~**Events routing to default service**~~ FIXED (Feb 9-14) — 34+ orchestration rules, all scenarios route correctly
4. ~~**66 scenarios not fully wired**~~ FIXED (Feb 18) — 51 enabled scenarios validated E2E (100% pass rate), 70 total
5. ~~**Datadog integration not e2e tested**~~ RESOLVED (Feb 14) — Graceful degradation; falls back to PagerDuty Events API

### Phase Completion

| Phase | Status | Details |
|-------|--------|---------|
| Phase 1: Foundation | DONE | Fixed workflows, deleted orphaned triggers |
| Phase 2: Jira | DONE | 6 workflows create Jira tickets |
| Phase 3: Scenario Readiness | DONE | READY scenarios improved 8 to 19 (137% increase) |
| Phase 4: Slack User Impersonation | DONE | Bot posts appear with user names/avatars |
| Phase 5: Core Reliability | DONE | 51/51 enabled scenarios E2E validated (Feb 18) |
| Phase 6: AIOps | Pending | Requires AIOps/EIM license add-on |
| Phase 7: RBA Content | Pending | RBA Runner exists (EC2 i-03ab4fd5f509a8342), runbook content needed |
| Phase 8: Documentation Audit | DONE | Credentials scrubbed, stale refs fixed, webhooks removed (Feb 17) |
| Phase 9: Resilience | DONE | Schedule rebalancing, retry logic, Slack health check (Feb 18) |
| Phase 10: Cache Variables | DONE | 7 cache variables, 4 new AIOPS scenarios, auto-pause (Feb 18) |

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for full roadmap.

---

## Documentation Structure

```
docs/
├── README.md                              # This file - documentation index
├── NEXT_DEVELOPER_PROMPT.md               # ⭐ START HERE - Complete context for new devs
├── IMPLEMENTATION_PLAN.md                 # Master implementation plan with phases
├── GOTCHAS_AND_WORKAROUNDS.md             # ⭐ READ THIS - Saves hours of debugging
├── SCENARIO_FLOWS.md                      # How each scenario type works
├── E2E_TEST_DOCUMENTATION.md              # End-to-end test suite docs
├── CREDENTIALS_REFERENCE.md               # External tool credentials (SENSITIVE)

│
├── development/                           # Developer documentation
│   ├── DEVELOPER_GUIDE.md                 # Development workflow & gotchas
│   ├── LAMBDA_LIFECYCLE_IMPLEMENTATION_GUIDE.md  # Lambda architecture
│   ├── RBA_SCHEDULED_JOBS.md              # RBA job scheduling
│   └── WORKAROUNDS.md                     # Historical workarounds
│
├── setup/                                 # Setup & deployment guides
│   ├── DEPLOYMENT.md                      # Terraform, Lambda deployment
│   ├── RBA_RUNNER_SETUP.md                # RBA runner deployment
│   └── MANUAL_SETUP_REQUIRED.md           # Manual configuration steps
│
├── project/                               # Project planning & vision
│   └── PROJECT_OVERVIEW.md                # Architecture, goals
│
├── features/                              # PagerDuty feature documentation
│   ├── EVENT_ORCHESTRATION.md             # Event Orchestration config
│   ├── INCIDENT_WORKFLOWS.md              # Incident Workflow details
│   └── RBA_DOCUMENTATION.md               # Runbook Automation docs
│
├── archive/                               # Historical/outdated documentation
│   ├── REMAINING_WORK.md                  # Old remaining work (see IMPLEMENTATION_PLAN.md)
│   ├── DEVELOPER_HANDOVER.md              # Old handover doc (see NEXT_DEVELOPER_PROMPT.md)
│   └── ...                                # Other historical docs
│
└── demo-scenarios/                        # React dashboard application
    └── (source code)
```

---

## AWS Infrastructure Status (February 2026)

The demo environment runs entirely on AWS Free Tier with no ongoing costs.

| Component | Resource | Status | Cost |
|-----------|----------|--------|------|
| RBA Runner | EC2 t2.micro | Running | FREE |
| Traffic Simulation | 8 Lambda functions | Active | FREE |
| Runner Storage | S3 bucket | Active | FREE |
| Scheduling | EventBridge rules | Active | FREE |

**AWS Account:** `127214181728` (us-east-1)

### Lambda Functions

| Function | Purpose | Schedule |
|----------|---------|----------|
| demo-simulator-orchestrator | Creates [DEMO] incidents randomly | Every hour (30% probability) |
| demo-simulator-controller | **NEW:** Full demo flow orchestration with pause/play | On-demand via API |
| demo-simulator-lifecycle | Manages incident lifecycle (ack/resolve) | Every 15 min |
| demo-simulator-notifier | Sends Slack DM notifications | Every 2 min |
| demo-simulator-metrics | Sends metrics to Datadog/New Relic | Every 5 min |
| demo-simulator-reset | Resolves all [DEMO] incidents | On demand |
| demo-simulator-user-activity | Simulates user actions on incidents | On demand |
| demo-simulator-health-check | Checks integration health status | Every 15 min |

### Demo Controller (NEW - February 2026)

The **demo-simulator-controller** is the primary Lambda for running controlled demos. It provides:

- **Full orchestration**: Reset → Trigger → Ack → Channel → Investigation → Resolution
- **66 scenarios**: Loads all scenarios from `scenarios.json`
- **Configurable timing**: 30-60 second delays between actions
- **Pause/Play**: Stop and resume demo flow at any point
- **Observer mode**: Admin (clynch) is never assigned to incidents, only observes

See [RBA_RUNNER_SETUP.md](setup/RBA_RUNNER_SETUP.md) for detailed runner deployment documentation including critical gotchas and workarounds.

---

## By Category

### Getting Started

1. **[Project Overview](project/PROJECT_OVERVIEW.md)** - Start here to understand the project
2. **[Scenario Flows](SCENARIO_FLOWS.md)** - How each demo scenario works
3. **[Deployment Guide](setup/DEPLOYMENT.md)** - How to deploy the environment
4. **[Manual Setup Required](setup/MANUAL_SETUP_REQUIRED.md)** - Steps that cannot be automated

### For Developers

1. **[Developer Guide](development/DEVELOPER_GUIDE.md)** - Architecture, gotchas, known issues
2. **[Secrets Management](setup/SECRETS.md)** - How credentials are handled
3. **[E2E Test Documentation](E2E_TEST_DOCUMENTATION.md)** - Test results and how to run tests

### PagerDuty Features

| Feature | Document | Description |
|---------|----------|-------------|
| Event Orchestration | [EVENT_ORCHESTRATION.md](features/EVENT_ORCHESTRATION.md) | Alert routing, enrichment, suppression |
| Incident Workflows | [INCIDENT_WORKFLOWS.md](features/INCIDENT_WORKFLOWS.md) | Automated incident response actions |
| Implementation Plan | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Phases, priorities, and roadmap |
| Runbook Automation | [RBA_DOCUMENTATION.md](features/RBA_DOCUMENTATION.md) | Automated runbooks |
| License Filtering | [LICENSE_FILTERING.md](features/LICENSE_FILTERING.md) | Plan-based feature availability |

### Reference

- **[Healthchecks Setup](setup/healthchecks_setup.md)** - External health monitoring configuration
- **[Credentials Reference](CREDENTIALS_REFERENCE.md)** - API keys and tokens for all integrations

### Archive (Historical)

The following documents are historical and may contain outdated information:

| Document | Description |
|----------|-------------|
| [Demo Environment Proposal](archive/DEMO_ENVIRONMENT_PROPOSAL.md) | Original comprehensive design document |
| [25-Tool Integration Plan](archive/COMPLETE_25_TOOL_INTEGRATION_PLAN.md) | Full integration roadmap |
| [Environment Audit](archive/EXHAUSTIVE_DEMO_ENVIRONMENT_AUDIT.md) | Complete audit and blockers |
| [Integration Requirements](archive/INTEGRATION_REQUIREMENTS_DETAILED.md) | Per-tool requirements |

---

## Demo Controller Usage

The **demo-simulator-controller** Lambda is the recommended way to run controlled demos. It provides a complete orchestrated flow from incident creation to resolution.

### Running a Demo

**Start a demo with a specific scenario:**
```bash
curl -X POST "https://<LAMBDA_URL>/" \
  -H "Content-Type: application/json" \
  -d '{"action": "run", "scenario_id": "PRO-001"}'
```

**List all available scenarios (66 total):**
```bash
curl -X POST "https://<LAMBDA_URL>/" \
  -H "Content-Type: application/json" \
  -d '{"action": "list_scenarios"}'
```

**Pause a running demo:**
```bash
curl -X POST "https://<LAMBDA_URL>/" \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}'
```

**Resume a paused demo:**
```bash
curl -X POST "https://<LAMBDA_URL>/" \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}'
```

**Reset all demo incidents:**
```bash
curl -X POST "https://<LAMBDA_URL>/" \
  -H "Content-Type: application/json" \
  -d '{"action": "reset"}'
```

### Demo Flow Sequence

When you run a demo, the controller executes these steps automatically:

1. **Reset** - Resolve all existing [DEMO] incidents
2. **Trigger** - Create new incident for selected scenario
3. **Wait** - Configurable delay (30-60 seconds)
4. **Acknowledge** - Fake user acknowledges incident
5. **Create Channel** - Slack channel created, admin added as observer
6. **Investigation** - Fake users post investigation messages
7. **Progress** - Multiple progress updates with delays
8. **Resolution** - Fake user resolves incident with root cause

### Scenario IDs

Scenarios are organized by PagerDuty plan tier:

| Prefix | Plan Tier | Example |
|--------|-----------|---------|
| FREE-* | Free | FREE-001: Simple Alert Routing |
| PRO-* | Professional | PRO-001: Priority-Based Routing |
| BUS-* | Business | BUS-001: Response Mobilizer |
| DIGOPS-* | Digital Operations | DIGOPS-001: Noise Reduction |
| AIOPS-* | AIOps Add-on | AIOPS-001: Intelligent Grouping |
| EIM-* | Enterprise | EIM-001: Incident Tasks |
| AUTO-* | Automation Add-on | AUTO-001: Automated Diagnostics |
| CSO-* | Customer Service Ops | CSO-001: Customer Impact |
| WF-* | Workflow Scenarios | WF-001: Status Page Integration |
| IND-* | Industry Specific | IND-001: Healthcare Compliance |
| SRE-* | SRE Agent | SRE-001: Autonomous Investigation |
| SCRIBE-* | Scribe Agent | SCRIBE-001: Automated Documentation |
| SHIFT-* | Shift Agent | SHIFT-001: Handoff Automation |
| AA-* | Automation Actions | AA-001: Diagnostic Collection |
| RBA-* | Runbook Automation | RBA-001: Interactive Runbooks |
| COMBO-* | Combined Features | COMBO-001: Full Pipeline |

---

## Demo Dashboard

The interactive Demo Scenarios Dashboard is located in `docs/demo-scenarios/`.

**Live URL:** https://lynchypin.github.io/TFTest/

**Local Development:**
```bash
cd docs/demo-scenarios
npm install
npm run dev
```

---

## Comprehensive Specification Summary

The `COMPREHENSIVE_DEMO_ENVIRONMENT_SPECIFICATION.md` defines 42 major scenarios across:

| Category | Scenarios | Example |
|----------|-----------|---------|
| Professional Tier | P1-P5 | Slack coordination, Jira automation |
| Business Tier | B1-B6 | Custom fields, service orchestration |
| Digital Operations | D1-D3 | AIOps grouping, past incidents |
| Enterprise Tier | E1-E5 | Incident tasks, ServiceNow integration |
| AIOps Add-on | AI1-AI3 | Intelligent grouping, noise reduction |
| SRE Agent | SRE1-SRE6 | Autonomous investigation and remediation |
| Scribe Agent | SCRIBE1-SCRIBE3 | Automated documentation |
| Shift Agent | SHIFT1-SHIFT3 | On-call handoff automation |
| Automation Actions | AA1-AA3 | Diagnostic collection, auto-remediation |
| Runbook Automation | RBA1-RBA4 | Interactive runbooks, self-service |
| Combined | COMBO1 | Full automation pipeline |

> **Note:** PagerDuty Advance (ADV1-ADV2) and PagerDuty Copilot (CP1) scenarios were removed as these products have been restructured into the AI Agents product line.

---

## Archived Documentation

Historical and superseded documentation is in `archive/docs/`:

| Document | Status |
|----------|--------|
| DEMO_HANDOVER.md | Superseded by PROJECT_OVERVIEW.md |
| DEVELOPER_HANDOVER.md | Superseded by DEVELOPER_GUIDE.md |
| QUICK_START.md | Superseded by DEPLOYMENT.md |
| MANUAL_SETUP_GUIDES.md | Superseded by MANUAL_SETUP_REQUIRED.md |
| SYSTEM_BLUEPRINT.md | Superseded by PROJECT_OVERVIEW.md |
| TODO.md | Completed |
| Others | Historical reference only |

---

## Known Limitations and Workarounds (February 2026)

This section documents critical platform limitations discovered during development that affect demo functionality.

### 1. Slack Guest Users Cannot Use PagerDuty App

**Limitation:** Slack guest accounts (single-channel or multi-channel guests) cannot interact with the PagerDuty Slack app. This is a Slack platform limitation, not PagerDuty.

**Impact:**
- Guest users cannot link PagerDuty to Slack
- Guest users cannot use `/pd` slash commands
- Guest users cannot receive PagerDuty DMs via Slack

**Workaround:** Only use full Slack members (not guests) in PagerDuty schedules. The incident lifecycle simulator can only impersonate full Slack members.

**Affected Users:** James Murphy, Paddy Losty, Kaptin Morgan, Uisce Beatha (PagerDuty-only, not in Slack)

### 2. Schedule Users Must Exist in Both Systems

**Limitation:** For the AWS Lambda lifecycle simulator to function correctly, users in on-call schedules must exist in BOTH PagerDuty AND Slack.

**Valid Users for Schedules:**
- Jim Beam, Jameson Casker, Arthur Guiness, Jose Cuervo, Jack Daniels, Ginny Tonic

**Configuration:** See `data_lookups.tf` - the `emails` local should only contain these 6 users.

### 3. Terraform Cannot Manage Incident Workflow Steps

**Limitation:** The PagerDuty Terraform provider can create workflow shells but cannot populate workflow steps. The API POST endpoint returns 404 for workflow step creation.

**Workaround:** Two-phase deployment:
1. Run `terraform apply` to create empty workflow shells
2. Run `python scripts/populate_workflow_steps.py --apply` to add steps via API PUT

See [DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md) for detailed instructions.

### 4. PagerDuty API Token May Lack Schedule Permissions

**Limitation:** Some PagerDuty API tokens do not have permission to modify schedules, even if they can read them.

**Symptom:** `403 Forbidden - Access Denied` when running Terraform for schedule changes.

**Workaround:** Use PagerDuty UI to update schedules, or obtain an admin API token.

---

## Quick Reference: Document Locations

| What You Need | Primary Document | Backup Document |
|---------------|------------------|-----------------|
| Critical workarounds/gotchas | [GOTCHAS_AND_WORKAROUNDS.md](GOTCHAS_AND_WORKAROUNDS.md) | [DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md) |
| Deployment procedures | [DEPLOYMENT.md](setup/DEPLOYMENT.md) | [RBA_RUNNER_SETUP.md](setup/RBA_RUNNER_SETUP.md) |
| User/schedule configuration | [DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md) | `data_lookups.tf` source |
| Workflow step population | [DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md) | `scripts/populate_workflow_steps.py` |
| Scenario definitions | [SCENARIO_FLOWS.md](SCENARIO_FLOWS.md) | [scenarios.json](../scenarios.json) |

---
