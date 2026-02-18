# PagerDuty Demo Environment - Deployment Summary

**Date:** February 2, 2026  
**Deployed By:** Automated via Terraform and RBA API  
**Environment:** csmscale (PagerDuty + Runbook Automation)

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Analysis](#pre-deployment-analysis)
3. [Terraform Deployment](#terraform-deployment)
4. [RBA Jobs Deployment](#rba-jobs-deployment)
5. [Resources Created](#resources-created)
6. [Configuration Files](#configuration-files)
7. [Access URLs](#access-urls)
8. [Troubleshooting Notes](#troubleshooting-notes)

---

## Overview

This document details the complete deployment of a PagerDuty demo environment, including:
- **205+ PagerDuty resources** deployed via Terraform
- **8 RBA scheduled jobs** deployed to Runbook Automation
- **1 new RBA project** created (`pagerduty-demo`)

---

## Pre-Deployment Analysis

### Initial State Assessment

Before deployment, the following issues were identified and resolved:

#### 1. Terraform Validation Errors

Multiple validation errors were discovered and fixed:

| File | Issue | Resolution |
|------|-------|------------|
| `automation_actions.tf` | Invalid `action_classification` values | Changed `diagnostic` to `remediate` |
| `escalation_policies.tf` | Missing team references | Added data sources for existing teams |
| `event_orchestration.tf` | Invalid `event_action` value | Changed `trigger_only` to `trigger` |
| `incident_workflows.tf` | Invalid `condition_type` | Changed `not_matching` to `attribute` with negation |
| `maintenance_windows.tf` | Invalid time format | Changed to `2026-12-31T23:59:59Z` format |
| `maintenance_windows.tf` | Duplicate service references | Removed duplicate services from lists |
| `routing_rules.tf` | Invalid comparison type | Changed `datetime` to `scheduled` |
| `schedules.tf` | Invalid `rotation_turn_length_seconds` | Changed 0 to 86400 (1 day minimum) |
| `services.tf` | Undefined variables | Moved variable definitions inline |
| `users.tf` | Invalid `role` value | Changed `limited_user` to `user` |

#### 2. Provider Configuration

The PagerDuty Terraform provider was configured with:
- **API Token:** `u+sGJdsPDfEBnLfZ5VVB`
- **Provider Version:** `~> 3.18`

#### 3. Data Sources Added

Created `data_teams.tf` to reference existing teams:
- Platform Engineering
- Backend Engineering  
- Frontend Engineering
- DevOps
- SRE
- QA Engineering
- Infrastructure
- Security
- Database
- Mobile

---

## Terraform Deployment

### Command Executed

```bash
terraform apply -auto-approve
```

### Deployment Results

**Status:** SUCCESS  
**Duration:** ~3 minutes  
**Resources Created:** 205+

### Resource Summary

| Resource Type | Count | Description |
|--------------|-------|-------------|
| `pagerduty_user` | 10 | Demo users (Jim Beam, Jameson Casker, etc.) |
| `pagerduty_team` | 10 | Engineering teams |
| `pagerduty_team_membership` | 20+ | User-to-team assignments |
| `pagerduty_service` | 30+ | Demo services (API Gateway, Payment, etc.) |
| `pagerduty_schedule` | 10 | On-call rotation schedules |
| `pagerduty_escalation_policy` | 15+ | Multi-level escalation policies |
| `pagerduty_service_integration` | 50+ | Service integrations |
| `pagerduty_event_orchestration` | 5+ | Global event routing rules |
| `pagerduty_service_event_rule` | 20+ | Service-level event rules |
| `pagerduty_incident_workflow` | 5+ | Automated incident workflows |
| `pagerduty_incident_workflow_trigger` | 5+ | Workflow triggers |
| `pagerduty_automation_action` | 10+ | RBA automation actions |
| `pagerduty_automation_actions_runner` | 1 | RBA runner configuration |
| `pagerduty_maintenance_window` | 3 | Scheduled maintenance windows |
| `pagerduty_response_play` | 5+ | Incident response plays |
| `pagerduty_business_service` | 5+ | Business service definitions |
| `pagerduty_service_dependency` | 10+ | Service dependency mappings |

### Users Created

| Username | Full Name | Email | Role |
|----------|-----------|-------|------|
| jbeam | Jim Beam | jbeam@losandesgaa.onmicrosoft.com | user |
| jcasker | Jameson Casker | jcasker@losandesgaa.onmicrosoft.com | user |
| aguiness | Arthur Guinness | aguiness@losandesgaa.onmicrosoft.com | user |
| jcuervo | Jose Cuervo | jcuervo@losandesgaa.onmicrosoft.com | user |
| jmurphy | James Murphy | jmurphy@losandesgaa.onmicrosoft.com | user |
| plosty | Paddy Losty | plosty@losandesgaa.onmicrosoft.com | user |
| kmorgan | Kaptin Morgan | kmorgan@losandesgaa.onmicrosoft.com | user |
| ubeatha | Uisce Beatha | ubeatha@losandesgaa.onmicrosoft.com | user |
| jdaniels | Jack Daniels | jdaniels@losandesgaa.onmicrosoft.com | user |
| gtonic | Ginny Tonic | gtonic@losandesgaa.onmicrosoft.com | user |

### Services Created

Services are organized by team:

**Platform Engineering:**
- API Gateway
- Load Balancer
- Service Mesh
- API Rate Limiter

**Backend Engineering:**
- Payment Service
- Order Service
- Inventory Service
- User Service
- Notification Service

**Frontend Engineering:**
- Web Application
- Mobile BFF
- CDN Service

**DevOps:**
- CI/CD Pipeline
- Deployment Service
- Config Management

**SRE:**
- Monitoring Service
- Alerting Service
- Incident Management

**Infrastructure:**
- Kubernetes Cluster
- Database Cluster
- Redis Cache
- Message Queue

**Security:**
- Auth Service
- WAF Service
- Secrets Manager

---

## RBA Jobs Deployment

### RBA Instance Details

- **URL:** https://csmscale.runbook.pagerduty.cloud
- **API Token:** `77nx840mR78mHf9J6kfTARQkhqdme2xy`
- **API Version:** 57
- **Rundeck Version:** 5.20-RBA-20260128

### Project Created

- **Project Name:** `pagerduty-demo`
- **Description:** PagerDuty Demo Project - Background scheduled jobs for SLA and stale incident monitoring
- **Created:** 2026-02-02T03:39:25Z

### Jobs Imported

All 8 jobs were successfully imported via the RBA API:

| Job Name | Job ID | Schedule | Description |
|----------|--------|----------|-------------|
| Background Metric Generator | `844ce3c6-59da-4bd1-8f60-738204831527` | Every 5 minutes | Generates synthetic metrics for Datadog/New Relic |
| Background Log Generator | `9d0de82d-67d2-45a8-a2bb-29cbff6b59b0` | Every 10 minutes | Generates synthetic application logs |
| User Activity Simulator | `e3776202-07a4-4ebf-927a-c28dd0526bae` | Every 15 min (weekdays 9-17) | Simulates user actions on incidents |
| Incident Lifecycle Simulator | `fe604c4c-43ad-4fb5-ad5e-cc88aecbb363` | Every 30 minutes | Manages incident state transitions |
| Integration Health Check | `d84c9401-35d6-44e7-a564-4e906d5deac5` | Every 15 minutes | Validates integration connectivity |
| Demo Reset (Quick) | `5bcc46e2-2b2a-4262-97c6-6476233a6043` | Manual | Quick cleanup of demo data |
| Demo Reset (Full) | `48f0c0a1-e929-4270-a92d-20b07d1eb11c` | Manual | Full environment reset |
| Scheduled Event Generator | `b6c1f846-bc95-46ec-8123-a31b8d9c06de` | Every 2 hours | Creates scheduled demo events |

### Job Details

#### 1. Background Metric Generator
- **Schedule:** `0 0,5,10,15,20,25,30,35,40,45,50,55 * * * ?`
- **Purpose:** Populates monitoring dashboards with realistic metrics
- **Metrics Generated:**
  - CPU utilization (30-70%)
  - Memory usage (40-75%)
  - Request latency (50-200ms)
  - Error rate (0-3%)
  - Requests per second (100-600)
- **Services Monitored:** api-gateway, payment-service, order-service, inventory-service, auth-service, checkout-service
- **Integrations:** Datadog, New Relic (when API keys configured)

#### 2. Background Log Generator
- **Schedule:** `0 0,10,20,30,40,50 * * * ?`
- **Purpose:** Generates realistic application logs for log aggregation tools
- **Log Levels:** INFO (67%), WARN (17%), ERROR (16%)
- **Log Types:**
  - INFO: Health checks, cache refreshes, successful operations
  - WARN: Slow queries, connection pool warnings, retry attempts
  - ERROR: Timeouts, API failures, authentication errors

#### 3. User Activity Simulator
- **Schedule:** `0 0,15,30,45 9-17 ? * MON-FRI`
- **Purpose:** Simulates realistic user interactions with incidents
- **Actions:**
  - Acknowledge incidents
  - Add investigation notes
  - Reassign to team members
- **Users Simulated:** All 10 demo users with individual API tokens

#### 4. Incident Lifecycle Simulator
- **Schedule:** `0 0,30 * * * ?`
- **Purpose:** Manages incident state transitions for demo realism
- **Actions:**
  - Acknowledge triggered incidents (>15 min old)
  - Resolve acknowledged incidents (>30 min old)
  - Add resolution notes

#### 5. Integration Health Check
- **Schedule:** `0 0,15,30,45 * * * ?`
- **Purpose:** Validates all integration endpoints are responsive
- **Checks:**
  - PagerDuty API connectivity
  - Datadog API (when configured)
  - New Relic API (when configured)
  - Slack webhooks (when configured)

#### 6. Demo Reset (Quick)
- **Schedule:** Manual trigger only
- **Purpose:** Quick cleanup between demo sessions
- **Actions:**
  - Resolve all open incidents
  - Clear recent alerts
  - Reset notification counts

#### 7. Demo Reset (Full)
- **Schedule:** Manual trigger only
- **Purpose:** Complete environment reset
- **Actions:**
  - All Quick Reset actions
  - Clear all incident history
  - Reset all metrics
  - Regenerate sample data

#### 8. Scheduled Event Generator
- **Schedule:** `0 0 */2 * * ?` (every 2 hours)
- **Purpose:** Creates variety of demo events
- **Event Types:**
  - Critical alerts
  - Warning notifications
  - Info events
  - Scheduled maintenance reminders

---

## Resources Created

### File Structure

```
/Users/conalllynch/TFTest/
├── terraform.tfstate              # Terraform state file
├── terraform.tfstate.backup       # State backup
├── *.tf                           # Terraform configuration files
├── rundeck/
│   └── jobs/
│       ├── background-scheduled-jobs.yaml    # Original multi-doc YAML
│       └── combined-jobs.yaml                # Single-doc YAML (used for import)
└── DEPLOYMENT_SUMMARY.md          # This document
```

### Terraform Files Modified

| File | Changes Made |
|------|--------------|
| `automation_actions.tf` | Fixed action_classification values |
| `data_teams.tf` | Created new file with team data sources |
| `escalation_policies.tf` | Added team data source references |
| `event_orchestration.tf` | Fixed event_action value |
| `incident_workflows.tf` | Fixed condition_type syntax |
| `maintenance_windows.tf` | Fixed time format and duplicate services |
| `routing_rules.tf` | Fixed comparison type |
| `schedules.tf` | Fixed rotation_turn_length_seconds |
| `services.tf` | Moved variable definitions inline |
| `users.tf` | Fixed role value |

---

## Access URLs

### PagerDuty

**Subdomain:** `pdt-losandes`
**Base URL:** https://pdt-losandes.pagerduty.com

| Page | URL |
|------|-----|
| Services | https://pdt-losandes.pagerduty.com/service-directory |
| Teams | https://pdt-losandes.pagerduty.com/teams |
| Schedules | https://pdt-losandes.pagerduty.com/schedules |
| Escalation Policies | https://pdt-losandes.pagerduty.com/escalation_policies |
| Users | https://pdt-losandes.pagerduty.com/users |
| Event Orchestration | https://pdt-losandes.pagerduty.com/event-orchestration |
| Incidents | https://pdt-losandes.pagerduty.com/incidents |
| Analytics | https://pdt-losandes.pagerduty.com/analytics |
| Automation Actions | https://pdt-losandes.pagerduty.com/automation-actions |

### Runbook Automation (RBA)

- **RBA Console:** https://csmscale.runbook.pagerduty.cloud
- **Project Jobs:** https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/jobs
- **API Endpoint:** https://csmscale.runbook.pagerduty.cloud/api/57

### Individual Job URLs

| Job | URL |
|-----|-----|
| Background Metric Generator | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/844ce3c6-59da-4bd1-8f60-738204831527 |
| Background Log Generator | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/9d0de82d-67d2-45a8-a2bb-29cbff6b59b0 |
| User Activity Simulator | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/e3776202-07a4-4ebf-927a-c28dd0526bae |
| Incident Lifecycle Simulator | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/fe604c4c-43ad-4fb5-ad5e-cc88aecbb363 |
| Integration Health Check | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/d84c9401-35d6-44e7-a564-4e906d5deac5 |
| Demo Reset (Quick) | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/5bcc46e2-2b2a-4262-97c6-6476233a6043 |
| Demo Reset (Full) | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/48f0c0a1-e929-4270-a92d-20b07d1eb11c |
| Scheduled Event Generator | https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/job/show/b6c1f846-bc95-46ec-8123-a31b8d9c06de |

---

## Troubleshooting Notes

### Issue 1: RBA URL Discovery

**Problem:** Initially attempted to connect to `csmscale.runbook.pagerduty.com`  
**Solution:** Correct domain is `csmscale.runbook.pagerduty.cloud` (note: `.cloud` not `.com`)

### Issue 2: YAML Multi-Document Format

**Problem:** RBA API rejected the jobs YAML with error:
```
expected a single document in the stream but found another document
```

**Solution:** Combined all job definitions into a single YAML document by removing `---` separators:
```bash
sed 's/^---$//' background-scheduled-jobs.yaml > combined-jobs.yaml
```

### Issue 3: Terraform Validation Errors

**Problem:** Multiple validation errors on first `terraform validate`  
**Solution:** Systematic review and correction of all `.tf` files as documented above

### Issue 4: Missing Team Data Sources

**Problem:** Escalation policies referenced teams that weren't defined as data sources  
**Solution:** Created `data_teams.tf` with `pagerduty_team` data sources for all existing teams

---

## API Commands Used

### Terraform Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan

# Apply deployment
terraform apply -auto-approve
```

### RBA API Commands

```bash
# Test API connectivity
curl -s "https://csmscale.runbook.pagerduty.cloud/api/44/system/info" \
  -H "X-Rundeck-Auth-Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy" \
  -H "Accept: application/json"

# List existing projects
curl -s "https://csmscale.runbook.pagerduty.cloud/api/44/projects" \
  -H "X-Rundeck-Auth-Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy" \
  -H "Accept: application/json"

# Create project
curl -s -X POST "https://csmscale.runbook.pagerduty.cloud/api/44/projects" \
  -H "X-Rundeck-Auth-Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"name":"pagerduty-demo","description":"..."}'

# Import jobs
curl -s -X POST "https://csmscale.runbook.pagerduty.cloud/api/44/project/pagerduty-demo/jobs/import?fileformat=yaml&dupeOption=update" \
  -H "X-Rundeck-Auth-Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy" \
  -H "Content-Type: application/yaml" \
  -H "Accept: application/json" \
  --data-binary @rundeck/jobs/combined-jobs.yaml

# List jobs in project
curl -s "https://csmscale.runbook.pagerduty.cloud/api/44/project/pagerduty-demo/jobs" \
  -H "X-Rundeck-Auth-Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy" \
  -H "Accept: application/json"
```

---

## AWS Lambda Orchestrator Deployment

**Date Deployed:** February 7, 2026
**Region:** eu-west-1

### Components Deployed

| Component | Name | Status |
|-----------|------|--------|
| Lambda Function | `demo-orchestrator` | ✅ Deployed |
| Lambda Function URL | `https://...lambda-url.eu-west-1.on.aws/` | ✅ Configured |
| DynamoDB Table | `demo-incident-state` | ✅ Created |
| EventBridge Scheduler | For scheduled actions | ✅ Configured |
| IAM Roles | Lambda execution, Scheduler | ✅ Created |

### Deployment Commands

```bash
cd aws

# Build Lambda package
zip -r lambda-demo-orchestrator.zip lambda-demo-orchestrator/

# Deploy via Terraform
terraform init
terraform plan
terraform apply -auto-approve
```

### Environment Variables Configured

| Variable | Description |
|----------|-------------|
| `PAGERDUTY_TOKEN` | API token for PagerDuty operations |
| `SLACK_BOT_TOKEN` | Slack bot token for channel operations |
| `DEMO_STATE_TABLE` | DynamoDB table name (`demo-incident-state`) |
| `SELF_LAMBDA_ARN` | Lambda function ARN for self-invocation |
| `SCHEDULER_ROLE_ARN` | IAM role for EventBridge Scheduler |
| `WEBHOOK_SECRET` | PagerDuty webhook signing secret |

### PagerDuty Webhook Configuration

| Setting | Value |
|---------|-------|
| Webhook URL | Lambda Function URL |
| Events Subscribed | `incident.triggered`, `incident.acknowledged`, `incident.resolved`, `incident.workflow.completed`, etc. |
| Signing Secret | Configured in Lambda env vars |

---

## PagerDuty Workflow Deployment (API-Created)

The "Demo Incident Channel Setup" workflow was created via PagerDuty REST API (not Terraform) because:
1. Terraform provider cannot create workflow steps
2. This workflow requires specific action configurations (Slack, Conference Bridge)

### Workflow Details

| Property | Value |
|----------|-------|
| Workflow ID | `PUXIPNC` |
| Workflow Name | Demo Incident Channel Setup |
| Team | PagerDuty Internal |

### Workflow Steps

1. **Create Incident Slack Channel**
   - Action ID: `pagerduty.com:slack:create-a-channel:4`
   - Channel Name: `demo-{{incident.number}}-{{incident.title}}`
   - Visibility: Public
   - Workspace: `T0A9LN53CPQ`
   - Output: Channel Link

2. **Add Conference Bridge**
   - Action ID: `pagerduty.com:incident-workflows:add-conference-bridge:1`
   - Conference URL: `{{steps.Create Incident Slack Channel.Channel Link}}`

### Trigger Configuration

| Property | Value |
|----------|-------|
| Trigger ID | `7c33cc98-3c3a-4da2-9f6f-2211a706ca29` |
| Type | Conditional |
| Condition | `incident.title matches part '[DEMO]'` |
| Fires On | Incident creation (triggered) |

### API Commands Used

```bash
# Create workflow
curl -X POST "https://api.pagerduty.com/incident_workflows" \
  -H "Authorization: Token token=$PD_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow": {...}}'

# Create trigger
curl -X POST "https://api.pagerduty.com/incident_workflows/PUXIPNC/triggers" \
  -H "Authorization: Token token=$PD_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"trigger": {"type": "conditional", "condition": {...}}}'
```

### Important Note: API Token Requirements

Creating workflows via API requires an **API User Token** (not a General API Key).
Even with admin scope, an API Key may return `403 User not permitted to create workflow`.

See `docs/GOTCHAS_AND_WORKAROUNDS.md` for full details.

---

## Next Steps

### Completed (as of 2026-02-07)
- [x] Configure Lambda environment variables
- [x] Set up PagerDuty webhooks pointing to Lambda
- [x] Create "Demo Incident Channel Setup" workflow via API
- [x] Configure conditional trigger for `[DEMO]` incidents

### Remaining Tasks

1. **Test End-to-End [DEMO] Incident Flow**
   - Create incident with `[DEMO]` in title
   - Verify workflow triggers and creates Slack channel
   - Verify Lambda receives `incident.workflow.completed` webhook
   - Verify Lambda invites users to channel

2. **Create Jira Projects** for workflow ticket creation:
   - SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA

3. **Configure Monitoring Credentials** (optional):
   - `DATADOG_API_KEY` - For metric submission
   - `DATADOG_SITE` - Datadog region (default: us5.datadoghq.com)
   - `NEW_RELIC_LICENSE_KEY` - For New Relic integration

4. **Run Populate Workflow Steps** for other Terraform-created workflows:
   ```bash
   python scripts/populate_workflow_steps.py
   ```

5. **Enable/Disable RBA Schedules** as needed via RBA UI or API

6. **Monitor Job Executions** via RBA Activity page:
   https://csmscale.runbook.pagerduty.cloud/project/pagerduty-demo/activity

---

## Related Documentation

- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Detailed change log
- [docs/DEVELOPER_HANDOVER.md](docs/DEVELOPER_HANDOVER.md) - Developer handover guide
- [docs/ARCHITECTURE_BLUEPRINT.md](docs/ARCHITECTURE_BLUEPRINT.md) - System architecture
- [docs/GOTCHAS_AND_WORKAROUNDS.md](docs/GOTCHAS_AND_WORKAROUNDS.md) - Known issues and solutions
- [docs/CREDENTIALS_REFERENCE.md](docs/CREDENTIALS_REFERENCE.md) - API keys and tokens

---

## Document Information

- **Created:** 2026-02-02
- **Last Updated:** 2026-02-07
- **Version:** 1.1
- **Authors:** Automated Deployment System, Development Team
