# Los Andes - Comprehensive Incident Workflow & Runbook Automation Plan

## Overview

This plan establishes a mature incident management automation framework combining:
- **PagerDuty Incident Workflows** - Multi-step orchestration triggered by incidents
- **PagerDuty Runbook Automation (RBA)** - Diagnostic/remediation job execution
- **Slack Integration** - Communication channel automation
- **Event Orchestration** - Automated response to specific event patterns

---

## Part 1: Runbook Automation Integration

### 1.1 RBA Environment Details
```
Instance URL: https://csmscale.runbook.pagerduty.cloud
API Token: 77nx840mR78mHf9J6kfTARQkhqdme2xy
```

### 1.2 Runner Setup Plan

**Step 1: Create RBA Runner in PagerDuty**
1. Navigate to: `Automation → Automation Actions → Runners → Add Runner`
2. Select: **Runbook Automation** type
3. Configure:
   - Name: `Los-Andes-RBA-Runner`
   - Description: `Primary runner linking PD to RBA SaaS for diagnostic and remediation jobs`
   - Subdomain: `csmscale`
   - API Token: `77nx840mR78mHf9J6kfTARQkhqdme2xy`
4. Verify green checkmark (active status)

### 1.3 RBA Project Structure

```
📁 RBA Projects
├── 📁 Los-Andes-Diagnostics
│   ├── 🔧 job: health-check-all-services
│   ├── 🔧 job: database-connection-test
│   ├── 🔧 job: api-endpoint-validator
│   ├── 🔧 job: log-aggregator
│   └── 🔧 job: resource-utilization-check
│
├── 📁 Los-Andes-Remediation
│   ├── 🔧 job: restart-service
│   ├── 🔧 job: clear-cache
│   ├── 🔧 job: scale-deployment
│   ├── 🔧 job: rollback-deployment
│   └── 🔧 job: failover-database
│
├── 📁 Los-Andes-Security
│   ├── 🔧 job: security-scan
│   ├── 🔧 job: block-suspicious-ip
│   ├── 🔧 job: rotate-credentials
│   └── 🔧 job: audit-log-export
│
└── 📁 Los-Andes-Payments
    ├── 🔧 job: payment-gateway-health
    ├── 🔧 job: transaction-queue-status
    └── 🔧 job: failover-to-backup-provider
```

### 1.4 Sample RBA Job Definitions

#### Job: health-check-all-services
```yaml
name: Health Check All Services
description: Comprehensive health check across all critical services
uuid: health-check-all-services
options:
  - name: pd_incident_id
    description: PagerDuty Incident ID
    required: true
  - name: service_name
    description: Specific service to check (optional)
    required: false
sequence:
  - step: Check API Gateway
    script: |
      curl -s -o /dev/null -w "%{http_code}" https://api.losandes.com/health
  - step: Check Database Connectivity
    script: |
      psql -h db.losandes.com -U monitor -c "SELECT 1" 2>&1 || echo "DB_UNREACHABLE"
  - step: Check Redis Cache
    script: |
      redis-cli -h cache.losandes.com PING 2>&1
  - step: Check Kubernetes Pods
    script: |
      kubectl get pods --all-namespaces --field-selector=status.phase!=Running -o name | wc -l
  - step: Send Results to PD Incident
    plugins:
      - type: pd-incident-output
        config:
          incident_id: ${option.pd_incident_id}
```

#### Job: restart-service
```yaml
name: Restart Service
description: Gracefully restart a specific service with health verification
options:
  - name: pd_incident_id
    required: true
  - name: service_name
    required: true
    values: [web-frontend, api-gateway, payment-service, auth-service]
  - name: wait_healthy
    default: "true"
sequence:
  - step: Pre-restart Health Check
    script: |
      kubectl get deployment ${option.service_name} -o jsonpath='{.status.readyReplicas}'
  - step: Rolling Restart
    script: |
      kubectl rollout restart deployment/${option.service_name}
  - step: Wait for Rollout
    script: |
      kubectl rollout status deployment/${option.service_name} --timeout=300s
  - step: Post-restart Verification
    script: |
      sleep 30
      kubectl get deployment ${option.service_name} -o jsonpath='{.status.readyReplicas}'
```

---

## Part 2: Complex Multi-Step Incident Workflows

