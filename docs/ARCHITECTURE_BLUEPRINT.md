# PagerDuty Demo Environment - Architecture Blueprint

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | COMPLETED - Fully deployed and tested |
| 🟡 | PARTIAL - Deployed but needs configuration |
| ⏳ | PENDING - Not yet deployed |
| 🔄 | IN_PROGRESS - Currently being worked on |
| ❌ | REMOVED - Deprecated or removed |
| ⚡ | ALTERED - Modified from original design |
| ➕ | ADDITION - Added beyond original scope |
| 🚫 | OBSOLETE - No longer needed |

> **IMPORTANT (February 17, 2026):** The diagrams below show the original webhook-driven architecture (`demo-simulator-orchestrator-v2`). The **current primary execution path** is the `demo-simulator-controller` Lambda, which is a self-contained scenario runner that triggers events, polls APIs (not webhooks), and runs the full incident lifecycle within a single invocation. The orchestrator Lambda and its DynamoDB/EventBridge components are still deployed but are considered legacy. The PagerDuty Generic Webhook subscription (PILGGJ0) was **deleted on Feb 17** as it was non-functional (Lambda Function URLs return 403 Forbidden). The orchestrator's API Gateway (`https://ynoioelti7.execute-api.us-east-1.amazonaws.com`) remains available for the GitHub Pages demo site. See `SCENARIO_FLOWS.md` for the current controller flow diagram.

