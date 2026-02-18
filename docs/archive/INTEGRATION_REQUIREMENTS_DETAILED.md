# Integration Requirements - Detailed Status & User Actions

> **Document Purpose**: Complete audit of all integrations, what I have/don't have access to, what's connected, and chronological user actions required.

---

## PART 1: CURRENT INTEGRATION STATUS AUDIT

### Legend
- **CONNECTED**: Integration configured in PagerDuty and working
- **PARTIALLY CONFIGURED**: Terraform references exist but needs PagerDuty UI setup
- **NOT CONNECTED**: No integration exists
- **CREDENTIALS MISSING**: Configuration exists but credentials placeholder only

---

## 1.1 PagerDuty Core (CONFIGURED)

| Component | Status | Notes |
|-----------|--------|-------|
| PagerDuty Admin API Token | UNKNOWN | Not visible - you must confirm |
| PagerDuty Subdomain | `losandes` (inferred from Jira URL) | Confirm: `https://losandes.pagerduty.com` |
| Terraform Provider | CONNECTED | Provider configured, state exists |
| Services | DEPLOYED | 12 services defined |
| Schedules | DEPLOYED | 5 schedules defined |
| Escalation Policies | DEPLOYED | 5 escalation policies |
| Incident Workflows | DEPLOYED | 15+ workflows with Slack/Jira steps |
| Automation Actions | DEPLOYED | Multiple diagnostic/remediation actions |

---

## 1.2 Slack Integration

| Component | Status | Value/Notes |
|-----------|--------|-------------|
| Slack Workspace ID | CONFIGURED | `T0A9LN53CPQ` |
| Slack Bot Token | CONFIGURED | Set via environment variable |
| Channel: Active Incidents | CONFIGURED | `C0A9GCXFSBD` |
| Channel: Platform | CONFIGURED | Team-specific channel |
| Channel: Apps | CONFIGURED | Team-specific channel |
| Channel: Data | CONFIGURED | Team-specific channel |
| Channel: Security | CONFIGURED | Team-specific channel |
| Channel: Handoff | CONFIGURED | Team-specific channel |

**Workflow Actions Using Slack:**
- `pagerduty.create-slack-channel` (Major Incident, Security, Breach, Payments, Infrastructure)
- `pagerduty.archive-slack-channel` (Incident Closeout)

**Required Slack App Scopes:**
```
channels:manage, channels:read, channels:write, chat:write,
groups:write, im:write, users:read, users:read.email
```

---

## 1.3 Jira Cloud Integration

| Component | Status | Value/Notes |
|-----------|--------|-------------|
| Jira Site URL | CONFIGURED | `https://losandes.atlassian.net` |
| Jira Account Name | CONFIGURED | `losandes` |
| Default Project Key | CONFIGURED | `KAN` (Kanban) |
| PagerDuty Jira Cloud Connection | CONFIGURED | Connected and verified |
| Jira API Token | CONFIGURED | Set via environment variable |
| Confluence Access | CONFIGURED | Part of same Atlassian instance |

**Jira Projects Referenced in Workflows (MUST CREATE):**

| Project Key | Purpose | Issue Types Needed |
|-------------|---------|-------------------|
| `SECOPS` | Security incidents | Security Incident |
| `COMPLIANCE` | Data breach/compliance | Data Breach |
| `INFRA` | Infrastructure incidents | Incident |
| `PIR` | Post-Incident Reviews | Post-Incident Review |
| `PAYMENTS` | Payment system outages | Outage |
| `DATA` | Data pipeline issues | Pipeline Issue |
| `KAN` | Default/general | Incident |

---

## 1.4 Zoom Integration

| Component | Status | Notes |
|-----------|--------|-------|
| Zoom Integration | UNKNOWN | Referenced in Major Incident workflow |
| Conference Bridge Type | `zoom` | Hardcoded in workflow |

**Workflow Actions Using Zoom:**
- `pagerduty.create-conference-bridge` with `conference_type = "zoom"`

---

## 1.5 Status Page Integration

| Component | Status | Notes |
|-----------|--------|-------|
| PagerDuty Status Page | UNKNOWN | Referenced in Major Incident workflow |

**Workflow Actions Using Status Page:**
- `pagerduty.post-to-status-page` with status and message

---

## 1.6 Monitoring Tools - INBOUND

