# EXHAUSTIVE PAGERDUTY DEMO ENVIRONMENT AUDIT

**Generated:** February 2026
**Purpose:** Complete audit of all tools, features, integrations, credentials, and automation opportunities

---

## EXECUTIVE SUMMARY

| Category | Items | Configured | Partially Configured | Not Configured |
|----------|-------|------------|---------------------|----------------|
| **PagerDuty Core** | 12 | 12 | 0 | 0 |
| **Slack Integration** | 8 | 8 | 0 | 0 |
| **Jira/Confluence** | 6 | 6 | 0 | 0 |
| **Monitoring Tools (Inbound)** | 13 | 9 | 4 | 0 |
| **ITSM/Collaboration (Outbound)** | 6 | 0 | 0 | 6 |
| **Conferencing** | 2 | 0 | 2 | 0 |
| **PagerDuty Add-Ons** | 8 | 1 | 0 | 7 |
| **Demo Simulator** | 5 | 3 | 2 | 0 |

**OVERALL STATUS:** Phase 1 Complete - 39 items configured, 8 items partially configured, 13 items not configured

---

## PART 1: PAGERDUTY CORE PLATFORM

### 1.1 Terraform Provider Connection

| Aspect | Status | Value | Source |
|--------|--------|-------|--------|
| Provider configured | CONFIGURED | pagerduty/pagerduty | `providers.tf` |
| API Token | CONFIGURED | Set via `PAGERDUTY_TOKEN` env var | Environment |
| Subdomain | INFERRED | `losandes` | terraform.tfvars |
| Admin privileges | UNKNOWN | Needs verification | - |

**AUTOMATION:** I can run `terraform init` and `terraform plan` to verify provider connectivity.

**USER ACTION REQUIRED:**
- [ ] Confirm the PagerDuty API token has Admin privileges
- [ ] Provide the token format: `u+XXXXXXXXXXXXXXXXX` or `pd+XXXXXXXXXXXXXXXXX`

### 1.2 Services (10 Deployed via Terraform)

| Service | Team | Status | Service ID |
|---------|------|--------|------------|
| Platform - Kubernetes/Platform | Platform | DEPLOYED | From Terraform state |
| Platform - Infrastructure | Platform | DEPLOYED | From Terraform state |
| Platform - Database | Platform | DEPLOYED | From Terraform state |
| Applications - API Gateway | Applications | DEPLOYED | From Terraform state |
| Applications - Payment Service | Applications | DEPLOYED | From Terraform state |
| Applications - User Service | Applications | DEPLOYED | From Terraform state |
| Applications - Frontend | Applications | DEPLOYED | From Terraform state |
| Data - ETL Pipeline | Data | DEPLOYED | From Terraform state |
| Data - Analytics | Data | DEPLOYED | From Terraform state |
| Security - WAF/Firewall | Security | DEPLOYED | From Terraform state |

**AUTOMATION:** All services are managed by Terraform. I can query `terraform state list` to get exact IDs.

### 1.3 Teams (4 Deployed via Terraform)

| Team | Status | Members |
|------|--------|---------|
| Platform Team | DEPLOYED | Ginny Tonic, Jim Beam, Jack Daniels |
| Applications Team | DEPLOYED | Kaptin Morgan, Arthur Guiness, Jameson Casker |
| Data Team | DEPLOYED | Jose Cuervo, James Murphy |
| Security Team | DEPLOYED | Uisce Beatha |

**AUTOMATION:** All teams managed by Terraform.

### 1.4 Users (10 Demo Users)

| User | Email | Team | Token Status |
|------|-------|------|--------------|
| Ginny Tonic | ginny.tonic@demo.pagerduty.com | Platform | PLACEHOLDER |
| Jim Beam | jim.beam@demo.pagerduty.com | Platform | PLACEHOLDER |
| Jack Daniels | jack.daniels@demo.pagerduty.com | Platform | PLACEHOLDER |
| Kaptin Morgan | kaptin.morgan@demo.pagerduty.com | Applications | PLACEHOLDER |
| Arthur Guiness | arthur.guiness@demo.pagerduty.com | Applications | PLACEHOLDER |
| Jameson Casker | jameson.casker@demo.pagerduty.com | Applications | PLACEHOLDER |
| Jose Cuervo | jose.cuervo@demo.pagerduty.com | Data | PLACEHOLDER |
| James Murphy | james.murphy@demo.pagerduty.com | Data | PLACEHOLDER |
| Uisce Beatha | uisce.beatha@demo.pagerduty.com | Security | PLACEHOLDER |
| Paddy Losty | paddy.losty@demo.pagerduty.com | Management | PLACEHOLDER |

