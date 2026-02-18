# Manual Setup Required

**Last Updated:** February 2026
**Purpose:** Items that CANNOT be automated via Terraform, REST API, or MCP tools

---

## Why This Document Exists

PagerDuty's automation capabilities have limitations. Some features:
- Lack Terraform provider support
- Have no public REST API endpoints
- Require UI-based OAuth flows
- Need manual approval steps

This document tracks everything that must be configured manually in the PagerDuty UI or external tool UIs.

---

## Table of Contents

1. [Integration OAuth Connections](#1-integration-oauth-connections)
2. [External Tool Integrations](#2-external-tool-integrations)
3. [Incident Workflow Triggers](#3-incident-workflow-triggers)
4. [AIOps Configuration](#4-aiops-configuration)
5. [Service Graph Setup](#5-service-graph-setup)
6. [Runbook Automation](#6-runbook-automation)
7. [Status Page Configuration](#7-status-page-configuration)
8. [Analytics Dashboard Customization](#8-analytics-dashboard-customization)
9. [Mobile App Push Configuration](#9-mobile-app-push-configuration)
10. [SSO/SAML Configuration](#10-ssosaml-configuration)
11. [Atlassian Confluence Setup](#11-atlassian-confluence-setup)
12. [Implementation Checklist](#12-implementation-checklist)

---

## 1. Integration OAuth Connections

### What Cannot Be Automated

OAuth-based integrations require manual authorization flows in the browser.

### Slack Integration

**Location:** Settings → Integrations → Slack

**Manual Steps:**
1. Navigate to `Integrations` → `Slack`
2. Click "Add to Slack" button
3. Complete OAuth flow in browser popup
4. Select Slack workspace: `PDT Los Andes (E0A9LN3JFBQ)`
5. Authorize requested permissions
6. Map PagerDuty teams to Slack channels (optional)

**Post-Setup Verification:**
```bash
# Verify Slack connection ID exists
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  "https://api.pagerduty.com/extensions" | jq '.extensions[] | select(.type == "slack")'
```

**Why Manual:** OAuth 2.0 authorization flow requires browser-based user consent.

---

### Jira Cloud Integration

**Location:** Settings → Integrations → Jira Cloud

**Manual Steps:**
1. Navigate to `Integrations` → `Jira Cloud`
2. Click "Connect to Jira Cloud"
3. Enter Jira instance URL: `https://losandes.atlassian.net`
4. Authenticate with Atlassian account
5. Grant PagerDuty access permissions
6. Configure default project: `KAN`
7. Map issue types (optional)

**Post-Setup Verification:**
```bash
# Verify Jira extension exists
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  "https://api.pagerduty.com/extensions" | jq '.extensions[] | select(.type == "jira_cloud")'
```

**Why Manual:** Atlassian OAuth requires interactive browser authentication.

---

### Salesforce Service Cloud Integration

**Location:** Settings → Integrations → Salesforce

**Prerequisites (Salesforce Admin):**

Before connecting in PagerDuty, the following must be configured in Salesforce:

1. **Create a Connected App:**
   - Setup → Apps → App Manager → New Connected App
   - Enable OAuth Settings
   - Callback URL: `https://app.pagerduty.com/oauth/callback`
   - OAuth Scopes: `Full access (full)`, `Perform requests at any time (refresh_token, offline_access)`
   - Save and wait 2-10 minutes for propagation

2. **Enable OAuth Password Flow (Critical):**
   - Setup → OAuth and OpenID Connect Settings
   - Check "Allow OAuth Username-Password Flows"
   - Save

3. **Relax IP Restrictions on Connected App:**
   - Setup → Apps → Manage Connected Apps → [Your App] → Edit Policies
   - Set "IP Relaxation" to "Relax IP restrictions"
   - Save

**Manual Steps in PagerDuty:**
1. Navigate to `Integrations` → `Salesforce Service Cloud`
2. Click "Connect to Salesforce"
3. Log in to Salesforce instance: `https://orgfarm-1336c36e19-dev-ed.develop.lightning.force.com`
4. Grant PagerDuty connected app permissions
5. Configure bidirectional sync settings:
   - PD Incident → SF Case
   - SF Case → PD Incident (optional)
6. Map priority/severity fields
7. Configure auto-case creation rules

**Why Manual:** Salesforce OAuth + complex field mapping UI + requires prior Connected App setup.

**Status:** API CREDENTIALS VALIDATED - PagerDuty OAuth connection pending

---

### Microsoft Teams Integration

**Location:** Settings → Integrations → Microsoft Teams

**Manual Steps:**
1. Navigate to `Integrations` → `Microsoft Teams`
2. Click "Add to Teams"
3. Sign in with Microsoft work account
4. Select Teams tenant
5. Choose channels for incident notifications
6. Configure bot permissions

**Why Manual:** Microsoft Graph API OAuth requires browser-based consent.

**Status:** NOT CONFIGURED (optional enhancement)

---

### Zoom Conference Bridge Integration

**Location:** Settings → Integrations → Zoom

**Manual Steps:**
1. Navigate to `Integrations` → `Zoom`
2. Click "Connect Zoom"
3. Sign in with Zoom account (Admin or Licensed user)
4. Authorize PagerDuty to access Zoom API
5. Configure default meeting settings:
   - Enable waiting room (optional)
   - Set default meeting duration
   - Configure host privileges
6. Test by creating a conference bridge from an incident

**Post-Setup Verification:**
```bash
# Verify Zoom extension exists
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  "https://api.pagerduty.com/extensions" | jq '.extensions[] | select(.type | contains("zoom"))'
```

**Used In Workflows:**
- Major Incident Full Mobilization
- Customer Impact Communication
- Platform Infrastructure Degradation

**Why Manual:** Zoom OAuth requires browser-based authorization.

**Status:** NOT YET CONFIGURED (required for conference bridge scenarios)

---

### ServiceNow Integration (ITSM)

**Location:** Settings → Integrations → ServiceNow

**Manual Steps for Basic Integration:**
1. Navigate to `Integrations` → `ServiceNow`
2. Click "Connect ServiceNow"
3. Enter ServiceNow instance URL: `https://your-instance.service-now.com`
4. Authenticate with ServiceNow admin account
5. Grant PagerDuty necessary permissions
6. Configure incident sync settings:
   - PagerDuty Incident → ServiceNow Incident (one-way)
   - Field mapping: priority, urgency, description

**Manual Steps for Bidirectional Sync (EIM Required):**
1. Complete basic integration above
2. Enable bidirectional sync in settings
3. Configure ServiceNow → PagerDuty sync:
   - ServiceNow incident updates → PagerDuty
   - Custom field bidirectional sync
4. Configure automation rules for ticket creation
5. Test bidirectional sync with sample incident

**Post-Setup Verification:**
```bash
# Verify ServiceNow extension exists
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  "https://api.pagerduty.com/extensions" | jq '.extensions[] | select(.type | contains("servicenow"))'
```

**Plan Requirements:**
- Basic ServiceNow sync: Business plan
- Bidirectional sync with custom fields: Enterprise Incident Management (EIM)

**Why Manual:** ServiceNow OAuth + complex bidirectional configuration UI.

**Status:** NOT YET CONFIGURED (required for ITSM scenarios)

---

## 2. External Tool Integrations

These integrations require manual UI configuration in external observability tools to connect to PagerDuty.

### New Relic Alert Workflow

**Location:** New Relic > Alerts > Workflows

**Manual Steps:**
1. Create Alert Policy: Alerts > Alert Policies > Create new policy
2. Add NRQL Condition to policy:
   - Query: `SELECT average(demo.api.response_time) FROM Metric`
   - Threshold: > 500ms for 1 minute
3. Create Workflow: Alerts > Workflows > Add a workflow
4. Add Trigger: Select the alert policy created above
5. Add Destination: PagerDuty
   - If destination doesn't exist, create new PagerDuty destination
   - Enter PagerDuty routing key: `ed6b71f8718b4302d054db5f4cf7228f`
6. Test by triggering a metric spike

**Why Manual:** New Relic's GraphQL API for workflows has complex syntax requirements. UI is more reliable.

---

### Sentry PagerDuty Integration

**Location:** Sentry > Settings > Integrations > PagerDuty

**Manual Steps:**
1. Navigate to Sentry project settings
2. Go to Integrations > PagerDuty
3. Click "Add Installation"
4. Authorize connection to PagerDuty
5. Map Sentry projects to PagerDuty services

**Note:** Sentry PagerDuty integration requires Sentry Business plan. Free tier uses PagerDuty direct fallback.

**Why Manual:** OAuth-based integration requiring browser authorization.

---

## 3. Incident Workflow Triggers

### What Cannot Be Automated

Terraform can create Incident Workflows, but **triggers** for those workflows must be configured manually.

### Current Workflows Needing Triggers

| Workflow | Trigger Type | Trigger Condition |
|----------|--------------|-------------------|
| Major Incident Auto-Mobilization | Conditional | `incident.priority.name matches "P1" OR incident.priority.name matches "P2"` |
| Security Incident Response | Conditional | `incident.title matches "(?i)security" OR incident.title matches "(?i)breach"` |
| Customer Communications | Manual | N/A (triggered by responder) |
| Closeout & Follow-Ups | Conditional | `incident.status == "resolved"` |
| Sustained Degradation | Conditional | `incident.urgency == "high" AND incident.created_at < now() - 30m` |
| Payments Provider Outage | Conditional | `incident.title matches "(?i)stripe" OR incident.title matches "(?i)adyen"` |

### Proposed Workflows Needing Triggers

| Workflow | Suggested Trigger Type | Suggested Condition |
|----------|------------------------|---------------------|
| Compliance Incident Response | Conditional | `incident.title matches "(?i)(hipaa|pci|sox|compliance|audit)"` |
| Customer Impact Assessment | Conditional | `incident.priority.name matches "P1" AND incident.service.name matches "(Checkout|API Gateway|Cart)"` |
| Vendor Escalation | Manual + Conditional | Manual OR `incident.title matches "(?i)(vendor|stripe|adyen|aws)"` |
| Change-Related Incident | Manual | Triggered when responder suspects change correlation |
| After-Hours Escalation | Conditional | `incident.priority.name matches "(P1|P2)" AND current_time NOT BETWEEN "09:00" AND "18:00"` |

### Manual Configuration Steps

**Location:** Automation → Incident Workflows → [Workflow Name] → Triggers

**For Each Workflow:**
1. Open the workflow in PagerDuty UI
2. Click "Add Trigger"
3. Select trigger type:
   - **Manual:** Appears in incident action menu
   - **Conditional:** Automatically fires when conditions match
4. For conditional triggers:
   - Set "When" condition (incident created, updated, resolved)
   - Add filter conditions using PagerDuty Expression Language
   - Set "Run on" scope (specific services or all)
5. Save and test with sample incident

**Why Manual:** Terraform provider does not support `pagerduty_incident_workflow_trigger` resource.

---

## 3. AIOps Configuration

### Intelligent Alert Grouping

**Location:** Service → [Service Name] → Settings → Alert Grouping

**Manual Steps per Service:**
1. Navigate to service settings
2. Enable "Intelligent Alert Grouping"
3. Choose grouping type:
   - **Intelligent (ML-based):** Learns from historical patterns
   - **Content-based:** Groups by specific field matches
   - **Time-based:** Groups alerts within time window
4. Configure timeout window (default: 5 minutes)
5. Review and approve grouping suggestions (learning period)

**Recommended Configuration:**

| Service | Grouping Type | Timeout | Reason |
|---------|---------------|---------|--------|
| Kubernetes Platform | Intelligent | 10 min | Cascade failures |
| Database Cluster | Content-based (host) | 5 min | Host-specific issues |
| API Gateway | Time-based | 2 min | Rapid-fire errors |
| Checkout Service | Intelligent | 5 min | Complex dependencies |

**Why Manual:** Alert grouping settings not exposed in Terraform provider.

---

### Similar Incidents

**Location:** AIOps → Similar Incidents → Settings

**Manual Steps:**
1. Navigate to AIOps settings
2. Enable "Similar Incidents" feature
3. Configure similarity factors:
   - Title similarity weight
   - Service matching
   - Time proximity
4. Review suggested similar incidents during incidents

**Why Manual:** AIOps features are account-level settings not in API.

---

### Past Incidents

**Location:** Automatically enabled for Business/Digital Operations plans

**No Configuration Needed:** Automatically suggests past incidents based on ML analysis.

---

## 4. Service Graph Setup

### Technical Service Dependencies

**Location:** Service Directory → Service Graph

**Manual Steps:**
1. Navigate to Service Directory
2. Click "Service Graph" tab
3. For each service relationship:
   - Click service node
   - Click "Add Dependency"
   - Select dependent service
   - Choose dependency type: `uses` or `used_by`
4. Verify graph shows expected architecture

**Recommended Dependencies:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ API Gateway │────▶│  Checkout   │────▶│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Payments   │
                    └─────────────┘
```

**API Alternative (Partial):**
```bash
# Can be done via API (but UI is easier for complex graphs)
curl -X POST "https://api.pagerduty.com/service_dependencies" \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "relationships": [{
      "supporting_service": {"id": "PXXXXXX", "type": "service"},
      "dependent_service": {"id": "PYYYYYY", "type": "service"}
    }]
  }'
```

**Why Partially Manual:** API exists but UI provides better visualization and validation.

---

### Business Service Dependencies

**Location:** Service Directory → Business Services

**Manual Steps:**
1. Create Business Services (can be done in Terraform)
2. Navigate to Business Service
3. Click "Add Supporting Services"
4. Select technical services that support this business capability
5. Configure impact settings

**Terraform Support:** `pagerduty_business_service_subscriber` resource exists but is limited.

---

## 5. Runbook Automation

### Automation Actions (PagerDuty Runbook Automation)

**Location:** Automation → Runbook Automation

**Manual Steps:**
1. Navigate to Automation → Runbook Automation
2. Create new automation:
   - Name: e.g., "Restart Kubernetes Pod"
   - Runner: Select Process Automation runner
   - Script/Job: Define automation steps
3. Configure triggers:
   - Manual (from incident)
   - Automatic (based on conditions)
4. Set permissions (who can run)
5. Test with dry-run

**Example Automations to Create:**

| Name | Trigger | Action |
|------|---------|--------|
| Restart K8s Pod | Manual | `kubectl rollout restart` |
| Clear Redis Cache | Manual | `redis-cli FLUSHDB` |
| Scale Up Service | Manual | `kubectl scale --replicas=5` |
| Database Failover | Manual (P1 only) | Initiate RDS failover |

**Why Manual:** Process Automation requires Rundeck/PRA integration setup that's organization-specific.

---

## 6. Status Page Configuration

### Internal Status Page Setup

**Location:** Status → Status Pages

**Manual Steps:**
1. Navigate to Status → Status Pages
2. Click "Create Status Page"
3. Configure:
   - Name: "Los Andes Platform Status"
   - Subdomain: `losandes.status.pagerduty.com`
   - Branding (logo, colors)
4. Add components (services to display)
5. Configure subscriber notifications
6. Set up scheduled maintenance templates

**Why Manual:** Status pages require visual branding setup and component selection.

---

## 7. Analytics Dashboard Customization

### Custom Dashboards

**Location:** Analytics → Dashboards

**Manual Steps:**
1. Navigate to Analytics
2. Click "Create Dashboard"
3. Add widgets:
   - Incident volume by service
   - MTTA/MTTR trends
   - On-call load distribution
   - SLA compliance
4. Set filters (date range, teams, services)
5. Save and share with team

**Why Manual:** Dashboard builder is UI-only feature.

---

### Service Standards

**Location:** Service Directory → Standards

**Manual Steps:**
1. Navigate to Service Directory
2. Click "Standards" tab
3. Define standards:
   - Service must have runbook
   - Service must have escalation policy
   - Service must have on-call schedule
4. Set compliance targets

**Why Manual:** Standards feature configuration is UI-only.

---

## 8. Mobile App Push Configuration

### Push Notification Settings

**Location:** User Profile → Notification Rules (per user)

**Manual Steps:**
1. Each user downloads PagerDuty mobile app
2. User logs in and grants push permissions
3. User configures notification preferences:
   - High urgency: Push + Sound
   - Low urgency: Push only
4. Test notifications

**Why Manual:** User-specific device registration.

---

## 9. SSO/SAML Configuration

### SAML 2.0 Setup

**Location:** Account Settings → Single Sign-On

**Manual Steps:**
1. Navigate to Account Settings → SSO
2. Click "Configure SAML"
3. Enter IdP metadata:
   - SSO URL
   - Certificate
   - Entity ID
4. Download SP metadata for IdP configuration
5. Configure user provisioning (SCIM optional)
6. Test SSO login

**Why Manual:** Requires IdP-side configuration and certificate exchange.

**Status:** NOT CONFIGURED (demo environment uses password auth)

---

## 10. Atlassian Confluence Setup

### What Needs Manual Setup

Confluence is not currently enabled for the Los Andes Atlassian site (`losandes.atlassian.net`). The Confluence API returns authentication errors because the product hasn't been provisioned.

### Prerequisites

1. **Atlassian Cloud Admin Access:** Must have admin access to `admin.atlassian.com`
2. **Product License:** Confluence Standard or Premium license

### Manual Setup Steps

**Step 1: Enable Confluence Product**

1. Go to `https://admin.atlassian.com`
2. Sign in with Atlassian account: `conalllynch88@gmail.com`
3. Select the "losandes" organization
4. Navigate to **Products** → **Add product**
5. Select **Confluence**
6. Choose plan (Standard recommended for demos)
7. Confirm and wait for provisioning (2-5 minutes)

**Step 2: Create Runbooks Space**

After Confluence is enabled:

1. Navigate to `https://losandes.atlassian.net/wiki`
2. Click **Create space**
3. Select **Blank space** template
4. Configure:
   - Space name: `Incident Runbooks`
   - Space key: `RUNBOOKS`
   - Description: `Operational runbooks and incident response procedures for the Los Andes PagerDuty demo environment`
5. Click **Create**

**Step 3: Create Initial Pages (Optional)**

Create the following pages in the RUNBOOKS space:

| Page Title | Purpose |
|------------|---------|
| Runbook Template | Standard template for new runbooks |
| P1 Response Checklist | High-priority incident response steps |
| Database Incident Runbook | Database-specific troubleshooting |
| Kubernetes Platform Runbook | K8s-specific troubleshooting |
| Payment System Runbook | Payment failure investigation |
| Security Incident Runbook | Security breach response steps |

**Step 4: Configure Permissions**

1. Go to **Space settings** → **Permissions**
2. Add groups/users with appropriate access:
   - Admins: Full access
   - Engineers: View and edit
   - Stakeholders: View only

### API Verification (After Setup)

```bash
# Test Confluence API access
curl -u "conalllynch88@gmail.com:$ATLASSIAN_API_TOKEN" \
  -H "Accept: application/json" \
  "https://losandes.atlassian.net/wiki/api/v2/spaces"

# Expected: JSON array with RUNBOOKS space
```

### Integration with PagerDuty

After Confluence is set up:

1. Runbook links can be added to PagerDuty services
2. Incident workflows can reference Confluence pages
3. Automation actions can include Confluence links in notifications

### Why Manual

- Confluence product enablement requires Atlassian admin console access
- Cannot be done via API or Terraform
- Requires billing/licensing decisions

**Status:** NOT YET ENABLED - Confluence returns 401 errors at `losandes.atlassian.net/wiki`

---

## 11. Implementation Checklist

### Required for Full Demo Functionality

| Task | Status | Priority | Assignee |
|------|--------|----------|----------|
| Slack OAuth connection | ✅ Done | Critical | - |
| Jira OAuth connection | ✅ Done | Critical | - |
| Jira projects created | ✅ Done | High | - |
| Confluence product enablement | ❌ Not Started | Medium | [TBD] |
| Confluence RUNBOOKS space | ❌ Not Started | Medium | [TBD] |
| Incident workflow triggers (existing 8) | ⚠️ Partial | High | [TBD] |
| Incident workflow triggers (proposed 5) | ❌ Not Started | Medium | [TBD] |
| Alert grouping per service | ⚠️ Partial | Medium | [TBD] |
| Service graph dependencies | ❌ Not Started | Medium | [TBD] |
| Status page setup | ❌ Not Started | Low | [TBD] |

### Optional Enhancements

| Task | Status | Priority | Assignee |
|------|--------|----------|----------|
| Salesforce integration | ❌ Not Started | Medium | [TBD] |
| Microsoft Teams integration | ❌ Not Started | Low | [TBD] |
| Runbook Automation setup | ❌ Not Started | Low | [TBD] |
| Custom analytics dashboards | ❌ Not Started | Low | [TBD] |
| SAML SSO | ❌ Not Started | Low | [TBD] |

---

## Appendix: API vs. Terraform vs. UI Comparison

| Feature | Terraform | REST API | UI Only |
|---------|-----------|----------|---------|
| Services | ✅ | ✅ | - |
| Teams | ✅ | ✅ | - |
| Escalation Policies | ✅ | ✅ | - |
| Schedules | ✅ | ✅ | - |
| Event Orchestration | ✅ | ✅ | - |
| Incident Workflows | ✅ | ✅ | - |
| Workflow Triggers | ❌ | ❌ | ✅ |
| Integrations (Generic) | ✅ | ✅ | - |
| Integrations (OAuth) | ❌ | ❌ | ✅ |
| Alert Grouping | ❌ | Partial | ✅ |
| Service Dependencies | ❌ | ✅ | ✅ |
| AIOps Settings | ❌ | ❌ | ✅ |
| Status Pages | Partial | Partial | ✅ |
| Analytics Dashboards | ❌ | ❌ | ✅ |

---

## Troubleshooting

### "Workflow not triggering automatically"

**Cause:** Trigger not configured in UI

**Solution:**
1. Go to workflow → Triggers
2. Add conditional trigger with appropriate conditions
3. Ensure "Run on" scope includes target services

### "Slack channel creation fails in workflow"

**Cause:** OAuth token expired or permissions changed

**Solution:**
1. Go to Integrations → Slack
2. Click "Reconnect"
3. Re-authorize permissions

### "Jira ticket creation fails"

**Cause:** Jira project permissions or OAuth token issue

**Solution:**
1. Verify Jira project exists and user has create permissions
2. Go to Integrations → Jira Cloud
3. Reconnect if needed

---

*Document maintained by Demo Engineering Team*
*Last verified: January 2025*
