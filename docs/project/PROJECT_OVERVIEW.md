# PagerDuty Demo Environment - Project Overview

**Version:** 3.2
**Last Updated:** February 18, 2026
**Status:** Production (51/51 Enabled Scenarios E2E Validated, 70 Total)

---

## Quick Start for New Developers

**Start here to understand the current state:**

| Document | Purpose |
|----------|---------|
| [NEXT_DEVELOPER_PROMPT.md](../NEXT_DEVELOPER_PROMPT.md) | **START HERE - Complete project context and handover** |
| [GOTCHAS_AND_WORKAROUNDS.md](../GOTCHAS_AND_WORKAROUNDS.md) | **Saves hours of debugging** |
| [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) | Master implementation plan with phases |
| [Lambda Implementation Guide](../development/LAMBDA_LIFECYCLE_IMPLEMENTATION_GUIDE.md) | Architecture, API reference |

**Key Components (February 18, 2026 Update):**

| Component | Status | Description |
|-----------|--------|-------------|
| Demo Controller Lambda | **PRIMARY** | `demo-simulator-controller` — self-contained scenario runner, single Lambda invocation |
| 51/70 Scenarios | VALIDATED | All enabled scenarios pass E2E via `scripts/test_all_scenarios.py` |
| Terraform Infrastructure | COMPLETE | 205+ PagerDuty resources (services, teams, workflows, orchestrations) |
| Cache Variables | COMPLETE | 7 Event Orchestration cache variables (3 global, 4 service-level) in `cache_variables.tf` |
| Auto-Pause Notifications | COMPLETE | `auto_pause_notifications_parameters` on services for transient alert handling |
| Slack Health Check | COMPLETE | Controller validates token at startup via `verify_token()` (Feb 18) |
| Slack User Impersonation | COMPLETE | Bot posts as users via `chat:write.customize` + `post_as_user()` |
| Multi-Message Conversations | COMPLETE | Phased messages from `CONVERSATION_LIBRARY` (investigating → resolved) |
| Schedule Rebalancing | COMPLETE | All 6 users have 2-3 schedule assignments (Feb 18) |
| Incident Resolution | IMPROVED | Retry logic with error logging on `resolve_incident()` (Feb 18) |
| Jira Integration | COMPLETE | 6 workflows create tickets automatically |
| Status Page API | COMPLETE | Rewritten Feb 14 to use correct PagerDuty Status Page API |
| Datadog Integration | GRACEFUL | Fallback to direct PagerDuty Events API if trial expired |
| API Gateway (Orchestrator) | WORKING | `https://ynoioelti7.execute-api.us-east-1.amazonaws.com` |
| Lambda Function URLs | **BROKEN** | Return 403 Forbidden on this AWS account — use `aws lambda invoke` or API Gateway |
| PagerDuty Webhook | **DELETED** | Subscription PILGGJ0 deleted Feb 17 — controller does not use webhooks |

**Remaining Work:**
- Enable 19 disabled scenarios (pending external integrations: ServiceNow, Grafana, UptimeRobot, etc.)
- AIOps/EIM features (requires add-on license)
- RBA interactive runbook content creation
- Fix Terraform Lambda code detection (Terraform doesn't detect Lambda code changes)
- Cache variable TTL tuning based on real demo usage patterns

See full details: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)

---

## Vision and Goals

### Purpose

This project provides a comprehensive PagerDuty demo environment that showcases the full capabilities of PagerDuty's incident management platform. It enables Sales Engineers, Solutions Architects, and Partners to demonstrate real-world incident response scenarios to prospects.

### Key Objectives

1. **Demonstrate Value Across Industries:** Pre-built scenarios for technology, finance, healthcare, retail, mining, energy, and more
2. **Show Feature Breadth:** Coverage of ~95% of PagerDuty features across all plan tiers
3. **Enable Self-Service Demos:** Web-based dashboard for triggering scenarios without CLI access
4. **Support Plan-Based Conversations:** Filter scenarios by customer's PagerDuty plan and add-ons
5. **Reduce Demo Prep Time:** From hours of manual setup to instant scenario execution

---

## Project Components

### 1. Terraform Infrastructure (`*.tf` files)

The core PagerDuty configuration managed as Infrastructure as Code:

| Component | Count | Purpose | File |
|-----------|-------|---------|------|
| Services | 12 | Simulate different team/application services | `variables_and_locals.tf`, `services.tf` |
| Teams | 5 | Platform, App, Support, Corp IT, SecOps | `data_lookups.tf` |
| Users | 10 | Demo personas mapped to real PD accounts | `data_lookups.tf` |
| Schedules | 5 | On-call rotations for different teams | `variables_and_locals.tf`, `schedules.tf` |
| Escalation Policies | 5 | Multi-tier escalation paths | `variables_and_locals.tf`, `escalation_policies.tf` |
| Business Services | 6 | Business-level service groupings | `business_services.tf` |
| Service Dependencies | 15+ | Service relationship mappings | `business_services.tf`, `bs_dependencies.tf` |
| Global Event Orchestration | 1 | Multi-rule routing across 5 rule sets | `global_orchestration.tf` |
| Service Orchestrations | 10 | Service-level routing and automation | `service_orchestrations.tf` |
| Incident Workflows | 22 | Automated response playbooks | `incident_workflows.tf` |
| Workflow Triggers | 22+ | Automatic/manual workflow triggers | `incident_workflow_triggers.tf` |
| Automation Actions (RBA) | 22 | 2 runners + 20 automation jobs | `automation_actions.tf` |
| Custom Fields | 4+ | Incident metadata fields | `custom_fields.tf` |
| Incident Types | 5+ | Categorization for incidents | `incident_types.tf` |
| Event Orchestration Integrations | 9 | Datadog, Prometheus, Splunk, etc. | `integrations.tf` |
| Routing Rules | 13+ | Event routing configuration | `routing_rules.tf` |