### 2.1 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INCIDENT WORKFLOWS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   TRIGGER    │───▶│   ACTIONS    │───▶│   OUTCOMES   │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                      │
│  Triggers:           Actions:             Outcomes:                  │
│  • Priority P1/P2    • Add Notes          • Faster MTTR              │
│  • Incident Type     • Add Responders     • Automated Diagnostics    │
│  • Service Match     • Create Slack       • Consistent Response      │
│  • Manual Invoke     • Run RBA Jobs       • Audit Trail              │
│  • Urgency Change    • Update Status      • Knowledge Capture        │
│                      • Conference Bridge                             │
│                      • Jira Ticket                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Workflow Definitions

---

#### WORKFLOW 1: Major Incident Full Mobilization
**Trigger:** Priority = P1 OR P2, Service = Any Customer-Facing
**Purpose:** Complete incident command structure setup with diagnostics

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Internal Note | "🚨 MAJOR INCIDENT AUTO-MOBILIZATION INITIATED" |
| 2 | Set Incident Type | "Major Incident" |
| 3 | Create Slack Channel | `inc-{{incident.incident_number}}-{{service.name_slug}}` (Public, Pinned) |
| 4 | Add Responders | Customer-Facing EP + Platform Core EP + On-Call Manager |
| 5 | Post to Slack | Incident summary with key details and runbook links |
| 6 | Run RBA: Health Check | Execute `health-check-all-services` job |
| 7 | Create Zoom Bridge | Auto-provision war room conference |
| 8 | Update Status Page | Draft status update for review |
| 9 | Add Note | Log all automated actions taken |

---

#### WORKFLOW 2: Security Incident Response (CONFIDENTIAL)
**Trigger:** Incident Type = "Security", Priority = Any
**Purpose:** Locked-down response with private communications

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Internal Note | "🔒 SECURITY INCIDENT - CONFIDENTIAL HANDLING" |
| 2 | Create Private Slack | `secinc-{{incident.incident_number}}` (Private, Pinned) |
| 3 | Add Responders | Security Monitoring (SOC) EP only |
| 4 | Run RBA: Security Scan | Execute initial security assessment |
| 5 | Run RBA: Audit Log Export | Capture relevant logs for forensics |
| 6 | Add Note | Document chain of custody initiated |
| 7 | Post to Private Slack | Security playbook checklist |

---

#### WORKFLOW 3: Platform Infrastructure Degradation
**Trigger:** Service matches "Platform-*", Urgency = High
**Purpose:** Infrastructure-focused response with auto-diagnostics

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "⚠️ Platform degradation detected - initiating diagnostics" |
| 2 | Create Slack Channel | `platform-{{incident.incident_number}}` (Public) |
| 3 | Run RBA: Resource Check | Execute `resource-utilization-check` |
| 4 | Run RBA: DB Connection | Execute `database-connection-test` |
| 5 | Add Responders | Platform Core EP + DBRE EP |
| 6 | Post to Slack | Diagnostic results summary |
| 7 | Conditional: High Memory | If memory > 90%, run `clear-cache` job |

---

#### WORKFLOW 4: Payments System Outage
**Trigger:** Service contains "Payment", Priority = P1/P2
**Purpose:** Financial impact mitigation with failover readiness

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "💳 PAYMENTS IMPACT - Initiating financial incident protocol" |
| 2 | Create Slack Channel | `payments-{{incident.incident_number}}` (Public, Pinned) |
| 3 | Add Responders | Business Ops EP + Platform Core EP |
| 4 | Run RBA: Gateway Health | Execute `payment-gateway-health` |
| 5 | Run RBA: Queue Status | Execute `transaction-queue-status` |
| 6 | Post to Slack | Payment system status + failover options |
| 7 | Add Note | Document transaction queue depth |
| 8 | Prepare Failover | Stage `failover-to-backup-provider` (manual trigger) |

---

#### WORKFLOW 5: Customer Impact Communication
**Trigger:** Manual invoke OR Incident has "customer-impact" tag
**Purpose:** Structured external communication workflow

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "📢 Customer communication workflow initiated" |
| 2 | Add Responders | Customer Success EP |
| 3 | Post to Slack | Communication draft template |
| 4 | Create Jira Ticket | Customer communication tracking ticket |
| 5 | Update Status Page | Draft update for approval |
| 6 | Add Note | Log stakeholder notification checklist |

---