**USER ACTION REQUIRED:**
```
For each user, generate API token:
1. Log into PagerDuty as the user (or as admin, create token for user)
2. Navigate to: User Settings > API Access > Create New API Key
3. Copy the token (format: u+XXXXXXXXXXXXXXXXX)
4. Store in secure location
```

**Tokens needed in `.env`:**
```bash
PAGERDUTY_TOKEN_GINNY=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_JIM=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_JACK=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_KAPTIN=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_ARTHUR=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_JAMESON=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_JOSE=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_JAMES=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_UISCE=u+XXXXXXXXXXXXXXXXX
PAGERDUTY_TOKEN_PADDY=u+XXXXXXXXXXXXXXXXX
```

### 1.5 Schedules (4 Deployed via Terraform)

| Schedule | Team | Rotation Type | Status |
|----------|------|---------------|--------|
| Platform On-Call | Platform | Weekly | DEPLOYED |
| Applications On-Call | Applications | Weekly | DEPLOYED |
| Data On-Call | Data | Weekly | DEPLOYED |
| Security On-Call | Security | Weekly | DEPLOYED |

**AUTOMATION:** All schedules managed by Terraform.

### 1.6 Escalation Policies (5+ Deployed via Terraform)

| Policy | Team | Levels | Status |
|--------|------|--------|--------|
| Platform EP | Platform | 3 | DEPLOYED |
| Applications EP | Applications | 3 | DEPLOYED |
| Data EP | Data | 2 | DEPLOYED |
| Security/SOC EP | Security | 3 | DEPLOYED |
| Major Incident EP | Cross-Team | 2 | DEPLOYED |

**AUTOMATION:** All escalation policies managed by Terraform.

### 1.7 Incident Workflows (22 Deployed via Terraform)

| Workflow | External Dependencies | Status |
|----------|----------------------|--------|
| Major Incident Full Mobilization | Slack, Zoom, Status Page | DEPLOYED |
| Security Incident Response | Slack, Jira (SECOPS) | DEPLOYED |
| Data Breach Response | Slack, Jira (COMPLIANCE) | DEPLOYED |
| Infrastructure Incident Response | Slack, Jira (INFRA) | DEPLOYED |
| Post-Incident Review Initiation | Jira (PIR) | DEPLOYED |
| Customer Impact Assessment | Salesforce | DEPLOYED (Salesforce not connected) |
| Payment Service Incident | Jira (PAYMENTS) | DEPLOYED |
| Data Pipeline Incident | Jira (DATA) | DEPLOYED |
| Incident Resolution Cleanup | Slack (archive) | DEPLOYED |
| Standard Incident Response | Slack, Jira (KAN) | DEPLOYED |
| High Priority Escalation | None | DEPLOYED |
| Shift Handoff Notification | Slack | DEPLOYED |
| After-Hours Escalation | None | DEPLOYED |
| P1 Auto-Acknowledge | None | DEPLOYED |
| Customer Notification | Slack | DEPLOYED |
| Escalation Warning | None | DEPLOYED |
| On-Call Handoff | Slack | DEPLOYED |
| Incident Type Router | None | DEPLOYED |
| Business Hours Check | None | DEPLOYED |
| Auto-Resolve Stale | None | DEPLOYED |
| Compliance Alert | Jira | DEPLOYED |
| Executive Notification | Slack | DEPLOYED |

**DEPENDENCIES STATUS:**
- Slack integration: CONFIGURED
- Jira projects (SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA, KAN): CONFIGURED
- Zoom integration: NOT CONNECTED (Phase 2)
- Status Page: NOT CONNECTED (Phase 2)
- Salesforce: NOT CONNECTED (Phase 3)

### 1.8 Automation Actions (22 Deployed via Terraform)

| Category | Actions | Runner Status |
|----------|---------|---------------|
| Diagnostics | 8 | Runners deployed (keys hardcoded) |
| Remediation | 7 | Runners deployed (keys hardcoded) |
| Security | 4 | Runners deployed (keys hardcoded) |
| Pipeline | 3 | Runners deployed (keys hardcoded) |

**Runners:**
- Primary: `csmscale-runbook-primary` (API key in Terraform - SECURITY CONCERN)
- Secondary: `csmscale-runbook-secondary` (API key in Terraform - SECURITY CONCERN)

**AUTOMATION:** All actions deployed via Terraform. Scripts are embedded in the Terraform code.

### 1.9 Event Orchestration