### 2. Demo Scenarios Dashboard (`docs/demo-scenarios/`)

A React-based web application for triggering demo scenarios:

**URL:** https://lynchypin.github.io/TFTest/

**Features:**
- 66 pre-configured scenarios across multiple industries
- Filter by: Integration, Severity, Team Type, Industry, Features, Tool Type, PagerDuty Agent
- License/plan-based filtering (Free, Professional, Business, Digital Operations, Enterprise)
- Dark mode UI
- Credential management via browser localStorage
- Two-tier integration flow: Full Flow (via external tools) and Fallback (direct PagerDuty API)

**Dashboard Settings:**
The dashboard requires minimal configuration. Users enter credentials via the Settings modal:

| Setting | Tab | Purpose |
|---------|-----|---------|
| PagerDuty Instance | PagerDuty | Subdomain for incident links (e.g., `acme`) |
| Fallback Routing Key | PagerDuty | Optional - only for direct API fallback |
| Datadog API Key/App Key | External Tools | For Full Flow Datadog scenarios |
| New Relic API Key/Account ID | External Tools | For Full Flow New Relic scenarios |
| Grafana API Key/Instance | External Tools | For Full Flow Grafana/Prometheus scenarios |
| CloudWatch Credentials | External Tools | For Full Flow CloudWatch scenarios |
| GitHub PAT/Repo | External Tools | For Full Flow GitHub Actions scenarios |

**Scenario Categories:**
| Category | ID Prefix | Count | Description |
|----------|-----------|-------|-------------|
| Free Tier | FREE | 2 | Basic routing and escalation |
| Professional | PRO | 3 | Priority assignment, basic workflows |
| Business | BUS | 5 | Response mobilizer, Slack integration |
| Digital Operations | DIGOPS | 7 | Global orchestration, intelligent routing |
| AIOps Add-on | AIOPS | 4 | Noise reduction, correlation |
| Enterprise IM | EIM | 5 | Incident tasks, roles, advanced workflows |
| Automation | AUTO | 3 | RBA automation scenarios |
| Customer Service Ops | CSO | 1 | Customer impact scenarios |
| Workflow | WF | 3 | Manual/conditional workflow triggers |
| Industry-Specific | IND | 13 | Healthcare, finance, mining, etc. |
| SRE Agent | SRE | 6 | Autonomous investigation and remediation |
| Scribe Agent | SCRIBE | 3 | Automated incident documentation |
| Shift Agent | SHIFT | 3 | On-call handoff automation |
| Automation Actions | AA | 3 | Diagnostic collection, auto-remediation |
| Runbook Automation | RBA | 4 | Interactive runbooks, self-service |
| Combined | COMBO | 1 | Full automation pipeline demo |

### 3. Documentation (`docs/`, root `.md` files)

| Document | Purpose |
|----------|---------|
| `PROJECT_OVERVIEW.md` | This file - comprehensive project description |
| `COMPREHENSIVE_DEMO_ENVIRONMENT_SPECIFICATION.md` | Full 45-scenario specification aligned to PD features |
| `DEVELOPER_GUIDE.md` | Technical guide for developers |
| `DEPLOYMENT.md` | Deployment procedures and security |
| `MANUAL_SETUP_REQUIRED.md` | Items requiring PagerDuty UI configuration |
| `SECRETS.md` | Credential reference (no actual secrets) |
| `DEMO_ENVIRONMENT_PROPOSAL.md` | Original proposal and architecture |
| `LICENSE_FILTERING.md` | Plan/add-on filtering specification |

### 4. AWS Lambda Traffic Simulation (`aws/`)

A fully cloud-based system running on AWS Free Tier ($0.00 cost verified):

| Component | Purpose |
|-----------|---------|
| `lambda-demo-controller/handler.py` | **PRIMARY** — Self-contained scenario runner (trigger → ack → actions → resolve) |
| `lambda-demo-orchestrator/handler.py` | Legacy webhook-driven handler, accessible via API Gateway |
| `lambda-metrics/handler.py` | Sends synthetic metrics to Datadog and New Relic |
| `lambda-lifecycle/handler.py` | Acknowledges, adds notes, and resolves aged incidents |
| `lambda-health-check/handler.py` | Checks integration health (PagerDuty, Datadog, Grafana, Jira) |
| `lambda-reset/handler.py` | Resets demo environment (quick or full mode) |

**Lambda Functions (all in us-east-1):**

