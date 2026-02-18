# Lambda Lifecycle Simulation - Implementation Guide

**Last Updated:** February 2026
**Status:** ✅ Major Refactor Complete - Shared Module + Demo Controller Implemented
**Primary Files:**
- `aws/shared/clients.py` - Unified PagerDuty and Slack clients
- `aws/lambda-demo-controller/handler.py` - Full demo orchestration (NEW)
- `aws/lambda-lifecycle/handler.py` - Background lifecycle processing

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [February 2026 Major Refactor](#february-2026-major-refactor)
3. [Architecture Overview](#architecture-overview)
4. [Demo Controller Lambda (NEW)](#demo-controller-lambda-new)
5. [User Configuration (CRITICAL)](#user-configuration-critical)
6. [Completed Tasks](#completed-tasks)
7. [Remaining Work](#remaining-work)
8. [Gotchas and Workarounds](#gotchas-and-workarounds)
9. [API Reference](#api-reference)
10. [Testing and Deployment](#testing-and-deployment)

---

## Executive Summary

The Lambda Lifecycle Simulation system automatically progresses `[DEMO]` incidents through realistic states (triggered → acknowledged → resolved) while posting human-like conversation messages to Slack channels.

**The Goal:** Make the demo environment look like a real, active incident response team is working 24/7, without any manual intervention.

**Key Constraint:** Only users who exist in BOTH PagerDuty AND Slack (as full members, not guests) can be used in schedules and simulated in Slack conversations.

---

## February 2026 Major Refactor

A significant refactor was completed that includes:

### 1. Unified Shared Module (`aws/shared/`)
- **Single PagerDutyClient class** used by all Lambdas (previously each had its own)
- **Single SlackClient class** with all needed methods
- **Centralized constants**: `DEMO_USERS`, `PAGERDUTY_TO_SLACK_USER_MAP`, `CONALL_EMAIL`, `CONALL_SLACK_USER_ID`
- Environment variables standardized: `PAGERDUTY_TOKEN` or `PAGERDUTY_ADMIN_TOKEN`

### 2. New Demo Controller Lambda
- **Full orchestrated demo flow**: Reset → Trigger → Ack → Channel → Investigation → Resolution
- **66 scenarios** loaded from `scenarios.json`
- **Pause/Play capability** via API
- **Configurable timing**: 30-60 second delays (via `ACTION_DELAY_MIN`/`ACTION_DELAY_MAX`)
- **Observer mode**: Admin (clynch) never assigned to incidents, only observes

### 3. Fixed Demo Flow Issues
- Observer (clynch@pagerduty.com) no longer assigned to demo incidents
- Slack channel created AFTER fake user acknowledges (not before)
- Admin added to channel as observer, not assignee
- All incident actions performed by fake demo users

### 4. Scenarios.json Integration
- `lambda-orchestrator` and `lambda-demo-controller` load scenarios from file
- Supports all 66 scenarios with IDs like FREE-001, PRO-001, BUS-001, etc.
- Fallback to built-in scenarios if file not found

---

## Architecture Overview

### Lambda Functions Overview (8 Total)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS LAMBDA FUNCTIONS (8 Total)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │  demo-simulator-     │    │  demo-simulator-     │                       │
│  │  CONTROLLER (NEW)    │    │  orchestrator        │                       │
│  │  ─────────────────   │    │  ─────────────────   │                       │
│  │  RECOMMENDED FOR     │    │  Creates random      │                       │
│  │  CONTROLLED DEMOS    │    │  [DEMO] incidents    │                       │
│  │  (on-demand)         │    │  (every hour)        │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │  demo-simulator-     │    │  demo-simulator-     │                       │
│  │  lifecycle           │    │  metrics             │                       │
│  │  ─────────────────   │    │  ─────────────────   │                       │
│  │  Background incident │    │  Sends synthetic     │                       │
│  │  lifecycle mgmt      │    │  metrics to Datadog  │                       │
│  │  (every 15 mins)     │    │  (every 5 mins)      │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │  demo-simulator-     │    │  demo-simulator-     │                       │
│  │  notifier            │    │  reset               │                       │
│  │  ─────────────────   │    │  ─────────────────   │                       │
│  │  Sends DMs to        │    │  Resolves all        │                       │
│  │  admin (Conall)      │    │  [DEMO] incidents    │                       │
│  │  (every 2 mins)      │    │  (on demand)         │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │  demo-simulator-     │    │  demo-simulator-     │                       │
│  │  user-activity       │    │  health-check        │                       │
│  │  ─────────────────   │    │  ─────────────────   │                       │
│  │  Simulates user      │    │  Checks integration  │                       │
│  │  activity on incs    │    │  health status       │                       │
│  │  (on demand)         │    │  (every 15 min)      │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Two Demo Modes

**Mode 1: Controlled Demo (RECOMMENDED) - Demo Controller**
```
User triggers demo → Controller resets all [DEMO] incidents
                   → Triggers scenario incident
                   → Waits 30-60 seconds
                   → Fake user acknowledges
                   → Creates Slack channel, adds observer
                   → Posts investigation messages
                   → Posts progress updates (with delays)
                   → Fake user resolves
```

**Mode 2: Background Simulation - Orchestrator + Lifecycle**
```
Orchestrator (hourly) → Creates random [DEMO] incidents
Lifecycle (15 min)    → Processes all [DEMO] incidents automatically
                      → Less predictable timing, no pause/play
```

---

## Demo Controller Lambda (NEW)

The `demo-simulator-controller` is the recommended way to run controlled demos.

### API Endpoints

| Action | Payload | Description |
|--------|---------|-------------|
| `run` | `{"action": "run", "scenario_id": "PRO-001"}` | Run specific scenario |
| `list_scenarios` | `{"action": "list_scenarios"}` | List all 66 scenarios |
| `pause` | `{"action": "pause"}` | Pause running demo |
| `resume` | `{"action": "resume"}` | Resume paused demo |
| `reset` | `{"action": "reset"}` | Reset all [DEMO] incidents |
| `status` | `{"action": "status"}` | Get current demo state |

### Demo Flow Sequence

1. **Reset Phase** - Resolve all existing [DEMO] incidents
2. **Trigger Phase** - Create incident for selected scenario
3. **Wait Phase** - Configurable delay (30-60 seconds)
4. **Acknowledge Phase** - Fake user acknowledges incident
5. **Channel Phase** - Create Slack channel, add observer
6. **Investigation Phase** - Post investigation messages with delays
7. **Progress Phase** - Multiple progress updates based on orchestration_trace
8. **Resolution Phase** - Fake user resolves with root cause

### Key Design Decisions

1. **Observer Never Assigned**: `clynch@pagerduty.com` is never assigned to incidents - only added to Slack channel to observe
2. **Channel After Ack**: Slack channel created only after fake user acknowledges
3. **Fake User Actions**: All incident actions (ack, notes, resolve) performed by demo users, not admin
4. **Scenario-Aware**: Uses `orchestration_trace` from scenarios.json for realistic messages

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ACTION_DELAY_MIN` | 30 | Minimum delay between actions (seconds) |
| `ACTION_DELAY_MAX` | 60 | Maximum delay between actions (seconds) |
| `SCENARIOS_FILE` | /var/task/scenarios.json | Path to scenarios file |

---

## Lifecycle Lambda Flow (Background Mode)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LIFECYCLE LAMBDA EXECUTION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

EventBridge (every 15 mins)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. CHECK FOR REAL INCIDENTS                                                 │
│     • List all open incidents                                               │
│     • If any incident WITHOUT "[DEMO]" prefix exists → PAUSE ALL DEMO       │
│     • Resolve all demo incidents, return early                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │ (no real incidents)
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. PROCESS TRIGGERED INCIDENTS (age >= 2 minutes)                          │
│     • Acknowledge the incident                                              │
│     • Find corresponding Slack channel (inc-{number}-{slug})                │
│     • Post ACK_MESSAGE to Slack as random responder                         │
│     • Add note to PagerDuty incident                                        │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. PROCESS ACKNOWLEDGED INCIDENTS                                           │
│                                                                              │
│     IF age >= 20 minutes:                                                   │
│       • Resolve the incident                                                │
│       • Post PROGRESS_MESSAGE + RESOLUTION_MESSAGE to Slack                 │
│       • Add resolution note to PagerDuty                                    │
│                                                                              │
│     ELSE IF age >= 5 minutes:                                               │
│       • Roll for action count (1-4 actions)                                 │
│       • Execute random actions from available_actions list                  │
│       • Post corresponding messages to Slack                                │
│       • Add notes to PagerDuty                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Action Selection Logic (Current)

```python
def select_action_count() -> int:
    roll = random.random()
    if roll < 0.17:      # 17% chance
        return 1         # → ALWAYS escalate when count=1
    elif roll < 0.44:    # 27% chance
        return 2
    elif roll < 0.72:    # 28% chance
        return 3
    else:                # 28% chance
        return 4

available_actions = ["investigate", "collaborate", "progress", "snooze", "escalate", "reassign"]
```

---

## User Configuration (CRITICAL)

### The Problem

The incident lifecycle simulator posts messages to Slack "impersonating" PagerDuty users. This uses Slack's `chat:write.customize` feature which allows the bot to post with a custom username and avatar.

**HOWEVER:** If a user doesn't exist in Slack, we can't look up their Slack user ID, avatar, or proper display name. The simulation looks broken or incomplete.

**ADDITIONALLY:** Slack guest users cannot use the PagerDuty Slack app due to a Slack platform limitation. This means guests cannot link their PagerDuty accounts, use `/pd` commands, or interact with PagerDuty message buttons.

### Valid Users for Schedules (February 2026)

These 6 users exist in BOTH PagerDuty AND Slack as **full members**:

| User | Email | PagerDuty ID | Slack User ID | Can Be Simulated |
|------|-------|--------------|---------------|------------------|
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PG6UTES | U0AA1LZSYHX | ✅ YES |
| Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | PCX6T22 | U0AA1LYLH2M | ✅ YES |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PYKISPC | U0A9SBF3MTN | ✅ YES |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PVOXRAP | U0A9LN3QVC6 | ✅ YES |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PR0E7IK | U0A9GC08EV9 | ✅ YES |
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PNRT76X | U0A9KANFCLV | ✅ YES |

### Invalid Users (DO NOT USE IN SCHEDULES)

| User | Email | PagerDuty ID | Reason |
|------|-------|--------------|--------|
| James Murphy | jmurphy@losandesgaa.onmicrosoft.com | - | Not in Slack workspace |
| Paddy Losty | plosty@losandesgaa.onmicrosoft.com | - | Not in Slack workspace |
| Kaptin Morgan | kmorgan@losandesgaa.onmicrosoft.com | - | Not in Slack workspace |
| Uisce Beatha | ubeatha@losandesgaa.onmicrosoft.com | - | Not in Slack workspace |

### Terraform Configuration

The `data_lookups.tf` file defines which users are available for schedules:

```hcl
locals {
  emails = {
    "jbeam@losandesgaa.onmicrosoft.com"    = "Jim Beam"
    "jcasker@losandesgaa.onmicrosoft.com"  = "Jameson Casker"
    "aguiness@losandesgaa.onmicrosoft.com" = "Arthur Guiness"
    "jcuervo@losandesgaa.onmicrosoft.com"  = "Jose Cuervo"
    "jdaniels@losandesgaa.onmicrosoft.com" = "Jack Daniels"
    "gtonic@losandesgaa.onmicrosoft.com"   = "Ginny Tonic"
  }
}
```

**IMPORTANT:** The current PagerDuty API token (`u+rRnDx15Dpsdsy8iM1Q`) does NOT have permission to update schedules via Terraform. You must either:
1. Update schedules via PagerDuty UI
2. Obtain an admin API token

---

## Current Implementation Status

### What's Working ✅

| Feature | Implementation | Location |
|---------|----------------|----------|
| Acknowledge triggered incidents | After 2 minutes | `handler.py:process_incidents()` |
| Resolve acknowledged incidents | After 20 minutes | `handler.py:process_incidents()` |
| Post ACK messages to Slack | When acknowledging | `handler.py:process_incidents()` |
| Post resolution messages to Slack | When resolving | `handler.py:process_incidents()` |
| Add notes to PagerDuty | On all actions | Throughout |
| Escalate incidents | 35% chance during actions | `handler.py:get_responder_actions()` |
| Snooze incidents | Random action | `handler.py:get_responder_actions()` |
| Reassign incidents | Random action | `handler.py:get_responder_actions()` |
| Pause for real incidents | Detects non-[DEMO] incidents | `handler.py:check_for_real_scenario()` |
| **Add Responders action** | Adds 2-4 responders with messages | `handler.py:PagerDutyClient.add_responders()` |
| **All responders participate** | 30% during actions, 100% before resolution | `handler.py:ensure_all_responders_participate()` |
| **Status updates** | Posts status updates with scenario messages | `handler.py:PagerDutyClient.post_status_update()` |
| **Trigger RBA actions** | Posts RBA-style messages (simulation) | `handler.py:get_responder_actions()` |
| **Invite responders to Slack** | Auto-invites on acknowledge | `handler.py:SlackClient.invite_users_to_channel()` |
| **Scenario-specific conversations** | Messages match incident type | `handler.py:get_scenario_messages()` |
| **Resolver selection** | Random selection from responders | `handler.py:select_resolver()` |

### What's Missing / Remaining Work ❌

| Feature | Needed For | Priority | Notes |
|---------|-----------|----------|-------|
| Schedules with only Slack users | Realistic responders | HIGH | Blocked - needs admin token or manual UI update |
| Trigger actual incident workflows | Workflow demo | MEDIUM | Workflows fire via triggers, not API |
| Update custom fields | Custom fields demo | LOW | API not tested |
| Assign incident roles | EIM feature demo | LOW | API not tested |
| Create incident tasks | EIM feature demo | LOW | API not tested |
| Dashboard integration with demo-controller | UI-triggered demos | MEDIUM | Dashboard currently doesn't call demo-controller |
| Slack command for pause/play | Easier control | LOW | Currently API-only |

---

## Completed Tasks (February 2026)

### Major Refactoring Complete

| Task | Status | Notes |
|------|--------|-------|
| Unified shared module | ✅ Complete | `aws/shared/clients.py` - single PagerDutyClient and SlackClient |
| Demo Controller Lambda | ✅ Complete | `aws/lambda-demo-controller/handler.py` - full orchestration |
| 66 scenarios from JSON | ✅ Complete | Loads from `scenarios.json`, falls back to built-in |
| 30-60 second delays | ✅ Complete | Configurable via `ACTION_DELAY_MIN`/`ACTION_DELAY_MAX` |
| Pause/Play capability | ✅ Complete | API actions: `pause`, `resume`, `status` |
| Observer mode | ✅ Complete | clynch never assigned to incidents |
| Channel after ack | ✅ Complete | Slack channel created after fake user acks |
| Fake user resolution | ✅ Complete | Resolution always by fake users |
| Metrics aligned with Grafana | ✅ Complete | Fixed metric names to match alert rules |
| Terraform for demo-controller | ✅ Complete | Added to `aws/main.tf` |

### Previously Completed Tasks

| Task | Status | Implementation |
|------|--------|----------------|
| Add Responders action | ✅ Complete | `PagerDutyClient.add_responders()` |
| All responders participate | ✅ Complete | `ensure_all_responders_participate()` |
| Status updates | ✅ Complete | `PagerDutyClient.post_status_update()` |
| RBA action simulation | ✅ Complete | `RBA_ACTION_MESSAGES` constant |
| Invite responders to Slack | ✅ Complete | `SlackClient.invite_users_to_channel()` |
| Scenario-specific conversations | ✅ Complete | `SCENARIO_CONVERSATIONS` dict |

---

## Gotchas and Workarounds

### 1. Slack Guest Users Cannot Use PagerDuty App

**Problem:** Slack guest accounts cannot interact with the PagerDuty Slack app (platform limitation).

**Workaround:** Only use full Slack members in schedules. The 6 valid demo users are listed in `DEMO_USERS` and `PAGERDUTY_TO_SLACK_USER_MAP`.

### 2. Environment Variable Names

**Problem:** Different Lambdas historically used different env var names for PagerDuty tokens.

**Workaround:** The shared module now accepts both `PAGERDUTY_TOKEN` and `PAGERDUTY_ADMIN_TOKEN`. Prefer `PAGERDUTY_ADMIN_TOKEN` for consistency.

### 3. Slack Channel Timing

**Problem:** Creating Slack channel before incident acknowledgment looked unnatural.

**Workaround:** Demo controller creates channel AFTER fake user acknowledges, mimicking real incident response.

### 4. API Rate Limits

**Problem:** Rapid API calls during demos can hit rate limits.

**Workaround:** Demo controller uses 30-60 second delays between actions. Adjust `ACTION_DELAY_MIN`/`ACTION_DELAY_MAX` if needed.

### 5. Terraform Schedule Permissions

**Problem:** Some API tokens cannot modify schedules via Terraform.

**Workaround:** Update schedules via PagerDuty UI, or obtain an admin API token.

### 6. Scenario Routing Keys

**Problem:** Not all target services in scenarios.json have routing keys configured.

**Workaround:** Falls back to `ROUTING_KEY_K8S` for unknown services. Add missing routing keys to `SERVICE_TO_ROUTING_KEY` mapping as needed.

### 7. Demo Controller Timeout

**Problem:** Long-running demos might timeout.

**Workaround:** Demo controller has 15-minute timeout (900 seconds) in Terraform. For very long demos with many steps, consider breaking into multiple invocations.

---

## Remaining Work - Detailed Specifications

### Task 1: Update Schedules to Use Only Slack Users

**Status:** In Progress (Blocked - needs admin token or UI update)

**What Needs to Happen:**
1. Update all 5 schedules to only include the 6 valid users
2. Distribute users across schedules so incidents hit different services

**Current Schedule Configuration (needs updating):**
- Primary 24x7 Schedule
- Secondary 24x7 Schedule
- Manager On-Call Schedule
- SOC 24x7 Schedule
- IT Support Business Hours Schedule

**Target Distribution:**

| Schedule | Users | Purpose |
|----------|-------|---------|
| Primary 24x7 | Jim Beam, Jameson Casker, Arthur Guiness, Jose Cuervo, Jack Daniels, Ginny Tonic | Main on-call rotation |
| Secondary 24x7 | Ginny Tonic, Jack Daniels, Arthur Guiness | Backup rotation |
| Manager | Jim Beam, Ginny Tonic | Management escalation |
| SOC 24x7 | Ginny Tonic, Jack Daniels | Security incidents |
| IT Support | Jack Daniels | IT support hours |

**How to Verify:**
```bash
# Check schedule via API
curl -s "https://api.pagerduty.com/schedules/SCHEDULE_ID" \
  -H "Authorization: Token token=$PAGERDUTY_TOKEN" | jq '.schedule.users'
```

---

### Task 2: Implement Add Responders Action

**Status:** ✅ COMPLETED (February 2026)

**Implementation:**
- Added `PagerDutyClient.add_responders()` method
- Added to `get_responder_actions()` with 15% chance (2 responders), 3% (3 responders), 1% (4 responders)
- Posts scenario-specific messages when adding responders
- Also invites new responders to the Slack channel

**Specification:**
- Add responders to incident with probability distribution matching escalate:
  - 15% chance: Add 2 additional responders
  - 3% chance: Add 3 additional responders
  - 1% chance: Add 4 additional responders

**PagerDuty API Endpoint:**
```
POST /incidents/{id}/responder_requests
```

**Implementation Code to Add:**

```python
def add_responders(self, incident_id: str, user_ids: List[str], message: str = None) -> bool:
    """Add responders to an incident using the responder_requests endpoint."""
    targets = [{"responder_request_target": {"id": uid, "type": "user_reference"}} for uid in user_ids]
    payload = {
        "requester_id": self.get_requester_id(),  # Need to implement this
        "message": message or "Additional support requested for this incident.",
        "responder_request_targets": targets,
    }
    try:
        response = requests.post(
            f"{self.api_base}/incidents/{incident_id}/responder_requests",
            headers=self._headers(),
            json=payload,
        )
        if response.status_code == 200:
            logger.info(f"Added {len(user_ids)} responders to incident {incident_id}")
            return True
        logger.error(f"Failed to add responders: {response.status_code} {response.text}")
        return False
    except Exception as e:
        logger.error(f"Error adding responders: {e}")
        return False

def select_add_responders_count() -> int:
    """Select number of responders to add based on probability distribution."""
    roll = random.random()
    if roll < 0.15:      # 15% chance
        return 2
    elif roll < 0.18:    # 3% chance (15% + 3% = 18%)
        return 3
    elif roll < 0.19:    # 1% chance (18% + 1% = 19%)
        return 4
    return 0              # 81% chance - don't add responders
```

**Integration Point:**
Add to `get_responder_actions()` function after line 568:

```python
available_actions = ["investigate", "collaborate", "progress", "snooze", "escalate", "reassign", "add_responders"]

# In the action handler loop:
elif action == "add_responders":
    add_count = select_add_responders_count()
    if add_count > 0:
        other_users = [u for u in all_users if u not in responders]
        if len(other_users) >= add_count:
            new_responders = random.sample(other_users, add_count)
            user_ids = [u["id"] for u in new_responders]
            if pd.add_responders(incident_id, user_ids):
                actions_taken["add_responders"] = [u["name"] for u in new_responders]
                names = ", ".join([u["name"] for u in new_responders])
                msg = f"Adding {names} to help with this incident."
                pd.add_note(incident_id, f"[Automated] {msg}")
                if channel_id:
                    # Also post to Slack
                    slack.post_message(channel_id, f":raising_hand: *{responders[0]['name']}*: {msg}")
    actions_taken["actions"].append("add_responders")
```

---

### Task 3: Implement Responder Action Logic (All Responders Participate)

**Status:** ✅ COMPLETED (February 2026)

**Implementation:**
- Added `ensure_all_responders_participate()` function
- Called with 30% probability during actions phase
- Called 100% before resolution to ensure all responders speak
- Added `select_resolver()` function for random resolver selection
- Resolution messages use scenario-specific content

---

### Task 4: Add Responders to Slack Channel Immediately

**Status:** ✅ COMPLETED (February 2026)

**Implementation:**
- Added `SlackClient.invite_users_to_channel()` method
- Added `PAGERDUTY_TO_SLACK_USER_MAP` for user ID mapping
- Added `get_slack_user_ids_for_responders()` helper function
- Auto-invites responders to Slack channel on acknowledge
- Handles `already_in_channel` error gracefully
- `groups:write.invites` - Invite to private channels

**Slack API Endpoint:**
```
POST /conversations.invite
```

**Implementation:**

```python
def invite_users_to_channel(self, channel_id: str, user_ids: List[str]) -> bool:
    """Invite users to a Slack channel."""
    if not self.bot_token:
        return False
    try:
        response = requests.post(
            f"{self.api_base}/conversations.invite",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            },
            json={"channel": channel_id, "users": ",".join(user_ids)}
        )
        data = response.json()
        if data.get("ok"):
            logger.info(f"Invited {len(user_ids)} users to channel {channel_id}")
            return True
        # already_in_channel is not an error
        if data.get("error") == "already_in_channel":
            return True
        logger.error(f"Failed to invite users: {data.get('error')}")
        return False
    except Exception as e:
        logger.error(f"Error inviting users to channel: {e}")
        return False
```

**User ID Mapping Required:**

You need a mapping from PagerDuty user email to Slack user ID:

```python
DEMO_USERS = [
    {'id': 'PG6UTES', 'email': 'jbeam@losandesgaa.onmicrosoft.com', 'name': 'Jim Beam', 'slack_id': 'U0AA1LZSYHX'},
    {'id': 'PR0E7IK', 'email': 'jdaniels@losandesgaa.onmicrosoft.com', 'name': 'Jack Daniels', 'slack_id': 'U0A9GC08EV9'},
    {'id': 'PCX6T22', 'email': 'jcasker@losandesgaa.onmicrosoft.com', 'name': 'Jameson Casker', 'slack_id': 'U0AA1LYLH2M'},
    {'id': 'PVOXRAP', 'email': 'jcuervo@losandesgaa.onmicrosoft.com', 'name': 'Jose Cuervo', 'slack_id': 'U0A9LN3QVC6'},
    {'id': 'PNRT76X', 'email': 'gtonic@losandesgaa.onmicrosoft.com', 'name': 'Ginny Tonic', 'slack_id': 'U0A9KANFCLV'},
    {'id': 'PYKISPC', 'email': 'aguiness@losandesgaa.onmicrosoft.com', 'name': 'Arthur Guinness', 'slack_id': 'U0A9SBF3MTN'},
]

# Authoritative source for user mappings - defined in shared module
PAGERDUTY_TO_SLACK_USER_MAP = {user['email']: user['slack_id'] for user in DEMO_USERS}

def get_slack_user_id(pd_user: Dict) -> Optional[str]:
    """Get Slack user ID from PagerDuty user."""
    email = pd_user.get("email", "")
    return PAGERDUTY_TO_SLACK_USER_MAP.get(email)
```

**Integration Point:**
In the acknowledge incident block (line 686-700):

```python
if pd.acknowledge_incident(incident_id):
    results["acknowledged"].append(incident_id)
    
    channel_name = get_incident_channel_name(incident)
    channel_id = slack.find_channel_by_pattern(f"^{channel_name[:20]}")
    
    if channel_id:
        responders = pick_responders(pd, incident, 2)
        
        # NEW: Invite responders to channel
        slack_user_ids = [get_slack_user_id(r) for r in responders if get_slack_user_id(r)]
        if slack_user_ids:
            slack.invite_users_to_channel(channel_id, slack_user_ids)
        
        ack_msg = random.choice(ACK_MESSAGES)
        post_conversation(slack, channel_id, [ack_msg], responders, incident, all_users)
```

---

### Task 5: Implement Status Updates

**Status:** ✅ COMPLETED (February 2026)

**Implementation:**
- Added `PagerDutyClient.post_status_update()` method
- Added `STATUS_UPDATE_MESSAGES` constant with scenario-aware messages
- Added to `get_responder_actions()` as `status_update` action
- Posts notification to Slack when status update is sent

---

### Task 6: Trigger Automation Actions (RBA)

**Status:** ✅ COMPLETED (February 2026) - Simulation Mode

**Implementation:**
- Added `RBA_ACTION_MESSAGES` constant with diagnostic/remediation messages
- Added `trigger_rba` action to `get_responder_actions()`
- Simulates RBA execution with realistic messages (actual RBA requires runner online)
- Posts diagnostic results to Slack channel

**Note:** Actual RBA execution depends on runner availability. The implementation simulates RBA output for demo purposes.

---

### Task 7: Scenario-Specific Conversation Libraries

**Status:** ✅ COMPLETED (February 2026)

**Implementation:**
- The demo-controller Lambda uses `orchestration_trace` from scenarios.json
- Each scenario in scenarios.json contains specific messages for each stage
- `get_orchestration_messages()` function extracts stage-specific messages
- Messages are posted during the demo flow based on scenario type

**Example from scenarios.json:**
```json
{
  "orchestration_trace": [
    {"stage": "Event Orchestration", "action": "Assign P1 priority"},
    {"stage": "Service Rules", "action": "Route to DBRE"},
    {"stage": "Investigation", "action": "Checking database connection pool"},
    {"stage": "Resolution", "action": "Connection pool scaled, queries recovered"}
  ]
}
```

**Note:** The original proposal for `SCENARIO_CONVERSATIONS` dict was superseded by using the structured `orchestration_trace` data already in scenarios.json.

---

## API Reference

### PagerDuty API Endpoints Used

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/users` | GET | List all users | ✅ Implemented |
| `/incidents` | GET | List incidents | ✅ Implemented |
| `/incidents/{id}` | PUT | Update incident (ack/resolve/escalate) | ✅ Implemented |
| `/incidents/{id}/notes` | POST | Add note | ✅ Implemented |
| `/incidents/{id}/snooze` | POST | Snooze incident | ✅ Implemented |
| `/incidents/{id}/responder_requests` | POST | Add responders | ✅ Implemented |
| `/incidents/{id}/status_updates` | POST | Post status update | ✅ Implemented |
| `/escalation_policies` | GET | List policies | ✅ Implemented |
| `/priorities` | GET | List priorities | ✅ Implemented |
| `/schedules` | GET/PUT | Manage schedules | ⚠️ Read only (write blocked by token) |

### Slack API Endpoints Used

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/chat.postMessage` | POST | Post message | ✅ Implemented |
| `/conversations.list` | GET | List channels | ✅ Implemented |
| `/conversations.info` | GET | Get channel info | ✅ Implemented |
| `/conversations.open` | POST | Open DM | ✅ Implemented |
| `/conversations.invite` | POST | Invite users to channel | ✅ Implemented |
| `/conversations.create` | POST | Create incident channel | ✅ Implemented |
| `/users` | GET | List all users | ✅ | |
| `/incidents` | GET | List incidents | ✅ | |
| `/incidents/{id}` | PUT | Update incident (ack/resolve/escalate) | ✅ | |
| `/incidents/{id}/notes` | POST | Add note | ✅ | |
| `/incidents/{id}/snooze` | POST | Snooze incident | ✅ | |
| `/incidents/{id}/responder_requests` | POST | Add responders | ❌ | ✅ |
| `/incidents/{id}/status_updates` | POST | Post status update | ❌ | ✅ |
| `/escalation_policies` | GET | List policies | ✅ | |
| `/priorities` | GET | List priorities | ✅ | |
| `/schedules` | GET/PUT | Manage schedules | ✅ Read | ❌ Write blocked |

### Slack API Endpoints Used

| Endpoint | Method | Purpose | Current | Needed |
|----------|--------|---------|---------|--------|
| `/chat.postMessage` | POST | Post message | ✅ | |
| `/conversations.list` | GET | List channels | ✅ | |
| `/conversations.info` | GET | Get channel info | ✅ | |
| `/conversations.open` | POST | Open DM | ✅ | |
| `/conversations.invite` | POST | Invite users to channel | ❌ | ✅ |

---

## Data Structures

### Incident Object (from PagerDuty API)

```json
{
  "id": "PXXXXXX",
  "incident_number": 1234,
  "title": "[DEMO] Database connection pool exhaustion",
  "status": "triggered|acknowledged|resolved",
  "created_at": "2026-02-04T12:00:00Z",
  "urgency": "high|low",
  "priority": {"id": "PXXXXXX", "summary": "P1"},
  "service": {"id": "PXXXXXX", "summary": "Platform - Database Operations"},
  "escalation_policy": {"id": "PXXXXXX", "summary": "Platform Primary"},
  "assignments": [
    {
      "at": "2026-02-04T12:00:00Z",
      "assignee": {"id": "PXXXXXX", "type": "user_reference", "summary": "Jim Beam"}
    }
  ],
  "last_status_change_by": {"id": "PXXXXXX", "type": "user_reference", "summary": "Jim Beam"}
}
```

### User Object (from PagerDuty API)

```json
{
  "id": "PG6UTES",
  "name": "Jim Beam",
  "email": "jbeam@losandesgaa.onmicrosoft.com",
  "role": "user",
  "job_title": "Senior SRE"
}
```

### Responder Object (internal)

```python
{
    "id": "PG6UTES",
    "name": "Jim Beam",
    "email": "jbeam@losandesgaa.onmicrosoft.com",
    "role": "user",
    "job_title": "Senior SRE",
    "slack_id": "U08CQAV8PEV"  # Added for Slack integration
}
```

---

## Testing and Deployment

### Local Testing

```bash
cd aws/lambda-lifecycle

# Load environment variables
source ../../scripts/demo-simulator/.env

# Or create a local .env file with:
# PAGERDUTY_ADMIN_TOKEN=u+rRnDx15Dpsdsy8iM1Q
# SLACK_BOT_TOKEN=xoxb-...

# Run locally
python handler.py
```

### Deploy to AWS Lambda

```bash
# Package the Lambda
cd aws/lambda-lifecycle
zip -r function.zip handler.py

# Update the Lambda function
aws lambda update-function-code \
  --function-name demo-simulator-lifecycle \
  --zip-file fileb://function.zip

# View logs
aws logs tail /aws/lambda/demo-simulator-lifecycle --since 1h
```

### Environment Variables Required

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `PAGERDUTY_ADMIN_TOKEN` | PagerDuty API token | PagerDuty → Integrations → API Access Keys |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) | Slack App → OAuth & Permissions |

### Verification Checklist

After making changes:

1. [ ] Create a test incident: `python scripts/demo-simulator/main.py incident --scenario "memory"`
2. [ ] Wait 5 minutes for lifecycle Lambda to process
3. [ ] Check PagerDuty: Incident should be acknowledged
4. [ ] Check Slack: Messages should appear in incident channel
5. [ ] Check CloudWatch logs for errors: `aws logs tail /aws/lambda/demo-simulator-lifecycle --since 30m`

---

## Integration Capabilities Reference

### Slack Bot Scopes (Current - All Required Scopes Enabled)

The Slack bot token (`SLACK_BOT_TOKEN`) has these scopes enabled:

| Scope | Purpose | Used By |
|-------|---------|---------|
| `app_mentions:read` | View messages mentioning the bot | Event subscriptions |
| `channels:history` | View messages in public channels | Check for real user activity |
| `channels:join` | Join public channels | Auto-join incident channels |
| `channels:read` | View channel info | `find_channel_by_pattern()` |
| `channels:write.invites` | Invite members to public channels | ✅ Task 4: Add responders |
| `chat:write` | Send messages | `post_message()` |
| `chat:write.customize` | Send as custom username/avatar | Simulating user messages |
| `conversations.connect:manage` | Manage Slack Connect channels | External connections |
| `groups:write.invites` | Invite members to private channels | ✅ Task 4: Add responders |
| `search:read.users` | Search workspace users | User lookups |
| `users.profile:read` | View user profiles | User info |
| `users:read` | View people in workspace | User ID lookups |
| `users:read.email` | View user emails | Email-based lookups |
| `users:write` | Set bot presence | Presence management |

### Task 4 Scopes - ALREADY ENABLED

**All required scopes for "Add Responders to Slack Channel Immediately" are already configured:**

| Scope | Purpose | Status |
|-------|---------|--------|
| `channels:write.invites` | Invite to public incident channels | ✅ Enabled |
| `groups:write.invites` | Invite to private incident channels | ✅ Enabled |

**API Method:** `conversations.invite` (uses the above scopes)

No Slack app changes required - ready to implement Task 4.

### PagerDuty API Token Capabilities

**Current Token:** `u+rRnDx15Dpsdsy8iM1Q`
**Token Type:** User API Token (not Admin)

| Capability | Status | Notes |
|------------|--------|-------|
| List incidents | ✅ Enabled | `GET /incidents` |
| Update incidents | ✅ Enabled | `PUT /incidents/{id}` |
| Acknowledge incidents | ✅ Enabled | `PUT /incidents/{id}` |
| Resolve incidents | ✅ Enabled | `PUT /incidents/{id}` |
| Add notes | ✅ Enabled | `POST /incidents/{id}/notes` |
| Escalate incidents | ✅ Enabled | `POST /incidents/{id}/escalate` |
| Reassign incidents | ✅ Enabled | `PUT /incidents/{id}` |
| Snooze incidents | ✅ Enabled | `PUT /incidents/{id}/snooze` |
| Add responders | ✅ Enabled | `POST /incidents/{id}/responder_requests` |
| Update priority | ✅ Enabled | `PUT /incidents/{id}` |
| Post status updates | ✅ Enabled | `POST /incidents/{id}/status_updates` |
| List users | ✅ Enabled | `GET /users` |
| List priorities | ✅ Enabled | `GET /priorities` |
| **Update schedules** | ❌ BLOCKED | Requires Admin token (403 Forbidden) |
| **Update escalation policies** | ❌ BLOCKED | Requires Admin token (403 Forbidden) |

**To Unlock Schedule Updates:**
1. Generate a new API key in PagerDuty → Integrations → API Access Keys
2. Ensure the key is created by an **Admin** user
3. Replace `PAGERDUTY_ADMIN_TOKEN` in Lambda environment variables

### AWS Infrastructure

**Account:** `127214181728` (us-east-1)
**Runtime:** Python 3.11
**Cost:** FREE (AWS Free Tier)

#### Lambda Functions (8 Total)

| Function | Purpose | Schedule | File |
|----------|---------|----------|------|
| `demo-simulator-controller` | **RECOMMENDED** Controlled demos with pause/play | Manual | `aws/lambda-demo-controller/handler.py` |
| `demo-simulator-orchestrator` | Creates random [DEMO] incidents | Every hour | `aws/lambda-orchestrator/handler.py` |
| `demo-simulator-lifecycle` | Manages incident lifecycle | Every 15 min | `aws/lambda-lifecycle/handler.py` |
| `demo-simulator-notifier` | Sends Slack DMs | Every 2 min | `aws/lambda-notifier/handler.py` |
| `demo-simulator-metrics` | Sends metrics to Datadog/NR | Every 5 min | `aws/lambda-metrics/handler.py` |
| `demo-simulator-user-activity` | Simulates user actions | 15 min (business hours) | (combined with lifecycle) |
| `demo-simulator-health-check` | Checks integration health | Every 15 min | `aws/lambda-health/handler.py` |
| `demo-simulator-reset` | Resets demo environment | Manual | `aws/lambda-reset/handler.py` |

#### ~~Function URLs~~ — BROKEN (403 Forbidden)

> **WARNING (Feb 17, 2026):** All Lambda Function URLs on this AWS account return 403 Forbidden. Use `aws lambda invoke` or the API Gateway URL instead.

| Function | Invocation |
|----------|------------|
| **`demo-simulator-controller`** | `aws lambda invoke --function-name demo-simulator-controller --payload '...' --cli-binary-format raw-in-base64-out --region us-east-1 out.json` |
| `demo-simulator-orchestrator-v2` | API Gateway: `https://ynoioelti7.execute-api.us-east-1.amazonaws.com` |
| `demo-simulator-health-check` | `aws lambda invoke --function-name demo-simulator-health-check --region us-east-1 out.json` |
| `demo-simulator-reset` | `aws lambda invoke --function-name demo-simulator-reset --payload '{"mode":"quick"}' --cli-binary-format raw-in-base64-out --region us-east-1 out.json` |

#### Environment Variables (All Lambdas)

| Variable | Description |
|----------|-------------|
| `PAGERDUTY_ADMIN_TOKEN` | PagerDuty API token for API calls |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) |
| `SLACK_CHANNEL` | Default Slack channel for notifications |
| `DATADOG_API_KEY` | For metrics Lambda only |
| `NEW_RELIC_API_KEY` | For metrics Lambda only |
| `ACTION_DELAY_MIN` | Demo controller: min delay between actions (default: 30) |
| `ACTION_DELAY_MAX` | Demo controller: max delay between actions (default: 60) |

#### EventBridge Rules

| Rule | Schedule | Target |
|------|----------|--------|
| `demo-orchestrator-schedule` | `rate(1 hour)` | `demo-simulator-orchestrator` |
| `demo-lifecycle-schedule` | `rate(15 minutes)` | `demo-simulator-lifecycle` |
| `demo-notifier-schedule` | `rate(2 minutes)` | `demo-simulator-notifier` |
| `demo-metrics-schedule` | `rate(5 minutes)` | `demo-simulator-metrics` |
| `demo-health-check-schedule` | `rate(15 minutes)` | `demo-simulator-health-check` |

#### CloudWatch Log Groups

| Log Group | Lambda |
|-----------|--------|
| `/aws/lambda/demo-simulator-controller` | Demo controller logs |
| `/aws/lambda/demo-simulator-orchestrator` | Incident creation logs |
| `/aws/lambda/demo-simulator-lifecycle` | Lifecycle management logs |
| `/aws/lambda/demo-simulator-notifier` | Slack notification logs |
| `/aws/lambda/demo-simulator-metrics` | Metrics submission logs |

**View Logs:**
```bash
aws logs tail /aws/lambda/demo-simulator-lifecycle --since 1h --follow
```

---

## Document History

| Date | Changes |
|------|---------|
| February 2026 | Created comprehensive implementation guide |
| February 2026 | Added user mapping, API reference, and code examples |
| February 2026 | Added Integration Capabilities Reference (Slack, PagerDuty, AWS) |