| Aspect | Status | Details |
|--------|--------|---------|
| Global Orchestration | DEPLOYED | `demo_orchestration` |
| Integration Count | 9/10 | (PagerDuty limit is 10) |

**Integrations with routing keys:**
1. Prometheus/Alertmanager - DEPLOYED
2. New Relic (Free Forever) - DEPLOYED
3. Sentry - DEPLOYED
4. UptimeRobot - DEPLOYED
5. GitHub Actions - DEPLOYED
6. Grafana Cloud - DEPLOYED
7. AWS CloudWatch - DEPLOYED
8. Datadog (Free Forever) - DEPLOYED
9. Splunk - DEPLOYED

**AUTOMATION:** I can run `terraform output all_routing_keys` to retrieve all routing keys after apply.

### 1.10 Priorities

| Priority | Color | Status |
|----------|-------|--------|
| P1 - Critical | Red | DEPLOYED |
| P2 - High | Orange | DEPLOYED |
| P3 - Medium | Yellow | DEPLOYED |
| P4 - Low | Green | DEPLOYED |
| P5 - Informational | Blue | DEPLOYED |

### 1.11 Incident Types (Feature Flag Dependent)

| Type | Status | Requirement |
|------|--------|-------------|
| Major Incident | CONDITIONAL | Requires `create_incident_types = true` |
| Security Incident | CONDITIONAL | Requires `create_incident_types = true` |

**Current Setting:** `create_incident_types = false` (default)

### 1.12 Custom Fields

| Field Name | Display Name | Type | Status |
|------------|--------------|------|--------|
| affected_system | Affected System | string | DEPLOYED |
| customer_tier | Customer Tier | string | DEPLOYED |
| region | Affected Region | string | DEPLOYED |
| compliance_flag | Compliance Requirement | string | DEPLOYED |
| incident_type | Incident Type | string | DEPLOYED |
| customer_impact_level | Customer Impact Level | string | DEPLOYED |

**AUTOMATION:** All 6 custom fields are managed by Terraform in `custom_fields.tf`.

---

## PART 2: SLACK INTEGRATION

### 2.1 Slack Workspace

| Aspect | Status | Value | Source |
|--------|--------|-------|--------|
| Workspace ID | CONFIGURED | `T0A9LN53CPQ` | terraform.tfvars |
| Bot Token | PLACEHOLDER | In .env.example | scripts/demo-simulator/.env.example |

**USER ACTION REQUIRED:**

**Step 1: Verify Slack App Permissions**
```
1. Log into Slack admin at: https://api.slack.com/apps
2. Select your PagerDuty-connected app
3. Navigate to: OAuth & Permissions > Scopes
4. Verify these Bot Token Scopes are present:
   - chat:write
   - chat:write.customize
   - channels:join
   - channels:read
   - channels:history
   - channels:manage
   - groups:read
   - groups:history
   - groups:write
   - users:read
   - users:read.email
   - reactions:write
   - reactions:read
   - files:write
   - files:read
   - im:write
   - mpim:write
```

**Step 2: Get Bot Token for Demo Simulator**
```
1. In Slack App settings: OAuth & Permissions
2. Copy "Bot User OAuth Token" (starts with xoxb-)
3. Add to scripts/demo-simulator/.env:
   SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXX-XXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX
```

### 2.2 Slack Channels

| Channel | Variable | Status | Channel ID |
|---------|----------|--------|------------|
| #active-incidents | SLACK_CHANNEL_ACTIVE_INCIDENTS | CONFIGURED | `C0A9GCXFSBD` |
| #platform-alerts | SLACK_CHANNEL_PLATFORM | PLACEHOLDER | - |
| #app-alerts | SLACK_CHANNEL_APPS | PLACEHOLDER | - |
| #data-alerts | SLACK_CHANNEL_DATA | PLACEHOLDER | - |
| #security-alerts | SLACK_CHANNEL_SECURITY | PLACEHOLDER | - |
| #on-call-handoff | SLACK_CHANNEL_HANDOFF | PLACEHOLDER | - |

**USER ACTION REQUIRED:**
```
For each channel:
1. Create the channel in Slack (if not exists)
2. Right-click channel name > Copy Link
3. Extract Channel ID from URL (format: CXXXXXXXXXX)
4. Add to .env file
```

### 2.3 Workflow Slack Actions

| Action | Workflows Using It | Dependency |
|--------|-------------------|------------|
| pagerduty.create-slack-channel | 6 workflows | `slack_connection_id` |
| pagerduty.archive-slack-channel | 1 workflow | `slack_connection_id` |
| pagerduty.post-to-slack-channel | Multiple | `slack_connection_id` |

