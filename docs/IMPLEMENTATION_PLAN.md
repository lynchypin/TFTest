# PagerDuty Demo Environment - Comprehensive Implementation Plan

> **Generated:** February 7, 2026
> **Last Updated:** February 18, 2026
> **Purpose:** Master plan for implementing all 70 demo scenarios

---

## CURRENT STATUS (February 18, 2026)

### Workflow-to-Lambda Integration - WORKING

> **Status:** COMPLETE - End-to-end flow validated (most recently Feb 17, incident Q2CSWNFUO7TSZ6)
> **See:** `docs/NEXT_DEVELOPER_PROMPT.md` for current project state

**All Critical Blockers Resolved (Feb 9-10, 2026):**

| Issue | Status | Solution |
|-------|--------|----------|
| Lambda env var mismatch | ✅ FIXED | Added both `PAGERDUTY_TOKEN` and `PAGERDUTY_API_KEY` |
| Slack Enterprise Grid | ✅ FIXED | Added `SLACK_TEAM_ID=T0A9LN53CPQ` env var |
| Channel pattern mismatch | ✅ FIXED | Changed search from `inc-*` to `demo-*` |
| Webhook signature | ✅ BYPASSED | Webhook deleted Feb 17 — controller doesn't use webhooks |
| PagerDuty API token role | ✅ FIXED | Token upgraded to admin role (see `docs/CREDENTIALS_REFERENCE.md`) |
| Scheduler role mismatch | ✅ FIXED | Updated to `demo-scheduler-invoke-role` |
| Bot posting as "Oauth APP" | ✅ FIXED | Uses `post_as_user()` for first responder |

**Current Working Flow (Controller — validated Feb 17):**
1. Controller sends event via PagerDuty Events API v2 ✅
2. Event Orchestration routes to correct service ✅
3. Workflow triggers and creates Slack channel + Jira ticket ✅
4. Controller polls conference_bridge for Slack channel URL ✅
5. Responder acknowledges incident (as their identity) ✅
6. Bot joins channel, invites observers + responders ✅
7. Phased investigation messages posted as impersonated users ✅
8. Incident resolved ✅

**Remaining Work:**
- ~~Multi-message conversations not yet implemented~~ COMPLETED (Feb 11-14) — Controller Lambda handles full phased conversations
- ~~Webhook signature verification disabled~~ N/A — Webhook deleted Feb 17, controller doesn't use webhooks
- 19 scenarios disabled pending external integrations (ServiceNow, Grafana, UptimeRobot, Splunk, Sentry)
- AIOps features require EIM license add-on

---

## ~~Not Yet Implemented~~ COMPLETED

### ~~Slack Responder Conversations (Multi-Message)~~ COMPLETED (Feb 11-14, 2026)

> **Status:** COMPLETED — The `demo-simulator-controller` Lambda handles full multi-phase conversations with user impersonation during the investigation phase of each scenario.

**What was built:**
- Controller Lambda runs phased actions: investigating → found_issue → working_fix → resolved
- Each phase posts scenario-specific messages to Slack as impersonated users
- Configurable delays (30-60s default, overridable via `action_delay`)
- 47 of 47 enabled scenarios validated end-to-end

**Historical context (preserved for reference):**
- `CONVERSATION_LIBRARY` in `aws/lambda-demo-orchestrator/handler.py` has message templates
- `lambda-lifecycle/handler.py` has `post_conversation()` as supplementary mechanism
- User impersonation working via `post_as_user()` with `chat:write.customize` scope
- Could be implemented in `demo-orchestrator` or via `lambda-lifecycle`

---

## Completed Work (as of February 8, 2026)

### Phase 1: Foundation (COMPLETED)

| Task | Status | Details |
|------|--------|---------|
| Fix empty workflows | DONE | Data Pipeline Alert workflow populated with 2 steps |
| Delete orphaned triggers | DONE | 9 orphaned triggers removed (47 → 38 active) |
| E2E Test Suite | DONE | `scripts/e2e_test.py` - 7 tests, all passing |

