# Demo Scenario Flows and Demonstrations

> **Last Updated:** February 18, 2026
> **Purpose:** Document how each demo scenario type flows and what it demonstrates

---

## Overview

The PagerDuty demo environment contains **70 scenarios** organized by prefix that indicate the tier/feature being demonstrated. Current readiness: **51 enabled and E2E validated** (100% pass rate), **19 disabled** (awaiting external integrations like ServiceNow, Grafana, UptimeRobot).

The primary execution engine is the `demo-simulator-controller` Lambda, which runs a complete incident lifecycle within a single invocation (up to 15 minutes). See the [README](../README.md) for invocation details.

| Prefix | Full Name | Scenarios | Target Audience |
|--------|-----------|-----------|-----------------|
| `IND` | Industry-Specific | 6 | Vertical sales |
| `DIGOPS` | Digital Operations | 7 | DigOps pitch |
| `SRE` | Site Reliability | 6 | SRE teams |
| `BUS` | Business Tier | 5 | Business tier upsell |
| `EIM` | Enterprise Incident Mgmt | 5 | Enterprise customers |
| `AIOPS` | AIOps Features | 8 | ML/AI capabilities, Cache Variables |
| `RBA` | Runbook Automation | 4 | Automation pitch |
| `AA` | Automation Actions | 4 | Action automation |
| `AUTO` | Auto-Remediation | 4 | Self-healing systems |
| `PRO` | Professional Tier | 3 | Pro tier demos |
| `SCRIBE` | AI Scribe | 3 | Documentation AI |
| `SHIFT` | Scheduling | 3 | On-call management |
| `WF` | Workflows | 3 | Workflow automation |
| `FREE` | Free Tier | 2 | Entry-level demos |
| `COMBO` | Full Pipeline | 2 | End-to-end showcase |
| `CSO` | Status Page | 2 | Status communication |

---

## Standard Incident Flow

All `[DEMO]` incidents follow this base flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEMO INCIDENT LIFECYCLE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. TRIGGER (Events API or Datadog/monitoring tool)                     │
│       │                                                                  │
│       ▼                                                                  │
│  2. EVENT ORCHESTRATION routes to correct service                       │
│       │                                                                  │
│       ▼                                                                  │
│  3. INCIDENT CREATED with [DEMO] prefix                                 │
│       │                                                                  │
│       ▼                                                                  │
│  4. WORKFLOW TRIGGER fires (condition: title contains '[DEMO]')         │
│       │                                                                  │
│       ├──────────────────────────────────────────────────────────┐      │
│       │                                                           │      │
│       ▼                                                           ▼      │
│  5. SLACK CHANNEL created                              6. JIRA TICKET    │
│       │                                                   created        │
│       ▼                                                                  │
│  7. RESPONDERS notified via escalation policy                           │
│       │                                                                  │
│       ▼                                                                  │
│  8. ACKNOWLEDGE (manual or automated)                                   │
│       │                                                                  │
│       ▼                                                                  │
│  9. INVESTIGATION in Slack channel                                      │
│       │                                                                  │
│       ▼                                                                  │
│  10. RESOLVE incident                                                   │
│       │                                                                  │
│       ▼                                                                  │
│  11. PIR workflow triggers (optional)                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow-Specific Flows

### Standard Incident Response (PH9KQ9H)

**Demonstrates:** Basic incident management with collaboration

**Flow:**
1. Create Incident Slack Channel
2. Create Jira Ticket (DEMO project)
3. Add Standard Response Note
4. Post to Incident Channel
5. Send Standard Status

**Jira Project:** DEMO

---

### Security Incident Response (P7AFJXW)

**Demonstrates:** Security-specific handling with SOC team paging

**Flow:**
1. Create Incident Slack Channel
2. Create Jira Ticket (SECOPS project)
3. Add Security Alert Note
4. Post to Incident Channel
5. Page SOC Team
6. Send Confidential Status Update

**Jira Project:** SECOPS

**Special:** Uses confidential channel settings

---

### Payments System Outage (PON3K9J)

**Demonstrates:** Financial impact handling with cross-team coordination

**Flow:**
1. Create Incident Slack Channel
2. Create Jira Ticket (PAY project)
3. Add Payments Alert Note
4. Post to Incident Channel
5. Add Payments Responders
6. Send Payments Status

**Jira Project:** PAY

---

### Data Pipeline Alert (PIZ3OEC)

**Demonstrates:** Data engineering incident handling

**Flow:**
1. Create Data Pipeline Incident Channel
2. Create Jira Ticket (DATA project)
3. Add Data Pipeline Note