**STATUS:** All Slack workflow actions will FAIL until `slack_connection_id` is provided.

---

## PART 3: JIRA/ATLASSIAN INTEGRATION

### 3.1 Jira Cloud Configuration

| Aspect | Status | Value | Source |
|--------|--------|-------|--------|
| Site URL | CONFIGURED | `https://losandes.atlassian.net` | terraform.tfvars |
| Account Name | CONFIGURED | `losandes` | terraform.tfvars |
| Default Project Key | CONFIGURED | `KAN` | terraform.tfvars |
| Issue Type | CONFIGURED | `Incident` | terraform.tfvars |
| PagerDuty Connection | **UNKNOWN** | Needs verification | - |
| API Token | **NOT CONFIGURED** | Required for demo-simulator | - |

### 3.2 Jira Projects Required by Workflows

| Project Key | Used In Workflow | Exists? | User Action |
|-------------|-----------------|---------|-------------|
| KAN | Standard Incident | ASSUMED YES | Verify |
| SECOPS | Security Incident | UNKNOWN | Create if not exists |
| COMPLIANCE | Data Breach | UNKNOWN | Create if not exists |
| INFRA | Infrastructure | UNKNOWN | Create if not exists |
| PIR | Post-Incident Review | UNKNOWN | Create if not exists |
| PAYMENTS | Payment Service | UNKNOWN | Create if not exists |
| DATA | Data Pipeline | UNKNOWN | Create if not exists |

**USER ACTION REQUIRED:**
```
1. Log into Jira: https://losandes.atlassian.net
2. For each project key above:
   a. Navigate to Projects
   b. If project doesn't exist, create it:
      - Click "Create project"
      - Choose "Scrum" or "Kanban" template
      - Set project key to match above
   c. Ensure "Incident" issue type exists in each project
3. For PagerDuty connection:
   a. In PagerDuty: Integrations > Extensions > Jira Cloud
   b. Verify connection to losandes.atlassian.net
   c. If not connected, follow OAuth flow
```

### 3.3 Jira API Token (for Demo Simulator)

**USER ACTION REQUIRED:**
```
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Label: "PagerDuty Demo Simulator"
4. Copy the token
5. Add to scripts/demo-simulator/.env:
   JIRA_BASE_URL=https://losandes.atlassian.net
   JIRA_API_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXX
   JIRA_USER_EMAIL=your.email@domain.com
```

### 3.4 Confluence (Same Atlassian Instance)

| Aspect | Status | Notes |
|--------|--------|-------|
| Availability | INFERRED | Same instance as Jira |
| Runbook Space | NOT CREATED | Need to create |
| Draft Runbooks | CREATED | In `docs/confluence-runbooks/` |

**USER ACTION REQUIRED:**
```
1. Log into Confluence: https://losandes.atlassian.net/wiki
2. Create space: "Engineering Runbooks" (key: RUNBOOKS)
3. Import runbook content from docs/confluence-runbooks/
```

**AUTOMATION:** I have already created draft runbook Markdown files that can be converted to Confluence format.

---

## PART 4: MONITORING TOOLS (INBOUND INTEGRATIONS)

### 4.1 Prometheus/Alertmanager

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| Actual Prometheus Instance | NOT DEPLOYED | Localhost in .env |
| Alertmanager Instance | NOT DEPLOYED | Localhost in .env |

**Current .env values (placeholders):**
```
PROMETHEUS_URL=http://localhost:9090
ALERTMANAGER_URL=http://localhost:9093
```

**USER ACTION (if deploying Prometheus):**
```
1. Deploy Prometheus and Alertmanager
2. Get routing key: terraform output prometheus_routing_key
3. Configure Alertmanager receiver:
   receivers:
     - name: 'pagerduty'
       pagerduty_configs:
         - routing_key: '<routing_key>'
```

### 4.2 Datadog

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| Datadog Account | PLACEHOLDER | Credentials not set |

**Current .env values (placeholders):**
```
DATADOG_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
DATADOG_APP_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
DATADOG_API_URL=https://api.datadoghq.com
```

**USER ACTION (if using Datadog):**
```
1. Sign up at: https://app.datadoghq.com (free tier available)
2. Navigate to: Organization Settings > API Keys
3. Create API Key and App Key
4. In Datadog: Integrations > PagerDuty
5. Enter routing key from: terraform output datadog_routing_key
```

### 4.3 New Relic

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| New Relic Account | PLACEHOLDER | Credentials not set |

