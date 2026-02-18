# PagerDuty Demo Environment - Changelog

All notable changes to this project will be documented in this file.
Format: [YYYY-MM-DD] [Category] Description

## Legend
- **[ADDED]** New features or components
- **[CHANGED]** Changes to existing functionality
- **[FIXED]** Bug fixes
- **[REMOVED]** Removed features
- **[DEPRECATED]** Soon-to-be removed features
- **[SECURITY]** Security improvements
- **[DOCS]** Documentation changes
- **[INFRA]** Infrastructure changes

---

## [2026-02-07] PagerDuty Workflow Integration & Slack Channel Automation

### [ADDED]
- **PagerDuty Workflow "Demo Incident Channel Setup"** (ID: `PUXIPNC`)
  - Automatically creates Slack channels for `[DEMO]` incidents
  - Step 1: Create Incident Slack Channel (name: `demo-{number}-{title}`, public)
  - Step 2: Add Conference Bridge (stores channel link in incident's conference URL)
  - Conditional trigger fires on incident creation when title contains `[DEMO]`
  - Trigger ID: `7c33cc98-3c3a-4da2-9f6f-2211a706ca29`

- **Conference Bridge Approach for Slack Channel URL Passthrough**
  - PagerDuty workflow sets `conference_bridge.url` to Slack channel link
  - Lambda reads channel URL from incident on `incident.workflow.completed` event
  - Extracts channel ID from URL format: `https://app.slack.com/client/{workspace}/{channel_id}`
  - No direct Slack channel creation from Lambda (avoids `channels:write` scope requirement)

- New webhook event handler: `incident.workflow.completed`
  - Extracts Slack channel URL from incident conference bridge
  - Invites demo users to channel using existing Slack bot token
  - Posts welcome message to channel

### [FIXED]
- **Webhook Event Type Mismatch**: Changed `workflow.completed` to `incident.workflow.completed`
  - PagerDuty sends full event types with `incident.` prefix for workflow completion
  - Lambda now correctly maps and processes these events

- **Workflow Event Title Extraction**: Fixed incident data parsing for workflow events
  - Workflow completion events have different payload structure than other incident events
  - Title/ID now correctly extracted from nested `incident` object in workflow result

- **PagerDuty Signature Verification**: Resolved HMAC signature mismatches
  - Used correct webhook signing secret from Generic Webhook subscription
  - Fixed raw body handling for signature computation

### [CHANGED]
- Removed direct Slack channel creation attempt from `on_incident_acknowledged`
  - Slack bot token lacks `channels:write` scope
  - Channel creation now delegated to PagerDuty workflow (native Slack integration)

- Lambda environment variables added:
  - `SELF_LAMBDA_ARN`: Required for EventBridge Scheduler self-invocation
  - `SCHEDULER_ROLE_ARN`: IAM role ARN for EventBridge Scheduler

### [INFRA]
- PagerDuty workflow created via REST API (not Terraform-managed)
  - Terraform provider cannot create workflow steps
  - Workflow and trigger managed directly in PagerDuty
  - See `docs/GOTCHAS_AND_WORKAROUNDS.md` for details

---

## [2026-02-06] Major Lambda Handler Enhancement

### [ADDED]
- Comprehensive PagerDuty API client stubs (~50+ methods)
  - Services: list, get, create, update, delete
  - Users: list, get, get_on_call
  - Teams: list, get
  - Schedules: list, get, get_oncalls
  - Escalation Policies: list, get, get_current_oncall
  - Incidents: snooze, merge, reassign, escalate
  - Response Plays: list, run
  - Incident Workflows: list, trigger
  - Business Services: list, get, update_impact
  - Maintenance Windows: list, create
  - Alerts: get_incident_alerts, update_alert
  - Timeline/Log Entries: get_incident_timeline
  - Tags: list, add_to_entity
  - Custom Fields: list, update_incident_custom_fields
  - Automation Actions: list, invoke
  - Analytics: get_incident_metrics
  - Events API v2: send_event, create_change_event

- Comprehensive webhook event handlers
  - `incident.escalated` - Handles escalation with ack retry logic
  - `incident.unacknowledged` - Handles ack timeout, reschedules ack
  - `incident.delegated` - Handles delegation/reassignment
  - `incident.reassigned` - Aliases to delegated handler
  - `incident.reopened` - Resets state and schedules new ack
  - `incident.responder.replied` - Tracks responder replies
  - `incident.priority_updated` - Stores priority changes
  - `incident.urgency_updated` - Stores urgency changes
  - `service.created/updated/deleted` - Service lifecycle logging

- Feature flags configuration for selective feature enabling
- Demo configuration with tunable parameters
- Force acknowledge action for escalation timeout scenarios

### [DOCS]
- Created `HOSTING_EVALUATION.md` - Oracle Cloud Free Tier vs AWS comparison
  - Cost analysis ($0 vs ~$5-20/month)
  - Architecture diagrams for both options
  - Step-by-step Oracle deployment guide
  - Hybrid approach recommendation
  - Quick decision guide

- Created project documentation suite:
  - `CHANGELOG.md` - This running changelog
  - `DEVELOPER_HANDOVER.md` - Complete developer handover documentation
  - `ARCHITECTURE_BLUEPRINT.md` - Architecture with component status tracking
  - `PROJECT_DESCRIPTION.md` - Detailed project context and nuance

### [CHANGED]
- Improved incident acknowledgment guarantee logic
  - Tracks ack attempts per incident
  - Handles escalation events with configurable retry delays (15-45s)
  - Forces acknowledgment after max attempts (default: 3)
  - Checks incident status before attempting ack to avoid errors

### [INFRA]
- Lambda handler expanded from ~1000 to ~1800 lines
- All PagerDuty capabilities now have placeholder implementations
- Ready for future feature expansion without architectural changes

---

## [2026-02-05] Terraform Foundation (Pre-existing)

### [ADDED]
- 205+ PagerDuty resources deployed via Terraform
  - 31 services across multiple domains
  - 6 teams (data sources)
  - 8 schedules with realistic coverage patterns
  - 22 escalation policies
  - 22 incident workflows (empty shells - steps pending)
  - Global event orchestration with routing rules
  - Service-level event orchestrations
  - 20+ automation actions for diagnostics/remediation
  - 2 RBA runners
  - Maintenance windows
  - Business services with dependencies

### [INFRA]
- 8 RBA scheduled jobs deployed
  - Metrics Simulator
  - Log Generator
  - User Activity Simulator
  - Incident Lifecycle Simulator
  - Health Check Monitor
  - Database Metrics Collector
  - API Performance Monitor
  - Security Event Generator

---

## Pending Changes Queue

### Completed (as of 2026-02-07)
| ID | Description | Status | Completion Date |
|----|-------------|--------|-----------------|
| P2 | Deploy AWS Lambda Demo Orchestrator | **DONE** | 2026-02-07 |
| M1 | Deploy incident workflow triggers | **DONE** | 2026-02-07 |

### High Priority
| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| P1 | Populate remaining incident workflow steps via API script | IN PROGRESS | "Demo Incident Channel Setup" created via API |
| P3 | Create Jira projects (SECOPS, COMPLIANCE, INFRA, PIR, PAYMENTS, DATA) | PENDING | Required for workflow ticket creation |
| T1 | Full end-to-end [DEMO] incident test | PENDING | Channel creation → Lambda processing → User invite |

### Medium Priority
| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| M2 | Configure Confluence RUNBOOKS space | PENDING | - |
| M3 | Verify Slack integration end-to-end | IN PROGRESS | Channel creation works, needs full test |

### Low Priority
| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| L1 | Configure Datadog credentials | PENDING | - |
| L2 | Create demo event generator scripts | PENDING | - |
| L3 | Set up Status Page integration | PENDING | - |

---

## Migration Notes

### Terraform Provider Workaround
The PagerDuty Terraform provider cannot create incident workflows with steps.
**Solution**: Two-phase deployment
1. Terraform creates empty workflow shells
2. `scripts/populate_workflow_steps.py` adds steps via PagerDuty REST API
3. **Alternative**: Create workflows with steps directly via API (e.g., "Demo Incident Channel Setup" workflow)

### State Management
- Terraform state stored locally in `terraform.tfstate`
- Multiple backup files exist (terraform.tfstate.*.backup)
- Consider migrating to remote state (S3 + DynamoDB) for production

---

## Rollback Procedures

### Terraform Resources
```bash
terraform destroy -target=<resource_type>.<resource_name>
terraform apply
```

### Workflow Steps (API-managed)
```bash
# Reset workflow to empty state
python scripts/reset_workflow_steps.py --workflow-id=<id>
# Re-populate with correct steps
python scripts/populate_workflow_steps.py --workflow=<name>
```

### Lambda Orchestrator
```bash
# Redeploy previous version
aws lambda update-function-code --function-name demo-orchestrator --s3-bucket <bucket> --s3-key <previous-version.zip>
```