**Jira Project:** DATA

---

### Database Emergency Response (P6LTPJ8)

**Demonstrates:** Database-specific incident handling

**Flow:**
1. Create Incident Slack Channel
2. Create Jira Ticket (INFRA project)
3. Add Database Alert Note
4. Post to Incident Channel
5. Add DBA Responders
6. Send Database Status

**Jira Project:** INFRA

---

### Compliance Incident Handler (PVVCLBZ)

**Demonstrates:** Compliance/regulatory incident handling

**Flow:**
1. Create Incident Slack Channel
2. Create Jira Ticket (COMP project)
3. Add Compliance Note
4. Post to Incident Channel
5. Send Compliance Status

**Jira Project:** COMP

---

## Scenario Category Details

### Industry-Specific (IND)

| ID | Name | Integration | Service | Demonstrates |
|----|------|-------------|---------|--------------|
| IND-001 | Manufacturing Floor Alert | datadog | OT Operations | Manufacturing monitoring |
| IND-002 | Mining Safety System Alert | sentry | Safety Operations | Safety-critical systems |
| IND-003 | Retail POS System Failure | grafana | Retail Systems | Retail operations |
| IND-004 | Fintech Payment Gateway | newrelic | Payment Processing | Financial services |
| IND-005 | Energy Grid Monitoring | cloudwatch | Grid Operations | Utilities |
| IND-006 | Telecom Network Congestion | cloudwatch | Network Operations | Telecommunications |

**Status:** All 6 enabled and E2E validated

---

### Digital Operations (DIGOPS)

| ID | Name | Feature | Demonstrates |
|----|------|---------|--------------|
| DIGOPS-001 | Alert Grouping | Alert Grouping | Noise reduction |
| DIGOPS-002 | Alert Suppression | Suppression Rules | Planned maintenance |
| DIGOPS-003 | Auto-Pause | Auto-Pause | Business hours |
| DIGOPS-004 | Service Dependency | Service Graph | Impact analysis |
| DIGOPS-005 | Dynamic Routing | Event Orchestration | Intelligent routing |
| DIGOPS-006 | Urgency Override | Urgency Rules | Priority management |
| DIGOPS-007 | Change Correlation | Change Events | Change impact |

**Status:** Enabled and E2E validated. Full AIOps features (alert grouping, suppression) require AIOps/EIM add-on.

---

### Enterprise Incident Management (EIM)

| ID | Name | Feature | Demonstrates |
|----|------|---------|--------------|
| EIM-001 | Incident Tasks | Tasks | Work tracking |
| EIM-002 | Incident Roles | Roles | Role assignment |
| EIM-003 | Incident Types | Types | Categorization |
| EIM-004 | Priority Matrix | Priority | Severity/Impact |
| EIM-005 | Custom Fields | Custom Fields | Data capture |

**Status:** Enabled and E2E validated. Enterprise-specific features (types, custom fields) require Enterprise tier.

---

### AIOps Features (AIOPS)

| ID | Name | Feature | Demonstrates |
|----|------|---------|--------------|
| AIOPS-001 | Global Event Orchestration | Event Orchestration | Intelligent routing |
| AIOPS-002 | Global Alert Grouping | Alert Grouping | Noise reduction |
| AIOPS-003 | Probable Origin Analysis | AIOps | Root cause analysis |
| AIOPS-004 | Outlier Incident Detection | AIOps | Anomaly detection |
| AIOPS-005 | Cache Variable - Event Source Tracking | Cache Variables | Recent value tracking across events |
| AIOPS-006 | Cache Variable - Critical Event Counting | Cache Variables | Trigger count thresholds |
| AIOPS-007 | Cache Variable - K8s Pod Restart Storm Detection | Cache Variables | Service-level restart storm detection |
| AIOPS-008 | Cache Variable - Payment Failure Burst Detection | Cache Variables | Service-level payment failure bursts |

**Status:** AIOPS-001 through AIOPS-004 enabled and E2E validated. AIOPS-005 through AIOPS-008 added Feb 18, 2026 — cache variable infrastructure deployed via Terraform (`cache_variables.tf`), 7 cache variable resources (3 global, 4 service-level). Full AIOps features (alert grouping, suppression, probable origin) require AIOps/EIM add-on.

---

### Runbook Automation (RBA)

| ID | Name | Feature | Demonstrates |
|----|------|---------|--------------|
| RBA-001 | Interactive Runbook | RBA | Guided remediation |
| RBA-002 | Approval Gates | RBA | Change approval |
| RBA-003 | Self-Service Portal | RBA | User empowerment |
| RBA-004 | Runbook Templates | RBA | Standardization |