| Function Name | Purpose | Invocation |
|---------------|---------|------------|
| **`demo-simulator-controller`** | **PRIMARY: Runs complete demo scenario** | `aws lambda invoke` (direct) |
| `demo-simulator-orchestrator-v2` | Legacy event-driven handler | API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com` |
| `demo-simulator-lifecycle` | Ack/resolve aged incidents | EventBridge (every 5 min) |
| `demo-simulator-health-check` | Check integration health | EventBridge (every 15 min) or `aws lambda invoke` |
| `demo-simulator-reset` | Reset demo environment | `aws lambda invoke` (manual) |

> **WARNING:** Lambda Function URLs on this AWS account return **403 Forbidden** due to an account-level restriction. Always use `aws lambda invoke` or the orchestrator's API Gateway URL.

**Key Features:**
- Runs entirely on AWS Free Tier (verified $0.00 cost)
- Controller runs full incident lifecycle in a single invocation (up to 15 min)
- Configurable action delays (`action_delay` parameter) for testing vs live demos
- Phased Slack conversations from `CONVERSATION_LIBRARY` (10 categories)
- Datadog integration with graceful fallback if trial expires

### 5. RBA Runner Infrastructure (`aws/`, `docs/setup/`)

A PagerDuty Runbook Automation (RBA) runner deployed on AWS EC2 for executing automation jobs:

| Component | Value |
|-----------|-------|
| EC2 Instance | `i-03ab4fd5f509a8342` (t2.micro - FREE TIER) |
| Runner Name | `aws-ec2-runner` |
| Runner ID | `c144f57c-b026-4174-88b9-d65b06a6d7cc` |
| Project | `pagerduty-demo` |
| Status | Active (polling for operations) |
| Jobs Configured | 8 |

**RBA Jobs Available:**
| Job Name | Purpose |
|----------|---------|
| Background Log Generator | Generates simulated log entries |
| Background Metric Generator | Sends background metrics |
| Demo Reset (Full) | Resets entire demo environment |
| Demo Reset (Quick) | Quick reset of active incidents |
| Incident Lifecycle Simulator | Simulates incident progression |
| Integration Health Check | Verifies all integrations |
| Scheduled Event Generator | Creates scheduled demo events |
| User Activity Simulator | Simulates user actions |

**Key Implementation Note:** The RBA runner uses a custom JAR deployment (not Docker) due to manual replica authentication requirements. See `docs/setup/RBA_RUNNER_SETUP.md` for detailed documentation on the issues encountered and workarounds discovered.

---

## Architecture

### Data Flow Overview

The demo environment supports two distinct integration flows:

**Flow 1: Full Flow (Recommended for Demos)**

This flow demonstrates realistic monitoring-to-incident patterns where external tools trigger PagerDuty:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FULL FLOW INTEGRATION PATH                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────┐
  │  Demo Dashboard │  User selects scenario, clicks "Trigger"
  │  (GitHub Pages) │
  └────────┬───────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    External Monitoring Tool                             │
  │  Dashboard sends metrics/events to: Datadog, New Relic, Grafana,       │
  │  CloudWatch, or GitHub Actions                                          │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Tool's Native Monitor/Alert                          │
  │  The external tool evaluates the metric and triggers its own alert     │
  │  (e.g., Datadog Monitor, New Relic Alert, CloudWatch Alarm)            │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │              Tool's PagerDuty Integration (Pre-configured)              │
  │  The tool sends to PagerDuty via its native integration                │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Global Event Orchestration                           │
  │  Events are enriched, categorized, and routed                          │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  [Continues to Service Orchestration → Incident → Workflows → Extensions]
```

**Flow 2: Fallback Flow (Direct PagerDuty API)**

Used when external tool credentials aren't configured or for quick demos:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FALLBACK FLOW (DIRECT API)                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────┐
  │  Demo Dashboard │  User selects scenario, clicks "Trigger"
  │  (GitHub Pages) │
  └────────┬───────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    PagerDuty Events API v2                              │
  │  Dashboard sends event directly using the Fallback Routing Key          │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Global Event Orchestration                           │
  │  • Environment routing (prod/staging/dev)                              │
  │  • Source-based categorization (monitoring/ITSM/custom)                │
  │  • Severity enhancement and priority assignment                        │
  │  • Security/compliance event detection                                 │
  │  • Time-based routing rules                                            │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Service Orchestration                                │
  │  • Service-specific routing rules                                      │
  │  • Auto-pause for transient alerts                                     │
  │  • Threshold-based priority escalation                                 │
  │  • Custom field population                                             │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         Incident Created                                │
  │  • Assigned to service and escalation policy                          │
  │  • Priority set based on orchestration rules                          │
  │  • Custom fields populated                                             │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                      Incident Workflows                                 │
  │  Triggered automatically based on conditions:                          │
  │  • P1/P2 → Major Incident Full Mobilization                           │
  │  • Security keywords → Security Incident Response                      │
  │  • Resolved status → Closeout and PIR Scheduling                      │
  │  • Manual triggers available for responders                           │
  └────────────────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Extensions (Outbound Actions)                        │
  │  • Slack: Create incident channel, post updates                       │
  │  • Jira: Create tracking ticket                                       │
  │  • Zoom: Start conference bridge                                      │
  │  • RBA: Execute diagnostic/remediation scripts                        │
  └────────────────────────────────────────────────────────────────────────┘
