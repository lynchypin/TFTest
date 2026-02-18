# Gotchas and Workarounds

> **Last Updated:** February 18, 2026
> **Purpose:** Document all non-obvious patterns, workarounds, and traps in the PagerDuty demo environment

---

## Table of Contents

1. [OPEN ISSUES (February 17, 2026)](#open-issues-february-17-2026)
2. [CRITICAL OPEN ISSUES (Historical)](#critical-open-issues-blocking-live-demos)
3. [RESOLVED ISSUES](#resolved-issues-february-9-2026)
4. [PagerDuty API Gotchas](#pagerduty-api-gotchas)
5. [Slack API Gotchas](#slack-api-gotchas)
6. [Jira Integration Gotchas](#jira-integration-gotchas)
7. [Terraform Limitations](#terraform-limitations)
8. [Workflow Configuration Gotchas](#workflow-configuration-gotchas)
9. [AWS/Lambda Gotchas](#awslambda-gotchas)
10. [E2E Testing Gotchas](#e2e-testing-gotchas)
11. [Datadog Integration Gotchas](#datadog-integration-gotchas)
12. [Status Page API Gotchas](#status-page-api-gotchas)
13. [Slack Channel Invite Gotchas](#slack-channel-invite-gotchas)
14. [Datadog Trial Expiry Handling](#datadog-trial-expiry)
15. [ACTION ITEMS / TODOs](#action-items--todos-february-18-2026)

---

## ~~OPEN ISSUES (February 17, 2026)~~ — ALL RESOLVED (February 18, 2026)

> **All three issues identified on February 17, 2026 have been fixed in the February 18 deployment.** Code changes were applied to `aws/lambda-demo-controller/handler.py`, `aws/shared/clients.py`, `aws/main.tf`, and `variables_and_locals.tf`. Terraform apply completed successfully: 35 added, 18 changed, 0 destroyed.

### ~~OPEN-1.~~ RESOLVED: Demo Owner (Conall) Not Being Added to Incident Slack Channels

**Status:** RESOLVED (February 18, 2026)

**Original Symptom:** The demo owner (`clynch@pagerduty.com` / `conalllynch88@gmail.com`) was not being invited to newly created incident Slack channels. Root cause was that only one Slack account was in the observer list, and `SLACK_TEAM_ID` was not passed to the controller Lambda.

**Fix Applied:**
1. Added `CONALL_SLACK_USER_ID` (`U0A9KAMT0BF`) to the default observer list alongside `CONALL_SLACK_USER_ID_PERSONAL` (`U0A9GBYT999`) in `handler.py:412`
2. Added `SLACK_TEAM_ID = var.slack_team_id` to the demo-controller Lambda env vars in `aws/main.tf:612`
3. Added `SlackClient.verify_token()` health check at controller startup (`handler.py:609-613`) — logs `SLACK TOKEN INVALID` if the token is missing or broken

---

### ~~OPEN-2.~~ RESOLVED: Jim Beam Incidents Fail Resolution More Often Than Other Users

**Status:** RESOLVED (February 18, 2026)

**Original Problem:** ~5% of demo incidents failed to resolve, primarily affecting Jim Beam who was over-scheduled (4 schedules vs 2-3 for others). Race condition between Events API resolve and REST API resolve compounded the issue.

**Fix Applied:**
1. Rebalanced schedules — replaced Jim Beam with Arthur Guinness on "Schedule - Business Ops Team" and "Schedule - Manager Escalation" in `variables_and_locals.tf`. All 6 users now have 2-3 schedule assignments.
2. Added retry logic with error logging to `resolve_incident()` in `handler.py:582-588` — if first attempt fails, waits 3 seconds and retries once.
3. Added structured error logging to `PagerDutyClient.resolve_incident()` in `aws/shared/clients.py`.

---

### ~~OPEN-3. No Slack Activity by the Bot — All Slack Operations May Be Failing Silently~~ FULLY RESOLVED (Feb 18, 2026)

**Status:** RESOLVED — Slack token validation and health checks now in place.

**Original Symptom:** No visible Slack activity from the bot in incident channels — all Slack operations were silently failing.

**Root Cause:** `SlackClient` methods return `{'ok': False, 'error': 'no_token'}` when token is empty, and the controller never checked these return values. The demo flow completed "successfully" even when Slack was completely non-functional.

**Fix Applied (Feb 18, 2026):**
1. Added `SlackClient.verify_token()` method (`aws/shared/clients.py:601-612`) — calls `auth.test` to validate token
2. Added Slack health check at start of `run_demo_flow()` (`handler.py:609-613`) — logs `SLACK TOKEN INVALID` at ERROR level if token is broken, providing immediate visibility
3. Added error logging for `post_as_user` resolve message (`handler.py:591-593`) — logs failure reason
4. `SLACK_TEAM_ID` now explicitly set on controller Lambda (`aws/main.tf:612`)

**Remaining Design Choice:** Slack failures still don't halt the demo flow. This is intentional — PagerDuty operations (acknowledge, notes, resolve) should complete even if Slack is down. The Slack health check at startup provides early warning in CloudWatch logs.

---

## ~~CRITICAL OPEN ISSUES (Blocking Live Demos)~~ ALL RESOLVED (Historical)

> **As of February 18, 2026, ALL issues (original critical + Feb 17 OPEN issues) are resolved.** The items below are preserved for historical context.

### ~~0. Workflow-to-Lambda Integration~~ FULLY RESOLVED (Feb 9-14, 2026)

> **Status:** FULLY RESOLVED — Controller Lambda handles the complete incident lifecycle including conversations.

**Original Problem:** PagerDuty Incident Workflows were not communicating with the demo-orchestrator Lambda.

**Root Causes Found & Fixed (Feb 9, 2026):**
1. **PagerDuty API Key Misconfiguration:** Lambda code looked for `PAGERDUTY_TOKEN` env var but was configured with `PAGERDUTY_API_KEY`. Fixed by adding both env vars.
2. **Slack Enterprise Grid:** The Slack workspace is Enterprise Grid, requiring `team_id` parameter in `conversations.list` API calls. Fixed by adding `SLACK_TEAM_ID=T0A9LN53CPQ` env var.
3. **Slack Channel Pattern Mismatch:** Lambda searched for `inc-*` channels but workflows create `demo-*` channels. Fixed channel search pattern.
4. **Webhook Signature Verification:** N/A — PagerDuty webhook PILGGJ0 was deleted Feb 17. The controller does not use webhooks.

**Final State (Feb 17, 2026):** The `demo-simulator-controller` Lambda runs the full incident lifecycle: trigger → acknowledge → multi-phase conversations with user impersonation → resolve. The webhook (PILGGJ0) was deleted Feb 17 as non-functional (Lambda Function URLs return 403). The orchestrator Lambda is accessible via API Gateway for `/health`, `/status`, `/trigger`, `/cleanup` endpoints.

### ~~0.5. Slack Responder Conversations~~ FULLY RESOLVED (Feb 11-14, 2026)

> **Status:** FULLY RESOLVED — The `demo-simulator-controller` Lambda handles multi-phase conversations with scenario-specific messages and user impersonation.

**Original Problem:** Slack channels were created but stayed empty (no simulated conversation).

**Resolution:** The `demo-simulator-controller` Lambda (built Feb 11-14) handles phased investigation messages (investigating → found_issue → working_fix → resolved) with scenario-specific content, user impersonation via `chat:write.customize`, and configurable delays. The `lambda-lifecycle` Lambda also has `post_conversation()` as a supplementary mechanism.

---

### ~~1. Events MUST Include `class`/`component` Fields for Routing~~ RESOLVED (Feb 14, 2026)

**Status:** RESOLVED — All 47 enabled scenarios include correct routing fields and route successfully.

**Problem:** Events sent to the Global Event Orchestration routing key fall through to "Default Service - Unrouted Events" unless they include specific fields.

**Root Cause:** The 12 routing rules check `event.class`, `event.component`, and `event.custom_details.*` fields - NOT the event `summary`.

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

**Working Example (Validated Feb 9, 2026):**
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
This routes to **Database Reliability** service correctly. Test incident Q2EE76G7QQE3UX confirmed working.

**Next Step:** Update all 66 scenario event payloads to include appropriate `class`/`component`/`custom_details` fields.

---

### ~~2. 66 Scenarios Not Fully Wired~~ ✅ RESOLVED (February 14, 2026)

**Status:** RESOLVED — 47 of 66 scenarios enabled and E2E validated (100% pass rate via `scripts/test_all_scenarios.py`). 19 scenarios disabled pending external integration setup (ServiceNow, Grafana, UptimeRobot, Splunk, Sentry).

**What Was Done:**
- All 47 enabled scenario event payloads include correct `class`/`component`/`custom_details` routing fields
- Event Orchestration routes all enabled scenarios to their target services
- Full E2E validation: trigger → routing → incident → workflow → Slack → acknowledgment → resolution

---

## RESOLVED ISSUES (February 9, 2026)

### 1. ~~Incidents Not Being Auto-Acknowledged~~ ✅ FIXED

**Problem:** Demo incidents were not automatically progressing through their lifecycle. They stayed in "triggered" state indefinitely.

**Root Cause:** Demo users (Jim Beam, Jack Daniels, etc.) had "observer" role in PagerDuty. The "observer" role does NOT have permission to acknowledge incidents via API.

**Solution:** Changed all demo users from "observer" to "responder" role (appears as "limited_user" in API).

**How the Fix Was Applied:**
1. User manually updated roles in PagerDuty Admin UI
2. Verified via API: `GET /users/{id}` shows `role: "limited_user"`
3. Tested: `PUT /incidents/{id}` with `status: acknowledged` now succeeds

**IMPORTANT FOR FUTURE:** When adding new demo users, ensure they have "responder" role, NOT "observer". Observer role appears to have full access but cannot modify incidents via API.

---

### 2. ~~Demo Owner Not Added to Slack Channels~~ ✅ FIXED

**Problem:** When demo incident channels were created, observers were not being added to the channel.

**Root Cause:** The `conversations.invite` call was attempting to add multiple users in a single API call. While this should work, Slack's API sometimes fails silently for specific users.

**Solution:** Modified `invite_users_to_channel` function to invite users one-by-one with individual error handling.

**Files Modified:**
- `aws/lambda-demo-orchestrator/handler.py`
- `aws/shared/clients.py`
- `aws/lambda-package/handler.py`

**Code Pattern:**
```python
def invite_users_to_channel(channel_id, user_ids):
    for user_id in user_ids:
        try:
            slack.conversations_invite(channel=channel_id, users=user_id)
        except SlackApiError as e:
            if "already_in_channel" not in str(e):
                logger.warning(f"Could not invite {user_id}: {e}")
```

**Observer Slack IDs (must be added to all demo channels):**
| Email | Slack ID |
|-------|----------|
| conalllynch88@gmail.com | U0A9GBYT999 |
| clynch@pagerduty.com | U0A9KAMT0BF |

---

### 3. ~~PagerDuty API Token Insufficient Permissions~~ - FIXED (February 9, 2026)

**Problem:** Responders were not acknowledging incidents in PagerDuty when the Lambda tried to acknowledge on their behalf.

**Root Cause:** The PagerDuty API token belonged to Arthur Guinness with `limited_user` role. A `limited_user` token can only perform actions the user themselves could do - it CANNOT act on behalf of other users (e.g., acknowledge incidents as Jim Beam).

**Symptoms:**
- Lambda logs showed: `Failed to acknowledge: User ... cannot acknowledge incident`
- API returned 400/403 errors when acknowledging incidents with `From` header set to another user

**Solution:** Updated the PagerDuty API token to an admin-level token (see `docs/CREDENTIALS_REFERENCE.md`) which has permission to act on behalf of any user in the account.

**How to Verify Token Role:**
```bash
curl -s "https://api.pagerduty.com/users/me" \
  -H "Authorization: Token token=YOUR_TOKEN" | jq '.user | {name, role}'
```

**CRITICAL FOR FUTURE:**
- Admin tokens can acknowledge incidents as any user (using `From:` header)
- `limited_user` tokens can ONLY acknowledge incidents where that user is assigned
- Always verify the token role when troubleshooting acknowledgment issues

---

### 4. ~~Slack Bot Token Missing Scopes / SLACK_TEAM_ID Required~~ - FIXED (February 9, 2026)

**Problem:** Slack API calls returned `missing_scope` errors and `conversations.list` returned empty results.

**Root Causes (Multiple):**
1. **Wrong token type:** Initially a Slack user token (`xoxp-*`) was used; it lacked required scopes
2. **Enterprise Grid requirement:** The Slack workspace is Enterprise Grid, which requires `team_id` parameter in API calls
3. **Missing environment variable:** Lambda didn't have `SLACK_TEAM_ID` configured

**Symptoms:**
- `SLACK_SEARCH: API error response - missing_scope` in Lambda logs
- `conversations.list` returned empty `channels: []` even though channels existed
- Channel search for `demo-*` patterns found nothing

**Solution Applied:**
1. Switched to the documented Slack bot token (see `docs/CREDENTIALS_REFERENCE.md`)
2. Added `SLACK_TEAM_ID=T0A9LN53CPQ` environment variable to Lambda
3. Updated Lambda code to pass `team_id` parameter to `conversations.list`

**Required Slack Bot Token Scopes:**
- `channels:read` - List and read channel info
- `channels:join` - Join public channels
- `channels:manage` - Manage channels
- `chat:write` - Post messages
- `chat:write.customize` - Post with custom username/icon (for user impersonation)
- `users:read` - Read user profiles
- `groups:read` - Read private channels

**Environment Variables Required:**
```
SLACK_BOT_TOKEN=<see CREDENTIALS_REFERENCE.md>
SLACK_TEAM_ID=T0A9LN53CPQ
```

**CRITICAL FOR FUTURE:** For Enterprise Grid workspaces, ALWAYS include `team_id` parameter in Slack API calls, or the API will return empty/incomplete results.

---

### 5. ~~Lambda iam:PassRole Permission Error~~ - FIXED (February 9, 2026)

**Problem:** Lambda failed to schedule actions via EventBridge Scheduler with `AccessDeniedException`.

**Error Message:**
```
AccessDeniedException: User arn:aws:sts::127214181728:assumed-role/demo-orchestrator-lambda-role/demo-simulator-orchestrator-v2
is not authorized to perform: iam:PassRole on resource: arn:aws:iam::127214181728:role/demo-scheduler-role
```

**Root Cause:** Mismatch between the scheduler role name in Lambda config vs the actual IAM role:
- Lambda `SCHEDULER_ROLE_ARN` was set to: `arn:aws:iam::127214181728:role/demo-scheduler-role` (doesn't exist)
- Actual IAM role created by Terraform: `arn:aws:iam::127214181728:role/demo-scheduler-invoke-role`

**Solution:** Updated Lambda environment variable to use the correct role:
```bash
aws lambda update-function-configuration \
  --function-name demo-simulator-orchestrator-v2 \
  --environment "Variables={...,SCHEDULER_ROLE_ARN=arn:aws:iam::127214181728:role/demo-scheduler-invoke-role,...}" \
  --region us-east-1
```

**CRITICAL FOR FUTURE:**
- The Terraform-managed role is `demo-scheduler-invoke-role` (defined in `aws/main.tf`)
- The Lambda IAM role must have `iam:PassRole` permission for this scheduler role
- Always verify the role exists: `aws iam get-role --role-name demo-scheduler-invoke-role`

---

### 6. ~~Bot Posting as "Oauth APP" Instead of User~~ - FIXED (February 9, 2026)

**Problem:** The "Team assembled for incident response" message in Slack appeared as posted by "Oauth APP" (the bot identity) rather than appearing as if posted by a responder.

**Root Cause:** The message was posted using `slack.post_message()` without specifying a username/icon, causing it to use the bot's default identity.

**Location:** `aws/lambda-demo-orchestrator/handler.py` line 728 in `on_workflow_completed()`:
```python
# Before (posted as bot):
slack.post_message(channel_id, "Team assembled for incident response. Let's investigate.")

# After (posted as first responder):
if state.get('responders'):
    first_responder = state['responders'][0]
    slack.post_as_user(
        first_responder.get('slack_id', ''),
        channel_id,
        "Team assembled for incident response. Let's investigate."
    )
```

**Solution:** Modified the code to use `slack.post_as_user()` which posts with the user's display name and avatar.

**CRITICAL FOR FUTURE:**
- Use `slack.post_as_user(user_slack_id, channel_id, message)` for messages that should appear as a specific user
- Use `slack.post_message(channel_id, message)` only for system/bot messages
- The "APP" badge still appears (Slack API limitation), but the username and avatar match the user

---

### 7. Demo Responder Limitation - Only 6 Users Have Slack Accounts

**IMPORTANT:** Only these 6 demo responders have BOTH PagerDuty AND Slack accounts. All demo scenarios MUST only use these users:

| Name | Email | PagerDuty ID | Slack ID |
|------|-------|--------------|----------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U0AA1LZSYHX |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U0A9GC08EV9 |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U0AA1LYLH2M |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U0A9LN3QVC6 |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U0A9KANFCLV |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U0A9SBF3MTN |

**Why this matters:** If a scenario assigns a responder without a Slack account, the Lambda will fail to post messages on their behalf, breaking the demo flow.

**Mapping Location:** `aws/shared/clients.py` and `variables_and_locals.tf`

---

### 4. ~~Datadog Monitors Using Wrong Service Name~~ ✅ FIXED (February 9, 2026)

**Problem:** Datadog monitors were configured to send to `@pagerduty-Los-Andes-Demo`, but this service didn't exist in the Datadog-PagerDuty integration.

**Root Cause:** Mismatch between monitor configuration and integration setup:
- Integration configured service: `demo-simulator-alerts` (routing key)
- Monitors sending to: `@pagerduty-Los-Andes-Demo` (invalid)

**Solution Applied:**
1. Updated monitors 17717886 and 17717887 to use `@pagerduty-demo-simulator-alerts`
2. Updated the Datadog PagerDuty integration routing key to use the Global Event Orchestration key: `R028NMN4RMUJEARZ18IJURLOU1VWQ779`

**Verification:**
```bash
# Check integration
curl -s "https://api.us5.datadoghq.com/api/v1/integration/pagerduty" \
  -H "DD-API-KEY: $DATADOG_API_KEY" \
  -H "DD-APPLICATION-KEY: $DATADOG_APP_KEY"
```

---

### 5. ~~Workflow Trigger Not Firing for [DEMO] Incidents~~ ✅ FIXED (February 9, 2026)

**Problem:** The "Demo Incident Channel Setup" workflow (PUXIPNC) was not firing for incidents with `[DEMO]` in the title despite correct API configuration.

**Root Cause:** Workflow trigger configuration issue in PagerDuty UI (specific fix applied by user in web interface).

**Solution:** User fixed the workflow trigger configuration in PagerDuty web UI.

**E2E Validation (February 9, 2026):**
Successfully validated full end-to-end flow:
1. Event sent to Global Orchestration routing key
2. Routed to "Database Reliability" service (via `class: database`, `component: redis`)
3. Workflow fired automatically
4. Slack channel created: `#demo-314-demo-e2e-workflow-`
5. Conference bridge populated
6. Arthur Guinness acknowledged the incident
7. Auto-resolve scheduled for 4 hours

**Test Command:**
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

---

## PagerDuty API Gotchas

### 1. The Admin Token Cannot Do Everything

**Problem:** An API key with "admin" scope can still return `403 User not permitted to create workflow`.

**Why:** PagerDuty distinguishes between:
- **API Keys** (account-level): Used for most operations
- **API User Tokens** (user-level): Required for workflow/trigger creation

**Solution:** For workflow operations, use the API User Token (format: `u+...`). The token must be from a user with appropriate permissions.

**Token Reference:** See `docs/CREDENTIALS_REFERENCE.md` for current tokens.
```
Admin API Key:    <see CREDENTIALS_REFERENCE.md>  (read operations, Terraform)
API User Token:   <see CREDENTIALS_REFERENCE.md>  (workflow/trigger operations)
```

---

### 2. The `From` Header Requirement

**Problem:** PUT/POST requests to update incidents require a `From` header with the user's email, not the token.

**Why:** PagerDuty tracks who made changes via this header.

**Solution:** Always include `From` header with a valid PagerDuty user email:
```python
headers = {
    'Authorization': f'Token token={TOKEN}',
    'Content-Type': 'application/json',
    'From': 'jbeam@losandesgaa.onmicrosoft.com'  # Any demo user email
}
```

**Available User Emails (demo users with "responder" role):**
| User | Email |
|------|-------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com |

---

### 3. Event Type Naming is Inconsistent

**Problem:** You might search for `workflow.completed` events. The actual event type is `incident.workflow.completed`.

**Rule:** All incident-related webhook events have the `incident.` prefix:
- `incident.triggered` (not `triggered`)
- `incident.acknowledged` (not `acknowledged`)
- `incident.resolved` (not `resolved`)
- `incident.workflow.completed` (not `workflow.completed`)

---

### 4. Workflow Action ID Versioning

**Problem:** Workflow action IDs include version numbers that change.

**Example:** `pagerduty.com:slack:create-a-channel:4` - the `:4` is the version.

**Solution:** Query the actions endpoint to get current versions:
```bash
curl -s -H "Authorization: Token token=$TOKEN" \
  "https://api.pagerduty.com/incident_workflows/actions" | jq '.actions[] | .id'
```

**Current Action IDs (as of Feb 2026):**
| Action | ID |
|--------|-----|
| Create Slack Channel | `pagerduty.com:slack:create-a-channel:4` |
| Add Conference Bridge | `pagerduty.com:incident-workflows:add-conference-bridge:1` |
| Add Note | `pagerduty.com:incident-workflows:add-notes-to-incident:1` |
| Create Jira Ticket | `pagerduty.com:jiracloud:create-jira-cloud-issue:4` |

---

### 5. Workflow Trigger Service Subscriptions

**Problem:** A workflow trigger with no service subscriptions never fires.

**Symptoms:** Workflow exists, trigger exists, but nothing happens when incident created.

**Check:**
```bash
curl -s -H "Authorization: Token token=$TOKEN" \
  "https://api.pagerduty.com/incident_workflows/triggers" | \
  jq '.triggers[] | {id: .id, workflow: .workflow.id, services: (.subscribed_to_all_services // .services | length)}'
```

**Solution:** Either:
1. Set `subscribed_to_all_services: true`, OR
2. Explicitly list service IDs in `services` array

We deleted 9 orphaned triggers (zero subscriptions) during Phase 1.

---

## Slack API Gotchas

### 1. Bot Token Lacks `channels:write` Scope

**Problem:** The Slack bot token cannot create channels.

**Error:** `missing_scope` when calling `conversations.create`

**Solution:** Use PagerDuty's native Slack workflow action to create channels. The Lambda function only joins existing channels.

---

### 2. Bot Must Join Channel Before Posting

**Problem:** `not_in_channel` error when posting messages.

**Solution:** Always call `conversations.join` before `conversations.postMessage`:
```python
slack_client.conversations_join(channel=channel_id)
slack_client.chat_postMessage(channel=channel_id, text=message)
```

---

### 3. Slack `conversations.list` Requires `team_id`

**Problem:** `missing_argument` error when listing channels.

**Solution:** Include `team_id` parameter:
```python
response = slack_client.conversations_list(
    team_id="T0A9LN53CPQ",
    types="public_channel",  # Bot lacks groups:read for private
    limit=1000
)
```

---

### 4. Bot Lacks `groups:read` Scope

**Problem:** Cannot list private channels.

**Solution:** Only use `types=public_channel` in API calls:
```python
types="public_channel"  # NOT "public_channel,private_channel"
```

---

### 5. Bot Posts As Itself, NOT As Users (RESOLVED)

**Problem:** All messages posted via the Slack bot token appear as coming from the app ("PagerDuty Demo Bot"), not from individual users like "Jim Beam" or "Jack Daniels".

**Why:** Slack's `chat.postMessage` API with a bot token always posts as the bot. To truly post as a user, you need individual user OAuth tokens.

**Solution Implemented (February 8, 2026):** The `SlackClient` class in `aws/lambda-demo-orchestrator/handler.py` and `aws/shared/clients.py` now includes:
1. `get_user_profile(slack_user_id)` - Fetches user display name and avatar from Slack API
2. `post_as_user(channel, text, user)` - Posts messages with the user's name and avatar
3. Profile caching to avoid repeated API calls

**How it works:**
```python
slack.post_as_user(channel_id, "Looking into this now...", user)
```

This internally calls `chat.postMessage` with:
- `username`: User's Slack display name
- `icon_url`: User's Slack avatar URL

**Note:** Messages still show an "APP" badge next to the username, making it clear they're from a bot. This is a Slack API limitation that cannot be avoided without user OAuth tokens. However, for demo purposes, the visual appearance of user-specific names and avatars is sufficient.

---

## Jira Integration Gotchas

### 1. Account Mapping ID is Required

**Problem:** Jira workflow actions fail without the Account Mapping ID.

**Solution:** The Account Mapping ID is the PagerDuty Extension ID:
```
Account Mapping ID: PUWL8VU
```

**How to Find:**
```bash
curl -s -H "Authorization: Token token=$TOKEN" \
  "https://api.pagerduty.com/extensions" | jq '.extensions[] | {id: .id, name: .name}'
```

---

### 2. Jira Project IDs vs Keys

**Problem:** Jira API uses project IDs (numbers), not keys (DEMO).

**Project Reference:**
| Key | ID | Name |
|-----|-----|------|
| COMP | 10068 | Compliance |
| DATA | 10072 | Data Engineering |
| DEMO | 10034 | Demo service space |
| INFRA | 10069 | Infrastructure |
| KAN | 10000 | Los Andes Initial |
| PAY | 10071 | Payments |
| PIR | 10070 | Post Incident Reviews |
| SECOPS | 10067 | Security Operations |

---

### 3. Jira Issue Type for Incidents

**Problem:** Need correct issue type ID for Incident.

**Solution:**
```
Issue Type ID: 10004
Issue Type Name: Incident
```

---

## Terraform Limitations

### 1. Terraform Cannot Create Workflow Steps

**Problem:** `pagerduty_incident_workflow` resource creates empty workflow shells.

**Why:** The Terraform provider doesn't support the `steps` attribute.

**Solution:** Create workflows via Terraform, then populate steps via API:
```bash
python scripts/populate_workflow_steps.py
```

---

### 2. Terraform Import Errors on Triggers

**Problem:** `terraform import` for workflow triggers fails with obscure errors.

**Solution:** Create triggers via API, not Terraform. Use `scripts/fix_workflow_trigger.py` pattern.

---

## Workflow Configuration Gotchas

### 1. Input Parameter Format

**Problem:** Workflow step inputs have specific format requirements.

**Correct Format:**
```python
{
    "name": "Step Name",
    "action_configuration": {
        "action_id": "pagerduty.com:...",
        "inputs": [
            {"name": "Parameter Name", "parameter_type": "text", "value": "..."}
        ]
    }
}
```

**Common Mistakes:**
- Using `type` instead of `parameter_type`
- Missing `action_configuration` wrapper
- Wrong `action_id` version

---

### 2. Slack Workspace ID in Workflow Steps

**Problem:** Slack channel creation steps need workspace ID.

**Solution:** Include in inputs:
```python
{"name": "Slack Workspace", "parameter_type": "text", "value": "T0A9LN53CPQ"}
```

---

## AWS/Lambda Gotchas

### 1. Two Different AWS Regions

**Problem:** Resources split across regions.

| Component | Region |
|-----------|--------|
| RBA Runner, Traffic Lambdas | us-east-1 |
| demo-orchestrator V1 (legacy), DynamoDB | eu-west-1 |
| **demo-simulator-orchestrator-v2 (ACTIVE)** | **us-east-1** |

**Solution:** Always specify region in AWS CLI commands. For the ACTIVE demo orchestrator:
```bash
aws lambda get-function --function-name demo-simulator-orchestrator-v2 --region us-east-1
```

---

### 2. Lambda Timeout for API Calls

**Problem:** PagerDuty API calls can be slow, causing Lambda timeouts.

**Solution:** Use timeouts in requests:
```python
requests.get(url, headers=headers, timeout=10)
```

---

### 3. Lambda Environment Variable Names Matter (CRITICAL)

**Problem:** Lambda code uses `PAGERDUTY_TOKEN` but Terraform configures `PAGERDUTY_API_KEY`.

**Root Cause (Feb 9, 2026):** The Lambda handler code in `handler.py` reads:
```python
self.token = os.environ.get('PAGERDUTY_TOKEN', '')
```

But Terraform and the Lambda configuration used `PAGERDUTY_API_KEY`.

**Solution:** Configure BOTH environment variables in the Lambda:
```bash
aws lambda update-function-configuration \
  --function-name demo-simulator-orchestrator-v2 \
  --environment "Variables={PAGERDUTY_TOKEN=<token>,PAGERDUTY_API_KEY=<token>,SLACK_TOKEN=<slack-bot-token>,SLACK_TEAM_ID=T0A9LN53CPQ}" \
  --region us-east-1
```

**Required Lambda Environment Variables:**
| Variable | Value | Purpose |
|----------|-------|---------|
| `PAGERDUTY_TOKEN` | See `CREDENTIALS_REFERENCE.md` | PagerDuty API authentication |
| `PAGERDUTY_API_KEY` | See `CREDENTIALS_REFERENCE.md` | Alternative PagerDuty API key |
| `SLACK_TOKEN` | See `CREDENTIALS_REFERENCE.md` | Slack API auth |
| `SLACK_TEAM_ID` | `T0A9LN53CPQ` | Required for Enterprise Grid |

---

### 4. Manual Lambda Deployment Required

**Problem:** Terraform doesn't automatically update Lambda code; you must manually deploy changes.

**Solution:** Deploy the Lambda function manually after code changes:
```bash
cd lambda/
rm -f ../handler.zip
zip -r ../handler.zip . -q
aws lambda update-function-code \
  --function-name demo-simulator-orchestrator-v2 \
  --zip-file fileb://../handler.zip \
  --region us-east-1
```

**Note:** The Lambda deployment package must include the `requests` library. The current package includes it.

---

### 5. Lambda Function Versions

| Version | Function Name | Region | Status |
|---------|---------------|--------|--------|
| V1 | `demo-orchestrator` | eu-west-1 | Legacy, not in use |
| V2 | `demo-simulator-orchestrator-v2` | us-east-1 | **ACTIVE** |

**Always use V2** (`demo-simulator-orchestrator-v2` in `us-east-1`).

---

## E2E Testing Gotchas

### 1. Timing Between Steps

**Problem:** PagerDuty workflows don't execute instantly.

**Solution:** Add delays between test steps:
```python
time.sleep(10)  # Wait for workflow to trigger
time.sleep(30)  # Wait for Slack channel creation
```

---

### 2. Channel Name Patterns

**Problem:** Channel names can use different prefixes.

**Patterns Seen:**
- `demo-*` (from Demo workflow)
- `inc-*` (from Standard workflow)
- `demo_inc_*` (from API-triggered incidents)

**Solution:** Match multiple patterns in E2E tests:
```python
if chan['name'].startswith(('demo-', 'inc-', 'demo_inc_')):
```

---

### 3. Assignee Email Lookup

**Problem:** Need email for `From` header when acknowledging incidents.

**Solution:** Map user IDs to emails:
```python
USER_EMAILS = {
    "PT49N1K": "alex.chen@pdt-losandes.pagerduty.com",
    "PMDH91S": "sarah.kim@pdt-losandes.pagerduty.com",
    # ...
}
```

---

## Quick Reference

### Essential IDs

| Item | Value |
|------|-------|
| PagerDuty Subdomain | pdt-losandes |
| Slack Workspace ID | T0A9LN53CPQ |
| Jira Account Mapping | PUWL8VU |
| Demo Workflow ID | PUXIPNC |
| Default Routing Key | 94e4c195... (K8s service) |

### Test Commands

```bash
# Test PagerDuty API
curl -s -H "Authorization: Token token=$PD_TOKEN" \
  "https://api.pagerduty.com/users/me" | jq '.user.name'

# Run E2E tests
python scripts/e2e_test.py

# Verify Jira steps (archived to scripts/archive/)
# python scripts/archive/verify_jira_steps.py

# Analyze triggers (archived to archive/scripts-oneoff/)
# python archive/scripts-oneoff/analyze_triggers.py
```

---

## Status Page API Gotchas

### 1. Status Page API Rewrite (February 14, 2026) {#status-page-api-rewrite}

**Problem:** The original `create_incident` and `update_incident` functions in `scripts/status_page_manager.py` used incorrect endpoints and payload structures, returning 400/404 errors from the PagerDuty Status Page API.

**Root Cause:** The Status Page API has a non-obvious data model. Creating or updating a "status page incident" is actually done through the **Posts** API, not a dedicated incidents endpoint. The payload requires object references (not raw strings) for `status`, `severity`, `impact`, and `impacted_services`.

**What Was Rewritten:**
- `create_incident()` now uses `POST /status_pages/{id}/posts` with `post_type: "incident"`
- `update_incident()` now uses `POST /status_pages/{id}/posts/{post_id}/post_updates`
- Added helper functions to fetch valid values: `get_status_page_statuses()`, `get_status_page_severities()`, `get_status_page_impacts()`, `get_status_page_services()`
- Added `find_by_name()` helper for case-insensitive lookup of API-returned objects

**Correct Payload Structure (create):**
```python
{
    "post": {
        "post_type": "incident",
        "title": "...",
        "starts_at": "ISO8601",
        "ends_at": "ISO8601",
        "status": {"id": "STATUS_ID"},
        "severity": {"id": "SEVERITY_ID"},
        "impact": {"id": "IMPACT_ID"},
        "impacted_services": [{"id": "SVC_ID"}],
        "updates": [{
            "update_frequency_ms": 1800000,
            "body": "...",
            "status": {"id": "STATUS_ID"},
            "severity": {"id": "SEVERITY_ID"},
            "impacted_services": [{"id": "SVC_ID"}]
        }]
    }
}
```

**Key Gotcha:** You MUST fetch the valid `status`, `severity`, `impact`, and `impacted_services` objects from the API first. These are account-specific and cannot be hardcoded. The helper functions in `status_page_manager.py` handle this.

---

### 2. Status Page API Endpoints Are Not RESTful

**Problem:** You might expect CRUD endpoints like `POST /status_pages/{id}/incidents`. This endpoint does not exist.

**Correct Endpoints:**
| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create incident post | `/status_pages/{id}/posts` | POST |
| Update incident post | `/status_pages/{id}/posts/{post_id}/post_updates` | POST |
| List posts | `/status_pages/{id}/posts` | GET |
| Get post | `/status_pages/{id}/posts/{post_id}` | GET |

**Note:** "Incidents" on a status page are just posts with `post_type: "incident"`. There is no separate incidents resource.

---

## Slack Channel Invite Gotchas

### 1. Batch Invite Fails Silently — Use One-by-One (February 14, 2026) {#slack-invite-fix}

**Problem:** Slack's `conversations.invite` API accepts a list of user IDs, but when one user in the batch fails (e.g., `already_in_channel`, `cant_invite_self`), the entire batch fails and no other users are invited. The error is not always propagated clearly.

**Root Cause:** The batch `conversations.invite` endpoint treats the user list atomically. If any single user fails validation, the whole call returns an error and no users are added.

**Fix Applied:** `SlackClient.invite_users_to_channel()` in `aws/shared/clients.py` now iterates through users one at a time, calling `invite_user_to_channel()` for each and handling `already_in_channel` and `cant_invite_self` errors gracefully per-user.

```python
def invite_users_to_channel(self, channel_id, user_ids):
    for user_id in user_ids:
        try:
            self.invite_user_to_channel(channel_id, user_id)
        except SlackApiError as e:
            if e.response['error'] in ('already_in_channel', 'cant_invite_self'):
                continue
            raise
```

**Additional Fix:** The `lambda-lifecycle` handler now explicitly invites both `CONALL_SLACK_USER_ID` and `CONALL_SLACK_USER_ID_PERSONAL` to incident Slack channels when a triggered incident is acknowledged, ensuring the demo owner always has visibility.

---

### 2. Observer Must Be Explicitly Invited

**Problem:** The demo owner's Slack accounts (`U0A9GBYT999`, `U0A9KAMT0BF`) were not being added to incident channels because they are not PagerDuty responders.

**Solution:** The lifecycle Lambda explicitly invites these user IDs alongside the demo responders mapped from the incident. This is hardcoded in `aws/shared/clients.py` as `CONALL_SLACK_USER_ID` and `CONALL_SLACK_USER_ID_PERSONAL`.

---

## Datadog Trial Expiry Handling {#datadog-trial-expiry}

### 1. Datadog API Key May Be Invalid/Expired

**Problem:** The Datadog account uses a trial API key. When the trial expires, the API returns 403 errors. The demo must continue to function without Datadog.

**How Each Lambda Handles This:**

| Lambda | Behavior When Datadog Key Is Invalid |
|--------|--------------------------------------|
| `lambda-demo-orchestrator` | `trigger_datadog()` fails gracefully; `handle_trigger()` falls back to `trigger_pagerduty_events()` (direct PagerDuty Events API call). Demo scenarios still fire. |
| `lambda-metrics-pkg` | `send_metrics()` / `send_logs()` return `{'status': 'skipped'}` if key is missing, or `{'status': 'error', 'code': 403}` if key is expired. No crash, but metrics/logs will not reach Datadog. There is no fallback to PagerDuty from this Lambda for metrics. |
| `lambda-health-check` | `check_datadog()` reports status as `SKIPPED` (key missing) or `FAILED` (key invalid). Does not crash. |

**Key Point:** The orchestrator's Datadog-to-PagerDuty fallback means demo scenarios that would normally route through Datadog monitors will still create PagerDuty incidents via the Events API v2 directly. The demo experience is preserved, but the Datadog integration step is skipped in the monitoring tool chain.

**To Re-enable Datadog:** Obtain a new API key from Datadog, then update the `DATADOG_API_KEY` environment variable on all three Lambdas. Run the health check to verify:
```bash
aws lambda invoke --function-name demo-simulator-health-check --payload '{}' /tmp/health-output.json && cat /tmp/health-output.json
```

> **NOTE:** Lambda Function URLs on this account return 403 Forbidden. Always use `aws lambda invoke` or the orchestrator API Gateway (`https://ynoioelti7.execute-api.us-east-1.amazonaws.com/health`) instead.

---

## ACTION ITEMS / TODOs (February 18, 2026)

> Items below require investigation or decisions. They are NOT blocking live demos.

### TODO-1. Slack Failures: No User-Facing Alerting

**Current State:** The Slack health check (`handler.py:609-613`) logs `SLACK TOKEN INVALID` at ERROR level, and `post_as_user`/`invite_user_to_channel` failures log errors. However, these only appear in CloudWatch Logs. **There is no proactive alert to the demo owner** (e.g., Slack DM, email, or PagerDuty incident).

**Action Required:** Decide if the demo owner should be alerted when Slack operations fail. Options:
1. Add a CloudWatch Alarm on the `SLACK TOKEN INVALID` log pattern → SNS → email/Slack notification
2. Have the controller return `slack_healthy: false` in its response payload so the dashboard can display a warning
3. Accept current CloudWatch-only logging (current behavior — requires manual log checking)

---

### TODO-2. RBA Runner EC2 Instance — MUST DELETE, Violates Zero-Cost Policy

> **ZERO-COST POLICY:** All infrastructure must be free or effectively zero-cost. EC2 instances are NOT acceptable — they incur hourly charges even when idle. See `NEXT_DEVELOPER_PROMPT.md` "READ THIS FIRST" for the full policy.

**Current State:** The RBA Runner is defined in `aws/main.tf:990` as `aws_instance.rba_runner` (instance ID `i-03ab4fd5f509a8342`). The Terraform config provisions a `t3.micro` EC2 instance with a security group, IAM role, and instance profile. **This MUST be deleted.**

**Action Required:**
1. Verify the instance is terminated in AWS Console or via CLI: `aws ec2 describe-instances --instance-ids i-03ab4fd5f509a8342 --query 'Reservations[].Instances[].State'`
2. If still running, terminate it: `aws ec2 terminate-instances --instance-ids i-03ab4fd5f509a8342`
3. Remove the EC2 instance, security group, IAM role, instance profile, and related outputs from `aws/main.tf` (lines ~945-1053) to prevent re-creation on next `terraform apply`
4. Remove `rba_runner_token` and `rba_runner_id` variables (lines ~906-915)
5. Run `terraform state rm aws_instance.rba_runner` if already terminated outside Terraform

**Free RBA Alternative (No Local Dependencies, No Self-Hosted Runners):**
- **Option A (Preferred): PagerDuty Automation Actions with Process Automation Cloud** — PagerDuty's built-in cloud runner executes jobs without any external infrastructure. No EC2, no local install. The 8 existing RBA jobs (`automation_actions.tf`) can use this.
- **Option B: AWS Lambda as automation target** — The controller Lambda is already deployed and pay-per-invocation. Runbook steps could be Lambda functions invoked by PagerDuty via webhook or Automation Actions.
- **Do NOT use:** EC2 instances, ECS tasks, self-hosted Rundeck runners, or any always-on compute.

---

### TODO-3. Lambda Function URLs — Surplus, Consider Removal

**Current State:** Four Lambda Function URLs are defined in Terraform:
- `aws_lambda_function_url.orchestrator` (`aws/main.tf:311`)
- `aws_lambda_function_url.demo_controller` (`aws/main.tf:627`)
- `aws_lambda_function_url.reset` (`aws/main.tf:727`)
- `aws_lambda_function_url.health_check` (`aws/main.tf:732`)
- `aws_lambda_function_url.demo_orchestrator` (`aws/demo_orchestrator.tf:179`)

All return **403 Forbidden** due to an account-level restriction. The controller is invoked via `aws lambda invoke` CLI, not via Function URLs.

**Impact on Functionality:** None. The dashboard Settings modal has an "Orchestrator URL" input field (`SettingsModal.jsx:180-198`) where users can paste a Lambda Function URL, but since all URLs return 403, this feature is non-functional. The dashboard works without it.

**Action Required:**
1. Remove all `aws_lambda_function_url` resources from `aws/main.tf` and `aws/demo_orchestrator.tf`
2. Remove associated outputs (`lambda_function_url`, `health_check_function_url`, `reset_function_url`)
3. Update or remove the "Demo Orchestrator URL" field in `SettingsModal.jsx` (or add a note that it's not currently functional)
4. Run `terraform apply` to clean up

**No cost impact** — Function URLs are free. This is purely a cleanup item.

---

### TODO-4. AIOps/EIM License — Already Active

**Note:** The AIOps/EIM add-on is confirmed active on the `pdt-losandes` account. This means the following features can now be implemented:
- Alert Grouping (DIGOPS-001, AIOPS-002)
- Alert Suppression (DIGOPS-002)
- Auto-Pause Notifications (DIGOPS-003)
- Change Correlation (DIGOPS-007)
- Probable Origin (AIOPS-003)
- AI Scribe (SCRIBE-001 to 003)

See `IMPLEMENTATION_PLAN.md` Phases 6 and 8 for task breakdowns.

---

### TODO-5. Status Page API `create_incident()` Returns Invalid Input

**Current State:** The `scripts/status_page_manager.py` `create_incident()` function (line 269) constructs a POST to `/status_pages/{page_id}/posts` with `post_type: "incident"`. The API returns "Invalid Input" — likely because the `status`, `severity`, and `impact` object references use IDs that don't match the status page's configured enums.

**Root Cause Analysis:**
The script dynamically fetches statuses/severities/impacts from the API (`get_status_page_statuses()`, etc.) and looks them up by name. The "Invalid Input" error likely occurs because:
1. The status page has not been created yet (no page exists to fetch enum values from)
2. The status page exists but has no configured statuses/severities/impacts (defaults not provisioned)
3. The `find_by_name()` lookup (line 265) is matching on wrong casing or name format

**UI Setup Required Before Using the Script:**
1. Go to PagerDuty → Status Pages → Create a new Status Page
2. Configure the subdomain, contact email, and set to Public
3. Add Component Groups and Components matching the services in `STATUS_PAGE_CONFIG` (line 31 of the script)
4. Verify the page has Status, Severity, and Impact values configured (PagerDuty auto-creates defaults)
5. Get the page ID from the URL: `https://pdt-losandes.pagerduty.com/status-pages/{PAGE_ID}`
6. Then run: `python3 scripts/status_page_manager.py list` to verify connectivity
7. Then run: `python3 scripts/status_page_manager.py incident` to test incident creation

**Alternative:** Create the Status Page entirely via the script: `python3 scripts/status_page_manager.py create` — this provisions the page, groups, and components. Then incident creation should work because the enum values will exist.

---

### TODO-6. Terraform Lambda Code Change Detection

**Current State:** Terraform doesn't reliably detect when Lambda function code (Python files) has changed — it only tracks the zip file hash. If you edit `.py` files without re-zipping, `terraform plan` shows no changes.

**This is NOT about deleting the Lambda.** The controller Lambda is the primary execution engine and must remain. The workaround is:
- After editing Python files, re-package the zip: `cd aws && ./package.sh` (or equivalent)
- Or deploy directly via CLI: `aws lambda update-function-code --function-name demo-simulator-controller --zip-file fileb://lambda-demo-controller.zip`
- See `docs/setup/DEPLOYMENT.md` for the full deployment procedure

---

## Event Orchestration Cache Variable Gotchas (February 18, 2026)

### Cache Variable Terraform Provider Version

**Requirement:** `pagerduty_event_orchestration_global_cache_variable` and `pagerduty_event_orchestration_service_cache_variable` resources require PagerDuty Terraform provider **v3.22.0+**. Earlier versions will fail with `Invalid resource type`.

**Fix:** Ensure `required_providers` block specifies `>= 3.22.0`:
```hcl
pagerduty = {
  source  = "PagerDuty/pagerduty"
  version = ">= 3.22.0"
}
```

### Cache Variable TTL Design

**Gotcha:** Cache variable TTL (`ttl_seconds`) determines how long the cached value persists. If TTL is too short, the variable resets before the orchestration rule can use it. If too long, stale data persists.

**Current Settings:**
| Variable | TTL | Rationale |
|----------|-----|-----------|
| `recent_alert_source` | 300s (5min) | Short — only need recent source for routing decisions |
| `critical_event_count` | 600s (10min) | Medium — count critical events within a meaningful window |
| `recent_hostname` | 600s (10min) | Medium — hostname context for correlation |
| `pod_restart_trigger_count` | 300s (5min) | Short — detect restart storms quickly |
| `recent_failing_pod` | 600s (10min) | Medium — keep failing pod context |
| `payment_failure_count` | 300s (5min) | Short — detect payment failure bursts quickly |
| `recent_slow_query_source` | 600s (10min) | Medium — keep DBRE context |

### Cache Variable Conditions Are Required

**Gotcha:** Each cache variable MUST have a `condition` block with an `expression`. Without it, Terraform will error. The condition determines which events update the cache variable — events that don't match the condition are ignored by that variable.

### Service-Level vs Global Cache Variables

**Gotcha:** Service-level cache variables (`pagerduty_event_orchestration_service_cache_variable`) reference a `service` ID, while global cache variables (`pagerduty_event_orchestration_global_cache_variable`) reference an `event_orchestration` ID. Mixing these up causes `404 Not Found` errors during apply.

**File:** All cache variables are in `cache_variables.tf` for easy management.

---

*This document should be updated whenever new gotchas are discovered. Save someone hours of debugging!*