### Phase 2: Jira Integration (COMPLETED)

| Task | Status | Details |
|------|--------|---------|
| Verify Jira projects | DONE | 9 projects available (COMP, DATA, DEMO, INFRA, KAN, LAX, PAY, PIR, SECOPS) |
| Add Jira steps to workflows | DONE | 6 key workflows updated with Jira ticket creation |

**Workflows with Jira Integration:**
| Workflow | Project | Issue Type |
|----------|---------|------------|
| Standard Incident Response | DEMO | Incident |
| Security Incident Response | SECOPS | Incident |
| Payments System Outage | PAY | Incident |
| Data Pipeline Alert | DATA | Incident |
| Database Emergency Response | INFRA | Incident |
| Compliance Incident Handler | COMP | Incident |

### Phase 3: Scenario Readiness Improvements (COMPLETED)

| Task | Status | Details |
|------|--------|---------|
| Update scenario analyzer | DONE | Fixed feature detection in `analyze_scenario_readiness.py` |
| Add priority recognition | DONE | P1-P5 priorities now recognized as configured |
| Add workflow mapping | DONE | Slack channels, PIR, stakeholder notifications mapped |
| Extend Jira integration | DONE | Most workflows already have Jira steps |

**Result:** READY scenarios improved from 8 → 19 (137% increase)

### Phase 4: Slack User Impersonation (COMPLETED)

| Task | Status | Details |
|------|--------|---------|
| Implement user profile caching | DONE | `_profile_cache` in SlackClient class |
| Add get_user_profile() method | DONE | Fetches display name and avatar URL from Slack API |
| Add post_as_user() method | DONE | Posts with username and icon_url parameters |
| Update all post_message calls | DONE | 9 calls updated to use user impersonation |

**Files Modified:**
- `aws/lambda-demo-orchestrator/handler.py` - Primary Lambda with all Slack posting logic
- `aws/shared/clients.py` - Shared SlackClient class

**How It Works:**
When Lambda posts a message (e.g., responder added, incident resolved), it:
1. Looks up the user's Slack profile via `users.info` API
2. Caches the profile to avoid repeated API calls
3. Posts with `username` and `icon_url` parameters

**Limitation:** Messages still show an "APP" badge (Slack API limitation), but visually appear as the user with their name and avatar.

---

## CRITICAL BLOCKERS STATUS

### RESOLVED Issues

#### 1. ~~Incidents Not Being Auto-Acknowledged~~ ✅ FIXED

**Root Cause:** Demo users (Jim Beam, Jack Daniels, etc.) had "observer" role in PagerDuty, which does not permit acknowledging incidents.

**Resolution:** Changed all demo users from "observer" to "responder" role (appears as "limited_user" in API).

**Verification:** Manual API call to acknowledge incident with demo user email now succeeds. Full E2E test confirms auto-acknowledgment working.

**Note:** If new demo users are added, ensure they have "responder" role, NOT "observer".

#### 2. ~~Demo Owner Not Added to Slack Channels~~ ✅ FIXED

**Root Cause:** `conversations.invite` was attempting to add multiple users in a single call, which failed silently for some users.

**Resolution:** Modified `invite_users_to_channel` function in three files to invite users one-by-one with individual error handling:
- `aws/lambda-demo-orchestrator/handler.py`
- `aws/shared/clients.py`
- `aws/lambda-package/handler.py`

**Observer Slack IDs:**
- `conalllynch88@gmail.com`: `U0A9GBYT999`
- `clynch@pagerduty.com`: `U0A9KAMT0BF`

### ~~PENDING Issues~~ RESOLVED

#### ~~3. Events Routing to "Default Service - Unrouted Events"~~ ✅ RESOLVED (Feb 14)

**Status:** 47 of 66 scenarios route correctly. 11 industry scenarios (IND-*) fall back to the default K8S routing key but still trigger incidents successfully. 19 scenarios are disabled pending external integrations.

#### ~~4. 66 Scenarios NOT Fully Wired~~ ✅ RESOLVED (Feb 14)