```

### Integration Architecture

**Inbound Integrations:**

The demo environment supports two integration flows:

**Full Flow Integrations (Native Tool -> PagerDuty):**
These integrations send real data to the monitoring tool, which then triggers PagerDuty through its native integration:

| Integration | Flow | Trigger Method |
|-------------|------|----------------|
| Datadog | Metrics Lambda -> Datadog -> Monitor -> PagerDuty | 5 monitors with 1-minute eval windows |
| New Relic | Metrics Lambda -> New Relic -> Workflow -> PagerDuty | NRQL alert conditions |
| Grafana Cloud | Dashboard -> Grafana -> Alert -> PagerDuty | Alert rules with PagerDuty contact point |
| Prometheus | Via Grafana Cloud (hosted Prometheus) | Grafana alert rules |
| CloudWatch | Custom Metrics -> Alarm -> SNS -> PagerDuty | SNS subscription to PD HTTPS endpoint |
| GitHub Actions | Workflow Dispatch -> PagerDuty API | Workflow uses PAGERDUTY_ROUTING_KEY secret |

**Fallback Integrations (Direct PagerDuty API):**
These integrations send events directly to PagerDuty when native integration is not feasible:

| Integration | Reason for Fallback |
|-------------|---------------------|
| Sentry | PagerDuty integration requires paid Sentry plan |
| Splunk | No free-tier cloud option available |
| UptimeRobot | Free tier doesn't support PagerDuty integration |

**Outbound Extensions (Actually Execute):**

These extensions are configured via OAuth and execute real actions:

| Extension | Connection Status | Actions |
|-----------|------------------|---------|
| Slack | Connected | Creates channels, posts messages |
| Jira Cloud | Connected | Creates issues in configured projects |
| Zoom | Manual setup required | Conference bridge creation |
| ServiceNow | Manual setup required | Bidirectional incident sync |

---

## Demo Scenarios

### Scenario Structure

Each scenario in `scenarios.json` contains:

```json
{
  "id": "SCENARIO-001",
  "name": "Human-readable name",
  "description": "What this scenario demonstrates",
  "severity": "critical|high|warning|info",
  "tags": {
    "industry": ["technology", "finance", ...],
    "team_type": ["sre", "platform", "devops", ...],
    "org_style": ["startup", "enterprise", ...],
    "features": ["feature_key1", "feature_key2"],
    "integration": "source_tool_name",
    "tool_type": ["integration", "extension", "chatops", "bidirectional"],
    "tool": ["datadog", "slack", ...]
  },
  "required_features": ["feature_keys_needed"],
  "features_demonstrated": ["features_shown_in_demo"],
  "target_service": "PagerDuty service name",
  "expected_priority": "P1|P2|P3|P4|P5",
  "payload": { /* Events API v2 payload */ },
  "orchestration_trace": [
    { "stage": "Stage Name", "action": "What happens" }
  ]
}
```

### Scenario Categories by Plan

**Professional Plan Scenarios (PRO-*):**
- Basic incident routing
- Priority assignment
- Simple escalation policies
- Basic workflow (single major incident template)
- Jira ticket creation

**Business Plan Scenarios (BUS-*):**
- Response Mobilizer for adding responders
- Slack incident channel creation
- Conference bridge integration
- Custom incident types
- Advanced service orchestration

**Digital Operations Scenarios (DIGOPS-*):**
- Global event orchestration rules
- Intelligent alert grouping
- Service graph dependencies
- Auto-pause for transient alerts
- Threshold-based routing
- Schedule-based routing
- Past incidents correlation

**AIOps Add-on Scenarios (AIOPS-*):**
- Noise reduction demonstration
- Event correlation across services
- ML-based alert grouping
- Anomaly detection
- Cache Variable - Event source tracking
- Cache Variable - Critical event counting
- Cache Variable - K8s pod restart storm detection
- Cache Variable - Payment failure burst detection

**Enterprise Incident Management Scenarios (EIM-*):**
- Incident tasks assignment
- Incident roles (IC, Communications, Scribe)
- Advanced workflow conditions
- Stakeholder notifications
- Full incident lifecycle automation

**Workflow-focused Scenarios (WF-*):**
- Manual workflow triggers
- Multi-step automation
- Conditional branching (EIM)

### Scenario Flow Examples

#### Flow 1: Major Production Outage (BUS-001)

**Trigger:** Critical database cluster failure

**Expected Flow:**
1. Event received via Events API (source: Datadog)
2. Global Orchestration: Marked as production, enhanced severity
3. Service Orchestration: Priority set to P1
4. Incident created on "Platform - DBRE" service
5. Workflow triggered: "Major Incident Full Mobilization"
   - Slack channel created: `#inc-dbre-<date>`
   - DBA team added as responders
   - Network team added as responders
   - Zoom conference bridge started
   - Stakeholder notification sent
6. Responders notified via configured notification rules

#### Flow 2: Security Breach Detection (EIM-003)

**Trigger:** Unauthorized access attempt detected

**Expected Flow:**
1. Event received via Events API (source: Splunk)
2. Global Orchestration: Security keyword detected, routed to SecOps
3. Priority set to P1 (security incidents always high)
4. Incident created on "SecOps" service
5. Workflow triggered: "Security Incident Response (Confidential)"
   - Security response channel created (private)
   - CISO notified immediately
   - Jira security ticket created
   - Compliance hold initiated
   - Evidence preservation workflow started
6. Incident Tasks assigned:
   - Identify affected systems
   - Contain the breach
   - Preserve forensic evidence
   - Notify legal/compliance

#### Flow 3: Noise Reduction Demo (AIOPS-001)

**Trigger:** Multiple related alerts from cascade failure

**Expected Flow:**
1. Multiple events received in rapid succession
2. Global Orchestration: All routed to same service
3. AIOps Intelligent Grouping: Alerts correlated
4. Single incident created (not multiple)
5. Subsequent alerts added to existing incident
6. **Demo Point:** Show noise reduction - 10 alerts → 1 incident