| Tool | Status | Credentials | Notes |
|------|--------|-------------|-------|
| **Datadog** | PARTIALLY CONFIGURED | Placeholder | `datadog/` folder exists with tfvars |
| **Splunk** | NOT CONNECTED | Placeholder | HEC URL/Token in .env.example |
| **New Relic** | NOT CONNECTED | Placeholder | API/Insights keys placeholder |
| **Prometheus/Alertmanager** | NOT CONNECTED | localhost URLs | Self-hosted required |
| **Elasticsearch** | NOT CONNECTED | Placeholder | localhost URL, API key placeholder |
| **Sentry** | NOT CONNECTED | Placeholder | DSN/Auth token placeholder |
| **Azure Monitor** | NOT CONNECTED | No config | Listed in spec only |
| **GCP Monitoring** | NOT CONNECTED | No config | Listed in spec only |
| **Nagios** | NOT CONNECTED | No config | Listed in spec only |
| **GitHub Actions** | NOT CONNECTED | No config | Listed in spec only |
| **UptimeRobot** | NOT CONNECTED | No config | Listed in spec only |

---

## 1.7 ITSM/Collaboration - OUTBOUND

| Tool | Status | Notes |
|------|--------|-------|
| **Slack** | CONFIGURED | Fully integrated with PagerDuty |
| **Microsoft Teams** | NOT CONNECTED | Listed in spec only |
| **Google Chat** | NOT CONNECTED | Listed in spec only |
| **Jira Cloud** | CONFIGURED | Fully integrated with PagerDuty |
| **ServiceNow** | NOT CONNECTED | Enterprise tier feature |
| **Salesforce** | NOT CONNECTED | CSOps tier feature |
| **Confluence** | CONFIGURED | Same Atlassian instance |
| **Zoom** | UNKNOWN | Referenced in workflow |
| **Google Meet** | NOT CONNECTED | Listed in spec only |

---

## 1.8 PagerDuty Add-Ons (STATUS UNKNOWN - USER MUST CONFIRM)

| Add-On | Required For | Status |
|--------|--------------|--------|
| **Runbook Automation (RBA)** | Automation Actions | UNKNOWN |
| **Rundeck** | RBA Jobs | UNKNOWN |
| **Event Intelligence (AIOps)** | Alert grouping, noise reduction | UNKNOWN |
| **SRE Agent** | Autonomous investigation | UNKNOWN |
| **Scribe Agent** | Auto documentation | UNKNOWN |
| **Shift Agent** | On-call handoff | UNKNOWN |
| **Status Pages** | Public/Internal status | UNKNOWN |
| **Jeli** | Post-Incident Reviews | UNKNOWN |

---

## 1.9 Demo Simulator User Tokens

| User | Email | Token Status |
|------|-------|--------------|
| Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Jim Beam | jbeam@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Kaptin Morgan | kmorgan@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Jameson Irish | jmurphy@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| James Casker | jcasker@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Uisce Beatha | ubeatha@losandesgaa.onmicrosoft.com | PLACEHOLDER |
| Paddy Losty | plosty@losandesgaa.onmicrosoft.com | PLACEHOLDER |

---

## PART 2: JIRA CLOUD & CONFLUENCE SETUP FOR RUNBOOKS

### 2.1 Required Jira Projects

I will draft Jira project configurations and Confluence space structure. You need to create these in Atlassian.

**Projects to Create:**

#### Project 1: SECOPS (Security Operations)
```
Key: SECOPS
Type: Team-managed or Company-managed
Template: IT Service Management or Kanban
Issue Types:
  - Security Incident
  - Security Alert
  - Vulnerability
  - Compliance Issue
Workflows: Simple (To Do → In Progress → Done) or ITSM
```

#### Project 2: COMPLIANCE
```
Key: COMPLIANCE
Type: Company-managed
Template: IT Service Management
Issue Types:
  - Data Breach
  - Regulatory Notice
  - Audit Finding
  - Policy Violation
Workflows: ITSM with approval gates
```

#### Project 3: INFRA (Infrastructure)
```
Key: INFRA
Type: Team-managed
Template: Kanban
Issue Types:
  - Incident
  - Problem
  - Change Request
  - Maintenance
Workflows: Simple Kanban
```