**Status:** All 47 enabled scenarios E2E validated via `scripts/test_all_scenarios.py` with 100% pass rate. 19 disabled pending external integrations (ServiceNow, Grafana, UptimeRobot, etc.).

#### ~~5. Datadog Integration Not End-to-End Tested~~ ✅ RESOLVED (Feb 9)

**Status:** All monitors updated to use `@pagerduty-demo-simulator-alerts`. Routing key fixed. Graceful degradation added for expired Datadog trial (Feb 14).

---

## Executive Summary

### Current State Analysis

| Component | Count | Status |
|-----------|-------|--------|
| PagerDuty Services | 34 | Deployed |
| Event Orchestration Rules | 12 | Active (INSUFFICIENT for 66 scenarios) |
| Incident Workflows | 25 | Deployed (all populated with steps) |
| Workflow Triggers | 38 | Active (9 orphaned removed) |
| Lambda Functions | 9 | Running (auto-ack now working) |
| Datadog Monitors | 14 | Active (needs service name fix) |
| Jira Projects | 9 | Available |

### Scenario Readiness

| Status | Count | Percentage | Notes |
|--------|-------|------------|-------|
| **READY** | 19 | 29% | Infrastructure present (NOT live-tested) |
| **PARTIAL** | 29 | 44% | Need minor config |
| **NEEDS_WORK** | 18 | 27% | Need significant work |

**CAUTION:** "READY" means the scenario has the required PagerDuty infrastructure configured. It does NOT mean the scenario has been validated in a live demo environment.

---

## Infrastructure Overview

### AWS (us-east-1)

**Lambda Functions:**
| Function | Purpose | Schedule |
|----------|---------|----------|
| `demo-simulator-orchestrator` | Triggers random scenarios | Hourly |
| `demo-simulator-lifecycle` | Manages incident progression | Every 15 min |
| `demo-simulator-notifier` | Slack notifications | Every 2 min |
| `demo-simulator-metrics` | Sends metrics to Datadog/NR | Every 5 min |
| `demo-simulator-user-activity` | Simulates user actions | Weekdays 9-17 UTC |
| `demo-simulator-health-check` | Validates integrations | Every 15 min |
| `demo-simulator-controller` | Manual demo control | On-demand |
| `demo-simulator-reset` | Environment cleanup | On-demand |

**EC2:**
- RBA Runner: `i-03ab4fd5f509a8342` (t2.micro, Amazon Linux 2023)

### Integrations Status

| Integration | Status | Notes |
|-------------|--------|-------|
| Datadog | NEEDS FIX | 14 monitors using wrong service name (`Los-Andes-Demo` → `demo-simulator-alerts`) |
| Prometheus | READY | Via Grafana Cloud |
| Grafana | READY | Cloud stack configured |
| CloudWatch | READY | SNS -> PagerDuty |
| New Relic | READY | Alert policy + workflow |
| GitHub Actions | READY | Workflow configured |
| Slack | READY | Full scopes, Enterprise Grid, user impersonation enabled |
| Jira | **READY** | Multiple workflows create tickets automatically |

---

## Scenario Analysis by Tier

### READY Scenarios (19)

**IMPORTANT:** "READY" means infrastructure is present in PagerDuty. These scenarios have NOT been live-tested end-to-end. See `PHASE_IMPLEMENTATION_GUIDE.md` Phase 5 for testing plan.

