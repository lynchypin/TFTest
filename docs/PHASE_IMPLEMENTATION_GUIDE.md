# PagerDuty Demo Environment - Phased Implementation Guide

> **Created:** February 8, 2026
> **Last Updated:** February 18, 2026
> **Purpose:** Master implementation plan for wiring all 70 demo scenarios with build-test-integrate methodology
> **Audience:** Developers continuing implementation of the demo environment
> **Status:** Phases 0-10 COMPLETED. Controller Lambda is primary execution path. 51/70 scenarios enabled and validated. 19 disabled pending external integrations. Remaining work: AIOps/EIM (requires license), RBA runbook content, 19 disabled scenarios (require external integrations).

---

## Executive Summary

This document provides a comprehensive, phased approach to completing the PagerDuty demo environment. The implementation follows a strict **Build → Test → Integrate** methodology where each component is verified in isolation before being connected to the main system.

### Project Goal

Create a fully automated demo environment where:
- 66 scenarios trigger appropriate PagerDuty incidents
- Events route to correct services via Global/Service Event Orchestration
- Demo orchestrator Lambda manages the incident lifecycle
- Observers (presenters) can watch and pause the demo in Slack
- Responders simulate realistic investigation conversations
- Incidents resolve automatically with configurable timing

### Key Constraints

- **No Breaking Changes**: All development happens in isolation until verified
- **Pause Support**: Presenter can pause demo progression at any time
- **Observer Access**: Both `conalllynch88@gmail.com` and `clynch@pagerduty.com` added to all Slack channels
- **Demo-Only Processing**: Only incidents with `[DEMO]` prefix are processed

---

## Current State (February 9, 2026)

### PHASE 0 STATUS: COMPLETED

**E2E Flow Validated on February 9, 2026:**
- Event sent to Global Orchestration routing key
- Routed to "Database Reliability" service (via `class: database`, `component: redis`)
- Workflow fired automatically (condition: `incident.title matches part '[DEMO]'`)
- Slack channel created: `#demo-314-demo-e2e-workflow-`
- Conference bridge populated with Slack channel URL
- Arthur Guinness acknowledged the incident
- Auto-resolve scheduled for 4 hours

### Resolved Issues

| Issue | Root Cause | Resolution | Date |
|-------|------------|------------|------|
| Auto-acknowledgment not working | Demo users had "observer" role | Changed all demo users to "responder" (limited_user) role | Feb 8 |
| Users not added to Slack channels | `conversations.invite` batch failing silently | Modified to invite users one-by-one | Feb 8 |
| Datadog monitors wrong service | Monitors sent to `@pagerduty-Los-Andes-Demo` | Updated to `@pagerduty-demo-simulator-alerts` + updated integration routing key | Feb 9 |
| Workflow trigger not firing | PagerDuty UI configuration issue | User fixed trigger in PagerDuty web UI | Feb 9 |

### CRITICAL DISCOVERY: Event Routing Requirements

**Events MUST include specific fields to route correctly through Global Event Orchestration.**

The 12 routing rules check `event.class`, `event.component`, and `event.custom_details.*` fields - NOT the event `summary` text.

**Routing Rules Summary:**
| Rule | Route To | Required Fields |
|------|----------|-----------------|
| Database events | Platform DBRE | `component`: mysql/postgres/redis/mongodb/cassandra OR `class`: *database* |
| Kubernetes events | Platform K8s | `source`: kubernetes/k8s/container/docker/prometheus |
| Network events | Platform Network | `class`: network* OR `summary`: connectivity/latency/packet loss |
| Security events | Security Monitoring | `class`: security* OR `custom_details.security_classification` exists |
| Payment events | Payments Ops | `custom_details.domain`: payments OR `class`: *payment* |
| Checkout events | App Checkout | `custom_details.service`: checkout/cart |
| Order events | App Orders | `custom_details.service`: order/fulfillment/inventory |
| Identity events | App Identity | `custom_details.service`: identity/auth/sso/login |
| Streaming events | Data Streaming | `custom_details.service`: streaming/kafka/kinesis/pubsub |
| Analytics events | Data Analytics | `custom_details.service`: analytics/warehouse/bigquery/snowflake/redshift |
| Default | Default Service - Unrouted Events | No match (catch-all) |