> **KNOWN ISSUES (February 17, 2026):** Three active issues affect the Slack integration path of the `demo-simulator-controller` Lambda: (1) demo owner not being invited to channels, (2) Jim Beam incidents failing resolution disproportionately due to over-scheduling across 4 on-call schedules, (3) no visible Slack bot activity — likely caused by an empty/invalid `SLACK_BOT_TOKEN` or missing `SLACK_TEAM_ID` env var on the controller Lambda. All Slack failures are silent (the controller never checks Slack API responses). See `docs/GOTCHAS_AND_WORKAROUNDS.md` "OPEN ISSUES" section for full analysis, verification commands, and fix recommendations.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EXTERNAL TRIGGERS                                      │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Datadog   │  │   Grafana   │  │  New Relic  │  │ CloudWatch  │  │   Manual    │    │
│  │   [✅]      │  │   [🟡]      │  │   [🟡]      │  │   [✅]      │  │   [✅]      │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┴────────────────┘            │
│                                           │                                              │
│                                           ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        PagerDuty Events API v2 [✅]                                 │ │
│  │                        (events.pagerduty.com/v2/enqueue)                           │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              PAGERDUTY PLATFORM [✅]                                     │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                    GLOBAL EVENT ORCHESTRATION [✅]                                  ││
│  │  • Routing rules based on event attributes                                          ││
│  │  • Priority assignment                                                              ││
│  │  • Event enrichment                                                                 ││
│  │  • Service routing                                                                  ││
│  └───────────────────────────────────────┬─────────────────────────────────────────────┘│
│                                          │                                              │
│                                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                    SERVICE EVENT ORCHESTRATION [✅]                                 ││
│  │  • Service-specific rules                                                           ││
│  │  • Suppression logic                                                                ││
│  │  • Alert grouping                                                                   ││
│  └───────────────────────────────────────┬─────────────────────────────────────────────┘│
│                                          │                                              │
│                                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                         SERVICES (30+) [✅]                                         ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               ││
│  │  │ Payment Svc  │ │ Database Svc │ │ API Gateway  │ │ Auth Service │ ...           ││
│  │  │    [✅]      │ │    [✅]      │ │    [✅]      │ │    [✅]      │               ││
│  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘               ││
│  │         └────────────────┴────────────────┴────────────────┘                        ││
│  │                                   │                                                 ││
│  └───────────────────────────────────┼─────────────────────────────────────────────────┘│
│                                      │                                                  │
│                                      ▼                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    ESCALATION POLICIES (22) [✅]                                   │ │
│  │                    ┌─────────────────────────────────────────┐                     │ │
│  │                    │ Level 1 → Level 2 → Level 3 → Manager  │                     │ │
│  │                    └─────────────────────────────────────────┘                     │ │
│  │                                   │                                                │ │
│  │                    ┌──────────────┴──────────────┐                                │ │
│  │                    ▼                              ▼                                │ │
│  │            ┌───────────────┐            ┌───────────────┐                         │ │
│  │            │  SCHEDULES    │            │    USERS      │                         │ │
│  │            │  (8) [✅]     │            │    (6) [✅]   │                         │ │
│  │            └───────────────┘            └───────────────┘                         │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                                  │
│                                      ▼                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         INCIDENT CREATED                                           │ │
│  │                              │                                                     │ │
│  │                              ▼                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │              INCIDENT WORKFLOW TRIGGERS (22+) [✅]                           │ │ │
│  │  │  Conditions: priority, service, urgency, incident_type                       │ │ │
│  │  │  NEW: [DEMO] title condition trigger (ID: 7c33cc98-...)                      │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────┘ │ │
│  │                              │                                                     │ │
│  │                              ▼                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │              INCIDENT WORKFLOWS (22+) [✅]                                   │ │ │
│  │  │  Most shells created via Terraform, steps populated via API                  │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │ Demo Incident Channel Setup (PUXIPNC) [✅] - API Created                │ │ │ │
│  │  │  │  Step 1: Create Slack Channel (demo-{number}-{title})                   │ │ │ │
│  │  │  │  Step 2: Add Conference Bridge (stores Slack URL)                       │ │ │ │
│  │  │  │                                                                          │ │ │ │
│  │  │  │ Other Workflows (Terraform shells):                                      │ │ │ │
│  │  │  │  1. Create Slack Channel [🟡]                                           │ │ │ │
│  │  │  │  2. Add Note [🟡]                                                        │ │ │ │
│  │  │  │  3. Create Jira Ticket [🟡]                                             │ │ │ │
│  │  │  │  4. Run Automation Action [🟡]                                          │ │ │ │
│  │  │  │  5. Update Status Page [🟡]                                             │ │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    AUTOMATION ACTIONS (20+) [✅]                                   │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │ │
│  │  │ Health Check │ │ DB Failover  │ │ Restart Svc  │ │ Scale Up     │ ...          │ │
│  │  │    [✅]      │ │    [✅]      │ │    [✅]      │ │    [✅]      │              │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘              │ │
│  │                                   │                                               │ │
│  │                    ┌──────────────┴──────────────┐                               │ │
│  │                    ▼                              ▼                               │ │
│  │            ┌───────────────┐            ┌───────────────┐                        │ │
│  │            │ RBA RUNNER 1  │            │ RBA RUNNER 2  │                        │ │
│  │            │    [✅]       │            │    [✅]       │                        │ │
│  │            └───────────────┘            └───────────────┘                        │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    BUSINESS SERVICES (12) [✅]                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    Payment Platform (P1)                                      │ │ │
│  │  │                           │                                                   │ │ │
│  │  │    ┌──────────────────────┼──────────────────────┐                           │ │ │
│  │  │    ▼                      ▼                      ▼                           │ │ │
│  │  │ Payment Gateway    Payment Processing     Payment Analytics                   │ │ │
│  │  │    (P1)                 (P2)                  (P3)                            │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                              ┌────────────┴────────────┐
                              │        WEBHOOKS         │
                              │     [✅ Configured]     │
                              │ incident.triggered      │
                              │ incident.acknowledged   │
                              │ incident.resolved       │
                              │ incident.workflow.*     │
                              └────────────┬────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              DEMO ORCHESTRATOR [✅]                                      │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    AWS LAMBDA FUNCTION [✅]                                        │ │