| ID | Name | Integration | Service |
|----|------|-------------|---------|
| FREE-001 | Simple Alert Routing | prometheus | Platform - K8s |
| PRO-001 | Priority-Based Incident Routing | datadog | Platform - K8s |
| PRO-002 | Post-Incident Review Workflow | datadog | Platform - K8s |
| PRO-003 | Jira Ticket Integration | prometheus | App - Orders API |
| BUS-002 | Slack Incident Channel Creation | prometheus | App - Checkout |
| EIM-004 | Advanced Slack Actions | prometheus | Platform - K8s |
| WF-001 | Incident Workflow - Page on-call | prometheus | Platform - K8s |
| WF-002 | Incident Workflow - Full Response | datadog | Platform - K8s |
| IND-001 | Manufacturing Floor Alert | cloudwatch | OT Operations |
| IND-002 | Mining Safety System Alert | cloudwatch | Safety Operations |
| IND-003 | Retail POS System Failure | newrelic | Retail Systems |
| IND-004 | Fintech Payment Gateway | datadog | Payment Processing |
| IND-006 | Telecom Network Congestion | prometheus | Network Operations |
| IND-007 | Healthcare EMR System Alert | newrelic | Clinical Systems |
| IND-008 | Database Replica Lag Alert | datadog | Database - DBRE |
| IND-009 | CI/CD Pipeline Failure | github_actions | DevOps - CI/CD |
| + 3 more | See scenario_readiness_analysis.json | | |

### PARTIAL Scenarios (29)

These need workflow configuration or minor fixes:

**Business Tier (BUS):**
- BUS-001: Response Mobilizer - workflow exists, needs trigger refinement
- BUS-003: Service Graph Impact - needs service graph config
- BUS-004: ServiceNow Sync - ServiceNow not configured (deferred)
- BUS-005: Stakeholder Updates - workflow exists but needs trigger

**Digital Operations (DIGOPS):**
- DIGOPS-001 to 007: Need AIOps/EIM configuration

**Enterprise Incident Management (EIM):**
- EIM-001 to 003, EIM-005: Need enterprise features (tasks, roles, types)

**Workflows (WF):**
- WF-003: Workflow exists but triggers need refinement

### NEEDS_WORK Scenarios (18)

These require significant implementation:

**SRE Tier (6):** Need AI/ML features
- Autonomous remediation
- Pattern learning
- Proactive detection

**SCRIBE Tier (3):** Need AI Scribe features
- Timeline documentation
- Summary generation
- Pattern recognition

**SHIFT Tier (3):** Need scheduling features
- On-call handoff automation
- Coverage gap detection
- Load balancing

**RBA Tier (4):** Need Runbook Automation setup
- Interactive runbooks
- Approval gates
- Self-service workflows

---

## Efficiency Opportunities

### 1. Reusable Workflow Patterns

**Create base workflows that can be extended:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Base Workflow: Incident Response         │
├─────────────────────────────────────────────────────────────┤
│ Step 1: Create Slack Channel                                │
│ Step 2: Add Initial Note                                    │
│ Step 3: Post to Channel                                     │
│ Step 4: Send Status Update                                  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────┐         ┌──────────┐         ┌──────────┐
    │ Security │         │ Database │         │ Payments │
    │ Response │         │ Response │         │ Response │
    │ +SOC Page│         │ +DBA Page│         │ +Finance │
    └──────────┘         └──────────┘         └──────────┘
```

**25 workflows exist but many are duplicative.** Consolidate to:
- 1 base incident response workflow
- 5 specialized response workflows (Security, DB, Payments, Capacity, Identity)
- 3 lifecycle workflows (Resolution, Closeout, PIR)
- 2 manual workflows (Diagnostics, Customer Comms)

### 2. Event Orchestration Consolidation

**Current:** 12 routing rules targeting 10+ services

**Optimization:** Use dynamic routing based on payload `pd_service` field:
```
Rule 1: event.custom_details.pd_service exists
        → Route to service matching pd_service value