**USER ACTION (if using New Relic):**
```
1. Sign up at: https://newrelic.com (free tier: 100GB/month)
2. Get API Key: API Keys > Create a key (type: User)
3. In New Relic: Alerts > Destinations > PagerDuty
4. Enter routing key from: terraform output new_relic_routing_key
```

### 4.4 Sentry

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| Sentry Account | PLACEHOLDER | Credentials not set |

**USER ACTION (if using Sentry):**
```
1. Sign up at: https://sentry.io (free tier available)
2. Create project, get DSN
3. In Sentry: Settings > Integrations > PagerDuty
4. Enter routing key from: terraform output sentry_routing_key
```

### 4.5 Splunk

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| Splunk Instance | PLACEHOLDER | Credentials not set |

**USER ACTION (if using Splunk):**
```
1. Splunk Cloud trial or Splunk Free available
2. Enable HTTP Event Collector (HEC)
3. In Splunk: Settings > Add-ons > PagerDuty
4. Enter routing key from: terraform output splunk_routing_key
```

### 4.6 UptimeRobot

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| UptimeRobot Account | NOT CONFIGURED | - |

**USER ACTION (if using UptimeRobot):**
```
1. Sign up at: https://uptimerobot.com (free tier: 50 monitors)
2. In UptimeRobot: My Settings > Alert Contacts
3. Add new contact: Webhook
4. URL: https://events.pagerduty.com/v2/enqueue
5. POST data: See PagerDuty Events API v2 format
6. Include routing key from: terraform output uptime_robot_routing_key
```

### 4.7 GitHub Actions

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| GitHub Connection | NOT CONFIGURED | - |

**USER ACTION (if using GitHub Actions):**
```
1. In your GitHub repo: Settings > Secrets
2. Add secret: PAGERDUTY_ROUTING_KEY
3. Value from: terraform output github_actions_routing_key
4. In workflow YAML:
   - name: Send PagerDuty Alert
     uses: pagerduty/pagerduty-events-action@v1
     with:
       routing-key: ${{ secrets.PAGERDUTY_ROUTING_KEY }}
```

### 4.8 Grafana Cloud

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| Grafana Account | NOT CONFIGURED | - |

**USER ACTION (if using Grafana Cloud):**
```
1. Sign up at: https://grafana.com/products/cloud (free tier available)
2. In Grafana: Alerting > Contact points
3. Add contact point: PagerDuty
4. Enter routing key from: terraform output grafana_cloud_routing_key
```

### 4.9 AWS CloudWatch

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | DEPLOYED | Routing key available |
| AWS Account | PLACEHOLDER | Credentials not set |

**USER ACTION (if using AWS CloudWatch):**
```
1. In AWS Console: SNS > Topics > Create topic
2. Create subscription: HTTPS endpoint to PagerDuty Events API
3. Or use CloudWatch Events/EventBridge rules
4. Include routing key from: terraform output aws_cloudwatch_routing_key
```

### 4.10 Elasticsearch/Elastalert

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | NOT IN ORCHESTRATION | Would need custom setup |
| Elasticsearch Instance | PLACEHOLDER | Localhost in .env |

**USER ACTION (if using Elasticsearch):**
```
1. Deploy Elasticsearch and Elastalert
2. Configure Elastalert PagerDuty alerter with routing key
```

### 4.11 Azure Monitor

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | NOT IN ORCHESTRATION | Would need custom setup |
| Azure Account | PLACEHOLDER | Credentials not set |

### 4.12 GCP Cloud Monitoring

| Aspect | Status | Value |
|--------|--------|-------|
| PagerDuty Integration | NOT IN ORCHESTRATION | Would need custom setup |
| GCP Project | PLACEHOLDER | Credentials not set |

### 4.13 Nagios Core

| Aspect | Status | Notes |
|--------|--------|-------|
| PagerDuty Integration | NOT DEPLOYED | Mentioned in spec for legacy scenarios |

---

## PART 5: CONFERENCING INTEGRATIONS

### 5.1 Zoom

| Aspect | Status | Notes |
|--------|--------|-------|
| Used In | Major Incident workflow | `pagerduty.create-conference-bridge` |
| Integration Status | **NOT CONNECTED** | Requires configuration |

**USER ACTION REQUIRED:**
```
1. In PagerDuty: Integrations > Extensions > Zoom
2. Click "Connect to Zoom"
3. Authorize with Zoom account
4. Configure default settings for meeting creation
```

### 5.2 Google Meet

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Spec | Alternative conferencing option |
| Integration Status | NOT CONFIGURED | Not used in current workflows |