---

## Feature Coverage Matrix

### Features by PagerDuty Plan

| Feature Category | Feature | Free | Pro | Bus | DO | EIM |
|------------------|---------|------|-----|-----|-----|-----|
| **Core** | On-call Schedules | 1 | ✓ | ✓ | ✓ | ✓ |
| | Escalation Policies | 1 | ✓ | ✓ | ✓ | ✓ |
| | Basic Routing | | ✓ | ✓ | ✓ | ✓ |
| **Orchestration** | Service Orchestration | | ✓ | ✓ | ✓ | ✓ |
| | Global Orchestration | | | | ✓ | ✓ |
| | Threshold Conditions | | | | ✓ | ✓ |
| | Schedule Conditions | | | | ✓ | ✓ |
| **Workflows** | Basic Workflow | | 1 | ✓ | ✓ | ✓ |
| | Full Workflows | | | ✓ | ✓ | ✓ |
| | Advanced Conditions | | | | | ✓ |
| **Collaboration** | Slack Integration | | | ✓ | ✓ | ✓ |
| | Conference Bridge | | | ✓ | ✓ | ✓ |
| | Response Mobilizer | | | ✓ | ✓ | ✓ |
| **Incident Mgmt** | Custom Incident Types | | | ✓ | ✓ | ✓ |
| | Incident Roles | | ✓ | ✓ | | ✓ |
| | Incident Tasks | | | | | ✓ |
| **AIOps** | Intelligent Grouping | | | | +AIOps | +AIOps |
| | Event Correlation | | | | +AIOps | +AIOps |
| **Automation** | RBA Jobs | | | | +RBA | +RBA |

*Note: DO = Digital Operations, EIM = Enterprise Incident Management*

---

## Getting Started

### For Demo Execution

1. Open https://conallpd.github.io/TFTest/
2. Click Settings (gear icon) and configure:
   - PagerDuty Instance (subdomain)
   - PagerDuty API Key (for native triggers)
   - Routing Key (from Event Orchestration)
3. Select filters (plan, industry, severity)
4. Choose a scenario and click "Trigger"

### For Development

See `DEVELOPER_GUIDE.md` for:
- Local development setup
- Terraform commands
- Adding new scenarios
- Known issues and workarounds

### For Deployment

See `DEPLOYMENT.md` for:
- GitHub Pages deployment
- AWS Lambda Traffic Simulation deployment
- Integration setup scripts
- Security considerations
- Pre-commit checklist

---

## Roadmap and Progress

### Current State Summary

| Component | Implemented |
|-----------|-------------|
| Dashboard Scenarios | 70 (51 enabled, 19 disabled) |
| Terraform Services | 12 |
| Incident Workflows | 22 |
| Automation Actions | 22 |
| Service Orchestrations | 10 |
| Cache Variables | 7 (3 global, 4 service-level) |
| Business Services | 6 |
| Escalation Policies | 5 |
| Schedules | 5 |
| AWS Lambda Functions | 3 |
| Observability Integrations | 6 (Datadog, New Relic, Grafana, CloudWatch, GitHub, Prometheus) |

### Implemented ✅

**Infrastructure:**
- [x] 12 PagerDuty services with escalation policies
- [x] 5 teams with user assignments
- [x] 5 on-call schedules with rotations
- [x] 6 business services with service dependencies
- [x] Global Event Orchestration with 34+ routing rules
- [x] 10 Service Orchestrations for service-specific logic
- [x] 7 Event Orchestration Cache Variables (event source tracking, trigger counting, pattern detection)
- [x] 22 Incident Workflows (empty shells - steps added via API)
- [x] 22 Automation Actions (RBA runners and diagnostic/remediation jobs)
- [x] 9 Event Orchestration Integrations (Datadog, Prometheus, Splunk, etc.)
- [x] Custom fields and incident types
- [x] Auto-pause notifications on services

**Demo Dashboard:**
- [x] 70 pre-configured scenarios across industries
- [x] License/plan-based filtering (Free through Enterprise)
- [x] Industry filtering (technology, healthcare, finance, mining, etc.)
- [x] Dark mode UI
- [x] Credential management via localStorage
- [x] Native integration triggers with PagerDuty fallback

**Traffic Simulation (AWS Lambda):**
- [x] Metrics Lambda - sends synthetic metrics to Datadog and New Relic
- [x] Orchestrator Lambda - creates `[DEMO]` incidents on schedule
- [x] Lifecycle Lambda - acknowledges and resolves aged incidents
- [x] CloudWatch scheduled triggers
- [x] Slack notifications for incident activity

**Observability Integrations (Full Flow):**
- [x] Datadog monitors with 1-minute evaluation windows -> PagerDuty
- [x] New Relic alert conditions and workflows -> PagerDuty
- [x] Grafana Cloud alert rules with PagerDuty contact point
- [x] CloudWatch alarms -> SNS -> PagerDuty
- [x] GitHub Actions workflow -> PagerDuty API

**Extensions:**
- [x] Slack integration configured
- [x] Jira Cloud integration configured

### Remaining Work

> **Note:** For the current implementation roadmap and priorities, see [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md).
> The sections below are detailed task breakdowns that align with the master plan.

#### Background Automation (Completed via AWS Lambda)

From Spec Section 4 - "Background Automation and Data Generation":