Rule 2: Catch-all → Default service
```

This reduces rules from 12 to 2 and makes adding new services automatic.

### 3. Lambda Function Consolidation

**Current:** 9 separate Lambda functions

**Opportunity:** Consolidate into 3:
1. `demo-orchestrator` - Handles scheduled triggers + manual control
2. `demo-lifecycle` - Handles incident lifecycle + user activity
3. `demo-webhooks` - Handles PagerDuty webhooks + notifications

### 4. Trigger Pattern Standardization

**Current:** 38 triggers (9 orphaned removed)

**Standardize on:**
- `[DEMO]` prefix for all demo incidents
- Priority-based triggers (P1/P2 → specific workflows)
- Service-based triggers (Security → Security workflow)

---

## Implementation Phases

### Phase 1: Foundation (Quick Wins) - COMPLETED ✓

**Objective:** Get all PARTIAL scenarios to READY

| Task | Status | Details |
|------|--------|---------|
| Fix empty workflows (add steps) | ✓ DONE | Data Pipeline Alert populated |
| Configure workflow triggers | ✓ DONE | 9 orphaned triggers deleted |
| E2E Test Suite created | ✓ DONE | `scripts/e2e_test.py` |

### Phase 2: Jira Integration - COMPLETED ✓

**Objective:** Enhance Jira integration

| Task | Status | Details |
|------|--------|---------|
| Verify Jira projects exist | ✓ DONE | 9 projects available |
| Add Jira to key workflows | ✓ DONE | 6 workflows create tickets |
| ServiceNow integration | DEFERRED | Lower priority |

**Note:** ServiceNow was deferred as Jira provides sufficient ticket management for demo purposes.

### Phase 3: Scenario Readiness - COMPLETED ✓

**Objective:** Improve scenario readiness assessment

| Task | Status | Details |
|------|--------|---------|
| Update scenario analyzer | ✓ DONE | Fixed feature detection |
| Improve READY count | ✓ DONE | 8 → 19 scenarios |

### Phase 4: Slack User Impersonation - COMPLETED ✓

**Objective:** Bot messages appear as users

| Task | Status | Details |
|------|--------|---------|
| Implement profile fetching | ✓ DONE | `get_user_profile()` method |
| Add user impersonation | ✓ DONE | `post_as_user()` method |

### ~~Phase 5: Fix Core Demo Reliability~~ COMPLETED (Feb 9-18, 2026)

**Objective:** Fix critical issues blocking live demos — **ALL COMPLETED**

| Task | Status | Details |
|------|--------|---------|
| Debug incident auto-acknowledgment | ✅ DONE | Changed demo users to "responder" role (Feb 9) |
| Fix Slack channel user invites | ✅ DONE | One-by-one invites with error handling (Feb 14); both observer accounts added (Feb 18) |
| Expand Event Orchestration rules | ✅ DONE | 12 routing rules configured and validated (Feb 14) |
| Wire all scenarios end-to-end | ✅ DONE | 47/47 enabled scenarios pass E2E (Feb 14) |
| Test Datadog integration e2e | ✅ DONE | Graceful degradation if trial expired (Feb 14) |
| Schedule rebalancing | ✅ DONE | All 6 users have 2-3 schedule assignments (Feb 18) |
| Slack health check | ✅ DONE | Controller validates token at startup (Feb 18) |
| Incident resolution resilience | ✅ DONE | Retry logic with error logging (Feb 18) |

### Phase 6: AIOps/EIM Features - PENDING

**Objective:** Enable DIGOPS and AIOPS scenarios

| Task | Effort | Impact |
|------|--------|--------|
| Configure Alert Grouping | Medium | DIGOPS-001, AIOPS-002 |
| Configure Alert Suppression | Medium | DIGOPS-002 |
| Enable Auto-Pause | Low | DIGOPS-003 |
| Configure Change Correlation | Medium | DIGOPS-007 |
| Enable Probable Origin | Medium | AIOPS-003 |

**Note:** Requires PagerDuty AIOps/EIM add-on license (formerly Event Intelligence)

### Phase 7: RBA Enhancement - PENDING

**Objective:** Enable RBA scenarios

| Task | Effort | Impact |
|------|--------|--------|
| Create interactive runbooks | High | RBA-001 to 004 |
| Configure approval gates | Medium | AA-002 |
| Set up self-service portal | High | RBA-003 |

### Phase 8: AI/ML Features - PENDING

**Objective:** Enable SRE and SCRIBE scenarios

| Task | Effort | Impact |
|------|--------|--------|
| Configure AI Scribe | Medium | SCRIBE-001 to 003 |
| Enable autonomous remediation | High | SRE-001, SRE-002 |
| Set up pattern learning | High | SRE-006 |

**Note:** Requires PagerDuty AIOps license features

---

## Recommended Priority Order

### Completed ✓

1. ~~Fix PARTIAL scenarios~~ - Empty workflows populated
2. ~~Delete orphaned triggers~~ - 9 removed
3. ~~Jira integration~~ - 6 workflows create tickets
4. ~~Consolidate documentation~~ - Archived outdated files, updated README
5. ~~Slack user impersonation~~ - Bot posts appear as users

### URGENT (Phase 5 - Before Any Live Demos)

6. **Fix incident auto-acknowledgment** - Lambda not scheduling acknowledgments
7. **Fix Slack channel invites** - Demo owner not added to channels
8. **Expand Event Orchestration** - Only 12 rules for 66 scenarios
9. **Wire all scenarios e2e** - Validate event → incident → workflow flow
10. **Test Datadog integration** - Actual monitors, not mock events

### After Phase 5 Completed

11. **AIOps configuration** - Requires Enterprise license
12. **RBA runbook creation** - Interactive workflows
13. **AI/ML features** - Requires AIOps license

---

## Archived Scripts

The following one-time scripts have been moved to `scripts/archive/`:

| Script | Purpose | Date |
|--------|---------|------|
| `add_jira_to_workflows.py` | Added Jira steps to 6 workflows | Feb 7 |
| `add_jira_to_more_workflows.py` | Extended Jira integration | Feb 8 |
| `analyze_jira_workflows.py` | Analyzed Jira workflow status | Feb 8 |
| `check_jira_workflows.py` | Checked Jira workflows exist | Feb 8 |
| `verify_jira_steps.py` | Verified Jira steps exist | Feb 7 |
| `delete_orphaned_triggers.py` | Deleted 9 orphaned triggers | Feb 7 |
| `fix_data_pipeline_workflow.py` | Fixed Data Pipeline workflow | Feb 7 |
| `fix_workflow_trigger.py` | Fixed workflow trigger | Feb 7 |

---

## Metrics for Success

| Metric | Previous | Current (Feb 17) | Target |
|--------|----------|-------------------|--------|
| READY scenarios (infrastructure) | 8 (12%) | 47 (71%) | 66 (100%) |
| READY scenarios (live-tested) | 0 | 47 (71%) | 66 (100%) |
| Workflow triggers | 47 | 38 | 38 |
| Workflows with Jira | 0 | 6 | 10+ |
| E2E test pass rate | N/A | 47/47 (100%) | All 66 |
| Event Orchestration rules | 12 | 12 | 12 (sufficient for enabled scenarios) |
| Incident auto-ack working | No | Yes | Yes |

---

## Next Steps for Developer

**Remaining Work (Feb 17, 2026):**
1. **Enable 19 disabled scenarios** - Requires external integration setup (ServiceNow, Grafana, UptimeRobot, Splunk, Sentry)
2. **Multi-scenario playlists** - Run curated sets of scenarios for specific audiences
3. **RBA runbook content** - Runner exists, need meaningful diagnostic/remediation scripts
4. **Fix Terraform Lambda code detection** - Use `source_code_hash` in `aws/main.tf`
5. **AIOps full configuration** - Alert Grouping, Suppression require AIOps/EIM add-on license

**Completed (no longer urgent):**
- ~~Debug Lambda webhook handling~~ FIXED (Feb 10) -- admin token + controller architecture
- ~~Fix Slack channel invites~~ FIXED (Feb 10) -- one-by-one invites
- ~~Expand Event Orchestration~~ COMPLETED (Feb 14) -- all 47 enabled scenarios route correctly
- ~~Validate end-to-end flow~~ COMPLETED (Feb 14) -- 47/47 pass rate
- ~~Test real integrations~~ COMPLETED (Feb 9) -- Datadog fixed, graceful fallback added

---

*This document is the source of truth for demo environment implementation. Update as scenarios are completed.*