**Status:** Enabled and E2E validated. RBA Runner exists (`i-03ab4fd5f509a8342`), but runbook content still needs creation.

---

## Event Orchestration Rules

The Global Event Orchestration routes events to services based on `class`, `component`, and `custom_details` fields (NOT summary text):

| Condition | Target Service |
|-----------|---------------|
| `class: "database"` OR `component: "postgres/mysql/redis/mongodb/cassandra"` | Database Reliability |
| `source: "kubernetes"` OR `source: "prometheus"` | Platform K8s |
| `class: "network"` | Platform Network |
| `class: "security"` OR `custom_details.security_classification` exists | Security Monitoring |
| `custom_details.domain: "payments"` OR `class: "payment"` | Payments Ops |
| `custom_details.service: "checkout"` OR `custom_details.service: "cart"` | App Checkout |
| `custom_details.service: "order/fulfillment/inventory"` | App Orders |
| `custom_details.service: "identity/auth/sso/login"` | App Identity |
| `custom_details.service: "streaming/kafka/kinesis/pubsub"` | Data Streaming |
| `custom_details.service: "analytics/warehouse/bigquery/snowflake/redshift"` | Data Analytics |
| Default (no match) | Default Service - Unrouted Events |

**Orchestration ID:** `94e4c195-79d1-44ca-b649-548acbf08ea2`

---

## Demo Execution Guide

### Running a Single Scenario

```bash
# Via Lambda controller (recommended)
aws lambda invoke --function-name demo-simulator-controller \
  --payload '{"action": "run_scenario", "scenario_id": "IND-001", "action_delay": 2}' \
  --cli-binary-format raw-in-base64-out /dev/stdout

# Via E2E test script
python scripts/e2e_test.py --scenario IND-001
```

### Running All Enabled Scenarios

```bash
# Validate all 51 enabled scenarios
python scripts/test_all_scenarios.py

# Run E2E test suite (7 core tests)
python scripts/e2e_test.py
```

### Checking Scenario Status

```bash
python scripts/analyze_scenario_readiness.py
```

---

## Scenario Readiness Summary

| Status | Count | Notes |
|--------|-------|-------|
| Enabled & E2E Validated | 51 | 100% pass rate (Feb 18, 2026) |
| Disabled (pending external integrations) | 19 | ServiceNow, Grafana, UptimeRobot, etc. |

---

## New Action Types (February 11-14, 2026)

The controller Lambda executes these action types during the investigation phase of each scenario:

| Action Type | Handler | Integration |
|-------------|---------|-------------|
| `aiops_correlate` | Fetches past incidents, finds related incidents | PagerDuty AIOps API |
| `status_page_update` | Creates/updates status page incidents and components | PagerDuty Status Page API (rewritten Feb 14) |
| `invoke_rba` | Invokes automation actions or triggers incident workflows | PagerDuty Automation Actions API |

---

## Integration Points

### Monitoring Tools → PagerDuty

| Tool | Integration Method | Status |
|------|-------------------|--------|
| Datadog | API monitors (14) | READY (graceful fallback if trial expired — see [Gotchas](GOTCHAS_AND_WORKAROUNDS.md#datadog-trial-expiry)) |
| Prometheus | Alertmanager | READY |
| Grafana | Alert channels | Configured (scenarios disabled pending setup) |
| CloudWatch | SNS topics | READY |
| New Relic | Workflow | Configured (scenarios disabled pending setup) |
| GitHub Actions | Workflow dispatch | READY |

### PagerDuty → Collaboration

| Tool | Integration Method | Status |
|------|-------------------|--------|
| Slack | Native app + Bot (`chat:write.customize`) | READY |
| Jira | OAuth + Workflows (6 projects) | READY |
| Status Page | PagerDuty Status Page API | READY (API rewritten Feb 14 — see [Gotchas](GOTCHAS_AND_WORKAROUNDS.md#status-page-api-rewrite)) |
| ServiceNow | Native PagerDuty extension | Connected (no custom code needed) |

---

## Next Steps for Scenario Expansion

1. Enable 19 disabled scenarios as external integrations are set up
2. Configure AIOps features for DIGOPS scenarios (requires AIOps/EIM add-on)
3. Create RBA runbooks for automation scenarios (runner exists, content needed)
4. Enable AI Scribe for SCRIBE scenarios (requires AIOps license)

---

*This document should be updated as scenarios are implemented or modified.*
