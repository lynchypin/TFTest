# PagerDuty Demo Environment - Enhanced Proposal

**Version:** 2.0  
**Status:** PROPOSAL - Awaiting Review  
**Date:** January 2025

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Assessment of Current Scenarios](#2-assessment-of-current-scenarios)
3. [New Architecture: Living Demo Environment](#3-new-architecture-living-demo-environment)
4. [Incident Lifecycle Scenario Flows](#4-incident-lifecycle-scenario-flows)
5. [Background Simulation Services](#5-background-simulation-services)
6. [Fake Log Generation System](#6-fake-log-generation-system)
7. [Multi-User Simulation](#7-multi-user-simulation)
8. [Enhanced Tagging System](#8-enhanced-tagging-system)
9. [Technical Implementation Plan](#9-technical-implementation-plan)
10. [Scenario Catalog](#10-scenario-catalog)

**Supplementary Documents:**
- [License/Plan-Based Filtering](./LICENSE_FILTERING.md) - Filter scenarios by PagerDuty plan and add-ons

---

## 1. Executive Summary

### Current State Assessment

The existing demo scenarios are **useful but limited**:
- 8 isolated scenarios that demonstrate individual features
- No connection between scenarios (no lifecycle flow)
- Static - requires manual triggering each time
- No background "noise" to make it feel like a real environment
- Doesn't showcase the full power of:
  - 15 incident workflows
  - 20 RBA automation actions
  - 10 service orchestrations
  - Complex nested orchestration rules

### Proposed Enhancement

Transform the demo from **isolated scenarios** into a **living, breathing demo environment** that:

1. **Runs continuously** with background activity generating realistic "noise"
2. **Simulates full incident lifecycles** from detection to resolution
3. **Shows multiple users** interacting (responders, managers, stakeholders)
4. **Generates realistic logs** that can be queried during demos
5. **Demonstrates every major feature** we've implemented

### Key Differentiators

| Aspect | Current | Proposed |
|--------|---------|----------|
| Scenario Count | 8 | 50+ (organized into 12 lifecycle flows) |
| Activity | Manual trigger only | Continuous background + on-demand |
| Realism | Single event | Multi-event with user interactions |
| Log Data | None | Constantly generated fake logs |
| User Simulation | None | 15+ simulated users/personas |
| Feature Coverage | ~30% | ~95% of implemented features |

### Implementation Status

**Demo Scenarios Dashboard:** IMPLEMENTED
- Live at: https://conallpd.github.io/TFTest/
- 50+ scenarios across multiple industries
- Filter by integration, severity, team type, industry
- Native external tool integrations (Sentry, Datadog, New Relic, etc.)
- Dark mode, credential management via localStorage

---

## 2. Assessment of Current Scenarios

### Scenarios to KEEP (with modifications)

| ID | Name | Assessment | Modifications Needed |
|----|------|------------|---------------------|
| `banking-soc-breach-001` | Unauthorized Database Access | **KEEP** - Good security scenario | Expand into full lifecycle flow |
| `retail-payments-timeout-001` | Stripe Payment Gateway Timeout | **KEEP** - Realistic payment scenario | Add workflow trigger, RBA actions |
| `tech-platform-k8s-node-001` | Kubernetes Node NotReady | **KEEP** - Core platform scenario | Expand with diagnostics, remediation |
| `mining-ot-scada-001` | Conveyor Belt Temperature | **KEEP** - Unique OT/industrial | Add safety workflow |
| `support-escalation-001` | Enterprise Customer Escalation | **KEEP** - Customer impact scenario | Add SLA tracking, comms workflow |

### Scenarios to UPDATE

| ID | Name | Issues | Updates Needed |
|----|------|--------|----------------|
| `demo-suppression-flapping-001` | Flapping Alert | Too simple | Make part of "noise reduction demo flow" |
| `demo-maintenance-suppression-001` | Maintenance Window | Isolated | Integrate into maintenance window lifecycle |
| `demo-nonprod-suspend-001` | Non-prod Suspend | Minimal value alone | Part of environment-based routing demo |

### Scenarios to DELETE

| ID | Name | Reason |
|----|------|--------|
| N/A | None currently | All existing scenarios have value, just need expansion |

### Gap Analysis

**Missing scenario coverage for:**
- Database incidents (we have DBRE orchestration, no scenarios)
- Identity/authentication failures (we have identity_crisis workflow)
- Data pipeline incidents (we have streaming orchestration)
- Analytics/BI incidents
- Multi-team collaboration
- Major incident coordination
- Post-incident review flow
- Compliance-driven responses
- On-call rotation scenarios

---

## 3. New Architecture: Living Demo Environment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEMO ENVIRONMENT ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKGROUND SERVICES (Always Running)                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │
│  │   Log Generator  │  │  Noise Generator │  │  Metric Simulator │              │
│  │  (Fake app logs) │  │  (Low-sev alerts)│  │  (Fake dashboards)│              │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘               │
│           │                     │                     │                          │
│  ┌────────▼─────────────────────▼─────────────────────▼─────────┐               │
│  │                     Log Aggregator (Loki/Files)               │               │
│  │     • Application logs    • System events    • Audit trails   │               │
│  └──────────────────────────────────────────────────────────────┘               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INCIDENT LIFECYCLE SIMULATOR                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │   TRIGGER   │───▶│   TRIAGE    │───▶│  RESPONSE   │───▶│ RESOLUTION  │       │
│  │   Events    │    │   Phase     │    │   Phase     │    │   Phase     │       │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘       │
│        │                  │                  │                  │                │
│        ▼                  ▼                  ▼                  ▼                │
│  • Alert fired      • Workflow       • RBA jobs run    • Resolution event       │
│  • Orchestration      triggers       • Slack updates   • PIR created            │
│  • Routing          • Users join     • Diagnostics     • Metrics updated        │
│                     • Comms sent     • Remediation                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER ACTIVITY SIMULATOR                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Responder  │  │   Manager   │  │  Stakeholder│  │  Customer   │            │
│  │  Actions    │  │  Actions    │  │  Actions    │  │  Actions    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                  │
│  • Acknowledge     • Join calls    • View status   • Report issue              │
│  • Run diagnostics • Escalate      • Request       • Check status              │
│  • Add notes       • Update status   updates       • Provide info              │
│  • Trigger RBA     • Notify exec   • Ask questions                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PAGERDUTY INTEGRATION                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        Global Orchestration (5 sets, 20+ rules)           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│  ┌───────────────────────────────────▼───────────────────────────────────────┐  │
│  │                        Event Router (13 routing rules)                    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┐  │
│  │  K8s     │  DBRE    │  Net     │ Security │ Payments │  Orders  │  ...   │  │
│  │  Orch    │  Orch    │  Orch    │  Orch    │  Orch    │  Orch    │        │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────┘  │
│                                      │                                          │
│  ┌───────────────────────────────────▼───────────────────────────────────────┐  │
│  │              15 Incident Workflows + 20 RBA Automation Actions            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose | Runs |
|-----------|---------|------|
| Log Generator | Creates realistic application/system logs | Continuously |
| Noise Generator | Low-severity alerts that get suppressed/suspended | Every 1-5 min |
| Metric Simulator | Fake metrics for dashboards | Continuously |
| Lifecycle Simulator | Orchestrates multi-phase incident scenarios | On-demand + scheduled |
| User Simulator | Simulates user actions (ack, notes, escalate) | Event-driven |

---

## 4. Incident Lifecycle Scenario Flows

### 4.1 Flow Structure

Each incident lifecycle flow consists of **6 phases**, each generating specific events and user actions:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          INCIDENT LIFECYCLE PHASES                               │
└─────────────────────────────────────────────────────────────────────────────────┘

PHASE 1: PRE-INCIDENT (Background Activity)
├── Normal log patterns
├── Healthy metric values
└── Occasional low-severity alerts (suppressed)

PHASE 2: DETECTION (T+0)
├── Monitoring detects anomaly
├── Event sent to PagerDuty
├── Global orchestration processes event
├── Event routed to appropriate service
└── Service orchestration applies rules

PHASE 3: TRIAGE (T+1 to T+5 minutes)
├── Incident created
├── Workflow triggered (based on priority/type)
├── On-call responder paged
├── Responder acknowledges
├── Initial diagnostics run (RBA)
└── Additional responders added if needed

PHASE 4: RESPONSE (T+5 to T+30 minutes)
├── Responders investigate
├── RBA jobs executed (diagnostics, remediation)
├── Stakeholder notifications sent
├── Status page updated (if customer-impacting)
├── Bridge call initiated (if major)
├── Additional teams engaged if needed
└── Notes added throughout

PHASE 5: RESOLUTION (T+30 to T+60 minutes)
├── Root cause identified
├── Fix implemented (or workaround)
├── Verification performed
├── Resolution event sent
├── Incident resolved
└── Status page updated

PHASE 6: POST-INCIDENT (T+60+)
├── PIR/Postmortem ticket created
├── Stakeholder summary sent
├── Metrics updated
└── Lessons learned documented
```

### 4.2 Proposed Lifecycle Flows (12 Total)

#### FLOW 1: Platform Infrastructure Crisis (P1)
**Showcases:** Major incident workflow, multi-team collaboration, all phases

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -10m | Normal K8s logs, healthy metrics | None | Background activity |
| Detection | T+0 | `KubeNodeNotReady` alert, 3 nodes fail | None | Global orchestration, routing |
| Triage | T+2m | Incident created P1, workflow fires | SRE-Alice acknowledges | `p1_critical_response` workflow |
| | T+3m | Slack channel created, bridge started | SRE-Bob joins, Manager-Carol joins | Workflow: create channel |
| | T+4m | Diagnostics auto-triggered | System runs `diagnostics_k8s_node_status` | RBA integration |
| Response | T+8m | Results show disk pressure | SRE-Alice adds note | RBA output handling |
| | T+12m | Node drain initiated | System runs `remediation_drain_node` | Remediation RBA |
| | T+15m | New nodes provisioned | SRE-Bob adds note | Manual action + note |
| | T+20m | Status page updated | Workflow: update status | `platform_infrastructure` workflow |
| Resolution | T+35m | All pods healthy | SRE-Alice resolves | Resolution handling |
| Post-incident | T+40m | PIR Jira created, summary sent | Workflow: create PIR | `incident_closeout` workflow |

**Events Generated:** 15+
**User Actions Simulated:** 20+
**Features Shown:** Global orchestration, service orchestration, P1 workflow, RBA diagnostics, RBA remediation, multi-user response, status page, PIR creation

---

#### FLOW 2: Security Breach Response (P1 - Security Type)
**Showcases:** Security workflows, confidential handling, compliance actions

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -5m | Normal auth logs | None | Background logs |
| Detection | T+0 | SIEM alert: bulk data export detected | None | Security routing, P1 auto-assign |
| Triage | T+1m | Incident created, marked Security type | SOC-Dan acknowledges | `security_incident_response` workflow |
| | T+2m | Private Slack channel created | SOC-Eve joins | Confidential channel |
| | T+3m | Audit log export triggered | System runs `security_audit_log_export` | Security RBA |
| Response | T+5m | Source IP identified | SOC-Dan adds note | Investigation |
| | T+8m | Host isolation triggered | System runs `security_isolate_host` | Security remediation RBA |
| | T+12m | Legal notification sent | Workflow: notify legal | Legal compliance |
| | T+15m | Data retention hold applied | System runs `security_data_retention_hold` | Data preservation |
| Resolution | T+45m | Breach contained | SOC-Dan resolves | Secure resolution |
| Post-incident | T+50m | Compliance Jira created | Workflow: create compliance ticket | `data_breach_response` workflow |

**Events Generated:** 12+
**User Actions Simulated:** 15+
**Features Shown:** Security orchestration, security workflows, security RBA jobs, confidential handling, compliance integration

---

#### FLOW 3: Database Emergency (P1)
**Showcases:** Database workflows, failover automation, DBRE team response

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -15m | Normal DB logs, healthy replication | None | Background DB logs |
| Detection | T+0 | Replication lag > 30s detected | None | DB routing, `svc_dbre` orchestration |
| | T+1m | Primary DB connection failures spike | None | Correlated alerts |
| Triage | T+2m | P1 incident created | DBA-Frank acknowledges | `database_emergency` workflow |
| | T+3m | Database diagnostics auto-run | System runs `diagnostics_database_status` | DB diagnostics RBA |
| | T+4m | DBRE team engaged | DBA-Grace joins | Team engagement |
| Response | T+8m | Primary confirmed degraded | DBA-Frank adds note with analysis | Investigation notes |
| | T+10m | Failover assessment triggered | System runs `remediation_database_failover` | DB failover RBA |
| | T+15m | Replica promoted to primary | System confirms promotion | Automated remediation |
| | T+18m | Connection strings updated | DBA-Grace adds note | Configuration change |
| | T+22m | Application reconnection verified | System health check | Verification |
| Resolution | T+30m | Database stable on new primary | DBA-Frank resolves | Resolution |
| Post-incident | T+35m | PIR created, capacity review scheduled | Workflow: PIR + followup | Post-incident tasks |

**Events Generated:** 18+
**User Actions Simulated:** 12+
**Features Shown:** DBRE orchestration, database workflow, database diagnostics, database failover, team collaboration

---

#### FLOW 4: Payment System Outage (P1 - Critical Business Impact)
**Showcases:** Payment workflows, business impact handling, customer communication

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -5m | Normal payment logs | None | Background payment logs |
| Detection | T+0 | Payment gateway timeout rate spikes to 40% | None | Payments routing |
| Triage | T+1m | P1 incident created | Payments-Henry acknowledges | `payments_outage` workflow |
| | T+2m | Finance team notified | Workflow: notify finance | Business impact notification |
| | T+3m | Revenue impact calculated: $15K/min | Workflow: calculate impact | Business context |
| Response | T+5m | Vendor status checked | System checks Stripe status | External dependency check |
| | T+8m | Circuit breaker triggered | System runs `remediation_circuit_breaker_reset` | Circuit breaker RBA |
| | T+12m | Fallback payment provider activated | Payments-Henry adds note | Failover action |
| | T+15m | Customer status page updated | Workflow: update status | Status page integration |
| | T+20m | Success rate recovering | Metrics normalize | Recovery tracking |
| Resolution | T+35m | Payment success rate at 99.5% | Payments-Henry resolves | Resolution |
| Post-incident | T+40m | Financial reconciliation initiated | Workflow: create reconciliation task | Business process integration |

**Events Generated:** 14+
**User Actions Simulated:** 10+
**Features Shown:** Payments orchestration, payments workflow, finance notification, revenue impact tracking, status page, business process integration

---

#### FLOW 5: Customer-Impacting Service Degradation (P2)
**Showcases:** Customer impact workflow, SLA tracking, customer communication

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -10m | Normal API response times | None | Background API logs |
| Detection | T+0 | Checkout API p99 latency > 5s | None | App routing, `svc_checkout_orch` |
| Triage | T+2m | P2 incident created | App-Ivan acknowledges | `customer_impacting` workflow |
| | T+3m | SLA timer started | Workflow: start SLA tracking | SLA tracking |
| | T+4m | Affected customer list generated | System identifies impacted customers | Customer impact analysis |
| Response | T+6m | Root cause: database connection pool | App-Ivan adds note | Investigation |
| | T+10m | Customer communication prepared | Workflow: prepare comms | Communication workflow |
| | T+12m | Connection pool size increased | System runs `remediation_restart_service` | Service restart RBA |
| | T+15m | Latency recovering | Metrics improving | Recovery monitoring |
| | T+18m | Customer communication sent | Support-Janet sends update | Customer notification |
| Resolution | T+25m | Latency normal, SLA met | App-Ivan resolves | SLA resolution |
| Post-incident | T+30m | Customer follow-up scheduled | Workflow: schedule followup | Customer success integration |

**Events Generated:** 12+
**User Actions Simulated:** 10+
**Features Shown:** Customer impact workflow, SLA tracking, customer communication, checkout orchestration

---

#### FLOW 6: Authentication/Identity Crisis (P1)
**Showcases:** Identity workflows, session management, wide impact handling

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -5m | Normal auth logs | None | Background auth logs |
| Detection | T+0 | Login failure rate spikes to 85% | None | Identity routing, `svc_identity_orch` |
| | T+1m | SSO provider errors detected | Correlated event | Correlation |
| Triage | T+2m | P1 incident created | Identity-Karen acknowledges | `identity_crisis` workflow |
| | T+3m | Identity team engaged | Identity-Leo joins | Team engagement |
| | T+4m | All-hands alert sent | Workflow: notify all teams | Wide impact notification |
| Response | T+6m | SSO provider investigation | Identity-Karen adds note | Investigation |
| | T+10m | Session validation errors found | System diagnostics | Root cause |
| | T+15m | Cache clear initiated | System runs `remediation_clear_cache` | Cache clear RBA |
| | T+18m | Session keys rotated | Manual action by Identity-Leo | Key rotation |
| | T+22m | Auth success rate recovering | Metrics improving | Recovery tracking |
| Resolution | T+30m | Auth fully restored | Identity-Karen resolves | Resolution |
| Post-incident | T+35m | Security review scheduled | Workflow: schedule review | Security followup |

**Events Generated:** 14+
**User Actions Simulated:** 12+
**Features Shown:** Identity orchestration, identity workflow, cache clearing, wide-impact handling

---

#### FLOW 7: Data Pipeline Failure (P2)
**Showcases:** Data/streaming workflows, pipeline diagnostics, data quality

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -20m | Normal pipeline throughput | None | Background pipeline logs |
| Detection | T+0 | Kafka consumer lag > 10M messages | None | Streaming routing, `svc_streaming_orch` |
| Triage | T+3m | P2 incident created | Data-Mike acknowledges | `data_pipeline_alert` workflow |
| | T+4m | Data engineering engaged | Data-Nancy joins | Team engagement |
| | T+5m | Pipeline diagnostics triggered | System runs `diagnostics_pipeline_health` | Pipeline diagnostics RBA |
| Response | T+10m | Consumer group identified as stuck | Data-Mike adds note | Investigation |
| | T+15m | Data quality check run | System runs `diagnostics_data_quality_check` | Data quality RBA |
| | T+20m | Consumer offsets reset | Manual action by Data-Nancy | Offset reset |
| | T+25m | Pipeline throughput recovering | Metrics improving | Recovery tracking |
| | T+30m | Data backfill initiated | Manual action | Backfill process |
| Resolution | T+45m | Pipeline caught up, data complete | Data-Mike resolves | Resolution |
| Post-incident | T+50m | Pipeline optimization ticket created | Workflow: create followup | Process improvement |

**Events Generated:** 10+
**User Actions Simulated:** 10+
**Features Shown:** Streaming orchestration, data pipeline workflow, pipeline diagnostics, data quality checks

---

#### FLOW 8: Maintenance Window Incident (P3)
**Showcases:** Maintenance handling, appropriate suppression, planned work

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Pre-incident | -1h | Maintenance window scheduled | Ops-Oscar sets maintenance flag | Maintenance scheduling |
| | -30m | Pre-maintenance checklist | Ops-Oscar runs health checks | Pre-maintenance process |
| Detection | T+0 | Multiple info/warning alerts during maintenance | None | Alerts fire during window |
| Triage | T+2m | Alerts suppressed due to maintenance=true | None | `maintenance_window` workflow, suppression rules |
| | T+5m | Unexpected critical alert | Ops-Oscar acknowledges | Critical bypass suppression |
| Response | T+8m | Critical issue investigated | Ops-Oscar adds note | Investigation during maintenance |
| | T+15m | Issue resolved, maintenance continues | Ops-Oscar resolves critical | Continue maintenance |
| | T+45m | Maintenance complete | Ops-Oscar clears maintenance flag | Maintenance end |
| Resolution | T+50m | All services healthy | Health checks pass | Post-maintenance verification |
| Post-incident | T+55m | Maintenance report generated | Workflow: generate report | Maintenance documentation |

**Events Generated:** 20+ (mostly suppressed)
**User Actions Simulated:** 8+
**Features Shown:** Maintenance suppression, critical alert bypass, maintenance workflow, noise reduction

---

#### FLOW 9: Escalation Timeout Handling (P2 → P1)
**Showcases:** Escalation workflows, timeout handling, manager engagement

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Detection | T+0 | API error rate > 10% | None | Standard routing |
| Triage | T+2m | P2 incident created | None (responder unavailable) | Incident created, no ack |
| | T+10m | No acknowledgment, escalation timer fires | None | Escalation timeout |
| Response | T+11m | Escalation workflow triggered | System notifies next level | `escalation_timeout` workflow |
| | T+12m | Manager-Patricia notified | Manager-Patricia acknowledges | Manager engagement |
| | T+13m | Priority upgraded to P1 | Workflow: upgrade priority | Priority escalation |
| | T+15m | Additional responders paged | App-Quinn, App-Rachel join | Team expansion |
| | T+20m | Root cause found: deployment regression | App-Quinn adds note | Investigation |
| | T+25m | Rollback initiated | System runs `remediation_rollback_deployment` | Rollback RBA |
| Resolution | T+35m | Error rate normalized | App-Quinn resolves | Resolution |
| Post-incident | T+40m | Escalation review scheduled | Workflow: schedule review | Process improvement |

**Events Generated:** 12+
**User Actions Simulated:** 10+
**Features Shown:** Escalation timeout, priority escalation, manager notification, rollback RBA

---

#### FLOW 10: Manual Diagnostic Workflow (On-Demand)
**Showcases:** Manual workflow triggers, comprehensive diagnostics

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Detection | T+0 | User-reported slowness (no alert) | Support-Sarah creates incident manually | Manual incident creation |
| Triage | T+1m | Incident created, type unclear | SRE-Tom acknowledges | Manual triage |
| Response | T+3m | Manual diagnostic workflow triggered | SRE-Tom triggers `manual_diagnostics` workflow | Manual workflow trigger |
| | T+4m | Comprehensive diagnostics run | System runs multiple RBA jobs | `diagnostics_health_check`, `diagnostics_k8s_pod_status`, `diagnostics_network_connectivity` |
| | T+10m | Results compiled | Workflow: compile results | Result aggregation |
| | T+12m | Issue identified: memory leak | SRE-Tom adds note | Analysis |
| | T+18m | Service restart with increased memory | System runs `remediation_restart_service` | Remediation |
| Resolution | T+25m | Performance normalized | SRE-Tom resolves | Resolution |
| Post-incident | T+30m | Memory leak ticket created | Manual Jira creation | Follow-up task |

**Events Generated:** 8+
**User Actions Simulated:** 8+
**Features Shown:** Manual workflow triggers, comprehensive diagnostics, multiple RBA jobs

---

#### FLOW 11: Customer Communication Workflow (On-Demand)
**Showcases:** Manual customer comms workflow, stakeholder management

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Context | T+0 | Existing P1 incident in progress | Multiple responders working | Ongoing incident |
| Trigger | T+5m | Customer asks for update | Support-Uma requests comms | Communication request |
| Response | T+6m | Manual comms workflow triggered | Manager-Victor triggers `manual_customer_comms` workflow | Manual workflow trigger |
| | T+7m | Draft communication prepared | Workflow: prepare draft | Communication template |
| | T+8m | Draft reviewed and edited | Manager-Victor edits draft | Human review |
| | T+10m | Communication approved | Manager-Victor approves | Approval flow |
| | T+11m | Customer notified via email/Slack | Workflow: send notification | Multi-channel notification |
| | T+12m | Status page updated | Workflow: update status page | Status page integration |
| Completion | T+15m | Communication logged | Workflow: log to incident | Audit trail |

**Events Generated:** 6+
**User Actions Simulated:** 6+
**Features Shown:** Manual comms workflow, approval flow, multi-channel notification, status page

---

#### FLOW 12: Multi-Environment Alert Storm (Noise Reduction Demo)
**Showcases:** Noise reduction, environment handling, suppression/suspension

| Phase | Time | Events | User Actions | Features Demonstrated |
|-------|------|--------|--------------|----------------------|
| Detection | T+0 | Dev environment: 50 error alerts | None | Dev env detection |
| | T+0 | Staging environment: 30 warning alerts | None | Staging env detection |
| | T+0 | Production: 5 critical alerts | None | Prod critical alerts |
| Triage | T+1m | Dev alerts: suspended 300s | None | Non-prod suspension |
| | T+1m | Staging alerts: suspended 300s | None | Non-prod suspension |
| | T+1m | Production alerts: routed, P1 created | SRE-Wendy acknowledges | Prod prioritization |
| | T+2m | Only 5 production alerts create incidents | None | Noise reduction result |
| Response | T+5m | Production issue investigated | SRE-Wendy adds note | Focus on production |
| | T+15m | Production fix deployed | System runs remediation | Production fix |
| | T+20m | Fix propagated to staging/dev | Deployment pipeline | Environment cascade |
| Resolution | T+25m | Production resolved | SRE-Wendy resolves | Production resolution |
| | T+30m | Staging/dev alerts auto-resolve | System cleanup | Environment cleanup |

**Events Generated:** 85+ (mostly suppressed/suspended)
**User Actions Simulated:** 5+
**Features Shown:** Noise reduction, environment-based suppression, production prioritization, alert storm handling

---

## 5. Background Simulation Services

### 5.1 Continuous Log Generator

**Purpose:** Generate realistic application logs constantly so demos have "real" data to query

**Log Types Generated:**

| Log Type | Format | Frequency | Example |
|----------|--------|-----------|---------|
| Application logs | JSON | 10-50/sec | `{"timestamp":"...","level":"INFO","service":"checkout-api","message":"Order processed","order_id":"ORD-123456","duration_ms":145}` |
| Access logs | CLF | 20-100/sec | `10.0.1.50 - user123 [10/Jan/2025:14:30:45 +0000] "POST /api/orders" 201 1234 0.145` |
| Error logs | JSON | 1-5/sec | `{"timestamp":"...","level":"ERROR","service":"payment-processor","error":"Connection timeout","vendor":"stripe"}` |
| Audit logs | JSON | 1-2/sec | `{"timestamp":"...","actor":"admin@company.com","action":"user.role.update","target":"user456","ip":"10.0.2.100"}` |
| K8s events | JSON | 5-10/sec | `{"timestamp":"...","namespace":"production","kind":"Pod","name":"checkout-api-abc123","type":"Normal","reason":"Scheduled"}` |
| Database logs | Text | 2-5/sec | `2025-01-10 14:30:45.123 UTC [12345] LOG: statement: SELECT * FROM orders WHERE id = $1` |

**Log Patterns:**

```
NORMAL PATTERN (95% of time):
├── High success rates (99%+)
├── Low latencies (p99 < 200ms)
├── Normal error rates (<0.1%)
└── Standard throughput

PRE-INCIDENT PATTERN (5 minutes before incident):
├── Gradual latency increase
├── Slight error rate uptick
├── Warning-level logs appear
└── Resource utilization climbing

INCIDENT PATTERN (during incident):
├── Error rate spikes
├── Latency p99 > thresholds
├── Error logs dominate
├── Timeout messages
└── Retry attempts visible

RECOVERY PATTERN (after resolution):
├── Gradual return to normal
├── Success rate climbing
├── Latency decreasing
└── "Recovered" messages
```

### 5.2 Noise Generator Service

**Purpose:** Generate low-severity alerts that showcase suppression/suspension

**Alert Types:**

| Alert Type | Severity | Frequency | Outcome |
|------------|----------|-----------|---------|
| Heartbeat/keepalive | info | Every 60s | Dropped by global orchestration |
| Network interface flapping | warning | Every 5-10min | Suppressed by flapping rule |
| Dev environment errors | error | Every 2-5min | Suspended 300s by env rule |
| Staging warnings | warning | Every 3-7min | Suspended 300s by env rule |
| Info-level metrics | info | Every 30s | Suspended 120s by severity rule |
| Known false positive | warning | Every 15-30min | Suppressed by custom rule |

**Expected Behavior:**
- 90% of noise alerts should be suppressed/suspended
- Only ~10% should create actual incidents
- Demonstrates noise reduction capabilities

### 5.3 Metric Simulator

**Purpose:** Generate fake metrics for dashboard demonstrations

**Metrics Generated:**

```
Service Health Metrics:
├── checkout_api_requests_total (counter)
├── checkout_api_latency_seconds (histogram)
├── checkout_api_errors_total (counter)
├── payment_success_rate (gauge)
├── order_throughput_per_minute (gauge)

Infrastructure Metrics:
├── k8s_pod_status{} (gauge)
├── k8s_node_cpu_usage (gauge)
├── k8s_node_memory_usage (gauge)
├── db_replication_lag_seconds (gauge)
├── db_connections_active (gauge)

Business Metrics:
├── orders_processed_total (counter)
├── revenue_per_minute (gauge)
├── cart_abandonment_rate (gauge)
├── customer_satisfaction_score (gauge)
```

**Dashboard Simulation:**
- Metrics feed into Grafana/dashboard displays
- Show normal patterns most of the time
- During incidents: metrics visibly degrade
- During recovery: metrics visibly improve

---

## 6. Fake Log Generation System

### 6.1 Log File Structure

```
logs/
├── applications/
│   ├── checkout-api/
│   │   ├── app.log           # Rolling application logs
│   │   ├── access.log        # Access logs (CLF format)
│   │   └── error.log         # Error logs only
│   ├── payment-processor/
│   │   ├── app.log
│   │   ├── transactions.log  # Transaction audit trail
│   │   └── vendor-calls.log  # External API calls
│   ├── identity-service/
│   │   ├── app.log
│   │   ├── auth.log          # Authentication events
│   │   └── audit.log         # Security audit trail
│   └── [other services...]
├── infrastructure/
│   ├── kubernetes/
│   │   ├── events.log        # K8s events
│   │   ├── scheduler.log     # Scheduling decisions
│   │   └── kubelet.log       # Node agent logs
│   ├── database/
│   │   ├── postgres.log      # PostgreSQL logs
│   │   ├── slow-queries.log  # Slow query log
│   │   └── replication.log   # Replication status
│   └── network/
│       ├── dns.log           # DNS resolution logs
│       ├── loadbalancer.log  # LB health checks
│       └── firewall.log      # Firewall events
├── security/
│   ├── auth-attempts.log     # All auth attempts
│   ├── privileged-actions.log # Privileged operations
│   └── anomalies.log         # Security anomaly detection
└── incidents/
    ├── incident-{id}/
    │   ├── timeline.log      # Incident timeline
    │   ├── diagnostics.log   # RBA diagnostic output
    │   └── remediation.log   # RBA remediation output
```

### 6.2 Log Correlation System

**Purpose:** Link logs to incidents for realistic querying

**Correlation Fields:**
- `trace_id` - Distributed tracing ID
- `incident_id` - PagerDuty incident ID (when relevant)
- `request_id` - Individual request tracking
- `session_id` - User session
- `deployment_id` - Deployment version

**Example Correlated Log Query:**
```
# During demo: "Let's see what was happening when this incident started"
# Query logs by incident_id or time range

logs/ $ grep "incident_id=INC-2025010112345" applications/*/app.log

# Shows:
# checkout-api/app.log: 2025-01-10T14:30:45Z ERROR incident_id=INC-2025010112345 Payment timeout
# payment-processor/app.log: 2025-01-10T14:30:44Z ERROR incident_id=INC-2025010112345 Stripe connection failed
# checkout-api/app.log: 2025-01-10T14:30:46Z WARN incident_id=INC-2025010112345 Retry attempt 1/3
```

### 6.3 Log Injection During Incidents

When an incident scenario runs, the log generator:

1. **Pre-incident (T-5m to T-0):**
   - Gradually increases warning logs
   - Introduces latency spikes in access logs
   - Adds resource utilization warnings

2. **During incident (T+0 to resolution):**
   - Floods with error logs related to incident
   - Correlates all logs with incident_id
   - Shows retry attempts, timeouts, failures
   - Includes diagnostic output from RBA jobs

3. **Post-resolution:**
   - Shows recovery messages
   - "Connection restored" / "Service healthy" logs
   - Gradually returns to normal pattern

---

## 7. Multi-User Simulation

> **IMPLEMENTATION NOTE: User Account Configuration**
>
> All demo personas are mapped to **actual Losandes Microsoft users** in PagerDuty.
> The simulation scripts will use these real accounts for authentication and actions.

### 7.1 Actual PagerDuty Users (Losandes Microsoft)

The following **10 actual users** exist in PagerDuty:

| PagerDuty User | Email | Display Name |
|----------------|-------|--------------|
| Jim Beam | `jbeam@losandesgaa.onmicrosoft.com` | Jim Beam |
| Jameson Casker | `jcasker@losandesgaa.onmicrosoft.com` | Jameson Casker |
| Arthur Guiness | `aguiness@losandesgaa.onmicrosoft.com` | Arthur Guiness |
| Jose Cuervo | `jcuervo@losandesgaa.onmicrosoft.com` | Jose Cuervo |
| James Murphy | `jmurphy@losandesgaa.onmicrosoft.com` | James Murphy |
| Paddy Losty | `plosty@losandesgaa.onmicrosoft.com` | Paddy Losty |
| Kaptin Morgan | `kmorgan@losandesgaa.onmicrosoft.com` | Kaptin Morgan |
| Uisce Beatha | `ubeatha@losandesgaa.onmicrosoft.com` | Uisce Beatha |
| Jack Daniels | `jdaniels@losandesgaa.onmicrosoft.com` | Jack Daniels |
| Ginny Tonic | `gtonic@losandesgaa.onmicrosoft.com` | Ginny Tonic |

### 7.2 Persona-to-User Mapping

Each demo persona maps to an actual Losandes user. The simulation scripts include the persona name in notes/actions:

| Persona | Actual User | Role | Team | Typical Actions |
|---------|-------------|------|------|-----------------|
| SRE-Alice | jbeam@losandesgaa.onmicrosoft.com | Sr. SRE | Platform | Ack, diagnose, remediate, resolve |
| SRE-Bob | jcasker@losandesgaa.onmicrosoft.com | SRE | Platform | Join incident, assist, add notes |
| SRE-Tom | aguiness@losandesgaa.onmicrosoft.com | SRE | Platform | Manual diagnostics, analysis |
| SRE-Wendy | jcuervo@losandesgaa.onmicrosoft.com | SRE | Platform | Multi-env handling |
| DBA-Frank | jmurphy@losandesgaa.onmicrosoft.com | Sr. DBA | DBRE | DB incidents, failover decisions |
| DBA-Grace | plosty@losandesgaa.onmicrosoft.com | DBA | DBRE | DB support, config changes |
| SOC-Dan | kmorgan@losandesgaa.onmicrosoft.com | Sr. Security Analyst | SecOps | Security incidents, investigation |
| SOC-Eve | ubeatha@losandesgaa.onmicrosoft.com | Security Analyst | SecOps | Security support, audit |
| App-Ivan | jdaniels@losandesgaa.onmicrosoft.com | Sr. Developer | App - Checkout | App incidents, code analysis |
| App-Quinn | gtonic@losandesgaa.onmicrosoft.com | Developer | App - Orders | App support, debugging |
| App-Rachel | jcuervo@losandesgaa.onmicrosoft.com | Developer | App - Identity | Identity issues |
| Payments-Henry | jbeam@losandesgaa.onmicrosoft.com | Payments Lead | Payments Ops | Payment incidents |
| Data-Mike | jcasker@losandesgaa.onmicrosoft.com | Data Engineer | Data | Pipeline incidents |
| Data-Nancy | aguiness@losandesgaa.onmicrosoft.com | Sr. Data Engineer | Data | Pipeline support |
| Manager-Carol | jmurphy@losandesgaa.onmicrosoft.com | Engineering Manager | Platform | Escalations, coordination |
| Manager-Patricia | plosty@losandesgaa.onmicrosoft.com | Director | Engineering | Major incidents, exec comms |
| Manager-Victor | kmorgan@losandesgaa.onmicrosoft.com | VP Engineering | Leadership | Customer comms approval |
| Support-Sarah | ubeatha@losandesgaa.onmicrosoft.com | Support Lead | Support | Customer escalations |
| Support-Uma | jdaniels@losandesgaa.onmicrosoft.com | Support Agent | Support | Customer communication |
| Support-Janet | gtonic@losandesgaa.onmicrosoft.com | Sr. Support | Support | Customer updates |
| Identity-Karen | jbeam@losandesgaa.onmicrosoft.com | Identity Lead | App - Identity | Identity incidents |
| Identity-Leo | jcasker@losandesgaa.onmicrosoft.com | Identity Engineer | App - Identity | Identity support |
| Ops-Oscar | aguiness@losandesgaa.onmicrosoft.com | Operations Engineer | Platform | Maintenance windows |

### 7.3 Simulated Actions

**Action Types and Timing:**

| Action | Simulated Timing | Example |
|--------|------------------|---------|
| Acknowledge | 30s - 3min after page | SRE-Alice (jbeam) acknowledges incident |
| Add note | Throughout incident | "Investigating database connection pool exhaustion" |
| Run RBA job | 2-5min after ack | Trigger diagnostics_k8s_pod_status |
| Escalate | If no progress after 10min | Escalate to Manager-Carol (jmurphy) |
| Reassign | When expertise needed | Reassign to DBA-Frank (jmurphy) |
| Add responder | When help needed | Add SRE-Bob (jcasker) to incident |
| Update status | Key milestones | "Identified root cause" |
| Resolve | When fixed | "Issue resolved, monitoring" |
| Create followup | Post-resolution | Create Jira ticket for PIR |

**Realistic Interaction Patterns:**

```
Typical P1 Incident Timeline:
├── T+0: Alert fires, incident created
├── T+0-2min: Primary on-call paged
├── T+1-3min: Primary acknowledges
├── T+2-4min: Primary adds initial note ("Looking into this")
├── T+3-5min: Workflow triggers diagnostics
├── T+5-8min: Primary reviews diagnostics, adds note with findings
├── T+8-10min: Primary requests additional responder or escalates
├── T+10-15min: Additional responders join, add perspectives
├── T+15-25min: Root cause identified, remediation started
├── T+25-35min: Fix applied, verification
├── T+35-45min: Resolution confirmed, incident resolved
├── T+45-60min: Post-incident tasks created
```

### 7.4 Realistic Communication Simulation

**Simulated Slack Messages (in incident channels):**

```
#inc-2025010112345-checkout-outage

[14:30:45] 🤖 PagerDuty Bot: Incident INC-2025010112345 created
           Priority: P1 | Service: App - Checkout Team
           Summary: Checkout API latency p99 > 5s

[14:32:12] Jim Beam (SRE-Alice): Acknowledged. Looking into this now.

[14:33:45] 🤖 PagerDuty Bot: Diagnostics running...

[14:35:22] Jim Beam (SRE-Alice): Diagnostics show DB connection pool at 100% utilization.
           All 50 connections in use, 23 requests queued.

[14:36:15] Jameson Casker (SRE-Bob): Joining to help. I'll check the recent deployment history.

[14:38:30] Jameson Casker (SRE-Bob): Found it - deployment at 14:15 increased DB query complexity.
           New feature added 3 additional queries per checkout.

[14:40:00] Jim Beam (SRE-Alice): Increasing connection pool to 100. Restarting service.

[14:42:15] 🤖 PagerDuty Bot: Remediation action completed: Service restarted

[14:45:30] Jim Beam (SRE-Alice): Latency recovering. P99 now at 800ms, dropping.

[14:50:00] Jim Beam (SRE-Alice): Resolved. Latency normalized at 120ms p99.
           Root cause: Connection pool exhaustion due to query increase in recent deploy.
```

---

## 8. Enhanced Tagging System

### 8.1 New Tags

**Lifecycle Phase Tags:**
| Tag | Description |
|-----|-------------|
| `lifecycle:detection` | Shows detection/alert phase |
| `lifecycle:triage` | Shows triage/acknowledgment phase |
| `lifecycle:response` | Shows investigation/response phase |
| `lifecycle:remediation` | Shows fix/remediation phase |
| `lifecycle:resolution` | Shows resolution phase |
| `lifecycle:postmortem` | Shows post-incident activities |
| `lifecycle:full` | Complete end-to-end lifecycle |

**User Interaction Tags:**
| Tag | Description |
|-----|-------------|
| `users:single` | Single responder scenario |
| `users:multi` | Multiple responders collaborate |
| `users:escalation` | Shows escalation to management |
| `users:cross-team` | Cross-team collaboration |
| `users:customer-facing` | Customer communication involved |

**Automation Tags:**
| Tag | Description |
|-----|-------------|
| `rba:diagnostics` | RBA diagnostic jobs demonstrated |
| `rba:remediation` | RBA remediation jobs demonstrated |
| `rba:security` | Security automation demonstrated |
| `workflow:conditional` | Conditional workflow trigger |
| `workflow:manual` | Manual workflow trigger |
| `orchestration:global` | Global orchestration rules shown |
| `orchestration:service` | Service-specific orchestration shown |

**Realism Tags:**
| Tag | Description |
|-----|-------------|
| `logs:included` | Fake logs generated with scenario |
| `metrics:included` | Fake metrics generated |
| `noise:included` | Background noise generated |
| `duration:5min` | ~5 minute scenario |
| `duration:15min` | ~15 minute scenario |
| `duration:30min` | ~30 minute scenario |
| `duration:60min` | ~60 minute scenario |

**Complexity Tags:**
| Tag | Description |
|-----|-------------|
| `complexity:basic` | Simple, single-service scenario |
| `complexity:intermediate` | Multi-step, single-team |
| `complexity:advanced` | Multi-team, complex orchestration |
| `complexity:expert` | Full lifecycle with all features |

### 8.2 Updated Industry Tags

| Tag | Description | Example Scenarios |
|-----|-------------|-------------------|
| `banking` | Financial services | Security breach, fraud detection |
| `fintech` | Payment/trading platforms | Payment outages, trading latency |
| `healthcare` | Medical systems | EHR outages, HIPAA compliance |
| `retail` | Physical + online retail | Checkout failures, inventory sync |
| `ecommerce` | Online-only retail | Cart abandonment, payment issues |
| `technology` | SaaS/software companies | API degradation, deployment issues |
| `mining` | Mining/extraction | SCADA alerts, safety incidents |
| `manufacturing` | Factories/production | Equipment failures, line stoppages |
| `energy` | Utilities/oil & gas | Grid issues, pipeline monitoring |
| `telecom` | Telecommunications | Network outages, capacity issues |
| `media` | Streaming/content | CDN issues, transcoding failures |
| `gaming` | Online gaming | Server capacity, latency spikes |
| `logistics` | Shipping/delivery | Tracking outages, routing failures |

### 8.3 Complete Tag Taxonomy

```yaml
tags:
  industry:
    - banking
    - fintech
    - healthcare
    - retail
    - ecommerce
    - technology
    - mining
    - manufacturing
    - energy
    - telecom
    - media
    - gaming
    - logistics

  team_type:
    - soc
    - noc
    - devops
    - platform
    - sre
    - support
    - dba
    - ot_ops
    - data_engineering
    - identity
    - payments

  org_style:
    - structured
    - messy
    - distributed
    - startup
    - enterprise

  features:
    - routing
    - enrichment
    - suppression
    - priority_assignment
    - severity_normalization
    - suspension
    - maintenance_windows
    - vendor_detection
    - deduplication
    - escalation
    - variable_extraction
    - custom_fields

  integration:
    - prometheus
    - grafana
    - datadog
    - newrelic
    - sentry
    - splunk
    - cloudwatch
    - github_actions
    - uptimerobot
    - pagerduty_events_api

  lifecycle:
    - detection
    - triage
    - response
    - remediation
    - resolution
    - postmortem
    - full

  users:
    - single
    - multi
    - escalation
    - cross-team
    - customer-facing

  automation:
    - rba_diagnostics
    - rba_remediation
    - rba_security
    - workflow_conditional
    - workflow_manual

  realism:
    - logs_included
    - metrics_included
    - noise_included

  duration:
    - "5min"
    - "15min"
    - "30min"
    - "60min"

  complexity:
    - basic
    - intermediate
    - advanced
    - expert

  severity:
    - critical
    - high
    - warning
    - info
```

---

## 9. Technical Implementation Plan

### 9.1 Component Architecture

```
demo-environment/
├── simulator/                    # Core simulation engine
│   ├── lifecycle/               # Incident lifecycle orchestrator
│   │   ├── engine.py           # Main lifecycle engine
│   │   ├── flows/              # Individual flow definitions
│   │   │   ├── platform_crisis.py
│   │   │   ├── security_breach.py
│   │   │   ├── database_emergency.py
│   │   │   └── [other flows...]
│   │   └── phases/             # Phase implementations
│   │       ├── detection.py
│   │       ├── triage.py
│   │       ├── response.py
│   │       └── resolution.py
│   ├── users/                   # User simulation
│   │   ├── personas.py         # User persona definitions
│   │   ├── actions.py          # Action implementations
│   │   └── patterns.py         # Realistic timing patterns
│   └── events/                  # Event generation
│       ├── pagerduty.py        # PagerDuty Events API v2
│       └── templates/          # Event payload templates
├── generators/                   # Background generators
│   ├── logs/                    # Log generation
│   │   ├── generator.py        # Main log generator
│   │   ├── patterns/           # Log patterns per service
│   │   │   ├── checkout_api.py
│   │   │   ├── payment_processor.py
│   │   │   └── [other services...]
│   │   └── correlator.py       # Log correlation system
│   ├── noise/                   # Noise generation
│   │   ├── generator.py        # Noise alert generator
│   │   └── patterns.py         # Noise patterns
│   └── metrics/                 # Metric simulation
│       ├── generator.py        # Metric generator
│       └── dashboards.py       # Dashboard data
├── config/                       # Configuration
│   ├── settings.yaml           # Main settings
│   ├── personas.yaml           # User personas
│   ├── services.yaml           # Service definitions
│   └── integrations.yaml       # Integration keys
├── output/                       # Generated output
│   ├── logs/                    # Generated log files
│   ├── metrics/                 # Metric data
│   └── incidents/               # Incident artifacts
├── web/                          # Web interface (GitHub Pages)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScenarioCard.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── LifecycleView.tsx
│   │   │   └── LogViewer.tsx
│   │   ├── data/
│   │   │   └── scenarios.json
│   │   └── services/
│   │       └── pagerduty.ts
│   └── public/
└── scripts/                      # Utility scripts
    ├── start-environment.sh     # Start all services
    ├── run-scenario.sh          # Run specific scenario
    └── generate-logs.sh         # Start log generation
```

### 9.2 Service Components

| Service | Purpose | Technology | Runs |
|---------|---------|------------|------|
| Log Generator | Continuous fake logs | Python | Daemon |
| Noise Generator | Low-severity alert noise | Python | Daemon |
| Metric Simulator | Fake Prometheus metrics | Python | Daemon |
| Lifecycle Engine | Orchestrates scenario flows | Python | On-demand |
| User Simulator | Simulates user actions | Python | Event-driven |
| Web Interface | Scenario browser/trigger | React/TS | Static |
| API Server | Backend for web interface | Python/FastAPI | Optional |

### 9.3 Implementation Phases

**Phase 1: Core Infrastructure (Week 1-2)**
- Set up project structure
- Implement basic log generator
- Create event templates
- Build simple lifecycle engine

**Phase 2: Log Generation (Week 2-3)**
- Implement all service log patterns
- Add log correlation system
- Create pre-incident/incident/recovery patterns
- Test log realism

**Phase 3: Lifecycle Flows (Week 3-5)**
- Implement all 12 lifecycle flows
- Add phase transitions
- Integrate with PagerDuty APIs
- Test full lifecycle scenarios

**Phase 4: User Simulation (Week 5-6)**
- Implement user personas
- Add realistic action timing
- Create interaction patterns
- Test multi-user scenarios

**Phase 5: Noise & Metrics (Week 6-7)**
- Implement noise generator
- Add metric simulator
- Create dashboard data feeds
- Test suppression/suspension

**Phase 6: Web Interface (Week 7-8)**
- Build React/TypeScript frontend
- Implement filtering/search
- Add lifecycle visualization
- Deploy to GitHub Pages

**Phase 7: Integration & Testing (Week 8-9)**
- End-to-end testing
- Performance optimization
- Documentation
- Demo preparation

---

## 10. Scenario Catalog

### 10.1 Full Lifecycle Scenarios (12)

| ID | Name | Complexity | Duration | Key Features |
|----|------|------------|----------|--------------|
| `lifecycle-platform-crisis-001` | Platform Infrastructure Crisis | Expert | 60min | Major incident, multi-team, all phases |
| `lifecycle-security-breach-001` | Security Breach Response | Expert | 60min | Security workflow, compliance, confidential |
| `lifecycle-database-emergency-001` | Database Emergency | Advanced | 45min | DBRE, failover, diagnostics |
| `lifecycle-payment-outage-001` | Payment System Outage | Advanced | 45min | Business impact, customer comms |
| `lifecycle-customer-impact-001` | Customer-Impacting Degradation | Intermediate | 30min | SLA tracking, customer workflow |
| `lifecycle-identity-crisis-001` | Authentication Crisis | Advanced | 45min | Identity workflow, wide impact |
| `lifecycle-data-pipeline-001` | Data Pipeline Failure | Intermediate | 30min | Pipeline diagnostics, data quality |
| `lifecycle-maintenance-window-001` | Maintenance Window Incident | Intermediate | 60min | Suppression, maintenance workflow |
| `lifecycle-escalation-timeout-001` | Escalation Timeout | Intermediate | 45min | Escalation, priority upgrade |
| `lifecycle-manual-diagnostics-001` | Manual Diagnostics | Basic | 30min | Manual workflow trigger |
| `lifecycle-customer-comms-001` | Customer Communication | Basic | 15min | Manual comms workflow |
| `lifecycle-noise-storm-001` | Alert Storm Handling | Intermediate | 30min | Noise reduction demo |

### 10.2 Quick Demo Scenarios (20)

| ID | Name | Duration | Feature Focus |
|----|------|----------|---------------|
| `quick-routing-001` | Basic Service Routing | 2min | Routing to correct service |
| `quick-routing-002` | Dynamic Routing | 2min | Variable extraction routing |
| `quick-suppression-001` | Flapping Alert Suppression | 2min | Suppression rule |
| `quick-suppression-002` | Heartbeat Drop | 2min | Info event suppression |
| `quick-enrichment-001` | Runbook URL Injection | 2min | Enrichment |
| `quick-enrichment-002` | Custom Field Population | 2min | Custom incident fields |
| `quick-priority-001` | Security P1 Assignment | 2min | Auto P1 for security |
| `quick-priority-002` | Customer Tier Priority | 2min | Priority based on tier |
| `quick-workflow-001` | Major Incident Workflow | 5min | Workflow trigger |
| `quick-workflow-002` | Security Workflow | 5min | Security workflow |
| `quick-rba-001` | K8s Diagnostics | 3min | RBA diagnostic job |
| `quick-rba-002` | Database Health Check | 3min | DB diagnostics |
| `quick-rba-003` | Service Restart | 3min | Remediation job |
| `quick-rba-004` | Pod Scaling | 3min | Scale remediation |
| `quick-noise-001` | Dev Environment Suspend | 2min | Environment handling |
| `quick-noise-002` | Warning Severity Suspend | 2min | Severity suspension |
| `quick-maintenance-001` | Maintenance Suppression | 2min | Maintenance handling |
| `quick-escalation-001` | Timeout Escalation | 5min | Escalation workflow |
| `quick-correlation-001` | Alert Correlation | 3min | Related alerts |
| `quick-multienv-001` | Multi-Environment | 3min | Env-based routing |

### 10.3 Industry-Specific Scenarios (18)

| ID | Industry | Scenario | Complexity |
|----|----------|----------|------------|
| `industry-banking-001` | Banking | Fraud Detection Alert | Advanced |
| `industry-banking-002` | Banking | Core Banking Outage | Expert |
| `industry-healthcare-001` | Healthcare | EHR System Down | Advanced |
| `industry-healthcare-002` | Healthcare | Medical Device Alert | Intermediate |
| `industry-retail-001` | Retail | Checkout Flow Failure | Advanced |
| `industry-retail-002` | Retail | Inventory Sync Error | Intermediate |
| `industry-ecommerce-001` | E-commerce | CDN Degradation | Intermediate |
| `industry-ecommerce-002` | E-commerce | Search Outage | Intermediate |
| `industry-fintech-001` | Fintech | Trading Platform Latency | Advanced |
| `industry-fintech-002` | Fintech | Settlement Failure | Expert |
| `industry-mining-001` | Mining | SCADA Sensor Alert | Intermediate |
| `industry-mining-002` | Mining | Safety System Breach | Expert |
| `industry-telecom-001` | Telecom | Network Capacity | Advanced |
| `industry-telecom-002` | Telecom | BGP Session Down | Advanced |
| `industry-media-001` | Media | Streaming Degradation | Intermediate |
| `industry-media-002` | Media | Transcoding Failure | Intermediate |
| `industry-gaming-001` | Gaming | Game Server Overload | Advanced |
| `industry-logistics-001` | Logistics | Tracking System Outage | Advanced |

---

## Summary

### What This Proposal Delivers

1. **Living Demo Environment**
   - Continuous background activity with realistic logs
   - Noise generation that showcases suppression
   - Metric simulation for dashboard demos

2. **Complete Incident Lifecycle Coverage**
   - 12 full lifecycle flows covering all phases
   - 20 quick demos for specific features
   - 18 industry-specific scenarios

3. **Multi-User Realism**
   - 23 simulated user personas
   - Realistic action timing and patterns
   - Simulated Slack conversations

4. **Comprehensive Feature Demonstration**
   - All 15 incident workflows exercised
   - All 20 RBA automation actions used
   - All 10 service orchestrations demonstrated
   - Global orchestration rules visible

5. **Enhanced Tagging for Discoverability**
   - Lifecycle phase tags
   - User interaction tags
   - Automation tags
   - Realism tags
   - Complexity tags

### Total Scenario Count

| Category | Count |
|----------|-------|
| Full Lifecycle Flows | 12 |
| Quick Demo Scenarios | 20 |
| Industry-Specific | 18 |
| **Total** | **50** |

### Next Steps

1. **Review this proposal** - Provide feedback on scope, priorities, gaps
2. **Prioritize scenarios** - Which flows are most important for demos?
3. **Refine user personas** - Are these the right roles/actions?
4. **Approve implementation plan** - Agree on timeline and phases
5. **Begin Phase 1** - Start building core infrastructure

---

**End of Proposal**

*Awaiting review and approval before implementation begins.*