#### Project 4: PIR (Post-Incident Reviews)
```
Key: PIR
Type: Team-managed
Template: Kanban or Scrum
Issue Types:
  - Post-Incident Review
  - Action Item
  - Follow-up Task
Workflows: PIR Workflow (New → Investigation → Review → Closed)
```

#### Project 5: PAYMENTS
```
Key: PAYMENTS
Type: Team-managed
Template: IT Service Management
Issue Types:
  - Outage
  - Incident
  - Problem
  - Change Request
Workflows: ITSM
```

#### Project 6: DATA (Data Engineering)
```
Key: DATA
Type: Team-managed
Template: Kanban
Issue Types:
  - Pipeline Issue
  - Data Quality
  - ETL Failure
  - Schema Change
Workflows: Simple Kanban
```

### 2.2 Confluence Space Structure for Runbooks

**Space to Create: `RUNBOOKS` (or use existing documentation space)**

I will draft the following Confluence pages with realistic content:

```
RUNBOOKS/
├── Home
├── How to Use These Runbooks
├── Platform/
│   ├── DBRE (Database)
│   │   ├── PostgreSQL Troubleshooting
│   │   ├── Redis Cache Issues
│   │   ├── MySQL Replication Failures
│   │   └── Database Failover Procedure
│   ├── Kubernetes
│   │   ├── Pod Crash Investigation
│   │   ├── Node Not Ready
│   │   ├── HPA Scaling Issues
│   │   └── Cluster Upgrade Procedure
│   └── Networking
│       ├── DNS Issues
│       ├── Load Balancer Troubleshooting
│       └── CDN Cache Invalidation
├── Application/
│   ├── Checkout
│   │   ├── Payment Gateway Failures
│   │   └── Cart Service Issues
│   ├── Orders API
│   │   ├── Order Processing Failures
│   │   └── Fulfillment Integration Issues
│   └── Identity
│       ├── Authentication Failures
│       ├── SSO Issues
│       └── Session Management
├── Data/
│   ├── Streaming
│   │   ├── Kafka Consumer Lag
│   │   └── Event Processing Failures
│   └── Analytics
│       ├── ETL Pipeline Failures
│       └── Data Quality Issues
├── Security/
│   ├── Security Incident Response
│   ├── Data Breach Protocol
│   └── Forensic Evidence Collection
├── Major Incident/
│   ├── Major Incident Protocol
│   ├── Communication Templates
│   └── Stakeholder Notification
└── Templates/
    ├── Runbook Template
    ├── PIR Template
    └── Communication Template
```

---

## PART 3: CHRONOLOGICAL USER ACTION LIST

### PRIORITY 1: IMMEDIATE (Required for Basic Functionality)

#### Action 1.1: Confirm PagerDuty Account Details
```
WHAT: Provide PagerDuty subdomain and admin access confirmation
WHERE: PagerDuty UI → Account Settings
WHY: Need to verify Terraform is connecting to correct account
PROVIDE:
  - PagerDuty subdomain: ______________ (e.g., "losandes")
  - Admin API token working: YES / NO
```

#### Action 1.2: Verify Slack Integration in PagerDuty
```
WHAT: Verify Slack integration exists in PagerDuty
WHERE: PagerDuty UI → Integrations → Slack
WHY: Incident workflows create Slack channels

STATUS: CONFIGURED - Slack integration is fully connected and operational.

VERIFIED:
  - Slack Workspace: YES
  - Channel creation working: YES
```

#### Action 1.3: Verify Jira Cloud Integration in PagerDuty
```
WHAT: Verify Jira Cloud integration exists in PagerDuty
WHERE: PagerDuty UI → Integrations → Jira Cloud
WHY: Incident workflows create Jira tickets

STATUS: CONFIGURED - Jira integration is fully connected and operational.

VERIFIED:
  - Jira integration working: YES
  - Can create issues from PagerDuty: YES
```

---

### PRIORITY 2: JIRA PROJECT SETUP (Required for Workflow Ticket Creation)

#### Action 2.1: Create SECOPS Project
```
WHAT: Create Jira project for security incidents
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Go to https://losandes.atlassian.net
2. Click "Projects" → "Create project"
3. Choose "Team-managed project" → "Kanban"
4. Name: "Security Operations"
5. Key: "SECOPS"
6. Add issue type: "Security Incident"
```