#### WORKFLOW 6: Incident Commander Handoff
**Trigger:** Manual invoke
**Purpose:** Structured IC role transition

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "🔄 Incident Commander handoff initiated" |
| 2 | Post to Slack | Current status summary for incoming IC |
| 3 | Post to Slack | Action items pending |
| 4 | Post to Slack | Key decisions made |
| 5 | Add Note | Document handoff completion |

---

#### WORKFLOW 7: Incident Closeout & PIR Scheduling
**Trigger:** Incident resolved AND was Priority P1/P2
**Purpose:** Structured closeout with PIR tracking

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "✅ Incident resolved - initiating closeout protocol" |
| 2 | Post to Slack | Resolution summary + timeline |
| 3 | Post to Slack | "Please document: Root cause, Timeline, Action items" |
| 4 | Create Jira Ticket | PIR tracking ticket with due date |
| 5 | Update Status Page | Final resolution update |
| 6 | Add Note | Archive channel reminder (24h) |

---

#### WORKFLOW 8: Automated Remediation - Service Restart
**Trigger:** Event Orchestration rule match (specific alert patterns)
**Purpose:** Auto-healing for known recoverable conditions

| Step | Action | Details |
|------|--------|---------|
| 1 | Add Note | "🔧 Automated remediation triggered" |
| 2 | Run RBA: Health Check | Verify service state |
| 3 | Run RBA: Restart Service | Execute `restart-service` with service from alert |
| 4 | Add Note | Log remediation attempt |
| 5 | Conditional: Still Failing | Escalate to human responder |

---

## Part 3: RBA Jobs to Build

### 3.1 Diagnostic Jobs

| Job Name | Project | Description | Inputs |
|----------|---------|-------------|--------|
| `health-check-all-services` | Diagnostics | Multi-service health sweep | pd_incident_id |
| `database-connection-test` | Diagnostics | Test DB connectivity + query performance | pd_incident_id, db_name |
| `api-endpoint-validator` | Diagnostics | Validate API endpoints respond correctly | pd_incident_id, endpoints[] |
| `log-aggregator` | Diagnostics | Collect last N minutes of logs | pd_incident_id, minutes, service |
| `resource-utilization-check` | Diagnostics | CPU/Memory/Disk across nodes | pd_incident_id, namespace |
| `kubernetes-pod-status` | Diagnostics | Check pod health in cluster | pd_incident_id, namespace |
| `network-latency-check` | Diagnostics | Test network paths between services | pd_incident_id |

### 3.2 Remediation Jobs

| Job Name | Project | Description | Inputs |
|----------|---------|-------------|--------|
| `restart-service` | Remediation | Rolling restart with verification | pd_incident_id, service_name |
| `clear-cache` | Remediation | Flush Redis/Memcached cache | pd_incident_id, cache_type |
| `scale-deployment` | Remediation | Scale K8s deployment up/down | pd_incident_id, deployment, replicas |
| `rollback-deployment` | Remediation | Rollback to previous version | pd_incident_id, deployment |
| `failover-database` | Remediation | Promote replica to primary | pd_incident_id, db_cluster |
| `drain-node` | Remediation | Drain K8s node for maintenance | pd_incident_id, node_name |

### 3.3 Security Jobs

| Job Name | Project | Description | Inputs |
|----------|---------|-------------|--------|
| `security-scan` | Security | Run vulnerability scan | pd_incident_id, target |
| `block-suspicious-ip` | Security | Add IP to firewall blocklist | pd_incident_id, ip_address |
| `rotate-credentials` | Security | Rotate service credentials | pd_incident_id, service |
| `audit-log-export` | Security | Export audit logs for timeframe | pd_incident_id, start_time, end_time |

### 3.4 Payments Jobs

| Job Name | Project | Description | Inputs |
|----------|---------|-------------|--------|
| `payment-gateway-health` | Payments | Check all payment providers | pd_incident_id |
| `transaction-queue-status` | Payments | Check pending transaction queues | pd_incident_id |
| `failover-to-backup-provider` | Payments | Switch to backup payment provider | pd_incident_id, target_provider |

---

## Part 4: Implementation Steps

### Phase 1: RBA Setup (Week 1)
1. ✅ Obtain RBA API token (complete)
2. ⬜ Create Runner in PagerDuty linking to `csmscale.runbook.pagerduty.cloud`
3. ⬜ Create RBA Projects structure
4. ⬜ Build initial diagnostic jobs
5. ⬜ Create Automation Actions linking jobs to PD services