| Item | Spec Reference | Status |
|------|----------------|--------|
| Metric Generator | 4.2 | Implemented (Lambda Metrics) |
| Log Generator | 4.3 | Implemented (Lambda Metrics sends to NR/DD) |
| Background Incident Lifecycle | 4.5 | Implemented (Lambda Lifecycle) |
| Integration Health Check | 4.6 | Implemented (Lambda Orchestrator) |
| Demo Environment State | 4.7 | Implemented (Incident lifecycle simulation) |
| Demo Reset and Cleanup | 4.9 | Implemented (Lambda Lifecycle resolves aged incidents) |

#### ~~Lambda Lifecycle Simulation Enhancements~~ COMPLETED (Feb 11-18, 2026)

> **All HIGH and MEDIUM priority items have been implemented in the `demo-simulator-controller` Lambda.** The controller (`aws/lambda-demo-controller/handler.py`) replaced `aws/lambda-lifecycle/handler.py` as the primary simulation engine.

| Task | Description | Status | Priority |
|------|-------------|--------|----------|
| **Schedule User Sync** | Schedules use only 6 valid PD+Slack users. Rebalanced Feb 18. | ✅ Done | HIGH |
| **Add Responders Action** | Controller selects 1-3 responders per scenario | ✅ Done | HIGH |
| **Responder Action Logic** | All responders perform actions; random resolver selection | ✅ Done | HIGH |
| **Status Updates** | Controller posts status updates during incident | ✅ Done | MEDIUM |
| **Automation Actions** | Controller executes notes, custom fields, status updates | ✅ Done | MEDIUM |
| **Workflow Triggers** | Managed via `incident_workflow_triggers.tf` | ✅ Done | MEDIUM |
| **Webhooks** | OBSOLETE — Controller polls PD API directly; webhook deleted Feb 17 | N/A | LOW |
| **Incident Types/Forms/Roles** | Requires AIOps/EIM add-on license | ⏳ Deferred | LOW |
| **Tasks/Custom Fields** | Controller updates custom fields per scenario | ✅ Done | LOW |
| **Slack Channel Responders** | Bot joins channel, invites observers + all responders | ✅ Done | HIGH |
| **Conversation Libraries** | `CONVERSATION_LIBRARY` in controller with scenario-specific phased messages | ✅ Done | MEDIUM |

**Implementation Notes:**
- The `aws/lambda-demo-controller/handler.py` is the PRIMARY simulation engine (not `lambda-lifecycle`)
- All users in schedules exist in both PagerDuty AND Slack (6 valid users)
- Valid users: Jim Beam, Jameson Casker, Arthur Guinness, Jose Cuervo, Jack Daniels, Ginny Tonic
- Admin token is now in use — Terraform manages schedules directly (no longer needs PagerDuty UI)

#### Phase 2: Dashboard Scenarios (Complete)

**PagerDuty Agent Scenarios (SRE, Scribe, Shift) - IMPLEMENTED:**
| Scenario ID | Name | Status |
|-------------|------|--------|
| SRE-001 | Autonomous Pod Crash Investigation | ✅ Implemented |
| SRE-002 | Autonomous Remediation with Approval | ✅ Implemented |
| SRE-003 | Database Connection Pool Remediation | ✅ Implemented |
| SRE-004 | Multi-Service Incident Correlation | ✅ Implemented |
| SRE-005 | Proactive Capacity Issue Prevention | ✅ Implemented |
| SRE-006 | Learning from Past Incidents | ✅ Implemented |
| SCRIBE-001 | Automated Incident Timeline Documentation | ✅ Implemented |
| SCRIBE-002 | Automated Post-Incident Summary Generation | ✅ Implemented |
| SCRIBE-003 | Knowledge Pattern Recognition | ✅ Implemented |
| SHIFT-001 | Automated On-Call Handoff | ✅ Implemented |
| SHIFT-002 | Schedule Coverage Gap Detection | ✅ Implemented |
| SHIFT-003 | On-Call Load Balancing and Wellness | ✅ Implemented |

**Automation Actions and RBA Scenarios - IMPLEMENTED:**
| Scenario ID | Name | Status |
|-------------|------|--------|
| AA-001 | Automated Diagnostic Collection | ✅ Implemented |
| AA-002 | Auto-Remediation with Approval Gate | ✅ Implemented |
| AA-003 | Cascading Automation for Complex Issues | ✅ Implemented |
| RBA-001 | Interactive Database Failover Runbook | ✅ Implemented |
| RBA-002 | Scheduled Maintenance Runbook | ✅ Implemented |
| RBA-003 | Self-Service Runbooks for L1 Support | ✅ Implemented |
| RBA-004 | Infrastructure Provisioning Runbook | ✅ Implemented |
| COMBO-001 | Full Incident Automation Pipeline | ✅ Implemented |

**PagerDuty Advance and Copilot Scenarios (Remaining):**
| Scenario ID | Name | Status |
|-------------|------|--------|
| ADV1 | AI-Generated Status Updates | Not Implemented |
| ADV2 | AI-Assisted Post-Incident Review | Not Implemented |
| CP1 | Conversational Incident Investigation | Not Implemented |

#### Phase 3: Enterprise Integrations (Lower Priority)

**Extension Setup Required:**
| Extension | Status | Notes |
|-----------|--------|-------|
| Zoom | Not Configured | Manual OAuth setup required |
| ServiceNow | Not Configured | Bidirectional sync scenarios E3 |
| Salesforce | Not Configured | Customer context scenario E4 |
| Google Meet | Not Configured | Alternative conference bridge |
| MS Teams | Not Configured | Alternative to Slack |