│  │                    (demo-simulator-orchestrator-v2)                                │ │
│  │                    Region: us-east-1                                               │ │
│  │                    API Gateway: https://ynoioelti7.execute-api.us-east-1.amazonaws.com/webhook │ │
│  │                                                                                    │ │
│  │  Handlers:                                                                        │ │
│  │  ├── handle_webhook()          [✅ Deployed]                                     │ │
│  │  ├── handle_scheduled_action() [✅ Deployed]                                     │ │
│  │  └── handle_api_request()      [✅ Deployed]                                     │ │
│  │                                                                                    │ │
│  │  Event Handlers:                                                                  │ │
│  │  ├── on_incident_triggered     [✅]                                              │ │
│  │  ├── on_incident_acknowledged  [✅]                                              │ │
│  │  ├── on_incident_resolved      [✅]                                              │ │
│  │  ├── on_workflow_completed     [✅] - Reads Slack URL from conference bridge     │ │
│  │  └── on_incident_escalated     [✅]                                              │ │
│  │                                                                                    │ │
│  │  Classes:                                                                         │ │
│  │  ├── DemoState (DynamoDB)      [✅ Deployed]                                     │ │
│  │  ├── PagerDutyClient           [✅ Deployed]                                     │ │
│  │  └── SlackClient               [✅ Deployed] (invites/messages/post_as_user)     │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                           │                                              │
│              ┌────────────────────────────┼────────────────────────────────┐                │
│              ▼                            ▼                            ▼                │
│  ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐           │
│  │   DYNAMODB [✅]   │      │  EVENTBRIDGE [✅] │      │ API GATEWAY [✅]  │           │
│  │ demo-incident-    │      │   Scheduler       │      │ Webhook endpoint  │           │
│  │ state table       │      │                   │      │                   │           │
│  └───────────────────┘      └───────────────────┘      └───────────────────┘           │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL INTEGRATIONS                                       │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │     SLACK       │  │     JIRA        │  │  STATUS PAGE    │  │  SERVICENOW     │    │
│  │     [✅]        │  │     [✅]        │  │     [✅]        │  │     [✅]        │    │
│  │                 │  │                 │  │                 │  │                 │    │
│  │ • Channel       │  │ Projects:       │  │ • Updates via   │  │ • Native PD     │    │
│  │   creation via  │  │ • SECOPS  [✅]  │  │   API + Lambda  │  │   extension     │    │
│  │   PD workflow   │  │ • COMPLIANCE[✅]│  │ • Component     │  │ • No custom     │    │
│  │ • User invite   │  │ • INFRA   [✅]  │  │   status mgmt   │  │   code needed   │    │
│  │   via Lambda    │  │ • PIR     [✅]  │  │ • Incident      │  │ • Connected     │    │
│  │ • Messages via  │  │ • PAYMENTS[✅]  │  │   posting       │  │   Feb 11 2026   │    │
│  │   Lambda        │  │ • DATA    [✅]  │  │                 │  │                 │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐                                               │
│  │   CONFLUENCE    │  │     AIOPS       │                                               │
│  │     [⏳]        │  │     [✅]        │                                               │
│  │                 │  │                 │                                               │
│  │ Space:          │  │ • Alert         │                                               │
│  │ • RUNBOOKS [⏳] │  │   Grouping      │                                               │
│  │                 │  │ • Correlation   │                                               │
│  │                 │  │ • Past incident │                                               │
│  │                 │  │   lookup        │                                               │
│  └─────────────────┘  └─────────────────┘                                               │
│                                                                                          │
│  SLACK INTEGRATION ARCHITECTURE:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │ [DEMO] Incident Created                                                             ││
│  │         │                                                                           ││
│  │         ▼                                                                           ││
│  │ PagerDuty Workflow "Demo Incident Channel Setup" (PUXIPNC)                          ││
│  │         │                                                                           ││
│  │         ├──> Step 1: Create Slack Channel (via PD native integration)              ││
│  │         │            Output: Channel Link                                           ││
│  │         │                                                                           ││
│  │         └──> Step 2: Add Conference Bridge (stores Channel Link)                   ││
│  │                                                                                     ││
│  │         ▼                                                                           ││
│  │ [Legacy: webhook] OR [Current: controller polls API directly]                       ││
│  │         │                                                                           ││
│  │         └──> Reads conference_bridge.conference_url → extracts channel_id           ││
│  │              Bot joins channel, invites users, posts messages                        ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│  NEW ACTION TYPE FLOW (Feb 11, 2026):                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │ Lambda (Controller/Orchestrator) performs actions during investigation:              ││
│  │                                                                                     ││
│  │   aiops_correlate ──> GET /incidents (past) ──> GET /related_incidents              ││
│  │                       Posts correlation results to Slack                             ││
│  │                                                                                     ││
│  │   status_page_update ──> GET /status_pages ──> POST /status_pages/{id}/posts        ││
│  │                          Updates component status via post_updates endpoint          ││
│  │                          Updates component status                                   ││
│  │                                                                                     ││
│  │   invoke_rba ──> GET /automation_actions ──> POST /invoke                           ││
│  │                  OR GET /incident_workflows ──> POST /trigger                       ││
│  │                  Posts results to incident timeline                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Status Matrix