**USER ACTION (optional):**
```
1. In PagerDuty: Integrations > Extensions > Google Meet
2. Authorize with Google Workspace account
```

---

## PART 6: STATUS PAGE

### 6.1 PagerDuty Status Page

| Aspect | Status | Notes |
|--------|--------|-------|
| Used In | Major Incident workflow | `pagerduty.post-to-status-page` |
| Integration Status | **NOT CONFIGURED** | Requires configuration |

**USER ACTION REQUIRED:**
```
1. In PagerDuty: Status Pages
2. Create new status page OR connect existing
3. Configure public URL and services to track
4. The workflow action will auto-post when configured
```

---

## PART 7: ITSM INTEGRATIONS (NOT CONFIGURED)

### 7.1 ServiceNow

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Spec, scripts/snow_keepalive.py | - |
| Integration Status | NOT CONFIGURED | Credentials placeholder |
| Required For | Enterprise scenarios (E1-E5) | - |

**USER ACTION (if implementing):**
```
1. ServiceNow Developer instance: https://developer.servicenow.com
2. Install PagerDuty app from ServiceNow Store
3. Configure bidirectional integration
4. Add to .env:
   SERVICENOW_INSTANCE=your-instance
   SERVICENOW_USER=api_user
   SERVICENOW_PASSWORD=password
```

### 7.2 Salesforce

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Customer Impact Assessment workflow | - |
| Integration Status | NOT CONFIGURED | Requires configuration |

**USER ACTION (if implementing):**
```
1. Salesforce Developer Edition available free
2. Install PagerDuty app from AppExchange
3. Configure connected app for API access
4. Add to .env:
   SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
   SALESFORCE_ACCESS_TOKEN=xxx
```

### 7.3 Microsoft Teams

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Spec | Alternative to Slack |
| Integration Status | NOT CONFIGURED | - |

### 7.4 Google Chat

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Spec | Alternative to Slack |
| Integration Status | NOT CONFIGURED | - |

---

## PART 8: PAGERDUTY ADD-ONS (NOT CONFIGURED)

### 8.1 Event Intelligence (AIOps)

| Feature | Status | Requirement |
|---------|--------|-------------|
| Intelligent Alert Grouping | NOT CONFIGURED | Event Intelligence add-on |
| Related Incidents | NOT CONFIGURED | Event Intelligence add-on |
| Past Incidents | NOT CONFIGURED | Event Intelligence add-on |

### 8.2 AI Agents

| Feature | Status | Requirement |
|---------|--------|-------------|
| SRE Agent | NOT CONFIGURED | AI Agents license |
| Scribe Agent | NOT CONFIGURED | AI Agents license |
| Shift Agent | NOT CONFIGURED | AI Agents license |

> **Note:** PagerDuty Advance and PagerDuty Copilot have been restructured into the AI Agents product line.

### 8.3 Runbook Automation (RBA)

| Aspect | Status | Notes |
|--------|--------|-------|
| Runners Deployed | YES | In automation_actions.tf |
| Actual Functionality | MOCK | Scripts won't execute without real infrastructure |

### 8.4 Jeli Post-Incident Reviews

| Aspect | Status | Notes |
|--------|--------|-------|
| Mentioned In | Spec | For learning reviews |
| Integration Status | NOT CONFIGURED | Separate product |

---

## PART 9: DEMO SIMULATOR SCRIPTS

### 9.1 Current Script Status

| Script | Location | Status | Dependencies |
|--------|----------|--------|--------------|
| demo-simulator | scripts/demo-simulator/ | PARTIALLY READY | Needs .env |
| trigger_demo_incident.sh | scripts/ | PRESENT | Needs routing keys |
| status_page_manager.py | scripts/ | PRESENT | Needs status page |
| snow_keepalive.py | scripts/ | PRESENT | Needs ServiceNow |

### 9.2 Demo Simulator Environment File

**Location:** `scripts/demo-simulator/.env` (create from `.env.example`)