#### Action 2.2: Create COMPLIANCE Project
```
WHAT: Create Jira project for compliance/breach tracking
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Create new project
2. Name: "Compliance"
3. Key: "COMPLIANCE"
4. Add issue type: "Data Breach"
```

#### Action 2.3: Create INFRA Project
```
WHAT: Create Jira project for infrastructure incidents
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Create new project
2. Name: "Infrastructure"
3. Key: "INFRA"
4. Add issue type: "Incident"
```

#### Action 2.4: Create PIR Project
```
WHAT: Create Jira project for post-incident reviews
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Create new project
2. Name: "Post-Incident Reviews"
3. Key: "PIR"
4. Add issue type: "Post-Incident Review"
```

#### Action 2.5: Create PAYMENTS Project
```
WHAT: Create Jira project for payment system issues
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Create new project
2. Name: "Payments"
3. Key: "PAYMENTS"
4. Add issue type: "Outage"
```

#### Action 2.6: Create DATA Project
```
WHAT: Create Jira project for data/pipeline issues
WHERE: Jira → Create Project
TIME: 5 minutes

STEPS:
1. Create new project
2. Name: "Data Engineering"
3. Key: "DATA"
4. Add issue type: "Pipeline Issue"
```

---

### PRIORITY 3: CONFLUENCE SETUP (Required for Runbook Links)

#### Action 3.1: Create Confluence Space for Runbooks
```
WHAT: Create space to host runbook documentation
WHERE: Confluence → Create Space
TIME: 2 minutes

STEPS:
1. Go to https://losandes.atlassian.net/wiki
2. Click "Spaces" → "Create space"
3. Choose "Documentation space"
4. Name: "Runbooks"
5. Key: "RUNBOOKS"
```

#### Action 3.2: Provide Confluence API Token
```
WHAT: API token for me to create runbook pages
WHERE: Atlassian Account Settings
WHY: I can draft and create all runbook content automatically

STEPS:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Label: "PagerDuty Demo Runbooks"
4. Copy the token

PROVIDE:
  - Atlassian Email: ______________
  - API Token: ______________
  
(I will use this to create all runbook pages automatically)
```

---

### PRIORITY 4: PAGERDUTY ADD-ONS CONFIRMATION

#### Action 4.1: Confirm Enabled Add-Ons
```
WHAT: Tell me which PagerDuty add-ons are enabled
WHERE: PagerDuty UI → Account Settings → Subscription
WHY: Determines which demo scenarios are available

CHECK AND RESPOND:
  [ ] Runbook Automation (RBA) - ENABLED / NOT ENABLED
  [ ] Event Intelligence (AIOps) - ENABLED / NOT ENABLED
  [ ] Status Pages - ENABLED / NOT ENABLED
  [ ] Jeli (PIR) - ENABLED / NOT ENABLED

AI AGENTS (if applicable):
  [ ] SRE Agent - ENABLED / NOT ENABLED
  [ ] Scribe Agent - ENABLED / NOT ENABLED
  [ ] Shift Agent - ENABLED / NOT ENABLED
```

---

### PRIORITY 5: ZOOM INTEGRATION (Optional - for Conference Bridges)

#### Action 5.1: Configure Zoom Integration
```
WHAT: Connect Zoom for automatic conference bridge creation
WHERE: PagerDuty UI → Integrations → Zoom
WHY: Major Incident workflow creates Zoom bridges

STEPS:
1. Go to https://[subdomain].pagerduty.com/integrations
2. Search for "Zoom"
3. Complete OAuth flow
```

---

### PRIORITY 6: STATUS PAGE SETUP (Optional - for Customer Communication)

#### Action 6.1: Create Status Page
```
WHAT: Create a PagerDuty Status Page
WHERE: PagerDuty UI → Status Pages
WHY: Major Incident workflow posts updates

STEPS:
1. Go to Status Pages in PagerDuty
2. Create new page (internal or public)
3. Add business services
```

---

### PRIORITY 7: MONITORING TOOL INTEGRATIONS (Optional - Enhances Realism)

For each monitoring tool you have access to, provide:

#### Datadog (if available)
```
PROVIDE:
  - Datadog API Key: ______________
  - Datadog APP Key: ______________
  - Datadog Site: (us1.datadoghq.com / eu.datadoghq.com / etc.)
```