### Terraform-Managed Resources

| Component | Count | Status | Notes |
|-----------|-------|--------|-------|
| Services | 30+ | ✅ | All deployed (12 via for_each + 20 individual) |
| Teams | 6 | ✅ | Data sources, pre-existing |
| Schedules | 8 | ✅ | All rotations configured |
| Escalation Policies | 22 | ✅ | All deployed |
| Incident Workflows | 22+ | 🟡 | Most shells via TF, Demo Channel Setup via API |
| Workflow Triggers | ~22+ | ✅ | Deployed, including [DEMO] conditional trigger |
| Automation Actions | 20+ | ✅ | All deployed |
| Service Orchestrations | 10+ | ✅ | All rules active |
| Global Orchestration | 1 | ✅ | Routing rules active |
| Business Services | 12 | ✅ | Hierarchy defined |
| Maintenance Windows | 4 | ✅ | Recurring configured |
| Custom Fields | 5 | ✅ | Deployed |

### API-Managed Resources (Not in Terraform)

| Component | ID | Status | Notes |
|-----------|-----|--------|-------|
| Demo Incident Channel Setup Workflow | `PUXIPNC` | ✅ | Created via API |
| [DEMO] Conditional Trigger | `7c33cc98-...` | ✅ | Fires on incident creation |

### AWS Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| **Lambda Function (`demo-simulator-controller`)** | **✅** | **PRIMARY — deployed to us-east-1** |
| Lambda Function (`demo-simulator-orchestrator-v2`) | ✅ | Legacy — deployed to us-east-1 |
| API Gateway (`ynoioelti7`) | ✅ | HTTP frontend for orchestrator (`https://ynoioelti7.execute-api.us-east-1.amazonaws.com`) |
| ~~Lambda Function URLs~~ | ❌ | Return 403 Forbidden (account-level restriction) — do not use |
| DynamoDB Table (`demo-incident-state`) | ✅ | Used by orchestrator only (not controller) |
| EventBridge Scheduler | ✅ | Used by orchestrator only (not controller) |
| IAM Roles (Lambda, Scheduler) | ✅ | Deployed via Terraform |
| CloudWatch Logs | ✅ | Auto-created |
| ~~PagerDuty Generic Webhook~~ | ❌ | Deleted Feb 17 — was non-functional (Function URL returned 403) |

### External Integrations

| Integration | PD Config | Credentials | End-to-End Test |
|-------------|-----------|-------------|-----------------|
| Slack | ✅ | ✅ | ✅ Channel creation via workflow works (Feb 9) |
| Jira Cloud | ✅ | ✅ | ✅ Workflows create tickets |
| Confluence | ⏳ | ⏳ | ⏳ |
| Datadog | ✅ | ✅ | ✅ Fixed Feb 9 (routing key updated) |
| Grafana | 🟡 | ⏳ | ⏳ |
| New Relic | 🟡 | ⏳ | ⏳ |
| Status Page | ✅ | ✅ | ✅ API rewritten Feb 14 (Posts endpoint + object references) |
| ServiceNow | ✅ | ✅ | ✅ Native PD extension, no custom code (Feb 11) |
| AIOps/EIM | ✅ | ✅ | ✅ Enabled, Lambda code deployed and working (Feb 11) |
| RBA/Rundeck | ✅ | ✅ | 🟡 Runner exists, jobs configured, Lambda code ready (Feb 11) |
| Zoom | 🟡 | ⏳ | ⏳ |