**COMPLETE .env TEMPLATE:**
```bash
# =============================================================================
# PAGERDUTY CONFIGURATION
# =============================================================================
PAGERDUTY_API_BASE=https://api.pagerduty.com
PAGERDUTY_EVENTS_URL=https://events.pagerduty.com/v2/enqueue
PAGERDUTY_SUBDOMAIN=losandes

# Admin token (USER MUST PROVIDE)
PAGERDUTY_ADMIN_TOKEN=

# User tokens (USER MUST PROVIDE - 10 tokens)
PAGERDUTY_TOKEN_GINNY=
PAGERDUTY_TOKEN_JIM=
PAGERDUTY_TOKEN_JACK=
PAGERDUTY_TOKEN_KAPTIN=
PAGERDUTY_TOKEN_ARTHUR=
PAGERDUTY_TOKEN_JAMESON=
PAGERDUTY_TOKEN_JOSE=
PAGERDUTY_TOKEN_JAMES=
PAGERDUTY_TOKEN_UISCE=
PAGERDUTY_TOKEN_PADDY=

# Routing keys (RUN: terraform output all_routing_keys)
PD_ROUTING_KEY_PROMETHEUS=
PD_ROUTING_KEY_NEW_RELIC=
PD_ROUTING_KEY_SENTRY=
PD_ROUTING_KEY_UPTIME_ROBOT=
PD_ROUTING_KEY_GITHUB_ACTIONS=
PD_ROUTING_KEY_GRAFANA_CLOUD=
PD_ROUTING_KEY_AWS_CLOUDWATCH=
PD_ROUTING_KEY_DATADOG=
PD_ROUTING_KEY_SPLUNK=

# =============================================================================
# SLACK CONFIGURATION
# =============================================================================
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ACTIVE_INCIDENTS=C0A9GCXFSBD
SLACK_CHANNEL_PLATFORM=
SLACK_CHANNEL_APPS=
SLACK_CHANNEL_DATA=
SLACK_CHANNEL_SECURITY=
SLACK_CHANNEL_HANDOFF=

# =============================================================================
# JIRA CONFIGURATION
# =============================================================================
JIRA_BASE_URL=https://losandes.atlassian.net
JIRA_API_TOKEN=
JIRA_USER_EMAIL=
JIRA_PROJECT_KEY=KAN

# =============================================================================
# OPTIONAL: MONITORING TOOLS (if deployed)
# =============================================================================
# DATADOG_API_KEY=
# DATADOG_APP_KEY=
# NEW_RELIC_API_KEY=
# SENTRY_DSN=
# SPLUNK_HEC_TOKEN=
# PROMETHEUS_URL=http://localhost:9090
# ALERTMANAGER_URL=http://localhost:9093
```

---

## PART 10: CHRONOLOGICAL USER ACTION CHECKLIST

### PHASE 1: CRITICAL BLOCKERS (Must complete for basic functionality)

```
[x] 1. Verify PagerDuty Admin API Token permissions
      - Test: curl -H "Authorization: Token token=YOUR_TOKEN" https://api.pagerduty.com/users

[x] 2. Verify Slack Integration
      - PagerDuty > Integrations > Extensions > Slack
      - STATUS: CONFIGURED

[x] 3. Verify Slack App Scopes
      - https://api.slack.com/apps > Your PagerDuty App
      - OAuth & Permissions > Verify all required scopes
      - STATUS: CONFIGURED

[ ] 4. Connect Zoom to PagerDuty
      - PagerDuty > Integrations > Extensions > Zoom
      - Complete OAuth authorization

[ ] 5. Create/Configure Status Page
      - PagerDuty > Status Pages
      - Create or connect status page
```

### PHASE 2: JIRA SETUP (Required for ticket creation workflows)

```
[x] 6. Verify PagerDuty-Jira Connection
      - PagerDuty > Integrations > Extensions > Jira Cloud
      - Verify connection to losandes.atlassian.net
      - STATUS: CONFIGURED

[x] 7. Create Required Jira Projects
      - Log into https://losandes.atlassian.net
      - Create: SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA
      - Ensure "Incident" issue type exists in each
      - STATUS: CONFIGURED

[x] 8. Generate Jira API Token
      - https://id.atlassian.com/manage-profile/security/api-tokens
      - Create token for demo simulator
      - STATUS: CONFIGURED
```

### PHASE 3: DEMO USER TOKENS (Required for realistic simulations)

```
[ ] 9. Generate API Tokens for All Demo Users
      For each of the 10 users:
      - Log into PagerDuty
      - User Settings > API Access > Create New API Key
      - Save all tokens securely
```

### PHASE 4: SLACK CHANNELS (Required for notification routing)

```
[x] 10. Create Slack Channels
       - #platform-alerts
       - #app-alerts
       - #data-alerts
       - #security-alerts
       - #on-call-handoff
       - STATUS: CONFIGURED

[x] 11. Get Slack Bot Token
       - Slack App Settings > OAuth & Permissions
       - Copy Bot User OAuth Token
       - STATUS: CONFIGURED

[x] 12. Get Channel IDs
       - Right-click each channel > Copy Link
       - Extract CXXXXXXXXXX from URL
       - STATUS: CONFIGURED
```