**Working E2E Test Command:**
```bash
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[DEMO] E2E Workflow Test - Redis cache eviction storm",
      "source": "demo-e2e-test",
      "severity": "critical",
      "class": "database",
      "component": "redis"
    }
  }'
```

### Infrastructure Inventory

| Component | Count | Status |
|-----------|-------|--------|
| PagerDuty Services | 34 | Deployed |
| Event Orchestration Rules | 12 | Active (routes by class/component/custom_details) |
| Incident Workflows | 25 | Deployed with steps |
| Workflow Triggers | 38 | Active |
| Lambda Functions | 9 | Running |
| Datadog Monitors | 14 | Fixed (Feb 9) |
| Demo Scenarios | 66 | Defined in scenarios.json |

### Key Identifiers

| Resource | ID/Value |
|----------|----------|
| Event Orchestration Routing Key | `R028NMN4RMUJEARZ18IJURLOU1VWQ779` |
| Observer Slack ID (conalllynch88@gmail.com) | `U0A9GBYT999` |
| Observer Slack ID (clynch@pagerduty.com) | `U0A9KAMT0BF` |
| Demo Orchestrator Lambda | `demo-simulator-orchestrator-v2` |
| Datadog Service Name | `demo-simulator-alerts` |
| Demo Incident Channel Setup Workflow | `PUXIPNC` |
| Workflow Trigger ID | `8189137e-21ad-46cc-88d4-e70834a33b88` |

---

## Implementation Phases

### Phase 0: Prerequisites - COMPLETED (February 9, 2026)