**Infrastructure (Optional - for realistic demo):**
| Component | Spec Reference | Status |
|-----------|----------------|--------|
| GCP/GKE Setup | 2.2-2.4 | Not Started |
| Prometheus Stack | 1.1 (Inbound) | Not Started |
| Nagios VM | 2.2 | Not Started |
| Elasticsearch | 1.1 (Inbound) | Not Started |

### Scenario Mapping: Dashboard vs Comprehensive Spec

The dashboard uses a different naming convention than the comprehensive spec. Current coverage:

| Dashboard Category | Dashboard IDs | Count | Coverage |
|-------------------|---------------|-------|----------|
| Free | FREE-001 to FREE-002 | 2 | Complete |
| Professional | PRO-001 to PRO-003 | 3 | Complete |
| Business | BUS-001 to BUS-005 | 5 | Complete |
| Digital Operations | DIGOPS-001 to DIGOPS-007 | 7 | Complete |
| AIOps | AIOPS-001 to AIOPS-004 | 4 | Complete |
| Enterprise | EIM-001 to EIM-005 | 5 | Complete |
| Automation | AUTO-001 to AUTO-003 | 3 | Complete |
| Customer Service Ops | CSO-001 | 1 | Complete |
| Workflow | WF-001 to WF-003 | 3 | Complete |
| Industry | IND-001 to IND-013 | 13 | Complete |
| SRE Agent | SRE-001 to SRE-006 | 6 | Complete |
| Scribe Agent | SCRIBE-001 to SCRIBE-003 | 3 | Complete |
| Shift Agent | SHIFT-001 to SHIFT-003 | 3 | Complete |
| Automation Actions | AA-001 to AA-003 | 3 | Complete |
| Runbook Automation | RBA-001 to RBA-004 | 4 | Complete |
| Combined | COMBO-001 | 1 | Complete |

**Total: 66 scenarios in dashboard**

**Remaining Gaps:**
1. Advance/Copilot scenarios (ADV1-2, CP1) - 3 scenarios not in dashboard (require API access)

**Recently Completed (February 2026):**
1. Background automation jobs - 8 RBA jobs deployed and active on `aws-ec2-runner`
2. Datadog monitors - 7 monitors configured to trigger PagerDuty via @pagerduty-demo-simulator-alerts
3. AWS Lambda traffic simulation - 4 functions deployed and scheduled
4. RBA runner - Custom JAR deployment on EC2 (t2.micro, FREE TIER)

---

## Current System Status (February 2026)

This section provides a quick reference for the current operational status of all components.

### Infrastructure Status

| Component | Status | Details |
|-----------|--------|---------|
| EC2 Instance (RBA Runner) | RUNNING | i-03ab4fd5f509a8342, t2.micro |
| Lambda Functions | DEPLOYED | 4 functions, scheduled via EventBridge |
| S3 Bucket | ACTIVE | pagerduty-demo-runner-bucket |
| AWS Cost | FREE | $0.00 (within free tier) |

### Integration Status

| Integration | Status | Last Verified |
|-------------|--------|---------------|
| Datadog Monitors | ACTIVE | 7 monitors configured |
| New Relic | ACTIVE | Alert policy and workflow configured |
| Slack | CONNECTED | Token updated February 2026 |
| Jira | CONNECTED | OAuth configured |
| RBA Jobs | ACTIVE | 8 jobs, runner polling |

### Full Flow Integration Path

The demo environment is designed to trigger incidents through external monitoring tools rather than directly through the PagerDuty API. This demonstrates realistic monitoring-to-incident flows:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FULL FLOW INTEGRATION PATH                            │
└─────────────────────────────────────────────────────────────────────────────┘

  GitHub Pages Dashboard (User clicks "Trigger")
            │
            ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Lambda sends metric spike to Datadog                 │
  │  (e.g., demo.api.response_time = 800ms, threshold is 500ms)            │
  └────────────────────────────────────────────────────────────────────────┘
            │
            ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Datadog Monitor evaluates metric                     │
  │  "API Response Time High" monitor detects breach                        │
  └────────────────────────────────────────────────────────────────────────┘
            │
            ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │              Datadog triggers @pagerduty-demo-simulator-alerts          │
  │  Native PagerDuty integration sends event                               │
  └────────────────────────────────────────────────────────────────────────┘
            │
            ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    PagerDuty Event Orchestration                        │
  │  Routes, enriches, and creates incident                                 │
  └────────────────────────────────────────────────────────────────────────┘
            │
            ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Incident Workflows Execute                           │
  │  Slack channel created, responders notified, RBA jobs triggered        │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## Contributing

1. Follow patterns in existing scenarios when adding new ones
2. Run `npm run build` in `docs/demo-scenarios/` to verify dashboard builds
3. Test scenarios against your own PagerDuty instance
4. Ensure no secrets are committed (see `CREDENTIALS_REFERENCE.md`)
5. Update relevant documentation

---

## Known Platform Limitations (Critical)

These are fundamental platform limitations discovered during development. Understanding these is essential for maintaining and extending the demo environment.

### Slack Guest User Limitation

**Problem:** Slack guest accounts CANNOT use the PagerDuty Slack app. This is a Slack platform design decision, not a PagerDuty issue.