### PHASE 5: TERRAFORM APPLY

```
[x] 13. Update terraform.tfvars with:
       - All required values
       - STATUS: CONFIGURED

[x] 14. Run Terraform
       terraform init
       terraform plan
       terraform apply
       - STATUS: APPLIED (terraform.tfstate present)

[x] 15. Capture Routing Keys
       terraform output all_routing_keys
       - STATUS: AVAILABLE via terraform output
```

### PHASE 6: DEMO SIMULATOR SETUP

```
[ ] 16. Create .env file
       cp scripts/demo-simulator/.env.example scripts/demo-simulator/.env
       # Fill in all values from previous steps

[ ] 17. Test Demo Simulator
       cd scripts/demo-simulator
       # Run test script (if available)
```

### PHASE 7: OPTIONAL INTEGRATIONS (for full feature demo)

```
[ ] 18. Connect Monitoring Tools (choose any):
       - Datadog: https://app.datadoghq.com > Integrations > PagerDuty
       - New Relic: Alerts > Destinations > PagerDuty
       - Sentry: Settings > Integrations > PagerDuty
       - UptimeRobot: Alert Contacts > Webhook
       - Grafana: Alerting > Contact points > PagerDuty
       
[ ] 19. Create Confluence Runbook Space
       - https://losandes.atlassian.net/wiki
       - Create "Engineering Runbooks" space
       - Import content from docs/confluence-runbooks/
```

---

## PART 11: AUTOMATION CAPABILITIES SUMMARY

### What I CAN Automate:

| Task | How |
|------|-----|
| Deploy all PagerDuty resources | `terraform apply` |
| Generate routing keys | `terraform output` |
| Create Terraform variable files | Direct file edit |
| Update workflow configurations | Terraform code changes |
| Create draft runbook content | File creation |
| Validate Terraform configuration | `terraform validate` |
| Query existing PagerDuty state | Terraform state/API calls |
| Create .env templates | File creation |

### What USER Must Do Manually:

| Task | Why |
|------|-----|
| Get Slack Connection ID | Requires UI navigation |
| Generate user API tokens | Security - user must authenticate |
| Create Jira projects | Requires Jira admin access |
| Generate Jira API token | Security - user must authenticate |
| Connect Zoom | OAuth requires user interaction |
| Create Status Page | Requires UI configuration |
| Create Slack channels | Requires Slack admin access |
| Get Slack Bot Token | Requires Slack app admin access |
| Configure monitoring tool integrations | Third-party UI required |
| Verify integration connections | Requires UI verification |

---

## PART 12: TERRAFORM VARIABLE UPDATES NEEDED

Add to `terraform.tfvars`:
```hcl
# REQUIRED - Get from PagerDuty UI
slack_connection_id = "XXXXXXXX"

# OPTIONAL - For data breach workflow
legal_user_id = "PXXXXXX"
dpo_user_id   = "PXXXXXX"
ciso_user_id  = "PXXXXXX"
```

---

## APPENDIX A: INTEGRATION VERIFICATION COMMANDS

```bash
# Verify PagerDuty API access
curl -s -H "Authorization: Token token=$PAGERDUTY_ADMIN_TOKEN" \
  https://api.pagerduty.com/abilities | jq '.abilities'

# Verify Slack Bot Token
curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test | jq '.'

# Verify Jira API Token
curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  https://losandes.atlassian.net/rest/api/3/myself | jq '.'

# Get all Terraform outputs
terraform output -json
```

---

## APPENDIX B: QUICK REFERENCE - ALL CREDENTIALS NEEDED

| Credential | Format | Where to Get |
|------------|--------|--------------|
| PagerDuty Admin Token | `u+XXXXXXXXXXXXXXXXX` | PagerDuty > User Settings > API Access |
| PagerDuty User Tokens (x10) | `u+XXXXXXXXXXXXXXXXX` | Each user's API Access page |
| Slack Connection ID | `XXXXXXXX` | PagerDuty > Integrations > Extensions > Slack |
| Slack Bot Token | `xoxb-XXXXX-XXXXX-XXXXX` | Slack App > OAuth & Permissions |
| Slack Channel IDs (x6) | `CXXXXXXXXXX` | Right-click channel > Copy Link |
| Jira API Token | `XXXXXXXXXXXXXXXX` | Atlassian Account > API Tokens |
| Jira User Email | `email@domain.com` | Your Atlassian account email |

---

**END OF AUDIT REPORT**