---

## RBA Scheduled Jobs

| Job | Purpose | Status |
|-----|---------|--------|
| Metrics Simulator | Generate realistic metrics data | ✅ |
| Log Generator | Create log entries for correlation | ✅ |
| User Activity Simulator | Simulate user actions | ⏳ Needs API tokens |
| Incident Lifecycle Simulator | Auto-progress incidents | ✅ |
| Health Check Monitor | Periodic health checks | ✅ |
| Database Metrics Collector | DB performance metrics | ✅ |
| API Performance Monitor | API latency tracking | ✅ |
| Security Event Generator | Security-related events | ✅ |

---

## Data Flow Diagram

```
EVENT SOURCE                    PAGERDUTY                         ORCHESTRATOR                    OUTPUTS
     │                              │                                  │                              │
     │  1. Alert/Event              │                                  │                              │
     │──────────────────────────────>                                  │                              │
     │                              │                                  │                              │
     │                              │  2. Process via                  │                              │
     │                              │     Event Orchestration          │                              │
     │                              │  3. Create Incident              │                              │
     │                              │  4. Notify Responders            │                              │
     │                              │                                  │                              │
     │                              │  5. Trigger Workflow             │                              │
     │                              │     (if conditions match)        │                              │
     │                              │                                  │                              │
     │                              │  6. Execute Workflow Steps       │                              │
     │                              │     - Create Slack Channel ──────│──────────────────────────────> Slack
     │                              │     - Create Jira Ticket ────────│──────────────────────────────> Jira
     │                              │     - Update Status Page ────────│──────────────────────────────> Status
     │                              │                                  │                              │
     │                              │  7. Send Webhook ────────────────>                              │
     │                              │                                  │                              │
     │                              │                                  │  8. Process Webhook          │
     │                              │                                  │  9. Invite to Slack ─────────> Slack
     │                              │                                  │  10. Post Messages ──────────> Slack
     │                              │                                  │  11. Schedule Actions         │
     │                              │                                  │                              │
     │                              │                                  │  12. Execute Scheduled       │
     │                              │                                  │      - Acknowledge ──────────> PagerDuty
     │                              │                                  │      - Add Note ─────────────> PagerDuty
     │                              │                                  │      - Resolve ──────────────> PagerDuty
     │                              │                                  │                              │
```

---

## Deployment Phases

### Phase 0: Pre-flight ✅
- [x] Verify PagerDuty API token
- [x] Verify Slack integration
- [x] Verify Jira integration
- [x] Confirm add-on availability

### Phase 1: Terraform Foundation ✅
- [x] Deploy services
- [x] Deploy schedules
- [x] Deploy escalation policies
- [x] Deploy automation actions
- [x] Deploy business services
- [x] Deploy workflow shells
- [x] Deploy workflow triggers

### Phase 2: Workflow Steps 🟡
- [x] Run `populate_workflow_steps.py` for most workflows
- [ ] Verify all steps in PD UI
- [x] Create "Demo Incident Channel Setup" workflow via API (ID: PUXIPNC)
- [x] Create [DEMO] conditional trigger via API

### Phase 3: AWS Orchestrator ✅
- [x] Create DynamoDB table (`demo-incident-state`)
- [x] Deploy Lambda function (`demo-orchestrator`)
- [x] ~~Configure Lambda Function URL (webhook endpoint)~~ — Function URLs return 403 (account restriction); API Gateway used instead
- [x] Configure EventBridge Scheduler
- [x] ~~Set up PD webhooks (Generic Webhooks V3)~~ — Webhook deleted Feb 17 (was non-functional)
- [x] Configure environment variables (SELF_LAMBDA_ARN, SCHEDULER_ROLE_ARN)