### Phase 2: Workflow Creation (Week 2)
1. ⬜ Delete existing simple workflows
2. ⬜ Create complex multi-step workflows via API
3. ⬜ Configure workflow triggers
4. ⬜ Test workflow execution on test incidents

### Phase 3: Event Orchestration Integration (Week 3)
1. ⬜ Create Event Orchestration rules for auto-remediation
2. ⬜ Link Automation Actions to orchestration
3. ⬜ Configure conditional logic paths

### Phase 4: Testing & Refinement (Week 4)
1. ⬜ End-to-end testing of all workflows
2. ⬜ Validate RBA job outputs appear in PD
3. ⬜ Tune triggers and thresholds
4. ⬜ Document runbooks and playbooks

---

## Part 5: Context Variables Reference

Use these in RBA jobs to access incident data:

```
${incident.id}                          - Incident ID
${incident.first_alert_id}              - First alert ID
${pd.alert.client}                      - Alert source
${pd.alert.creation_time}               - Alert timestamp
${pd.alert.dedup_key}                   - Deduplication key
${pd.alert.description}                 - Alert description
${pd.alert.severity}                    - Alert severity
${pd.alert.source_component}            - Source component
${pd.alert.details.custom_field}        - Custom alert fields
${pd.incident.custom_fields.field_name} - Incident custom fields
${user.id}                              - User who invoked action
```

---

## Part 6: Terraform Resources

```hcl
# Automation Actions Runner
resource "pagerduty_automation_actions_runner" "rba_runner" {
  name           = "Los-Andes-RBA-Runner"
  description    = "Primary RBA SaaS runner"
  runner_type    = "runbook"
  runbook_base_uri = "https://csmscale.runbook.pagerduty.cloud"
  runbook_api_key  = var.rba_api_token
}

# Automation Action
resource "pagerduty_automation_actions_action" "health_check" {
  name        = "Health Check All Services"
  description = "Comprehensive service health diagnostic"
  action_type = "process_automation"
  runner_id   = pagerduty_automation_actions_runner.rba_runner.id
  
  action_data_reference {
    process_automation_job_id = "health-check-all-services"
    process_automation_job_arguments = "-pd_incident_id ${pagerduty.incidentId}"
  }
  
  action_classification = "diagnostic"
}

# Associate with services
resource "pagerduty_automation_actions_action_service_association" "health_check_services" {
  action_id  = pagerduty_automation_actions_action.health_check.id
  service_id = pagerduty_service.platform_api.id
}
```

---

## Summary

This plan establishes a mature incident automation framework that:

1. **Reduces MTTR** through automated diagnostics and prepared remediation
2. **Ensures Consistency** via standardized response workflows
3. **Enables Self-Healing** with Event Orchestration + RBA integration
4. **Improves Communication** with automated Slack channels and status updates
5. **Maintains Audit Trail** through comprehensive logging and notes
6. **Scales Response** by automating repetitive tasks

The integration between PagerDuty Incident Workflows, Automation Actions, and Runbook Automation creates a powerful automation layer that reduces toil and improves incident response quality.

---

## IMPORTANT: Workflow Creation Process

**As of January 2026**, due to a known issue with the PagerDuty Terraform provider (404 errors when creating new incident workflows), workflows must be created via the **PagerDuty API** rather than Terraform.

### Steps to Create New Workflows:

1. **Create workflow with steps via API (RECOMMENDED):**
```bash
curl -X POST "https://api.pagerduty.com/incident_workflows" \
  -H "Authorization: Token token=${PAGERDUTY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_workflow": {
      "name": "Workflow Name",
      "description": "Description",
      "team": {"id": "TEAM_ID", "type": "team_reference"},
      "steps": [
        {
          "name": "Step Name",
          "configuration": {
            "action_id": "pagerduty.add-incident-note",
            "inputs": [{"name": "note", "value": "Your note text"}]
          }
        }
      ]
    }
  }'
```

2. **Or add steps via PagerDuty UI:**
   - Navigate to: Automation -> Incident Workflows
   - Edit the workflow and add steps using the visual builder
   - Available actions: Slack channel creation, message posting, add responders, run automation actions, etc.

3. **Import into Terraform (optional):**
```bash
terraform import pagerduty_incident_workflow.<name> <workflow_id>
```

**Automation Script:** `scripts/data-generators/build_workflows_via_api.py`

See `DEVELOPER_GUIDE.md` for the full workflow inventory and action reference.