#### Splunk (if available)
```
PROVIDE:
  - Splunk HEC URL: ______________
  - Splunk HEC Token: ______________
  - Splunk Index: ______________
```

#### New Relic (if available)
```
PROVIDE:
  - New Relic API Key: ______________
  - New Relic Account ID: ______________
```

#### Sentry (if available)
```
PROVIDE:
  - Sentry DSN: ______________
  - Sentry Auth Token: ______________
  - Sentry Org Slug: ______________
```

---

### PRIORITY 8: DEMO USER API TOKENS (Required for Realistic Attribution)

#### Action 8.1: Generate User API Tokens
```
WHAT: Each demo user needs their own API token
WHERE: PagerDuty UI → Each user's profile → API Access
WHY: Actions appear under correct user names

FOR EACH USER:
1. Log in as the user (or have admin access)
2. Go to User Settings → API Access
3. Create new API key
4. Label: "Demo Simulator"
5. Copy the key

USERS NEEDING TOKENS:
  - gtonic@losandesgaa.onmicrosoft.com (Ginny Tonic)
  - jbeam@losandesgaa.onmicrosoft.com (Jim Beam)
  - jdaniels@losandesgaa.onmicrosoft.com (Jack Daniels)
  - kmorgan@losandesgaa.onmicrosoft.com (Kaptin Morgan)
  - aguiness@losandesgaa.onmicrosoft.com (Arthur Guinness)
  - jmurphy@losandesgaa.onmicrosoft.com (Jameson)
  - jcuervo@losandesgaa.onmicrosoft.com (Jose Cuervo)
  - jcasker@losandesgaa.onmicrosoft.com (James Casker)
  - ubeatha@losandesgaa.onmicrosoft.com (Uisce Beatha)
  - plosty@losandesgaa.onmicrosoft.com (Paddy Losty)
```

---

## PART 4: WHAT I CAN DO AUTOMATICALLY

Once you provide the required information, I can:

### Immediate (No Additional Input Needed)
1. Update `terraform.tfvars` with Slack connection ID
2. Update `.env` file with all provided credentials
3. Update runbook URLs to point to Confluence pages
4. Run Terraform to deploy updated configurations

### With Confluence API Access
1. Create all runbook pages with realistic content
2. Create incident response templates
3. Create PIR templates
4. Create communication templates
5. Link all runbooks to PagerDuty services

### With Jira Projects Created
1. Test workflow ticket creation
2. Verify bidirectional sync configuration
3. Update project keys in incident workflows if needed

### With Monitoring Tool Credentials
1. Configure service integrations
2. Set up event routing rules
3. Test alert flow end-to-end

---

## PART 5: BIDIRECTIONAL JIRA SYNC

### Current State
- PagerDuty → Jira: PARTIALLY CONFIGURED (workflows create tickets)
- Jira → PagerDuty: NOT CONFIGURED

### For Full Bidirectional Sync

#### Option A: PagerDuty Jira Cloud Integration (Simpler)
```
WHERE: PagerDuty UI → Extensions → Jira Cloud
ENABLES:
  - Auto-sync incident status to Jira
  - Comments sync both ways
  - Priority mapping
  - Custom field mapping (Business tier+)
```

#### Option B: Jira Automation Rules (More Control)
```
WHERE: Jira → Project Settings → Automation
RULES TO CREATE:
  1. When issue transitions → Update PagerDuty incident
  2. When comment added → Add note to PagerDuty incident
  3. When priority changes → Update PagerDuty priority
```

---

## SUMMARY: MINIMUM VIABLE SETUP

To get the demo working with Jira/Confluence integration:

| Step | Priority | Effort | Blocker |
|------|----------|--------|---------|
| Confirm Slack connection ID | P1 | 2 min | YES - workflows fail without it |
| Confirm Jira integration | P1 | 2 min | YES - tickets won't create |
| Create 6 Jira projects | P2 | 30 min | YES - specific project keys required |
| Create Confluence space | P3 | 5 min | NO - runbook links just won't work |
| Provide Confluence API token | P3 | 2 min | NO - I can provide page content for manual creation |
| Confirm PD add-ons | P4 | 5 min | PARTIAL - affects available scenarios |
| User API tokens | P5 | 20 min | NO - simulator works with single admin token |

---

*Document generated by integration audit. Last updated: Current session.*