### Phase 4: Integration Setup ✅
- [x] Create Jira projects (SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA) — all exist
- [ ] Create Confluence space (RUNBOOKS) — deferred, not needed for demo
- [x] Configure monitoring credentials (Datadog) — fixed Feb 9
- [x] Slack integration working via conference bridge approach
- [ ] Grafana credentials — configured but not E2E tested
- [ ] New Relic credentials — configured but not E2E tested

### Phase 5: Testing 🟡
- [x] Webhook signature verification tested
- [x] incident.workflow.completed event handling tested
- [x] E2E database scenario validated (Feb 9)
- [x] Full end-to-end scenario tests — 47/47 enabled scenarios passing (Feb 14, 2026)
- [x] Slack channel population verification (Feb 12 — bot joins, invites observers)
- [x] Jira ticket verification (6 workflows working)
- [ ] Automation action verification

### Phase 6: Real PagerDuty Feature Integration ✅ (Feb 11-12, 2026)
- [x] AIOps/EIM enabled in account
- [x] AIOps API methods added to Lambda code (get_past_incidents, get_related_incidents)
- [x] Status Page API methods added (list_status_pages, create_status_incident, update_status_component)
- [x] RBA/Automation Actions API methods added (list_automation_actions, invoke_automation_action)
- [x] ServiceNow connected via native PagerDuty extension (no custom code)
- [x] New action types added: aiops_correlate, status_page_update, invoke_rba
- [x] Feature flags enabled: enable_status_page_updates, status_pages, aiops
- [x] Status Page API validation — rewritten Feb 14 with correct Posts endpoint and object-reference payloads
- [x] Deploy updated Lambda code to AWS (deployed Feb 12 via direct CLI)
- [x] E2E test 6 scenarios: FREE-001, FREE-002, PRO-002, BUS-003, DIGOPS-001, AIOPS-001
- [x] E2E test remaining scenarios — All 47 enabled scenarios validated (Feb 14, 2026) via `scripts/test_all_scenarios.py`

### Phase 7: Demo Controller Architecture ✅ (Feb 12, 2026)
- [x] demo-simulator-controller Lambda deployed as self-contained scenario runner
- [x] Slack channel discovery via conference_bridge polling
- [x] Bot self-join before inviting users
- [x] Observer auto-invite (conalllynch88@gmail.com)
- [x] Phased action flow: investigating → found_issue → working_fix → resolved
- [x] User-impersonated Slack messages with conversation library
- [x] Configurable timing (30-60s default, overridable via action_delay)
- [x] 47 enabled scenarios E2E validated with 100% pass rate (Feb 14, 2026)

---

## Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `provider.tf` | Terraform provider config | ✅ |
| `backend.tf` | State backend config | ✅ |
| `terraform.tfvars` | Variable values | 🟡 Sensitive |
| `aws/terraform.tfvars` | AWS-specific variables | 🟡 Sensitive |
| `aws/main.tf` | AWS Lambda + infrastructure config | ✅ |
| `aws/demo_orchestrator.tf` | Legacy orchestrator config | ✅ |
| `docs/demo-scenarios/src/data/scenarios.json` | 66 demo scenario definitions | ✅ |
| `events/samples/*.json` | Event payloads | ✅ |

---

## Change Log