**Impact:**
- Guest users cannot link PagerDuty to Slack
- Guest users cannot use `/pd` slash commands
- The incident lifecycle simulator cannot reliably impersonate guest users

**Solution:** Only include full Slack members (not guests) in PagerDuty schedules:
- **Valid Users:** Jim Beam, Jameson Casker, Arthur Guiness, Jose Cuervo, Jack Daniels, Ginny Tonic
- **Invalid Users:** James Murphy, Paddy Losty, Kaptin Morgan, Uisce Beatha (PagerDuty-only)

See `docs/development/DEVELOPER_GUIDE.md` section 6 for complete details.

### Terraform Workflow Step Limitation

**Problem:** PagerDuty Terraform provider cannot create workflow steps. The POST API endpoint returns 404.

**Solution:** Two-phase deployment:
1. `terraform apply` creates empty workflow shells
2. `python scripts/populate_workflow_steps.py --apply` adds steps via PUT API

### PagerDuty API Token Permissions

**Problem:** Some API tokens lack permission to modify schedules, even if they can read them.

**Symptom:** `403 Forbidden - Access Denied` on schedule PUT requests

**Solution:** Use PagerDuty UI for schedule changes, or obtain an admin API token.

---

## Support

- **Documentation:** Start with `DEVELOPER_GUIDE.md`
- **Manual Steps:** See `MANUAL_SETUP_REQUIRED.md`
- **Troubleshooting:** Check "Known Issues" in `DEVELOPER_GUIDE.md`
- **Full Specification:** See `COMPREHENSIVE_DEMO_ENVIRONMENT_SPECIFICATION.md`
- **RBA Runner Issues:** See `docs/setup/RBA_RUNNER_SETUP.md` for detailed troubleshooting
- **Credentials:** See `docs/CREDENTIALS_REFERENCE.md` for all API keys and tokens
- **Implementation Roadmap:** See `docs/IMPLEMENTATION_PLAN.md` for phases and priorities

---

## Current Status (February 6, 2026)

### Recent Changes Completed

| Change | Status | Notes |
|--------|--------|-------|
| Datadog-PagerDuty Integration Fix | COMPLETE | Now uses Event Orchestration routing key `R028NMN4RMUJEARZ18IJURLOU1VWQ779` |
| Slack Profile Updates | ✅ DEPLOYED (Feb 18) | Both Conall profiles added and deployed via `terraform apply` |
| Documentation Updates | COMPLETE | All docs updated Feb 18 |

### ~~Pending Deployment Actions~~ ALL DEPLOYED (Feb 18, 2026)

> **Terraform apply completed successfully on Feb 18, 2026:** 35 added, 18 changed, 0 destroyed. All Lambda functions and infrastructure are deployed and current.

### Known Issues (Updated Feb 18, 2026)

| Issue | Severity | Impact | Status |
|-------|----------|--------|--------|
| ~~PagerDuty REST API Token (401)~~ | ~~MEDIUM~~ | ~~Cannot query incidents via API~~ | ✅ RESOLVED (Feb 10) — Admin token in use |
| 15 Missing PagerDuty Services | LOW | Some disabled scenarios reference non-existent services | Deferred — only affects 19 disabled scenarios |
| 4 Scenario Payload Mismatches | LOW | Metadata inconsistency in PRO-001, DIGOPS-002, EIM-001, AUTO-003 | Cosmetic — does not affect demo execution |
| ~~Lambda Deployment Pending~~ | ~~HIGH~~ | ~~Slack profiles not active until deployed~~ | ✅ RESOLVED (Feb 18) — Deployed |

### Integration Status (Updated Feb 18, 2026)

| Integration | Status | Configuration |
|-------------|--------|---------------|
| Datadog → PagerDuty | WORKING | Routing key: `R028NMN4RMUJEARZ18IJURLOU1VWQ779` |
| PagerDuty → Slack | WORKING | Both Conall profiles deployed; Slack health check at controller startup |
| PagerDuty Events API | WORKING | Routing keys functional |
| PagerDuty REST API | WORKING | Admin token active (see `CREDENTIALS_REFERENCE.md`) |

### Quick Verification Commands

```bash
# Test Datadog routing key
curl -s -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{"routing_key":"R028NMN4RMUJEARZ18IJURLOU1VWQ779","event_action":"trigger","payload":{"summary":"[TEST]","severity":"warning","source":"test"}}'

# Check Lambda was updated
aws lambda get-function --function-name demo-simulator-controller --query 'Configuration.LastModified'
```

---

## Document History

| Date | Changes |
|------|---------|
| February 18, 2026 | Updated all task statuses to reflect Feb 18 deployment; marked deployment actions as complete; updated integration status (REST API now WORKING); updated Known Issues |
| February 18, 2026 | Updated Lambda Lifecycle Simulation Enhancements — all HIGH/MEDIUM items completed by controller Lambda |
| February 18, 2026 | Updated component table with Slack Health Check, Schedule Rebalancing, Incident Resolution entries |
| February 2026 | Added Known Platform Limitations section documenting Slack guest and token permission issues |
| February 2026 | Updated user documentation to reflect valid vs invalid schedule users |
| February 2026 | Added Current System Status section, Full Flow Integration Path diagram |
| February 2026 | Updated Remaining Gaps to reflect completed RBA jobs |
| February 2026 | Added RBA Runner Infrastructure section |
| February 2026 | Added notifier Lambda to AWS components |
