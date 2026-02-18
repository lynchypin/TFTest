# Next Developer Handover Prompt

**Date Created:** February 7, 2026
**Last Updated:** February 18, 2026
**Project:** PagerDuty Demo Environment
**Repository:** TFTest

---

## READ THIS FIRST

You are taking over a PagerDuty demo environment project. This is a "living demo" that showcases PagerDuty's incident management platform to prospective customers. The goal is to have realistic-looking incidents that progress through their lifecycle automatically, with multi-user Slack conversations, automated actions, and integration with external tools.

**This is NOT a simple project.** It involves:
- PagerDuty (incident management platform)
- Terraform (infrastructure as code)
- AWS Lambda (serverless functions)
- DynamoDB (state storage)
- Slack (team communication)
- Jira (ticket management)
- PagerDuty Incident Workflows (automation)
- PagerDuty REST API (direct API calls for things Terraform can't do)

> **ZERO-COST POLICY:** All infrastructure MUST be free or effectively zero-cost. AWS Lambda (pay-per-invocation), DynamoDB (on-demand), and API Gateway (pay-per-request) are acceptable because they cost fractions of a cent per demo run. **Do NOT provision EC2 instances, NAT gateways, RDS, ELBs, or any always-on compute.** If a feature requires a paid service, use PagerDuty's own built-in capabilities first (e.g., Automation Actions, Process Automation Cloud) — PagerDuty is the one platform available for use. No local dependencies or self-hosted runners. See `GOTCHAS_AND_WORKAROUNDS.md` TODO-2 for the RBA Runner removal and free alternatives.

---

## CRITICAL FIXES APPLIED (February 9-10, 2026)

Before diving into remaining work, understand these fixes that resolved major blocking issues:

### 1. PagerDuty API Token - Changed to Admin Token

**Issue:** The original API token belonged to Arthur Guinness (`limited_user` role). This token could NOT acknowledge incidents on behalf of other users.

**Fix:** Replaced with admin-level token (see `docs/CREDENTIALS_REFERENCE.md`).

**Verification:**
```bash
curl -s "https://api.pagerduty.com/users/me" \
  -H "Authorization: Token token=$PD_TOKEN" | jq '.user.role'
# Should return "admin" or "owner"
```

### 2. Slack Token + SLACK_TEAM_ID Required

**Issue:** Slack `conversations.list` returned empty results because the workspace is Enterprise Grid, which requires `team_id` parameter.

**Fix:**
- Lambda uses Enterprise Grid bot token (see `docs/CREDENTIALS_REFERENCE.md`)
- Added `SLACK_TEAM_ID=T0A9LN53CPQ` environment variable
- Code passes `team_id` to all Slack API calls

### 3. Scheduler Role ARN Mismatch

**Issue:** Lambda's `SCHEDULER_ROLE_ARN` pointed to non-existent `demo-scheduler-role`.

**Fix:** Updated to correct role: `arn:aws:iam::127214181728:role/demo-scheduler-invoke-role`

### 4. Bot Posting as "Oauth APP"

**Issue:** "Team assembled" message appeared as posted by the bot instead of a responder.

**Fix:** Modified `on_workflow_completed()` to use `slack.post_as_user()` with first responder's identity.

---

## ~~YOUR FIRST TASK: Enable Slack Responder Conversations~~ COMPLETED

> **Status:** COMPLETED — The `demo-simulator-controller` Lambda now handles full multi-phase conversations with user impersonation during the investigation phase of each scenario. See the [README](../README.md#automated-incident-lifecycle) for the timeline.
>
> **Historical context (preserved for reference):** Prior to the controller Lambda, conversations were not implemented. The orchestrator posted a single "Team assembled" message. The controller was built in Feb 11-14 2026 and handles phased investigation messages (investigating → found_issue → working_fix → resolved) with scenario-specific content, user impersonation, and configurable delays. The `lambda-lifecycle` Lambda also has a `post_conversation()` function that can supplement this.

---

## ~~ACTIVE ISSUES — START HERE (February 17, 2026)~~ ALL RESOLVED (February 18, 2026)

> **All three issues from February 17 have been fixed and deployed.** Terraform apply completed: 35 added, 18 changed, 0 destroyed.

### ~~Issue 1: Demo Owner Not Added to Slack Channels~~ RESOLVED (Feb 18)

**Fix:** Both Conall Slack accounts (`U0A9GBYT999` personal, `U0A9KAMT0BF` work) now in default observer list at `handler.py:412`. `SLACK_TEAM_ID` added to controller Lambda env vars at `aws/main.tf:612`.

### ~~Issue 2: Jim Beam Incidents Fail Resolution More Than Others~~ RESOLVED (Feb 18)

**Fix:** Rebalanced schedules — replaced Jim Beam with Arthur Guinness on "Business Ops" and "Manager Escalation" schedules (`variables_and_locals.tf`). Added retry logic with error logging to `resolve_incident()` in `handler.py:582-588`.

### ~~Issue 3: No Slack Activity by Bot~~ RESOLVED (Feb 18)

**Fix:** Added `SlackClient.verify_token()` method (`clients.py:601-612`). Controller now validates Slack token at startup (`handler.py:609-613`) and logs `SLACK TOKEN INVALID` if broken. Error logging added for `post_as_user` and `invite_user_to_channel` failures.

---

## CURRENT PROJECT STATE (as of February 18, 2026)

### E2E FLOW VALIDATED

The full pipeline was last validated on February 18, 2026 via `terraform apply` (35 added, 18 changed, 0 destroyed). Previous E2E test on February 17, 2026 (incident `Q2CSWNFUO7TSZ6`):

```
Controller invoked with scenario_id
    -> Events API v2 (with routing key for target service)
    -> Global Event Orchestration routes to correct service
    -> Cache Variables track event source, hostname, trigger counts
    -> Incident Created with [DEMO] prefix
    -> Workflow Trigger fires (condition: title contains '[DEMO]')
    -> Slack Channel Created + Jira Ticket Created
    -> Controller polls conference_bridge for Slack channel URL
    -> Responder Acknowledges (via admin API token From: header)
    -> Bot joins Slack channel, invites observers + responders
    -> Phased investigation messages posted as impersonated users
    -> Actions executed (notes, status updates, custom fields, etc.)
    -> Incident auto-resolved
```

**Test Incidents:**
- Q2EE76G7QQE3UX - Routed to "Database Reliability" with Slack channel `#demo-314-demo-e2e-workflow-`
- Q042RCJLVIXWF7 - "[DEMO] Bot message fix test" - Verified acknowledgment flow

### What's DONE and WORKING:
1. **Terraform infrastructure** - 205+ PagerDuty resources deployed (services, teams, schedules, escalation policies, etc.)
2. **AWS Lambda `demo-simulator-controller`** - PRIMARY execution path in `us-east-1`, runs full incident lifecycle (conversation phases, timing, state management) in a single invocation
3. **AWS Lambda `demo-simulator-orchestrator-v2`** - Legacy webhook-driven handler, accessible via API Gateway (`https://ynoioelti7.execute-api.us-east-1.amazonaws.com`)
4. **PagerDuty Generic Webhook** - **DELETED (Feb 17)** — was non-functional (Lambda Function URLs return 403 Forbidden). The controller does not use webhooks.
5. **PagerDuty Workflow "Demo Incident Channel Setup"** (ID: `PUXIPNC`) - Creates Slack channels for `[DEMO]` incidents
6. **Workflow conditional trigger** - Fires when incident title contains `[DEMO]` — managed via `incident_workflow_triggers.tf`
7. **DynamoDB table** (`demo-incident-state`) - Stores incident state for demo orchestration
8. **E2E Test Suite** - `scripts/e2e_test.py` with 7 tests, all passing; `scripts/test_all_scenarios.py` validates all 51 enabled scenarios (100% pass rate)
9. **Jira Integration** - Multiple workflows create tickets automatically in domain-specific projects
10. **Priority Configuration** - P1-P5 priorities configured and available
11. **Datadog Integration** - Fixed Feb 9, monitors now send to correct service with correct routing key
12. **Event Routing** - Working when events include proper `class`/`component`/`custom_details` fields
13. **PagerDuty Admin Token** - FIXED Feb 10, can now acknowledge incidents as any user
14. **Slack Integration** - FIXED Feb 10, bot token with proper scopes + SLACK_TEAM_ID configured (including on controller Lambda as of Feb 18)
15. **EventBridge Scheduler** - FIXED Feb 10, correct scheduler role ARN configured
16. **User Impersonation** - FIXED Feb 10, messages posted as first responder (not bot)
17. **Controller Lambda** - `demo-simulator-controller` runs full incident lifecycle with multi-phase conversations, user impersonation, and configurable delays (Feb 11-14)
18. **Status Page API** - `scripts/status_page_manager.py` rewritten to use correct Posts API with object-reference payloads (Feb 14)
19. **Slack Channel Invites** - Fixed one-by-one invite with per-user error handling; both Conall observer accounts explicitly invited (Feb 14, updated Feb 18)
20. **Datadog Graceful Degradation** - All Lambdas handle expired/missing Datadog API key without crashing; orchestrator falls back to PagerDuty Events API (Feb 14)
21. **Slack Health Check** - Controller validates Slack token at startup via `verify_token()`, logs `SLACK TOKEN INVALID` if broken (Feb 18)
22. **Schedule Rebalancing** - Jim Beam removed from Manager Escalation and Business Ops schedules, replaced by Arthur Guinness. All users now have 2-3 schedule assignments (Feb 18)
23. **Incident Resolution Resilience** - Controller `resolve_incident()` now retries once on failure with 3-second backoff and structured error logging (Feb 18)
24. **Identity Team Service Fix** - Fixed double-space typo in service name and replaced data source lookups with direct resource references in `bs_dependencies.tf` (Feb 18)
25. **Incident Workflow Slack Fix** - Fixed Slack connection ID reference in `incident_workflows.tf` to use correct `pagerduty_slack_connection` resource (Feb 18)
26. **Event Orchestration Cache Variables** - 7 cache variable resources deployed via `cache_variables.tf` (3 global, 4 service-level) for event source tracking, critical event counting, K8s pod restart storm detection, payment failure burst detection, and DBRE slow query tracking (Feb 18)
27. **Auto-Pause Notifications** - `auto_pause_notifications_parameters` configured on services for transient alert handling (Feb 18)
28. **4 New AIOPS Scenarios** - AIOPS-005 through AIOPS-008 added to `scenarios.json` demonstrating cache variable features (Feb 18)

### What's PARTIALLY DONE:
1. **70 Demo Scenarios** - 51 enabled and E2E validated (100% pass rate, Feb 18), 19 disabled (awaiting external integrations)
2. **AIOps Features** - Cache variables deployed; Alert Grouping and intelligent features not fully configured (requires AIOps/EIM add-on)

### What's NOT DONE:
1. **ServiceNow Integration** - Deferred (Jira sufficient for demo)
2. **RBA Interactive Runbooks** - RBA Runner exists but runbooks need creation
3. **AI Scribe/ML Features** - Requires AIOps/EIM license

### ALL BLOCKING ISSUES RESOLVED:

#### RESOLVED (February 9-10, 2026):

1. ~~**Incidents Not Being Auto-Acknowledged**~~ FIXED
   - **Root Cause:** Demo users had "observer" role which cannot acknowledge via API
   - **Fix:** Changed all demo users to "responder" role (appears as "limited_user" in API)
   - **IMPORTANT:** New demo users MUST have "responder" role, NOT "observer"

2. ~~**Demo Owner Not Being Added to Slack Channels**~~ FIXED
   - **Root Cause:** Batch `conversations.invite` was failing silently
   - **Fix:** Modified to invite users one-by-one with individual error handling
   - **Observer Slack IDs (already in code):** `U0A9GBYT999` (conalllynch88@gmail.com), `U0A9KAMT0BF` (clynch@pagerduty.com)

3. ~~**PagerDuty API Token Insufficient**~~ FIXED (Feb 10)
   - **Root Cause:** Token was `limited_user` role, couldn't acknowledge as other users
   - **Fix:** Replaced with admin token (see `docs/CREDENTIALS_REFERENCE.md`)

4. ~~**Slack conversations.list Empty**~~ FIXED (Feb 10)
   - **Root Cause:** Enterprise Grid workspace requires `team_id` parameter
   - **Fix:** Added `SLACK_TEAM_ID=T0A9LN53CPQ` to Lambda environment

5. ~~**EventBridge Scheduler iam:PassRole Error**~~ FIXED (Feb 10)
   - **Root Cause:** `SCHEDULER_ROLE_ARN` pointed to non-existent role
   - **Fix:** Updated to `arn:aws:iam::127214181728:role/demo-scheduler-invoke-role`

6. ~~**Bot Posting as "Oauth APP"**~~ FIXED (Feb 10)
   - **Root Cause:** `post_message()` used bot identity instead of user
   - **Fix:** Changed to `post_as_user()` with first responder's Slack ID

7. ~~**Datadog Monitors Using Wrong Service Name**~~ FIXED (Feb 9)
   - **Root Cause:** 14 Datadog monitors sent to `@pagerduty-Los-Andes-Demo` (doesn't exist)
   - **Fix:** Updated monitors to use `@pagerduty-demo-simulator-alerts`

8. ~~**Workflow Trigger Not Firing**~~ FIXED (Feb 9)
   - **Root Cause:** PagerDuty UI configuration issue
   - **Fix:** User fixed trigger configuration in PagerDuty web UI

9. ~~**Events Routing to "Default Service - Unrouted Events"**~~ UNDERSTOOD (Feb 9)
   - **Root Cause:** Events must include `class`, `component`, or `custom_details.*` fields
   - **Solution:** Events MUST include routing fields - summary text alone is NOT sufficient

---

## IMPORTANT IMPLEMENTATION REFERENCE

**For detailed phased implementation plan with Build -> Test -> Integrate methodology, see:**
`docs/PHASE_IMPLEMENTATION_GUIDE.md`

This document includes:
- Phase 0: Prerequisites - **COMPLETED Feb 9**
- Phase 1: Datadog Integration Fix - **COMPLETED Feb 9**
- Phase 2: Global Event Orchestration Expansion - **COMPLETED** (12 routing rules configured, validated)
- Phase 3: Service-Level Orchestrations - **COMPLETED** (services created via `services.tf`)
- Phase 4: Lambda Enhancements (Observer Invites, Responder Chat, Pause/Resume) - **COMPLETED Feb 11-18** (controller handles full lifecycle)
- Phase 5: Integration Testing - **COMPLETED Feb 14** (47/47 scenarios pass E2E)
- Phase 6: Production Deployment - **COMPLETED Feb 18** (35 added, 18 changed, 0 destroyed)
- Phase 7-9: Hardening, Documentation, Resilience - **COMPLETED Feb 14-18**
- Phase 10: Cache Variables & AIOps Scenarios - **COMPLETED Feb 18** (7 cache variables, 4 new scenarios, 70 total)

---

## CRITICAL: Event Routing Requirements

**THIS IS THE MOST IMPORTANT SECTION FOR NEW DEVELOPERS**

Events sent to the Global Event Orchestration routing key (`R028NMN4RMUJEARZ18IJURLOU1VWQ779`) will fall through to "Default Service - Unrouted Events" UNLESS they include specific fields that match the routing rules.

**The routing rules check `event.class`, `event.component`, and `event.custom_details.*` fields - NOT the event summary text.**

### Routing Rules Quick Reference

| To Route To | Include These Fields |
|-------------|---------------------|
| Database Reliability | `class: "database"` OR `component: "postgres/mysql/redis/mongodb/cassandra"` |
| Platform K8s | `source: "kubernetes"` OR `source: "prometheus"` |
| Platform Network | `class: "network"` OR summary containing "connectivity/latency/packet loss" |
| Security Monitoring | `class: "security"` OR `custom_details.security_classification` exists |
| Payments Ops | `custom_details.domain: "payments"` OR `class: "payment"` |
| App Checkout | `custom_details.service: "checkout"` OR `custom_details.service: "cart"` |
| App Orders | `custom_details.service: "order/fulfillment/inventory"` |
| App Identity | `custom_details.service: "identity/auth/sso/login"` |
| Data Streaming | `custom_details.service: "streaming/kafka/kinesis/pubsub"` |
| Data Analytics | `custom_details.service: "analytics/warehouse/bigquery/snowflake/redshift"` |

### Working Event Example

```bash
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[DEMO] Database connection pool exhausted",
      "source": "demo-test",
      "severity": "critical",
      "class": "database",
      "component": "postgres"
    }
  }'
```

This routes to **Database Reliability** service with P1 priority.

### Validated Demo Responders (MUST USE THESE)

Only these 6 demo responders have BOTH PagerDuty AND Slack accounts:

| Name | Email | PagerDuty ID | Slack ID |
|------|-------|--------------|----------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U0AA1LZSYHX |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U0A9GC08EV9 |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U0AA1LYLH2M |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U0A9LN3QVC6 |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U0A9KANFCLV |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U0A9SBF3MTN |

---

## RECENT CHANGES

### Phase 10: Cache Variables & AIOps Scenarios (February 18, 2026) - COMPLETED
- **Event Orchestration Cache Variables:** Added `cache_variables.tf` with 7 cache variable resources:
  - 3 Global: `recent_alert_source` (tracks event.source, 5min TTL), `critical_event_count` (counts critical events, 10min TTL), `recent_hostname` (tracks hostname from custom_details, 10min TTL)
  - 4 Service-level: `pod_restart_trigger_count` (K8s service, counts restart/CrashLoopBackOff events), `recent_failing_pod` (K8s service, extracts pod name via regex), `payment_failure_count` (Payments service, counts critical payment events), `recent_slow_query_source` (DBRE service, tracks slow query hostnames)
- **Auto-Pause Notifications:** Added `auto_pause_notifications_parameters` to services in `services.tf` for transient alert handling
- **4 New AIOPS Scenarios:** Added AIOPS-005 through AIOPS-008 to `scenarios.json` (70 total scenarios, 51 enabled):
  - AIOPS-005: Cache Variable - Event Source Tracking
  - AIOPS-006: Cache Variable - Critical Event Counting
  - AIOPS-007: Cache Variable - K8s Pod Restart Storm Detection
  - AIOPS-008: Cache Variable - Payment Failure Burst Detection
- **Dashboard Updated:** GitHub Pages deployment triggered for updated scenario dashboard
- **Terraform Provider:** Requires PagerDuty provider v3.22.0+ for cache variable resources
- **File Archival:** Moved 10 tfplan artifacts, runner.jar, alertmanager config, 4 one-time scripts, 3 log/json outputs, and 2 yaml configs to `archive/` subdirectories

### Phase 9: Resilience & Schedule Rebalancing (February 18, 2026) - COMPLETED
- **Slack Integration Fix:** Fixed Slack connection ID reference in `incident_workflows.tf` to use correct `pagerduty_slack_connection` resource
- **Schedule Rebalancing:** Replaced Jim Beam with Arthur Guinness on "Business Ops" and "Manager Escalation" schedules in `variables_and_locals.tf`. All 6 demo users now have 2-3 schedule assignments (previously Jim Beam had 4).
- **Incident Resolution Resilience:** Added retry logic with exponential backoff to `PagerDutyClient.resolve_incident()` in `aws/shared/clients.py`. Controller `resolve_incident()` in `handler.py:582-588` now retries once after 3-second wait on failure.
- **Slack Health Check:** Added `SlackClient.verify_token()` method (`clients.py:601-612`). Controller `run_demo_flow()` validates token at startup (`handler.py:609-613`), logging `SLACK TOKEN INVALID` at ERROR level if broken.
- **Observer List Fix:** Added both Conall Slack accounts to default observer list (`handler.py:412`): `U0A9GBYT999` (personal) + `U0A9KAMT0BF` (work)
- **SLACK_TEAM_ID on Controller:** Added `SLACK_TEAM_ID = var.slack_team_id` to controller Lambda env vars in `aws/main.tf:612`
- **Identity Team Fix:** Fixed double-space typo (`"App -  Identity Team"` → `"App - Identity Team"`) and replaced data source lookups with direct resource references in `bs_dependencies.tf`
- **Error Logging:** Added error logging for Slack `post_as_user` resolve message and `invite_user_to_channel` failures
- **Terraform State Cleanup:** Resolved 10+ open PagerDuty incidents blocking schedule changes, removed orphaned schedule key via `terraform state rm`, deleted duplicate workflow trigger via PagerDuty API
- **Terraform Apply Result:** 35 added, 18 changed, 0 destroyed (exit code 0)
- **Archived Obsolete Files:** Moved 17 terraform state backups to `archive/terraform-state-backups/`, moved GCP service account key and AWS root key CSV to `archive/credentials-obsolete/`

### Phase 8: Documentation Audit & Pipeline Validation (February 17, 2026) - COMPLETED
- **PagerDuty Webhook Deleted:** Generic Webhook subscription PILGGJ0 was deleted — the controller does not use webhooks
- **Lambda Function URLs Confirmed Broken:** All Function URLs return 403 Forbidden (account-level restriction). Documented `aws lambda invoke` and API Gateway as alternatives
- **Full Pipeline E2E Validated:** Controller invoked with FREE-001 scenario → incident Q2CSWNFUO7TSZ6 created → acknowledged → actions completed → resolved. All via `aws lambda invoke` (async)
- **Documentation Overhaul:** Removed hardcoded credentials from DEPLOYMENT.md, updated all stale references across 8+ docs, fixed Lambda URL references, marked obsolete webhook sections
- **Temp Files Archived:** `ctrl-result.json` moved to `archive/`

### Phase 7: Hardening & Documentation (February 14, 2026) - COMPLETED
- **Status Page API Rewrite:** `create_incident()` and `update_incident()` in `scripts/status_page_manager.py` completely rewritten to use correct endpoints (`/posts` and `/post_updates`) and object-reference payloads.
- **Slack Channel Invite Fix:** `invite_users_to_channel()` in `aws/shared/clients.py` changed from batch invite to one-by-one with per-user error handling.
- **Datadog Trial Graceful Degradation:** Verified all Lambdas handle expired/missing Datadog API key without crashing.
- **47 of 66 scenarios validated** end-to-end (100% pass rate via `scripts/test_all_scenarios.py`). 19 disabled pending external integrations.

### Phase 5: E2E Validation & Fixes (February 9, 2026) - COMPLETED
- Fixed Datadog monitors to use correct service name `@pagerduty-demo-simulator-alerts`
- Updated Datadog-PagerDuty integration routing key to Global Orchestration key
- Discovered and documented event routing field requirements
- User fixed workflow trigger in PagerDuty UI
- Validated full E2E flow: Event -> Routing -> Service -> Workflow -> Slack Channel -> Acknowledgement
- Test incident Q2EE76G7QQE3UX successfully routed and processed

### Phase 4: Slack User Impersonation (February 8, 2026) - COMPLETED
- Implemented user profile fetching via Slack `users.info` API
- Added profile caching (`_profile_cache`) to avoid repeated API calls
- Created `get_user_profile()` method to retrieve display name and avatar URL
- Created `post_as_user()` method that posts messages with user's name and avatar
- Updated all 9 `post_message` calls in Lambda to use user impersonation
- **Files modified:** `aws/lambda-demo-orchestrator/handler.py`, `aws/shared/clients.py`
- **Limitation:** Messages still show "APP" badge (Slack API limitation), but visually appear as the user

### Phase 3: Scenario Readiness Improvements (February 8, 2026) - COMPLETED
- Updated `scripts/analyze_scenario_readiness.py` to properly recognize configured features
- Improved scenario detection for: priority_assignment, slack_incident_channel, post_incident_reviews, stakeholder_notifications, incident_workflows, service_rules, status_pages, slack_actions
- Extended Jira integration to additional workflows (most already configured)
- **Result:** READY scenarios improved from 8 -> 19 (137% increase)

### Phase 2: Jira Integration (February 7, 2026) - COMPLETED
- Verified 9 Jira projects available (COMP, DATA, DEMO, INFRA, KAN, LAX, PAY, PIR, SECOPS)
- Added Jira ticket creation to 6 key workflows:
  | Workflow | Jira Project |
  |----------|--------------|
  | Standard Incident Response | DEMO |
  | Security Incident Response | SECOPS |
  | Payments System Outage | PAY |
  | Data Pipeline Alert | DATA |
  | Database Emergency Response | INFRA |
  | Compliance Incident Handler | COMP |

### Phase 1: Foundation (February 7, 2026) - COMPLETED
- Fixed "Data Pipeline Alert" workflow (was empty, now has 2 steps)
- Deleted 9 orphaned workflow triggers (47 -> 38 active)
- Created comprehensive E2E test suite (`scripts/e2e_test.py`)

---

## CRITICAL CONTEXT: NON-STANDARD PATTERNS

### 1. Slack Channels Are Created by PagerDuty, NOT Lambda

**Why this matters:** You might assume the Lambda function creates Slack channels. IT DOES NOT.

**The Flow (Controller — current):**
```
[DEMO] Incident Created in PagerDuty
        │
        ▼
PagerDuty Workflow Trigger fires (condition: title contains '[DEMO]')
        │
        ▼
Workflow Step 1: "Create Incident Slack Channel" (PD's native Slack integration)
        │
        ▼
Workflow Step 2: "Add Conference Bridge" (sets incident.conference_bridge.url = Slack channel URL)
        │
        ▼
Controller polls incident conference_bridge field to discover channel URL
        │
        ▼
Controller extracts channel ID, bot joins, invites observers + responders
```

**Why we did it this way:** The Slack bot token does NOT have `channels:write` scope. PagerDuty's native Slack integration CAN create channels, so we use that.

**The "Conference Bridge Hack":** The `conference_bridge.url` field is normally for Zoom/Meet links. We're hijacking it to store the Slack channel URL so the controller can read it. This is documented in `docs/GOTCHAS_AND_WORKAROUNDS.md`.

---

### 2. Terraform CANNOT Create Workflow Steps

**Why this matters:** You might try to add workflow steps in `.tf` files. This will fail.

**The Reality:**
- `pagerduty_incident_workflow` resource creates an empty workflow shell
- There is NO `steps` attribute in the Terraform provider
- Steps must be added via PagerDuty REST API or manually in the UI

**Our Approach:**
- Terraform creates workflow shells
- `scripts/populate_workflow_steps.py` adds steps via API for most workflows
- The "Demo Incident Channel Setup" workflow was created entirely via API (not Terraform)

**See:** `docs/GOTCHAS_AND_WORKAROUNDS.md` section "Terraform Cannot Create Workflow Steps"

---

### 3. Two Different AWS Regions in Use

| Component | Region | Why |
|-----------|--------|-----|
| RBA Runner (EC2) | `us-east-1` | Historical - deployed before this project |
| Traffic simulation Lambdas | `us-east-1` | Deployed with RBA runner |
| **demo-simulator-controller Lambda** | **`us-east-1`** | **PRIMARY** — Terraform-managed, runs full incident lifecycle |
| demo-simulator-orchestrator-v2 Lambda | `us-east-1` | Legacy webhook handler, accessible via API Gateway |
| DynamoDB table | `us-east-1` | Co-located with Lambdas |

**This means:** When debugging, CloudWatch logs for all demo components are in `us-east-1`.

---

### 4. Multiple PagerDuty API Tokens with Different Capabilities

| Token | Use Case | Limitation |
|-------|----------|------------|
| API Key (General Access) | Most API operations, Terraform | Cannot create workflows via API |
| API User Token | Workflow creation, trigger creation | Must be from a user with appropriate permissions |
| ~~Webhook Signing Secret~~ | ~~Signature verification~~ | OBSOLETE — PD webhook deleted Feb 17; controller doesn't use webhooks |

**The 403 Trap:** An API Key with "admin" scope can STILL return `403 User not permitted to create workflow`. You need an API User Token for workflow creation.

**Token locations:** `aws/terraform.tfvars`, `terraform.tfvars`, `docs/CREDENTIALS_REFERENCE.md`

---

### 5. Event Type Naming is Inconsistent

**The Trap:** You might search for `workflow.completed` events. The actual event type is `incident.workflow.completed`.

**Rule:** All incident-related webhook events have the `incident.` prefix:
- `incident.triggered` (not `triggered`)
- `incident.acknowledged` (not `acknowledged`)
- `incident.workflow.completed` (not `workflow.completed`)

**See:** `aws/lambda-demo-orchestrator/handler.py` for the full event type mapping.

---

## KEY IDS AND CONFIGURATION

| Item | ID/Value | Notes |
|------|----------|-------|
| PagerDuty Subdomain | `pdt-losandes` | URL: https://pdt-losandes.pagerduty.com |
| Demo Workflow ID | `PUXIPNC` | "Demo Incident Channel Setup" workflow |
| Workflow Trigger ID | `7c33cc98-3c3a-4da2-9f6f-2211a706ca29` | Conditional trigger for [DEMO] |
| Slack Workspace ID | `T0A9LN53CPQ` | Used in workflow Slack steps |
| DynamoDB Table | `demo-incident-state` | In us-east-1 |
| Lambda Function (PRIMARY) | `demo-simulator-controller` | In us-east-1 — runs full incident lifecycle |
| Lambda Function (Legacy) | `demo-simulator-orchestrator-v2` | In us-east-1 — webhook handler, via API Gateway |
| Event Orchestration Routing Key | `R028NMN4RMUJEARZ18IJURLOU1VWQ779` | Global Event Orchestration |
| Slack Channel Action ID | `pagerduty.com:slack:create-a-channel:4` | For workflow API calls |
| Conference Bridge Action ID | `pagerduty.com:incident-workflows:add-conference-bridge:1` | For workflow API calls |
| Observer Slack ID 1 | `U0A9GBYT999` | conalllynch88@gmail.com |
| Observer Slack ID 2 | `U0A9KAMT0BF` | clynch@pagerduty.com |
| Datadog Integration Service | `demo-simulator-alerts` | NOT Los-Andes-Demo |

### Demo Responders with Slack Users

**IMPORTANT:** Only these 6 responders have Slack accounts and should be used in demo scenarios:

| Name | Email | PagerDuty ID | Slack ID |
|------|-------|--------------|----------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U0AA1LZSYHX |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U0A9GC08EV9 |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U0AA1LYLH2M |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U0A9LN3QVC6 |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U0A9KANFCLV |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U0A9SBF3MTN |

The mapping is defined in `aws/shared/clients.py` and `variables_and_locals.tf`.

---

## DIRECTORY STRUCTURE - WHERE TO FIND THINGS

```
TFTest/
├── *.tf                           # PagerDuty Terraform configs (root level)
├── terraform.tfvars               # PagerDuty credentials (SENSITIVE)
├── README.md                      # Project overview
│
├── aws/                           # AWS infrastructure
│   ├── main.tf                    # AWS resources (Lambdas, DynamoDB, IAM, etc.)
│   ├── terraform.tfvars           # AWS credentials (SENSITIVE)
│   ├── lambda-demo-controller/    # *** PRIMARY Lambda — scenario runner ***
│   │   ├── handler.py             # ~700 lines, full incident lifecycle
│   │   └── scenarios.json         # 70 demo scenario definitions
│   ├── lambda-demo-orchestrator/  # Legacy webhook handler (via API Gateway)
│   │   └── handler.py             # ~1800 lines, event-driven handler
│   └── shared/                    # Shared code (copied into both Lambdas)
│       └── clients.py             # PagerDutyClient, SlackClient, DatadogClient
│
├── cache_variables.tf             # 7 Event Orchestration Cache Variables
│
├── docs/
│   ├── NEXT_DEVELOPER_PROMPT.md   # *** START HERE — this file ***
│   ├── GOTCHAS_AND_WORKAROUNDS.md # Saves hours of debugging (READ THIS)
│   ├── PROJECT_DESCRIPTION.md     # Detailed project description
│   ├── IMPLEMENTATION_PLAN.md     # Master plan with phases
│   ├── CREDENTIALS_REFERENCE.md   # All API keys/tokens (SENSITIVE)
│   ├── setup/DEPLOYMENT.md        # Deployment guide with terraform procedures
│   └── archive/                   # Outdated documentation
│
├── scripts/
│   ├── e2e_test.py                # E2E test suite (7 tests)
│   ├── test_all_scenarios.py      # Validates all 51 enabled scenarios
│   ├── populate_workflow_steps.py # Adds steps to workflows via API
│   ├── trigger_demo_incident.sh   # Creates test [DEMO] incidents
│   └── archive/                   # One-time scripts (already run)
│
├── archive/                       # Obsolete files
│   ├── tfplan-artifacts/          # 10 old terraform plan files
│   ├── scripts-oneoff/            # One-time scripts, logs, analysis JSONs
│   ├── config-samples/            # Sample config files
│   ├── terraform-state-backups/   # 17 .backup files moved Feb 18
│   └── credentials-obsolete/      # Old credential files
│
```

---

## FIRST STEPS WHEN YOU PICK THIS UP

### 1. Verify Your Access

```bash
# Test PagerDuty API access (get token from CREDENTIALS_REFERENCE.md or Lambda env vars)
export PD_TOKEN="<your-pagerduty-admin-token>"
curl -s "https://api.pagerduty.com/users/me" \
  -H "Authorization: Token token=$PD_TOKEN" | jq '.user.name'

# Test AWS access (us-east-1)
aws lambda get-function --function-name demo-simulator-controller --region us-east-1

# Test Slack API access (get token from CREDENTIALS_REFERENCE.md or Lambda env vars)
export SLACK_TOKEN="<your-slack-bot-token>"
curl -s "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer $SLACK_TOKEN" | jq '.ok'

# Test Jira API access (get credentials from CREDENTIALS_REFERENCE.md)
curl -s -u "<jira-email>:<jira-api-token>" \
  "https://losandesgaa.atlassian.net/rest/api/3/myself" | jq '.displayName'
```

### 2. Run the End-to-End Test Suite

```bash
# Activate virtual environment
source .venv/bin/activate

# Run full E2E test (all 7 tests)
python scripts/e2e_test.py
```

**Expected Output:**
```
=== PagerDuty Demo E2E Test Suite ===

Test 1: Trigger incident via PagerDuty Events API
  Incident triggered successfully

Test 2: Verify incident created in PagerDuty
  Incident found: [DEMO] ... (ID: Q3...)

Test 3: Verify Slack channel created by workflow
  Found channel: demo-...

Test 4: Simulate Slack conversation
  Messages posted successfully

Test 5: Simulate responder actions
  Incident acknowledged and runbook run

Test 6: Trigger via Datadog-style event
  Datadog-style event triggered

Test 7: Resolve and clean up
  Incident resolved

=== All tests passed! ===
```

### 3. Read the Documentation

In order of importance:
1. `docs/GOTCHAS_AND_WORKAROUNDS.md` - Will save you HOURS
2. `docs/IMPLEMENTATION_PLAN.md` - Master plan with phases
3. `docs/SCENARIO_FLOWS.md` - Scenario types, flows, readiness (70 scenarios)
4. `docs/setup/DEPLOYMENT.md` - Deployment procedures

---

## DEBUGGING TIPS

### ~~Lambda Not Receiving Webhooks?~~ (OBSOLETE — Webhook Deleted Feb 17)

> The PagerDuty Generic Webhook subscription (PILGGJ0) was deleted on Feb 17, 2026. The `demo-simulator-controller` does not use webhooks — it polls the PagerDuty API directly. The orchestrator's API Gateway (`https://ynoioelti7.execute-api.us-east-1.amazonaws.com`) can still receive webhooks if a new subscription is created, but this is not required for normal operation.

> **Lambda Function URLs** on this AWS account return **403 Forbidden** due to an account-level restriction. Always use `aws lambda invoke` or the API Gateway URL instead.

### Slack Channel Not Created?

1. Check if workflow ran: PagerDuty → Automation → Incident Workflows → Run History
2. Verify incident title contains `[DEMO]` (case-sensitive)
3. Check Slack Workspace ID in workflow matches `T0A9LN53CPQ`
4. Check PagerDuty's Slack integration is connected

### Lambda Not Inviting Users to Slack?

1. Check CloudWatch logs for `demo-simulator-controller` for `SLACK TOKEN INVALID`, `invite`, or `user_is_restricted` messages
2. Verify `conference_bridge.url` is set on incident: `curl -s "https://api.pagerduty.com/incidents/<ID>?include[]=conference_bridge" -H "Authorization: Token token=$PD_TOKEN" | jq '.incident.conference_bridge'`
3. Check Slack bot token is valid: `curl -s "https://slack.com/api/auth.test" -H "Authorization: Bearer $SLACK_TOKEN" | jq .`
4. Verify channel ID extraction from URL is working

### Jira Ticket Not Created?

1. Check workflow run history for errors
2. Verify Account Mapping ID is `PUWL8VU`
3. Verify Jira project exists (use `scripts/verify_jira_steps.py`)
4. Check Jira API token is still valid

---

## THINGS THAT LOOK WRONG BUT ARE INTENTIONAL

1. **Conference bridge used for Slack URL** - Intentional workaround, not a bug
2. **Workflow created via API, not Terraform** - Terraform can't create workflow steps
3. **All AWS resources in us-east-1** - All Lambdas, DynamoDB, and CloudWatch logs are in the same region
4. **Empty workflow shells in Terraform** - Steps added separately via API
5. **`[DEMO]` prefix in incident titles** - Used to filter demo vs real incidents
6. **Users in PagerDuty but not Slack** - Only 6 users have both accounts (see README)
7. **9 orphaned triggers deleted** - Were never firing, cleaned up intentionally

---

## REMAINING WORK

### Already Completed (Phases 1-4)
- E2E test suite - `scripts/e2e_test.py` (7 tests passing)
- Jira project creation - 9 projects exist
- Jira workflow integration - 6 workflows create tickets
- Fix empty workflows - All populated
- Clean up orphaned triggers - 9 deleted
- Scenario readiness improvements - 19 READY (up from 8)
- Slack user impersonation - Bot posts appear with user names/avatars
- **Auto-acknowledgment fix** - Changed demo users from "observer" to "responder" role ✅
- **Slack channel invites fix** - Modified to invite users one-by-one ✅

### ~~URGENT - Phase 5: Fix Core Demo Reliability~~ COMPLETED

**All critical reliability fixes have been applied (Feb 9-14, 2026).**

1. **~~Fix Datadog Monitor Service Name~~** COMPLETED (Feb 9, 2026)
   - Updated 14 monitors from `@pagerduty-Los-Andes-Demo` to `@pagerduty-demo-simulator-alerts`
   - Additionally, all Lambdas now handle expired Datadog API key gracefully (Feb 14)

2. **~~Fix Event Orchestration Routing~~** COMPLETED (Feb 14, 2026)
   - Routing rules expanded and validated for all 47 enabled scenarios
   - Events route correctly when `class`, `component`, or `custom_details.*` fields are included
   - See routing rules quick reference in [Event Routing Requirements](#critical-event-routing-requirements) below

3. **~~Wire All 66 Scenarios End-to-End~~** COMPLETED (Feb 14, 2026)
   - All 47 enabled scenarios validated end-to-end via `scripts/test_all_scenarios.py`
   - 19 disabled scenarios pending external integration setup (ServiceNow, Grafana, UptimeRobot, etc.)
   - Dashboard updated with "Coming Soon!" ribbon for disabled scenarios

4. **Test Datadog Integration End-to-End** (REMAINING — low priority, depends on Datadog trial status)
   - Current tests use direct Events API, not actual Datadog monitors
   - If Datadog trial is active: verify 14 monitors send alerts through PagerDuty integration
   - If Datadog trial is expired: orchestrator falls back to PagerDuty Events API automatically (see [Gotchas](GOTCHAS_AND_WORKAROUNDS.md#datadog-trial-expiry))

### High Priority - Phase 6: AIOps/EIM Features
1. **Configure AIOps features** - Alert Grouping, Suppression (requires AIOps/EIM add-on)
2. **Test disabled scenarios** - 19 scenarios need external integration setup before testing
3. **Enable AIOps intelligent features** - For DIGOPS scenarios
4. **Configure enterprise incident types** - For EIM scenarios

**Note:** AIOps features (formerly Event Intelligence) are now part of the AIOps/EIM add-on. Check account tier before attempting configuration.

### Medium Priority - Phase 7: RBA/Automation
1. **Create RBA interactive runbooks** - RBA Runner exists (`i-03ab4fd5f509a8342`), needs runbook content
2. **Configure approval gates** - For AA (Automated Actions) scenarios
3. **Set up self-service portal** - RBA-003 scenario
4. **Build runbook content** - See `docs/confluence-runbooks/` for templates

**RBA Architecture:**
- EC2 Runner at `us-east-1` (Java JAR)
- 8 RBA jobs configured in PagerDuty
- Jobs execute via `ProcessAutomationJobAction`
- See `docs/features/RBA_DOCUMENTATION.md` for setup

### Low Priority - Phase 8: AI/ML Features
1. **Configure AI Scribe** - For SCRIBE scenarios (requires AIOps license)
2. **Enable autonomous remediation** - For SRE scenarios
3. **Lambda consolidation** - Consider reducing from 9 to 3 functions (optional optimization)

### Deferred (Not Required for Demo)
- **ServiceNow integration** - Jira sufficient for demo purposes
- **Confluence RUNBOOKS space** - Using Jira PIR project instead
- **Terraform remote state** - Works fine locally for now

---

## UTILITY SCRIPTS

### Active Scripts (scripts/)
| Script | Purpose | Run Frequency |
|--------|---------|---------------|
| `scripts/e2e_test.py` | Run full E2E test suite | After changes |
| `scripts/test_all_scenarios.py` | Validate all 51 enabled scenarios | After scenario changes |
| `scripts/analyze_scenario_readiness.py` | Check scenario status | Weekly |
| `scripts/populate_workflow_steps.py` | Add steps to workflows | After new workflows |
| `scripts/status_page_manager.py` | Manage Status Page incidents/posts (rewritten Feb 14) | For status page demos |
| `scripts/trigger_demo_incident.sh` | Create test incidents | For testing |

### Archived Scripts
One-time scripts that have been run and are preserved for reference:

**`archive/scripts-oneoff/` (moved Feb 18):**
- `analyze_triggers.py` - Check trigger subscriptions
- `study_pagerduty.py` - Dump PagerDuty config
- `validate_scenarios.py` - Validate scenario JSON schema
- `list_workflows.py` - List all workflows
- `test_results.json`, `test_output.log`, `rerun_output.log` - Test run outputs
- `job_update.yaml`, `rba_jobs.yaml` - RBA job configs
- `pagerduty_analysis.json`, `scenario_readiness_analysis.json` - Generated analysis snapshots

**`scripts/archive/` (moved earlier):**
- `add_jira_to_workflows.py` - Added Jira steps to workflows (Feb 7)
- `add_jira_to_more_workflows.py` - Extended Jira integration (Feb 8)
- `analyze_jira_workflows.py` - Analyzed Jira workflow status (Feb 8)
- `check_jira_workflows.py` - Checked Jira workflows exist (Feb 8)
- `verify_jira_steps.py` - Verified Jira steps exist (Feb 7)
- `delete_orphaned_triggers.py` - Removed 9 orphaned triggers (Feb 7)
- `fix_data_pipeline_workflow.py` - Fixed empty workflow (Feb 7)
- `fix_workflow_trigger.py` - Fixed workflow trigger (Feb 7)
- `bootstrap_s3_backend.sh` - One-time S3 backend setup (archived Feb 8)
- `setup_webhook.py` - One-time webhook setup (archived Feb 8)
- `snow_keepalive.py` - ServiceNow keepalive, deferred (archived Feb 8)
- `snow_keepalive.yml` - ServiceNow keepalive config (archived Feb 8)
- `check_progress.py` - One-time test progress checker (archived Feb 14)
- `check_routing.py` - One-time routing analysis (archived Feb 14)
- `add_tier_data.py` - One-time tier data migration (archived Feb 14)

---

## KEY IDS QUICK REFERENCE

| Item | ID/Value |
|------|----------|
| PagerDuty Subdomain | `pdt-losandes` |
| Demo Workflow | `PUXIPNC` |
| Slack Workspace | `T0A9LN53CPQ` |
| Jira Account Mapping | `PUWL8VU` |
| Controller Lambda (PRIMARY) | `demo-simulator-controller` |
| Orchestrator Lambda (Legacy) | `demo-simulator-orchestrator-v2` |
| DynamoDB Table | `demo-incident-state` |
| Global Event Orchestration | `94e4c195-79d1-44ca-b649-548acbf08ea2` |
| Event Orchestration Routing Key | `R028NMN4RMUJEARZ18IJURLOU1VWQ779` |
| Observer Slack ID 1 | `U0A9GBYT999` (conalllynch88@gmail.com) |
| Observer Slack ID 2 | `U0A9KAMT0BF` (clynch@pagerduty.com) |
| Datadog Service Name | `demo-simulator-alerts` |

---

## CONTACT / ESCALATION

- **Project Owner**: Conall Lynch (clynch@pagerduty.com)
- **PD User ID**: PSLR7NC
- **Slack User ID**: U0A9KAMT0BF

---

## FINAL ADVICE

1. **Read `GOTCHAS_AND_WORKAROUNDS.md` before changing anything** - It will save you from re-discovering painful issues
2. **Read `PHASE_IMPLEMENTATION_GUIDE.md` for implementation steps** - Detailed phased approach with testing methodology
3. **Run E2E tests frequently** - `python scripts/e2e_test.py`
4. **Use `print()` in Lambda, not `logger.info()`** - CloudWatch visibility is better with print
5. **Webhooks are deleted** - The controller polls the PagerDuty API directly, no webhooks needed
6. **All Lambda/DynamoDB components are in us-east-1** - Check CloudWatch logs there
7. **The Terraform provider is limited** - If something seems impossible, check if it's a provider limitation (probably is)
8. **When in doubt, check the API** - PagerDuty REST API can do more than the Terraform provider
9. **Use the archived scripts as templates** - `scripts/archive/` has one-time scripts that show patterns
10. **Demo users must have "responder" role** - "observer" role cannot acknowledge via API
11. **Events MUST include routing fields** - `class`, `component`, or `custom_details.*` fields are required for routing (Feb 9 discovery)

Good luck!

---

## SESSION SUMMARY (February 9, 2026)

### What Was Accomplished

1. **Phase 0 Prerequisites - COMPLETED**
   - Verified all 6 demo users have "responder" role
   - Confirmed webhook subscription is enabled
   - Tested E2E flow successfully

2. **Phase 1 Datadog Integration - COMPLETED**
   - Updated monitors 17717886 and 17717887 to use `@pagerduty-demo-simulator-alerts`
   - Updated Datadog-PagerDuty integration routing key to `R028NMN4RMUJEARZ18IJURLOU1VWQ779`

3. **Critical Discovery: Event Routing Requirements**
   - Events must include `class`, `component`, or `custom_details.*` fields to match routing rules
   - Summary text alone is NOT sufficient for routing
   - Documented routing rules quick reference (see above)

4. **E2E Flow Validated**
   - Full pipeline tested: Event -> Routing -> Service -> Workflow -> Slack Channel -> Acknowledgement
   - Test incident: Q2EE76G7QQE3UX routed to "Database Reliability"
   - Slack channel created: `#demo-314-demo-e2e-workflow-`

5. **Workflow Trigger Fixed**
   - User fixed workflow trigger configuration in PagerDuty web UI
   - Workflow "Demo Incident Channel Setup" (PUXIPNC) now fires correctly

### What Remains To Be Done

**Next Steps (Priority Order) — updated Feb 14, 2026:**

1. **~~Phase 2: Global Event Orchestration Expansion~~** COMPLETED (Feb 14, 2026)
   - Routing rules validated for all 47 enabled scenarios
   - Events route correctly using `class`/`component`/`custom_details` fields

2. **~~Phase 3: Service-Level Orchestrations~~** COMPLETED (Feb 18, 2026)
   - Services created via `services.tf`, event routing configured via Global Event Orchestration
   - AIOps-specific features (suppression, alert grouping) deferred — requires AIOps add-on

3. **~~Phase 4: Lambda Enhancements~~** COMPLETED (Feb 11-14, 2026)
   - Controller Lambda implements full pause/resume, multi-phase conversations, and realistic timing
   - Conversation simulation runs with scenario-specific messages and user impersonation

4. **~~Phase 5: Integration Testing~~** COMPLETED (Feb 14, 2026)
   - All 47 enabled scenarios tested end-to-end via `scripts/test_all_scenarios.py` (100% pass rate)
   - 19 disabled scenarios documented with "Coming Soon!" on dashboard

5. **~~Phase 6: Status Pages~~** COMPLETED (Feb 14, 2026)
   - Status Page API rewritten with correct endpoints and object-reference payloads
   - `status_page_update` action type implemented in controller Lambda

6. **Phase 7: RBA Interactive Features** (Low Priority — REMAINING)
   - RBA Runner exists, 8 jobs configured
   - Need to create runbook content, configure approval gates
   - See `docs/features/RBA_DOCUMENTATION.md`

7. **Enable 19 disabled scenarios** (Low Priority — REMAINING)
   - Requires external integration setup: ServiceNow, Grafana, UptimeRobot, etc.
   - Each scenario's `enabled: false` flag can be flipped once its integration is connected

8. **AIOps/EIM features** (Low Priority — REMAINING, requires license)
   - Alert Grouping, Suppression, AI Scribe for DIGOPS/AIOPS/SCRIBE scenarios
   - Requires AIOps/EIM add-on — check account tier before attempting

~~9. **Webhook Signature Verification**~~ (OBSOLETE — Webhook Deleted Feb 17)
   - PagerDuty Generic Webhook subscription (PILGGJ0) was deleted
   - The `demo-simulator-controller` does not use webhooks
   - If re-enabling webhooks, point at API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com/webhook`

### Key Files Modified This Session

| File | Changes |
|------|---------|
| `docs/PHASE_IMPLEMENTATION_GUIDE.md` | Updated Phase 0/1 as completed, added routing discovery |
| `docs/NEXT_DEVELOPER_PROMPT.md` | Added routing requirements, updated status |
| `docs/GOTCHAS_AND_WORKAROUNDS.md` | Added Datadog fix, workflow fix, routing requirements |
| `docs/ARCHITECTURE_BLUEPRINT.md` | Updated integration status |

### Test Commands for Verification

```bash
# Verify Datadog integration
curl -s "https://api.us5.datadoghq.com/api/v1/integration/pagerduty" \
  -H "DD-API-KEY: $DATADOG_API_KEY" \
  -H "DD-APPLICATION-KEY: $DATADOG_APP_KEY" | jq '.services'

# Test event routing (should route to Database Reliability)
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[DEMO] Test routing - Database alert",
      "source": "test",
      "severity": "critical",
      "class": "database",
      "component": "postgres"
    }
  }'

# Check incident routing
curl -s "https://api.pagerduty.com/incidents?sort_by=created_at:desc&limit=1" \
  -H "Authorization: Token token=$PD_TOKEN" | \
  jq '.incidents[0] | {id, title, service: .service.summary}'
```
