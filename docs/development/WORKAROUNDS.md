# Development Workarounds & Unique Techniques

**Last Updated:** February 18, 2026
**Purpose:** Document uncommon techniques, API workarounds, and non-obvious solutions used in this project

---

## Table of Contents

1. [PagerDuty Terraform Provider Limitations](#1-pagerduty-terraform-provider-limitations)
   - [Incident Workflows Cannot Be Created via API](#incident-workflows-cannot-be-created-via-api)
   - [Workflow Steps Cannot Be Updated via REST API](#workflow-steps-cannot-be-updated-via-rest-api-500-internal-server-error)
   - [Automation Actions Runner Configuration](#automation-actions-runner-configuration)
   - [Early Access Feature Flags Required](#early-access-feature-flags-required)
2. [Atlassian API Workarounds](#2-atlassian-api-workarounds)
3. [Confluence Content Population](#3-confluence-content-population)
4. [Global Event Orchestration CEL Syntax](#4-global-event-orchestration-cel-syntax)
5. [Terraform State Recovery](#5-terraform-state-recovery)
6. [Demo Dashboard Integration Architecture](#6-demo-dashboard-integration-architecture)
   - [Two-Tier Integration Flow Design](#two-tier-integration-flow-design)
   - [GitHub Actions Deployment Queuing Issues](#github-actions-deployment-queuing-issues)
   - [Browser localStorage Credential Storage](#browser-localstorage-credential-storage)
7. [Lambda Lifecycle Workarounds](#7-lambda-lifecycle-workarounds)

---

## 1. PagerDuty Terraform Provider Limitations

### Incident Workflows Cannot Be Created via API

**Problem:** The PagerDuty Terraform provider's `pagerduty_incident_workflow` resource cannot create new workflows. API POST requests to `/incident_workflows` return 404 Not Found.

**Behavior Observed:**
- `GET /incident_workflows` - Works (list existing)
- `PUT /incident_workflows/{id}` - Works (update existing)
- `POST /incident_workflows` - Returns 404 (cannot create)

**Workaround:**
1. Create workflows manually via PagerDuty UI first
2. Reference them in Terraform as data sources:
```hcl
data "pagerduty_incident_workflow" "data_breach_response" {
  name = "Data Breach Response"
}
```
3. Workflow TRIGGERS can still be managed via Terraform:
```hcl
resource "pagerduty_incident_workflow_trigger" "data_breach_auto" {
  type     = "conditional"
  workflow = data.pagerduty_incident_workflow.data_breach_response.id
  # ...
}
```

**File Reference:** `incident_workflows.tf` (lines 1-30 contain detailed notes)

**Status:** Resolved - Use `pagerduty_incident_workflow` resource for empty workflows, steps must be added manually (see below).

---

### Workflow Steps Cannot Be Updated via REST API (500 Internal Server Error)

**Problem:** When attempting to update incident workflows with steps via the REST API, PagerDuty returns 500 Internal Server Error responses. This affects both the `PUT /incident_workflows/{id}` endpoint and any attempt to add steps programmatically.

**Behavior Observed:**
- `PUT /incident_workflows/{id}` with `steps: []` (empty) - Works
- `PUT /incident_workflows/{id}` with populated steps - Returns 500 Internal Server Error
- Creating workflows with steps in a single POST - Returns 500
- The PagerDuty MCP server also does NOT support workflow step updates (only list/get/start operations)

**Correct Action IDs (discovered via API inspection):**
| Action | Action ID |
|--------|-----------|
| Add Note | `pagerduty.com:incident-workflows:add-notes-to-incident:1` |
| Add Responders | `pagerduty.com:incident-workflows:add-responders:2` |
| Send Status Update | `pagerduty.com:incident-workflows:send-status-update:5` |

**Required Input Parameters:**
```json
// Add Note action
{"name": "Incident ID", "value": "{{incident.id}}"},
{"name": "Message", "value": "Your note content here"}

// Add Responders action
{"name": "Responders", "value": "[{\"type\":\"escalation_policy_reference\",\"id\":\"POLICY_ID\"}]"}

// Send Status Update action
{"name": "Status Update template", "value": "Your template"},
{"name": "Message (SMS, Push and Status Page update)", "value": "Short message"}
```

**Workaround:**
1. Create empty workflows via Terraform (name, description, team only)
2. Configure triggers via Terraform (`pagerduty_incident_workflow_trigger`)
3. **Add workflow steps manually via PagerDuty UI:**
   - Navigate to Automation → Incident Workflows
   - Click on the workflow
   - Use the visual builder to add steps
4. The script `archive/scripts_oneoff/populate_workflow_steps.py` contains correct payload formats for reference if the API is fixed in the future

**File Reference:** `archive/scripts_oneoff/populate_workflow_steps.py` (contains step definitions and correct action IDs)

---

### Automation Actions Runner Configuration

**Problem:** The `pagerduty_automation_actions_runner` resource requires specific runner configuration that isn't well documented.

**Workaround:** Use the runner ID from the PagerDuty UI after manually registering a runner:
```hcl
data "pagerduty_automation_actions_runner" "default" {
  id = "PRUNNER_ID"  # From UI after registration
}
```

---

### Early Access Feature Flags Required

**Problem:** Certain PagerDuty Terraform resources (incident workflows, workflow triggers) require explicit early access feature flags to function. Without these flags, resources may fail to create or update with cryptic errors.

**Workaround:** Create a separate `provider_early_access_override.tf` file:
```hcl
provider "pagerduty" {
  early_access = ["incident_workflows", "incident_workflow_triggers"]
}
```

**Why a Separate File:**
- Keeps early access configuration isolated and easy to manage
- Can be removed when features graduate to general availability
- Makes it clear which features are using early access APIs

**File Reference:** `provider_early_access_override.tf`

**Known Early Access Features:**
| Feature | Flag | Status |
|---------|------|--------|
| Incident Workflows | `incident_workflows` | Required |
| Workflow Triggers | `incident_workflow_triggers` | Required |

---

## 2. Atlassian API Workarounds

### Confluence Space Creation

**Problem:** Confluence must be enabled at the organization level before the REST API is accessible. Without Confluence enabled, all API calls return 401 Unauthorized.

**Solution Flow:**
1. Enable Confluence manually via `admin.atlassian.com`
2. Wait 1-2 minutes for API propagation
3. Use REST API v1 for space creation:
```python
url = f"{BASE_URL}/wiki/rest/api/space"
payload = {
    "key": "RUNBOOKS",
    "name": "PagerDuty Runbooks",
    "type": "global",
    "description": {"plain": {"value": "...", "representation": "plain"}}
}
response = requests.post(url, json=payload, auth=(USER, TOKEN))
```

**Note:** The API v2 (`/wiki/api/v2/spaces`) has different behavior and is not fully backwards compatible.

---

### Atlassian Admin API Limitations

**Problem:** The Atlassian Organization Admin API (`https://api.atlassian.com/admin/v1/orgs/{org_id}`) cannot enable products like Confluence. It's read-only for organization metadata.

**Attempted Endpoints That Failed:**
- `GET /admin/v1/orgs/{org_id}/sites` - 404 Not Found
- `GET /admin/v1/orgs/{org_id}/products` - 404 Not Found

**Solution:** Confluence enablement must be done manually via `admin.atlassian.com` UI.

---

### Jira Project Creation

**Problem:** Jira projects require specific configuration including lead account ID and project type.

**Workaround Script Pattern:**
```python
payload = {
    "key": "SECOPS",
    "name": "Security Operations",
    "projectTypeKey": "software",
    "leadAccountId": "712020:xxx",  # Must be valid Atlassian account ID
    "description": "..."
}
response = requests.post(f"{BASE_URL}/rest/api/3/project", json=payload, auth=auth)

# Handle "already exists" gracefully
if response.status_code == 400 and "already exists" in response.text:
    print(f"Project {key} already exists")
```

**File Reference:** Script pattern preserved in `archive/scripts_oneoff/` for reference.

---

## 3. Confluence Content Population

### Storage Format (XHTML) Requirements

**Problem:** Confluence pages require content in "Storage Format" which is XHTML-based, not Markdown.

**Key Requirements:**
- Content must be wrapped in `<p>`, `<table>`, `<ac:structured-macro>` tags
- Markdown will NOT render - must use HTML
- Status macros use: `<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter>...</ac:structured-macro>`
- Info panels use: `<ac:structured-macro ac:name="info">...</ac:structured-macro>`

**Example Pattern:**
```python
CONTENT = """
<h2>Section Title</h2>
<p>Paragraph text here.</p>
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>This is an info panel</p>
  </ac:rich-text-body>
</ac:structured-macro>
<table>
  <tr><th>Header</th></tr>
  <tr><td>Data</td></tr>
</table>
"""
```

---

### Page Hierarchy and Parent IDs

**Problem:** Child pages require the parent page ID, which must be retrieved after parent creation.

**Solution Pattern:**
```python
def create_page(title, body, parent_id=None):
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE_KEY},
        "body": {"storage": {"value": body, "representation": "storage"}}
    }
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    
    response = requests.post(url, json=payload, auth=auth)
    return response.json().get("id")  # Return ID for children

# Usage
home_id = create_page("Home", HOME_CONTENT)
child_id = create_page("Child Page", CHILD_CONTENT, parent_id=home_id)
```

**File Reference:** `scripts/populate_confluence.py`

---

## 4. Global Event Orchestration CEL Syntax

### CEL Expression Syntax Errors

**Problem:** The PagerDuty Terraform provider is strict about CEL (Common Expression Language) syntax in event orchestration rules.

**Common Errors:**
1. Using `event.dedup_key` when field doesn't exist
2. Incorrect string matching syntax
3. Boolean expression format in router rules

**Correct Patterns:**
```hcl
# String matching
condition = "event.summary matches part 'database'"

# Multiple conditions
condition = "event.severity matches 'critical' or event.severity matches 'error'"

# Field existence check (if unsure)
condition = "event.custom_details.priority matches 'P1'"
```

**Incorrect Patterns:**
```hcl
# WRONG: matches requires 'part' for substring
condition = "event.summary matches 'database'"

# WRONG: && is not valid, use 'and'
condition = "event.severity == 'critical' && event.source == 'datadog'"
```

**File Reference:** `global_orchestration.tf`, `routing_rules.tf`

---

## 5. Terraform State Recovery

### Stale State from Deleted Resources

**Problem:** When resources are deleted outside of Terraform (via UI), terraform apply may fail with errors referencing non-existent resources.

**Symptoms:**
```
Error: Error reading X: HTTP Status 404 Not Found
```

**Solution:**
```bash
# 1. Refresh state to detect drift
terraform refresh

# 2. If resource truly deleted, remove from state
terraform state rm 'resource_type.resource_name'

# 3. Re-run plan/apply
terraform plan
terraform apply
```

### Open Incidents Blocking Schedule Destruction

**Problem (encountered Feb 18, 2026):** `terraform apply` fails when trying to destroy/recreate schedules that have open incidents assigned through their escalation policies.

**Solution:** Resolve all open incidents first, then re-run apply. See `docs/setup/DEPLOYMENT.md` → "Step 3: Plan and Apply" → "Resolving Open Incidents Blocking Schedule Changes" for detailed commands.

### Renamed Resource Keys Causing Destroy/Create Cycles

**Problem (encountered Feb 18, 2026):** If a Terraform map key is renamed (e.g., schedule name change), Terraform treats this as a destroy + create. The destroy may fail if the resource is in use, leaving orphaned state.

**Solution:** Remove the old key from state with `terraform state rm`, then apply to create the new key. See `docs/setup/DEPLOYMENT.md` → "Removing Orphaned State Entries" for details.

---

## 6. Demo Dashboard Integration Architecture

### Two-Tier Integration Flow Design

**Problem:** The demo dashboard needs to demonstrate realistic incident flows where alerts originate from external monitoring tools (Datadog, Grafana, etc.) and flow through their native PagerDuty integrations. However, users may not have all external tools configured.

**Design Decision:** Implemented a two-tier flow system:

1. **Full Flow (Primary):** Demo App → External Tool API → Tool's Native Monitor/Alert → PagerDuty Integration → Incident
2. **Fallback Flow (Secondary):** Demo App → PagerDuty Events API (direct) → Incident

**Why This Matters:**
- Full Flow demonstrates real-world integration patterns where monitoring tools trigger PagerDuty
- Fallback Flow ensures demos can proceed even without external tool credentials
- The dashboard does NOT require PagerDuty routing keys for Full Flow integrations because the external tools have their own PagerDuty integrations configured

**Implementation Details:**

| Integration | Flow Type | What Happens |
|-------------|-----------|--------------|
| Datadog | Full Flow | Dashboard sends metrics → Datadog Monitor triggers → PagerDuty Event via Datadog's integration |
| Grafana Cloud | Full Flow | Dashboard sends annotation → Grafana Alert fires → PagerDuty Event via Grafana's integration |
| New Relic | Full Flow | Dashboard sends custom event → New Relic Alert triggers → PagerDuty Event via NR integration |
| CloudWatch | Full Flow | Dashboard publishes metric → CloudWatch Alarm fires → SNS → PagerDuty |
| GitHub Actions | Full Flow | Dashboard triggers workflow → Workflow sends PagerDuty event via configured secret |
| Prometheus | Full Flow | Routes through Grafana Cloud (Grafana hosts Prometheus) |
| Sentry | Fallback | Dashboard sends directly to PagerDuty Events API |
| Splunk | Fallback | Dashboard sends directly to PagerDuty Events API |
| UptimeRobot | Fallback | Dashboard sends directly to PagerDuty Events API |

**Settings Simplification (February 2026):**

The original implementation asked users for routing keys for each integration type. This was unnecessary and confusing because:
- Full Flow integrations don't need routing keys in the dashboard (they're configured in the external tools)
- Only Fallback integrations need a single routing key

**Current Settings Structure:**
```
PagerDuty Tab:
├── PagerDuty Instance (subdomain for display links)
└── Fallback Routing Key (optional - for direct API calls when external tool isn't configured)

External Tools Tab:
├── Datadog: API Key, App Key
├── New Relic: API Key, Account ID
├── Grafana: API Key, Instance URL
├── CloudWatch: Access Key, Secret Key, Region
└── GitHub Actions: PAT, Repo Owner, Repo Name
```

**File References:**
- `docs/demo-scenarios/src/components/SettingsModal.jsx` - Settings UI
- `docs/demo-scenarios/src/services/integrations/index.js` - Integration service implementations
- `docs/demo-scenarios/src/App.jsx` - Flow orchestration logic

---

### GitHub Actions Deployment Queuing Issues

**Problem:** GitHub Actions workflows may remain in "queued" status for extended periods, especially during GitHub infrastructure incidents or high load times.

**Symptoms:**
- Workflow shows "queued" status for more than 2 minutes
- `gh run watch` times out
- Deployments to GitHub Pages don't complete

**Diagnosis Steps:**
```bash
# Check workflow status
gh run list --workflow=deploy-demo.yml --limit=1 --json status,conclusion -q '.[0]'

# Check GitHub status for incidents
# Visit: https://www.githubstatus.com/

# Check if environment approval is needed
gh api repos/{owner}/{repo}/environments/github-pages --jq '.protection_rules'
```

**Workarounds:**
1. **Wait for GitHub to resolve** - Most queueing issues are temporary
2. **Cancel and retry:**
   ```bash
   gh run cancel {run_id}
   gh workflow run deploy-demo.yml
   ```
3. **Manual deployment** if urgent:
   ```bash
   cd docs/demo-scenarios
   npm run build
   # Upload dist/ contents via GitHub web UI to gh-pages branch
   ```

**GitHub Pages Environment Configuration:**
- The `github-pages` environment has `custom_branch_policies: true`
- Only the `main` branch is allowed to deploy
- No manual approval required (branch policy only)

---

### Browser localStorage Credential Storage

**Problem:** Dashboard credentials are stored in browser localStorage, which has security and persistence implications.

**Design Rationale:**
- No backend server = credentials never leave the user's browser
- Credentials are sent ONLY to their respective APIs (PagerDuty, Datadog, etc.)
- localStorage persists across sessions without requiring re-entry

**Security Considerations:**
- localStorage is accessible to any JavaScript on the same origin
- Credentials are stored in plaintext
- Clearing browser data removes all stored credentials

**Gotcha:** If users report "lost credentials," they likely:
1. Cleared browser data
2. Used private/incognito mode
3. Switched browsers
4. Domain changed (localhost vs deployed URL)

**localStorage Keys Used:**
```javascript
pagerduty_instance      // e.g., "acme" for acme.pagerduty.com
pagerduty_routing_key   // Fallback routing key
datadog_api_key         // Datadog API key
datadog_app_key         // Datadog Application key
newrelic_api_key        // New Relic User API key
newrelic_account_id     // New Relic Account ID
grafana_api_key         // Grafana Cloud API key
grafana_instance        // Grafana instance URL
aws_access_key          // AWS Access Key ID
aws_secret_key          // AWS Secret Access Key
aws_region              // AWS Region
github_token            // GitHub Personal Access Token
github_owner            // GitHub repository owner
github_repo             // GitHub repository name
```

---

## Quick Reference: API Endpoints Used

| Service | Endpoint | Auth Method |
|---------|----------|-------------|
| PagerDuty | `api.pagerduty.com` | `Authorization: Token token=XXX` |
| PagerDuty Events | `events.pagerduty.com/v2/enqueue` | Routing Key in payload |
| Jira | `{instance}.atlassian.net/rest/api/3/` | Basic Auth (email:token) |
| Confluence | `{instance}.atlassian.net/wiki/rest/api/` | Basic Auth (email:token) |
| Atlassian Admin | `api.atlassian.com/admin/v1/` | Bearer Token (Admin API key) |
| Datadog | `api.datadoghq.com/api/v1/` | `DD-API-KEY` and `DD-APPLICATION-KEY` headers |
| Grafana Cloud | `{instance}.grafana.net/api/` | `Authorization: Bearer {api_key}` |
| New Relic | `api.newrelic.com/graphql` | `API-Key` header |

---

## Files to Review

| File | Contains |
|------|----------|
| `incident_workflows.tf` | Workflow resource definitions (empty - steps added manually) |
| `incident_workflow_triggers.tf` | Workflow trigger definitions |
| `archive/scripts_oneoff/populate_workflow_steps.py` | Workflow step definitions and correct action IDs (reference only - API returns 500) |
| `scripts/list_workflows.py` | Utility to list workflows and generate import commands |
| `archive/scripts_oneoff/migrate_workflow_state.sh` | One-time script to import workflows into Terraform state |
| `archive/scripts_oneoff/populate_confluence.py` | Confluence content patterns |
| `global_orchestration.tf` | CEL expression examples |
| `docs/setup/MANUAL_SETUP_REQUIRED.md` | Manual setup procedures |
| `docs/demo-scenarios/src/components/SettingsModal.jsx` | Dashboard settings UI |
| `docs/demo-scenarios/src/services/integrations/` | Integration service implementations |

---

## 7. Lambda Lifecycle Workarounds

### PagerDuty User to Slack User Mapping

**Problem:** PagerDuty user IDs don't match Slack user IDs, so when you have responders from PagerDuty, you can't directly invite them to Slack channels or mention them.

**Solution:** Maintain a manual mapping in `aws/lambda-lifecycle/handler.py`:
```python
PAGERDUTY_TO_SLACK_USER_MAP = {
    "PD_USER_ID": "SLACK_USER_ID",
}
```

**How to populate:**
1. Get PagerDuty user IDs: `GET /users` API or Terraform output
2. Get Slack user IDs: Slack admin panel or `users.list` API
3. Match by email address

---

### Slack API Rate Limits

**Problem:** Posting many messages quickly can hit Slack rate limits.

**Solution:** The handler uses 2-3 second delays between messages:
```python
time.sleep(random.uniform(2, 3))
```

---

### Slack Channel Membership Requirements

**Problem:** Before posting to a channel or inviting users, the bot must be a member.

**Solution:**
- For incident channels created by PagerDuty, the Slack integration usually auto-adds the PagerDuty bot
- For the lifecycle Lambda's Slack app, ensure it has `channels:join` scope and call `conversations.join` if needed
- The `invite_users_to_channel` method handles the `already_in_channel` error gracefully

---

### Slack Guest Users Cannot Be Simulated

**Problem:** Slack guest users (single-channel or multi-channel guests) cannot be added to incident channels programmatically.

**Solution:** Only use full Slack workspace members for demo users.

---

### PagerDuty Add Responders API

**Problem:** The `POST /incidents/{id}/responders` endpoint requires specific payload format.

**Correct Format:**
```python
{
    "requester_id": "PXXXXXX",
    "message": "Optional message",
    "responders": [
        {"responder_request_target": {"id": "PXXXXXX", "type": "user"}}
    ]
}
```

---

### Status Update API

**Problem:** Status updates require a `from` email and specific message format.

**Correct Format:**
```python
{
    "message": "Status update text",
    "from": "user@example.com"
}
```

**Gotcha:** The `from` field is the email address, not user ID.

---

### Real Incident Detection

**Problem:** Demo automation should pause when real incidents occur to avoid confusion.

**Solution:** The handler checks for incidents NOT created by the simulator user:
```python
def check_for_real_scenario(pd, all_incidents):
    simulator_email = os.environ.get("SIMULATOR_USER_EMAIL", "yourname@example.com")
    for incident in all_incidents:
        creator = incident.get("created_by", {}).get("summary", "")
        if simulator_email not in creator.lower():
            return True
    return False
```

---

### Scenario Detection from Service Names

**Problem:** Different incident types should have different conversation styles.

**Solution:** Parse the service name to determine scenario type:
```python
def get_scenario_type(incident):
    service_name = incident.get("service", {}).get("summary", "").lower()
    if "database" in service_name or "db" in service_name:
        return "database"
    elif "payment" in service_name or "checkout" in service_name:
        return "payment"
    # etc.
```

---

### Lambda Environment Variables

Required environment variables (set in Terraform):

| Variable | Description |
|----------|-------------|
| `PAGERDUTY_API_TOKEN` | API token with write access |
| `PAGERDUTY_FROM_EMAIL` | Email for API requests requiring `From` header |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) |
| `SIMULATOR_USER_EMAIL` | Email of the demo user creating incidents |

---

### Responder Selection Logic

**Problem:** Need fair distribution of work among responders.

**Solution:** The handler uses a "prefer on-call responder" approach with random fallback:
```python
def select_resolver(responders, all_users):
    for r in responders:
        if r.get("type") == "user":
            return r
    return random.choice(all_users) if all_users else None
```

---

### Ensuring All Responders Participate

**Problem:** In demos, it looks odd if some responders never speak.

**Solution:** The `ensure_all_responders_participate` function tracks who has posted and ensures everyone contributes at least one message before resolution.

---

### Error Handling for Missing Channels

**Problem:** Incident channels may not exist yet when Lambda runs.

**Solution:** Graceful handling with retry-friendly design:
```python
channel_id = slack.find_channel_by_pattern(channel_name)
if not channel_id:
    logger.warning(f"Channel not found: {channel_name}")
    return  # Skip this incident, retry on next Lambda invocation
```

---

## 8. Datadog-PagerDuty Integration Workarounds

### Datadog Integration Must Use Event Orchestration Routing Key

**Problem:** When configuring the Datadog PagerDuty integration, you must use the Global Event Orchestration routing key - NOT a service-specific integration key.

**Background:**
Datadog's PagerDuty integration sends events to a "service" configured in Datadog. Originally, this was configured to send to a non-existent service `demo-simulator-alerts`, causing events to fail silently.

**Correct Configuration:**

1. In Datadog: Navigate to Integrations → PagerDuty
2. Add/Edit a service with:
   - **Service Name:** `demo-simulator-alerts` (this is what monitors reference)
   - **Integration Key:** Use the **Event Orchestration routing key**, NOT a service key

**Getting the Event Orchestration Routing Key:**
```bash
# From Terraform
terraform output datadog_routing_key
# Output: R028NMN4RMUJEARZ18IJURLOU1VWQ779
```

**Verification:**
```bash
# Test direct event to routing key
curl -s -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "R028NMN4RMUJEARZ18IJURLOU1VWQ779",
    "event_action": "trigger",
    "payload": {
      "summary": "[TEST] Datadog Integration Test",
      "severity": "warning",
      "source": "datadog-test"
    }
  }'
# Should return: {"status":"success",...}
```

**Why This Matters:**
- Service-specific integration keys route directly to that service
- Event Orchestration routing keys go through Global Event Orchestration rules
- The demo scenarios require Event Orchestration to route events based on payload content

**File Reference:**
- `aws/setup_integrations.py` - Contains the `create_pagerduty_integration()` function
- `integrations.tf` - Terraform definition for Event Orchestration integrations

---

### Datadog Monitor Notification Format

**Problem:** Datadog monitors must reference the exact service name configured in the PagerDuty integration.

**Correct Format:**
```
@pagerduty-demo-simulator-alerts
```

**Common Mistakes:**
- `@pagerduty-Demo-Simulator-Alerts` (case mismatch)
- `@pagerduty demo-simulator-alerts` (missing hyphen)
- `@pagerduty-demo_simulator_alerts` (underscore instead of hyphen)

**Monitor Message Example:**
```
Monitor: {{check_name}} is {{status}}
Host: {{host.name}}
Value: {{value}}

@pagerduty-demo-simulator-alerts
```

---

### Datadog Metrics Must Exceed Threshold for Evaluation Period

**Problem:** Sending a single high metric value may not trigger a monitor alert.

**Explanation:**
Datadog monitors evaluate metrics over time windows (typically 5 minutes). A single data point at time T=0 may not trigger an alert until:
1. The evaluation window fills with data
2. The average/max/min over the window exceeds the threshold

**Workaround:**
Send multiple metric values over several minutes:
```bash
for i in {1..5}; do
  curl -X POST "https://api.datadoghq.com/api/v2/series" \
    -H "Content-Type: application/json" \
    -H "DD-API-KEY: YOUR_API_KEY" \
    -d '{
      "series": [{
        "metric": "demo.api.response_time",
        "type": 0,
        "points": [['"$(date +%s)"', 500]],
        "tags": ["env:demo"]
      }]
    }'
  sleep 60
done
```

Or use the Lambda metrics function which sends metrics on a schedule.

---

## 9. Slack Integration Workarounds

### Multiple Slack Profiles for Channel Invitations

**Problem:** Admin user may have multiple Slack accounts (work and personal) and needs to be invited to incident channels on both.

**Solution:** Define both Slack user IDs as constants and invite both:

```python
# In aws/shared/clients.py
CONALL_SLACK_USER_ID = 'U0A9KAMT0BF'           # Work account
CONALL_SLACK_USER_ID_PERSONAL = 'U0A9GBYT999'  # Personal account

# In handler.py
def invite_to_slack_channel(channel_id, user_ids=None):
    if user_ids is None:
        user_ids = [CONALL_SLACK_USER_ID, CONALL_SLACK_USER_ID_PERSONAL]

    for user_id in user_ids:
        try:
            slack_client.conversations_invite(channel=channel_id, users=user_id)
        except SlackApiError as e:
            if 'already_in_channel' in str(e):
                pass  # Ignore - user already in channel
            else:
                logger.warning(f"Failed to invite {user_id}: {e}")
```

**Important:** After modifying this code, you MUST deploy the Lambda functions for the changes to take effect.

---

### Finding Slack User IDs

**Problem:** Slack user IDs are not visible in the Slack UI by default.

**Solutions:**

1. **Slack Admin Panel:**
   - Go to your Slack workspace admin: `{workspace}.slack.com/admin`
   - Click on a user → Their ID is in the URL

2. **Slack API:**
   ```bash
   curl -s "https://slack.com/api/users.list" \
     -H "Authorization: Bearer xoxb-YOUR-TOKEN" | \
     jq '.members[] | {id, name, profile: .profile.email}'
   ```

3. **User Profile in Slack:**
   - Click on a user's name
   - Click "More" → "Copy member ID"

---

## 10. PagerDuty API Token Issues

### Token Returns 401 Unauthorized

**Problem:** PagerDuty REST API tokens can expire or be revoked, causing 401 errors.

**Symptoms:**
```bash
curl -sI "https://api.pagerduty.com/incidents" \
  -H "Authorization: Token token=u+XXXXX"
# HTTP/1.1 401 Unauthorized
```

**Note:** This does NOT affect the Events API (events.pagerduty.com) which uses routing keys, not tokens.

**Diagnosis:**
1. Check if token exists in PagerDuty: People → API Access Keys
2. Try with a known working token
3. Check if token has required permissions

**Resolution:**
1. Generate new API token in PagerDuty UI
2. Update Lambda environment variables
3. Update local `.env` files
4. Update documentation with new token (redact in commits)

**Affected Operations When Token is Invalid:**
- Listing incidents
- Getting incident details
- Adding notes
- Updating incident status
- Listing users

**Unaffected Operations (use routing keys):**
- Triggering incidents via Events API
- Resolving incidents via Events API

---

## Files to Review (Updated)

| File | Contains |
|------|----------|
| `incident_workflows.tf` | Workflow resource definitions (empty - steps added manually) |
| `incident_workflow_triggers.tf` | Workflow trigger definitions |
| `archive/scripts_oneoff/populate_workflow_steps.py` | Workflow step definitions and correct action IDs (reference only - API returns 500) |
| `scripts/list_workflows.py` | Utility to list workflows and generate import commands |
| `archive/scripts_oneoff/migrate_workflow_state.sh` | One-time script to import workflows into Terraform state |
| `archive/scripts_oneoff/populate_confluence.py` | Confluence content patterns |
| `global_orchestration.tf` | CEL expression examples |
| `docs/setup/MANUAL_SETUP_REQUIRED.md` | Manual setup procedures |
| `docs/demo-scenarios/src/components/SettingsModal.jsx` | Dashboard settings UI |
| `docs/demo-scenarios/src/services/integrations/` | Integration service implementations |
| `aws/lambda-lifecycle/handler.py` | Lambda lifecycle simulator with responder actions |
| `aws/shared/clients.py` | Shared client code including Slack user mappings |
| `aws/setup_integrations.py` | Datadog/PagerDuty integration setup script |
| `integrations.tf` | Terraform definitions for Event Orchestration integrations |
| `docs/development/LAMBDA_LIFECYCLE_IMPLEMENTATION_GUIDE.md` | Detailed implementation guide for Lambda lifecycle |