| Date | Component | Change Type | Description |
|------|-----------|-------------|-------------|
| 2026-02-14 | Status Page | ✅ COMPLETED | Status Page API rewritten with correct Posts endpoint and object-reference payloads |
| 2026-02-14 | Slack | ✅ COMPLETED | Channel invite fix (one-by-one), observer accounts explicitly invited |
| 2026-02-14 | Datadog | ✅ COMPLETED | Graceful degradation for expired Datadog trial across all Lambdas |
| 2026-02-14 | Scripts | ⚡ ALTERED | 6 single-use scripts archived (check_progress, check_routing, add_tier_data, etc.) |
| 2026-02-14 | Documentation | ✅ COMPLETED | All docs audited and updated for accuracy |
| 2026-02-14 | Testing | ✅ COMPLETED | All 47 enabled scenarios E2E validated via test_all_scenarios.py, dashboard updated |
| 2026-02-12 | Lambda Code | ✅ COMPLETED | demo-simulator-controller deployed, initial 6 scenarios E2E validated |
| 2026-02-12 | Slack | ✅ COMPLETED | Bot self-join, observer invite, conference_bridge channel discovery |
| 2026-02-12 | Architecture | ⚡ ALTERED | Controller replaces webhook-driven orchestrator as primary runner |
| 2026-02-12 | Scripts | ⚡ ALTERED | test_demo_logic.py moved to archive |
| 2026-02-11 | Lambda Code | ✅ COMPLETED | AIOps, Status Page, RBA action types added to controller + orchestrator |
| 2026-02-11 | Integration | ✅ COMPLETED | ServiceNow connected via native PD extension |
| 2026-02-11 | Integration | ✅ COMPLETED | Status Page API integration (rewritten Feb 14 with correct endpoints) |
| 2026-02-11 | Lambda Code | ✅ COMPLETED | PagerDutyClient expanded with AIOps/StatusPage/RBA methods |
| 2026-02-11 | Feature Flags | ✅ COMPLETED | status_pages, aiops, enable_status_page_updates enabled |
| 2026-02-11 | Scripts | ⚡ ALTERED | Obsolete scripts moved to archive directories |
| 2026-02-09 | E2E | ✅ COMPLETED | Full pipeline validated: Event→Routing→Service→Workflow→Slack |
| 2026-02-09 | Datadog | ✅ COMPLETED | Monitors and routing key fixed |
| 2026-02-07 | AWS Lambda | ✅ COMPLETED | demo-orchestrator Lambda deployed |
| 2026-02-07 | Workflow | ➕ ADDITION | "Demo Incident Channel Setup" workflow via API |
| 2026-02-07 | Integration | ⚡ ALTERED | Slack channels via PD workflow + conference bridge |
| 2026-02-06 | Documentation | ➕ ADDITION | Created architecture blueprint |
| 2026-02-05 | Services | ✅ COMPLETED | All 30+ services deployed |
| 2026-02-05 | Automation | ✅ COMPLETED | 20+ actions deployed |

---

## Future Enhancements

| Enhancement | Priority | Status | Notes |
|-------------|----------|--------|-------|
| ~~E2E validate remaining 60 scenarios~~ | ~~High~~ | ✅ DONE | 47/47 enabled scenarios validated (Feb 14). 19 disabled pending external integrations. |
| ~~Status Page API enum fix~~ | ~~High~~ | ✅ DONE | API rewritten Feb 14 with correct Posts endpoint and object-reference payloads |
| ~~Webhook signature verification~~ | ~~Low~~ | 🚫 OBSOLETE | PD webhook subscription (PILGGJ0) deleted Feb 17. Controller doesn't use webhooks. |
| Enable 19 disabled scenarios | Medium | ⏳ | Require external integration setup (ServiceNow, Grafana, UptimeRobot, etc.) |
| Multi-scenario orchestration / playlists | Medium | ⏳ | Run curated sets of scenarios for specific audiences |
| RBA runbook content | Medium | ⏳ | Runner exists, need meaningful script content |
| Fix Terraform Lambda code detection | Low | ⏳ | Terraform doesn't reliably detect source changes |
| AIOps full configuration | Low | ⏳ | Alert Grouping, Suppression require AIOps/EIM add-on tier |
| Jeli integration | Low | ⏳ | Post-incident learning |
| SRE Agent integration | Low | ⏳ | AI-powered assistance |
| Multi-region support | Low | ⏳ | Disaster recovery demo |