**Tasks Completed:**
1. ~~Fix Datadog monitors to use correct service name~~ DONE
2. ~~Verify all demo users have "responder" role~~ DONE (6 users verified)
3. ~~Confirm webhook subscription is enabled~~ DONE *(Note: Webhook later deleted Feb 17 — controller doesn't use webhooks)*
4. ~~Test one scenario end-to-end manually~~ DONE (Incident Q2EE76G7QQE3UX)

**Validated E2E Flow:**
```
Event (with class/component) -> Global Orchestration -> Service Routing ->
Workflow Fires -> Slack Channel Created -> Responder Acknowledges -> Auto-resolve Scheduled
```

---

### Phase 1: Datadog Integration Fix - COMPLETED (February 9, 2026)

**Goal:** Fix Datadog monitors to correctly trigger PagerDuty incidents

**Resolution:**
1. Updated monitors 17717886 and 17717887 to use `@pagerduty-demo-simulator-alerts`
2. Updated Datadog PagerDuty integration routing key to `R028NMN4RMUJEARZ18IJURLOU1VWQ779`

**Verification:**
```bash
curl -s "https://api.us5.datadoghq.com/api/v1/integration/pagerduty" \
  -H "DD-API-KEY: $DATADOG_API_KEY" \
  -H "DD-APPLICATION-KEY: $DATADOG_APP_KEY"
```

---

### ~~Phase 1.5: Workflow Failure Investigation~~ RESOLVED (February 14, 2026)

> **Status:** RESOLVED — All workflows validated. 47/47 enabled scenarios pass E2E.
> **Original Priority:** CRITICAL
> **Resolution:** Workflow failures were caused by multiple root causes (API token role, Slack Enterprise Grid `team_id`, channel pattern mismatch) all fixed Feb 9-10. The controller Lambda architecture (Feb 12) eliminated webhook dependency entirely. Full E2E validation completed Feb 14.

**Original Problem:** Many PagerDuty Incident Workflows and their steps were failing silently.

**Root Causes Found & Fixed:**

| Error | Cause | Fix | Date |
|-------|-------|-----|------|
| Workflows not triggering | PagerDuty UI config issue | User fixed trigger in PD web UI | Feb 9 |
| Slack channels not created | Enterprise Grid requires `team_id` | Added `SLACK_TEAM_ID=T0A9LN53CPQ` | Feb 9 |
| Conference bridge not populated | Channel pattern mismatch (`inc-*` vs `demo-*`) | Fixed search pattern | Feb 9 |
| Acknowledgment failures | API token was `limited_user` role | Upgraded to admin token | Feb 10 |
| Webhook delivery failures | Lambda Function URLs return 403 | Replaced with controller polling (no webhooks) | Feb 12 |

**Validation:** All steps in "Demo Incident Channel Setup" (PUXIPNC) complete successfully. 47 enabled scenarios E2E validated via `scripts/test_all_scenarios.py` (Feb 14).

---

### Phase 2: Global Event Orchestration Expansion

**Goal:** Route all 66 scenarios to correct services

**Current State:** 12 rules exist (priority/severity assignment only)
**Target State:** ~70 rules (one per scenario + category fallbacks + catch-all)

**Source of Truth:** `docs/demo-scenarios/src/data/scenarios.json`

**Rule Structure:**

```
Priority 1: Exact scenario_id matching (66 rules)
Priority 2: Integration source matching (10 rules)
Priority 3: Category pattern matching (8 rules)
Priority 4: Catch-all for [DEMO] events (1 rule)
```

**Steps:**

1. **Extract scenario-to-service mapping:**
   ```python
   import json
   scenarios = json.load(open('docs/demo-scenarios/src/data/scenarios.json'))['scenarios']
   for s in scenarios:
       print(f"{s['id']} -> {s.get('target_service', 'UNMAPPED')}")
   ```

2. **Create Terraform rules in `global_orchestration.tf`:**
   ```hcl
   # Example rule for FREE-001
   set {
     id = "FREE-001-routing"
     rule {
       label = "FREE-001: Simple Alert Routing"
       condition {
         expression = "event.custom_details.scenario_id matches part 'FREE-001'"
       }
       actions {
         route_to = pagerduty_service.platform_kubernetes.id
         priority = null  # No priority for FREE tier
       }
     }
   }
   ```

3. **Service mapping for missing services:**
   | Scenario Target | Maps To Existing Service |
   |-----------------|--------------------------|
   | Clinical Systems - EMR | Support |
   | Mining Operations - Equipment | Support |
   | OT Operations - Factory Floor | Support |
   | Grid Operations Center | Support |
   | Retail Systems - POS | Checkout Service |

4. **Testing methodology:**
   - Deploy rules to staging branch (not production)
   - Test each scenario category with one representative event
   - Verify routing in PagerDuty incident details

**Important:** Do NOT deploy to production until all rules are tested

---

### Phase 3: Service-Level Orchestrations

**Goal:** Create service-specific rules for 5 key services to demonstrate advanced features

**Services to configure:**

1. **Platform - Kubernetes/Platform**
   - Features: alert_grouping, suppression, threshold_conditions
   - Rules: Group similar alerts, suppress transient issues

2. **Database Reliability**
   - Features: diagnostic_gathering, incident_enrichment
   - Rules: Add database metrics to incident, trigger runbooks

3. **Payments Platform**
   - Features: priority_assignment, business_services
   - Rules: Auto-escalate payment failures to P1

4. **Security Operations**
   - Features: incident_roles, severity-based routing
   - Rules: Assign security analyst role, route by CVE severity

5. **Checkout Service**
   - Features: stakeholder_notifications, status_pages
   - Rules: Notify business stakeholders on checkout failures

**Steps:**

1. **Create service orchestration in Terraform:**
   ```hcl
   resource "pagerduty_service_event_rule" "kubernetes_grouping" {
     service  = pagerduty_service.platform_kubernetes.id
     position = 0
     
     conditions {
       operator = "and"
       subconditions {
         operator = "contains"
         parameter {
           value = "pod"
           path  = "payload.summary"
         }
       }
     }
     
     actions {
       alert_grouping {
         type    = "intelligent"
         timeout = 300
       }
     }
   }
   ```

2. **Test each service orchestration in isolation**

3. **Document demonstrated features for each service**

---

### Phase 4: Lambda Enhancements

**Goal:** Add observer invites, responder chat simulation, and pause functionality

#### 4.1 Observer Invites

**Requirement:** Add both observer emails to every demo Slack channel

**Implementation location:** `aws/lambda-demo-orchestrator/handler.py`

**Logic:**
```
OBSERVER_SLACK_IDS = ["U0A9GBYT999", "U0A9KAMT0BF"]

def on_workflow_completed(event):
    channel_id = extract_channel_id(event)
    
    # Invite all responders (existing logic)
    for responder in responders:
        invite_user(channel_id, responder.slack_id)
    
    # NEW: Invite observers
    for observer_id in OBSERVER_SLACK_IDS:
        try:
            slack.conversations_invite(channel=channel_id, users=observer_id)
        except SlackApiError as e:
            if "already_in_channel" not in str(e):
                logger.warning(f"Could not add observer {observer_id}: {e}")
```

#### 4.2 Responder Chat Simulation

**Requirement:** Post realistic responder messages every 30-60 seconds

**Chat message templates by scenario category:**

| Category | Investigation | Progress | Resolution |
|----------|--------------|----------|------------|
| database | "Checking connection pool stats..." | "Found problematic query..." | "Index applied, latency normal" |
| kubernetes | "Checking pod status and logs..." | "Found OOMKilled pods, scaling..." | "All pods healthy" |
| payment | "Checking transaction logs..." | "Found failed auth with gateway..." | "Gateway connection restored" |
| security | "Analyzing security logs..." | "Identified suspicious IP range..." | "IPs blocked, monitoring" |
| network | "Running traceroute diagnostics..." | "Found packet loss at router..." | "Traffic rerouted successfully" |
| default | "Looking into this now..." | "Found the issue, working on fix..." | "Fixed and monitoring" |

**Scheduling logic:**
```
Timeline (from incident trigger):
+30-60s:   Acknowledge + first message ("Looking into this now")
+60-90s:   Investigation message
+90-120s:  Progress message
+120-150s: Near-resolution message
+150-180s: Resolution summary
+180-240s: Resolve incident
```

#### 4.3 Pause/Resume Functionality

**Requirement:** Allow presenter to pause all automated actions

**State storage:** DynamoDB table `demo-state`

**Pause flow:**
1. Presenter calls `POST /pause` endpoint
2. Lambda sets `paused: true` in DynamoDB for current incident
3. All scheduled actions check pause state before executing
4. If paused, action is skipped (not rescheduled)

**Resume flow:**
1. Presenter calls `POST /resume` endpoint
2. Lambda sets `paused: false` in DynamoDB
3. Next scheduled action executes normally
4. Remaining timeline continues from where it left off

**Pause timeout:**
- If paused > 15 minutes, auto-resolve incident
- Prevents orphaned demo incidents

**Implementation:**
```python
def check_pause_state(incident_id):
    item = dynamodb.get_item(Key={'incident_id': incident_id})
    return item.get('Item', {}).get('paused', False)

def execute_scheduled_action(event):
    incident_id = event['incident_id']
    action = event['action']
    
    if check_pause_state(incident_id):
        logger.info(f"Demo paused, skipping action: {action}")
        return
    
    # Execute the action
    ...
```

---

### Phase 5: Integration Testing

**Goal:** Verify complete flow for all scenario categories

**Test matrix:**

| Tier | Count | Representative Scenario | Test Status |
|------|-------|------------------------|-------------|
| FREE | 2 | FREE-001 | ⬜ |
| PRO | 3 | PRO-001 | ⬜ |
| BUS | 5 | BUS-002 | ⬜ |
| EIM | 5 | EIM-001 | ⬜ |
| AIOPS | 4 | AIOPS-001 | ⬜ |
| DIGOPS | 7 | DIGOPS-001 | ⬜ |
| SRE | 6 | SRE-001 | ⬜ |
| IND | 13 | IND-001 | ⬜ |
| WF | 3 | WF-001 | ⬜ |
| RBA | 4 | RBA-001 | ⬜ |
| SCRIBE | 3 | SCRIBE-001 | ⬜ |
| SHIFT | 3 | SHIFT-001 | ⬜ |
| AUTO | 3 | AUTO-001 | ⬜ |
| AA | 3 | AA-001 | ⬜ |
| CSO | 1 | CSO-001 | ⬜ |
| COMBO | 1 | COMBO-001 | ⬜ |

**For each test:**
1. Trigger scenario via API
2. Verify service routing (check incident details)
3. Verify Slack channel created
4. Verify observers added
5. Verify responder messages appear
6. Test pause/resume
7. Verify resolution

---

### Phase 6: Production Deployment

**Goal:** Deploy verified code to production Lambda

**Pre-deployment checklist:**
- [ ] All 16 scenario categories tested
- [ ] Pause/resume verified
- [ ] Observer invites working
- [ ] Responder chat messages realistic
- [ ] Resolution timing appropriate (3-5 min default)
- [ ] Datadog monitors fixed
- [ ] No regressions in existing functionality

**Deployment steps:**

1. **Create deployment package:**
   ```bash
   cd aws/lambda-demo-orchestrator
   pip install -r requirements.txt -t ./package/
   cp handler.py ./package/
   cd package && zip -r ../deployment.zip .
   ```

2. **Deploy to Lambda:**
   ```bash
   aws lambda update-function-code \
     --function-name demo-simulator-orchestrator-v2 \
     --zip-file fileb://deployment.zip
   ```

3. **Update environment variables if needed:**
   ```bash
   aws lambda update-function-configuration \
     --function-name demo-simulator-orchestrator-v2 \
     --environment "Variables={...}"
   ```

4. **Verify deployment:**
   - Trigger test incident
   - Check CloudWatch logs
   - Verify Slack activity

---

## Build → Test → Integrate Methodology

### Principle

Every component must be verified in isolation before connecting to the main system.

### Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. BUILD (Local/Staging)                                                   │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ • Write code in feature branch                                        │  │
│   │ • Use mock data and test fixtures                                     │  │
│   │ • No connection to production services                                │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   2. TEST (Isolated)                                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ • Unit tests for new functions                                        │  │
│   │ • Integration tests with test PagerDuty/Slack (if available)         │  │
│   │ • Manual verification of expected behavior                            │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   3. INTEGRATE (Production)                                                  │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ • Deploy to production Lambda                                         │  │
│   │ • Run E2E test with real incident                                     │  │
│   │ • Monitor CloudWatch logs for errors                                  │  │
│   │ • Verify Slack channel activity                                       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Rollback Plan

If deployment causes issues:

1. **Immediate:** Revert Lambda to previous version (webhook subscription no longer exists — deleted Feb 17)
2. **Short-term:** Revert Lambda to previous version
   ```bash
   aws lambda update-function-code \
     --function-name demo-simulator-orchestrator-v2 \
     --s3-bucket lambda-deployments \
     --s3-key previous-version.zip
   ```
3. **Investigation:** Check CloudWatch logs for error patterns

---

## Slack Integration Workflow - Complete Guide

This section documents **every step** that happens with Slack when a demo incident is triggered, including the PagerDuty workflow configuration, Lambda processing, and troubleshooting.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        SLACK INTEGRATION ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   PagerDuty                          AWS Lambda                      Slack               │
│   ┌──────────────────┐              ┌──────────────────┐            ┌──────────────────┐│
│   │ Incident Created │              │ demo-orchestrator │            │ Los Andes        ││
│   │ (with [DEMO])    │──webhook──▶  │ Lambda           │───API────▶ │ Workspace        ││
│   └────────┬─────────┘              └──────────────────┘            └──────────────────┘│
│            │                                                                             │
│            ▼                                                                             │
│   ┌──────────────────┐                                                                   │
│   │ Incident Workflow│                                                                   │
│   │ (creates channel)│───────────────────────────────────────────────────────────────▶   │
│   └──────────────────┘                                                                   │
│                                                                                          │
│   NOTE: Channel is created by PagerDuty's native Slack integration, NOT by Lambda       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### PagerDuty Incident Workflow: "Demo Incident Channel Setup"

**Workflow ID:** `PUXIPNC`
**Trigger Condition:** Incident title contains `[DEMO]`

**Workflow Steps (in order):**

| Step | Action | Configuration |
|------|--------|---------------|
| 1 | Create Slack Channel | Workspace: `T0A9LN53CPQ`, Name: `demo-{incident_number}` |
| 2 | Add Conference Bridge | Type: URL, Value: Slack channel URL |
| 3 | Post to Channel | Initial incident details message |
| 4 | Add Incident Note | "Slack channel created for incident coordination" |

**Why This Configuration:**
- Lambda cannot create Slack channels (missing `channels:write` scope)
- PagerDuty's native Slack integration CAN create channels
- Conference Bridge field stores channel URL for Lambda to retrieve later
- This is a documented workaround, not a bug

### Step-by-Step: What Happens Every Time

#### Step 1: Incident Creation (Time 0)

**Trigger:** Event sent to PagerDuty Events API with `[DEMO]` in summary

```bash
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[DEMO] Database connection pool exhausted",
      "severity": "critical",
      "source": "monitoring-system",
      "custom_details": {
        "scenario_id": "BUS-002",
        "category": "database"
      }
    }
  }'
```

**What Happens:**
1. Event received by PagerDuty
2. Global Event Orchestration routes to correct service
3. Incident created in triggered state
4. On-call user assigned from schedule

#### Step 2: Workflow Execution (Time 0-10s)

**Trigger:** Workflow trigger condition matches (`[DEMO]` in title)

**What Happens:**
1. Workflow "Demo Incident Channel Setup" starts
2. **Step 1:** PagerDuty calls Slack API to create channel `demo-{incident_number}`
3. **Step 2:** Channel URL stored in `incident.conference_bridge.url`
4. **Step 3:** Initial message posted to channel
5. **Step 4:** Note added to incident timeline
6. Workflow completes
7. PagerDuty sends `incident.workflow.completed` webhook

#### Step 3: Lambda Processes Webhook (Time 10-15s)

**Trigger:** `incident.workflow.completed` webhook received

**What Happens in Lambda:**

```python
def on_workflow_completed(event):
    incident = event['data']['incident']

    # 1. Extract Slack channel URL from conference bridge
    channel_url = incident.get('conference_bridge', {}).get('url', '')
    # URL format: https://losandesgaa.slack.com/archives/C0XXXXXXX

    # 2. Parse channel ID from URL
    channel_id = channel_url.split('/archives/')[-1] if '/archives/' in channel_url else None

    # 3. Get list of responders to invite
    responders = get_incident_responders(incident['id'])

    # 4. Invite responders one-by-one
    for responder in responders:
        try:
            slack.conversations_invite(channel=channel_id, users=responder.slack_id)
        except SlackApiError as e:
            if "already_in_channel" not in str(e):
                logger.warning(f"Could not invite {responder.email}: {e}")

    # 5. Invite observers (CRITICAL - both presenter emails)
    OBSERVER_SLACK_IDS = ["U0A9GBYT999", "U0A9KAMT0BF"]
    for observer_id in OBSERVER_SLACK_IDS:
        try:
            slack.conversations_invite(channel=channel_id, users=observer_id)
        except SlackApiError as e:
            if "already_in_channel" not in str(e):
                logger.warning(f"Could not add observer {observer_id}: {e}")

    # 6. Post welcome message as responder
    responder = responders[0]
    slack.post_as_user(
        channel=channel_id,
        user_id=responder.slack_id,
        text="I'm looking into this now. Will update shortly."
    )
```

#### Step 4: Auto-Acknowledge (Time 30-60s)

**Trigger:** EventBridge Scheduler invokes Lambda

**What Happens:**
1. Lambda receives scheduled action
2. Checks if incident still in triggered state
3. Calls PagerDuty API to acknowledge:
   ```python
   requests.put(
       f"https://api.pagerduty.com/incidents/{incident_id}",
       headers={"From": responder_email, "Authorization": f"Token token={token}"},
       json={"incident": {"type": "incident", "status": "acknowledged"}}
   )
   ```
4. Posts acknowledgment message to Slack channel

#### Step 5: Investigation Messages (Time 60-180s)

**Trigger:** Scheduled actions at intervals

**What Happens:**
- Multiple responder messages posted to channel
- Messages selected based on scenario category (database, network, memory, CPU)
- Each message posted with responder's name and avatar

**Example Messages by Category:**

| Category | Message |
|----------|---------|
| database | "Checking connection pool stats on the primary replica..." |
| network | "Running traceroute to identify where the latency spike is coming from..." |
| memory | "Heap dump shows HashMap objects consuming 2GB of memory..." |
| kubernetes | "Checking pod status across all nodes in the cluster..." |
| default | "Investigating the issue now, pulling up logs and metrics..." |

#### Step 6: Resolution (Time 180-300s)

**Trigger:** Final scheduled action

**What Happens:**
1. Resolution message posted to Slack
2. Incident status changed to resolved:
   ```python
   requests.put(
       f"https://api.pagerduty.com/incidents/{incident_id}",
       headers={"From": responder_email, "Authorization": f"Token token={token}"},
       json={"incident": {"type": "incident", "status": "resolved"}}
   )
   ```
3. Final summary note added to incident
4. DynamoDB state cleaned up

### Slack Bot Token Scopes Required

| Scope | Purpose | Required For |
|-------|---------|--------------|
| `chat:write` | Post messages to channels | All messages |
| `channels:read` | Read channel info | Verifying channel exists |
| `users:read` | Get user profiles | User impersonation (name/avatar) |
| `channels:manage` | Invite users to channels | Adding responders/observers |

**Current Token:** See `docs/CREDENTIALS_REFERENCE.md` (stored in Lambda env vars as `SLACK_BOT_TOKEN`)

### Troubleshooting Slack Issues

#### Issue: Channel Not Created

**Symptoms:** No Slack channel appears after incident triggered

**Debug Steps:**
1. Verify incident title contains `[DEMO]` (case-sensitive)
2. Check workflow run history in PagerDuty:
   - Navigate to **Automation → Incident Workflows → Run History**
   - Look for errors in "Demo Incident Channel Setup"
3. Verify Slack Workspace ID matches `T0A9LN53CPQ`
4. Check PagerDuty's Slack integration is connected:
   - **Integrations → Extensions → Slack**

#### Issue: Observers Not Added to Channel

**Symptoms:** Channel exists but observers not invited

**Debug Steps:**
1. Check CloudWatch logs for `ON_WORKFLOW_COMPLETED` handler
2. Look for `conversations.invite` errors
3. Verify observer Slack IDs are correct:
   - `U0A9GBYT999` (conalllynch88@gmail.com)
   - `U0A9KAMT0BF` (clynch@pagerduty.com)
4. Check if `conference_bridge.url` was set:
   ```bash
   curl -s "https://api.pagerduty.com/incidents/{ID}" \
     -H "Authorization: Token token=$PD_TOKEN" | jq '.incident.conference_bridge'
   ```

#### Issue: Messages Not Appearing in Channel

**Symptoms:** Channel created, users invited, but no messages

**Debug Steps:**
1. Check CloudWatch logs for Slack API errors
2. Verify `SLACK_BOT_TOKEN` env var in Lambda
3. Test token directly:
   ```bash
   curl -s "https://slack.com/api/auth.test" \
     -H "Authorization: Bearer $SLACK_BOT_TOKEN" | jq '.ok'
   ```
4. Verify bot is a member of the channel

#### Issue: User Impersonation Not Working

**Symptoms:** Messages appear but show bot name, not responder name

**Debug Steps:**
1. Check `users.info` API is returning profile data
2. Verify `chat.postMessage` includes `username` and `icon_url` params
3. Note: Messages will still show "APP" badge (Slack limitation)

### Verifying Slack Integration

**Quick Verification Test:**

```bash
# 1. Trigger test incident
./scripts/trigger_demo_incident.sh

# 2. Wait 15 seconds

# 3. Check PagerDuty for incident
curl -s "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged" \
  -H "Authorization: Token token=$PD_TOKEN" | jq '.incidents[0] | {id, title, conference_bridge}'

# 4. Verify channel URL is present in conference_bridge.url

# 5. Check Slack channel exists
curl -s "https://slack.com/api/conversations.list?types=public_channel&limit=10" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" | jq '.channels[] | select(.name | startswith("demo-"))'

# 6. Check channel members
CHANNEL_ID="C0XXXXXXX"
curl -s "https://slack.com/api/conversations.members?channel=$CHANNEL_ID" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" | jq '.members'
```

### PagerDuty Workflow API Reference

**Creating Workflow Steps via API:**

The workflow must be configured with these exact action IDs:

| Action | ID | Version |
|--------|-----|---------|
| Create Slack Channel | `pagerduty.com:slack:create-a-channel:4` | 4 |
| Add Conference Bridge | `pagerduty.com:incident-workflows:add-conference-bridge:1` | 1 |
| Post to Channel | `pagerduty.com:slack:send-message-to-channel:2` | 2 |
| Add Incident Note | `pagerduty.com:incident-workflows:add-notes-to-incident:1` | 1 |

**Script to Populate Workflow Steps:** `scripts/populate_workflow_steps.py`

**When to Re-run:**
- After creating new workflow via Terraform (creates empty shell)
- After workflow action versions are updated by PagerDuty
- If workflow steps are accidentally deleted

---

## Workarounds and Gotchas Reference

See `docs/GOTCHAS_AND_WORKAROUNDS.md` for detailed workaround examples.

### Key Issues to Be Aware Of

1. **Terraform cannot create workflow steps** - Use API script `scripts/populate_workflow_steps.py`

2. **Demo users need "responder" role** - "observer" role cannot acknowledge incidents

3. **Slack invite must be one-by-one** - Batch invites fail silently for some users

4. **Datadog monitors use wrong service name** - Fix before testing Datadog flow

5. **Two Lambda versions exist** - Use `demo-simulator-orchestrator-v2` (Terraform-managed)

6. **Webhook can be disabled** - Check PagerDuty webhook subscription if Lambda not triggering

---

## Scenario Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEMO SCENARIO FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   TRIGGER (API or Datadog)                                                   │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ POST to Events API with scenario_id in custom_details                 │  │
│   │ routing_key: R028NMN4RMUJEARZ18IJURLOU1VWQ779                        │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   GLOBAL EVENT ORCHESTRATION                                                 │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Match scenario_id → Route to target service                          │  │
│   │ Set priority based on severity                                        │  │
│   │ Add custom fields for demo tracking                                   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   INCIDENT WORKFLOW                                                          │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Create Slack channel                                                  │  │
│   │ Post initial message                                                  │  │
│   │ Add incident note                                                     │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   WEBHOOK → LAMBDA                                                           │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ on_incident_triggered:                                                │  │
│   │   • Store state in DynamoDB                                          │  │
│   │   • Schedule acknowledge (30-60s)                                    │  │
│   │                                                                       │  │
│   │ on_workflow_completed:                                                │  │
│   │   • Invite responders to Slack                                       │  │
│   │   • Invite observers (conalllynch88, clynch@pagerduty)              │  │
│   │   • Post initial responder message                                   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│   SCHEDULED ACTIONS (via EventBridge Scheduler)                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ +30-60s:  Acknowledge incident                                       │  │
│   │ +60-90s:  Post investigation message                                 │  │
│   │ +90-120s: Post progress message                                      │  │
│   │ +120-150s: Post near-resolution message                              │  │
│   │ +180-240s: Resolve incident                                          │  │
│   │                                                                       │  │
│   │ ** CHECK PAUSE STATE BEFORE EACH ACTION **                           │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Reference Files

| Purpose | File Location |
|---------|---------------|
| Scenario definitions | `docs/demo-scenarios/src/data/scenarios.json` |
| Lambda handler | `aws/lambda-demo-orchestrator/handler.py` |
| Shared Slack client | `aws/shared/clients.py` |
| Global orchestration | `global_orchestration.tf` |
| Service orchestrations | `service_orchestrations.tf` |
| Workflow definitions | `incident_workflows.tf` |
| Workflow population script | `scripts/populate_workflow_steps.py` |
| E2E test suite | `scripts/e2e_test.py` |

---

## Success Criteria

Phase implementation is complete when:

1. ✅ All 66 scenarios route to correct services
2. ✅ Datadog monitors trigger PagerDuty incidents
3. ✅ Slack channels created for all incidents
4. ✅ Observers automatically added to all channels
5. ✅ Responder chat messages appear realistically
6. ✅ Pause/resume works for presenter control
7. ✅ Incidents resolve within 3-5 minutes
8. ✅ No orphaned demo incidents
9. ✅ CloudWatch logs show no errors
10. ✅ E2E test suite passes

---

## Contact and Escalation

For questions about this implementation:
- Review `docs/GOTCHAS_AND_WORKAROUNDS.md` for known issues
- Check `docs/NEXT_DEVELOPER_PROMPT.md` for context
- CloudWatch logs in `us-east-1` for Lambda debugging
