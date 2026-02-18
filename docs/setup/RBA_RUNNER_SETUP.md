# PagerDuty Runbook Automation (RBA) Runner Setup Guide

## Overview

This document describes the setup of a PagerDuty Runbook Automation (RBA) runner on AWS EC2, including the issues encountered, troubleshooting steps taken, and the working solution.

## Table of Contents

1. [Background](#background)
2. [The Problem](#the-problem)
3. [What Was Tried](#what-was-tried)
4. [The Working Solution](#the-working-solution)
5. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
6. [Resources and References](#resources-and-references)
7. [Architecture Diagram](#architecture-diagram)

---

## Background

### What is an RBA Runner?

A PagerDuty Runbook Automation (RBA) Runner is an agent that executes automation jobs within your infrastructure. It:
- Polls the PagerDuty RBA cloud for pending operations
- Executes scripts, commands, and workflows on target systems
- Reports results back to PagerDuty
- Enables secure execution without exposing internal systems to the internet

### Why Do We Need a Runner?

Runners allow PagerDuty automation to execute commands within private networks (VPCs) without requiring inbound firewall rules. The runner initiates outbound connections to PagerDuty, making it firewall-friendly.

### Our Setup

- **Runner Name**: `aws-ec2-runner`
- **Runner ID**: `c144f57c-b026-4174-88b9-d65b06a6d7cc`
- **Replica ID**: `019c24fa-022a-7eba-bc2b-e7d71fcb6cc3`
- **Project**: `pagerduty-demo`
- **EC2 Instance**: `i-03ab4fd5f509a8342`
- **Region**: `us-east-1`

---

## The Problem

### Initial Symptoms

When attempting to run the PagerDuty RBA runner using the official Docker container with environment variables, the runner failed to connect properly, exhibiting the following errors:

```
RecoveryInterceptor: Connection not established
Bad Request (400) errors
Runner continuously restarting
Replica status stuck on "New" in PagerDuty UI
```

### Docker Container Approach (FAILED)

The official documentation suggests running the runner using:

```bash
docker run -d \
  --name runner \
  -e RUNNER_RUNDECK_SERVER_TOKEN="<token>" \
  -e RUNNER_RUNDECK_SERVER_URL="https://api.runbook.pagerduty.cloud" \
  -e RUNNER_RUNDECK_CLIENT_ID="<runner-id>" \
  rundeckpro/runner:5.19.0
```

**This approach did NOT work** for manual replica types.

### Root Cause

The issue stems from how PagerDuty RBA handles different replica types:

1. **Automatic Replicas**: Created automatically when using the Docker container with the runner token. The container generates its own replica ID.

2. **Manual Replicas**: Require pre-registration via API and use a **replica-specific token** and a **custom JAR download** with embedded credentials.

When the runner is configured with `replicaType: manual`, the generic Docker container cannot authenticate properly because:
- It expects to create its own replica
- The runner token alone is insufficient
- The `RUNNER_RUNDECK_CLIENT_ID` semantics differ between automatic and manual modes

---

## What Was Tried

### Attempt 1: Docker with Runner ID as Client ID

```bash
docker run -d \
  --name runner \
  -e RUNNER_RUNDECK_SERVER_TOKEN="OFQxJ44WT15xGXhywkhXf8xP7mpi5m8L" \
  -e RUNNER_RUNDECK_SERVER_URL="https://api.runbook.pagerduty.cloud" \
  -e RUNNER_RUNDECK_CLIENT_ID="c144f57c-b026-4174-88b9-d65b06a6d7cc" \
  rundeckpro/runner:5.19.0
```

**Result**: `RecoveryInterceptor` errors, connection failures, continuous restarts.

### Attempt 2: Docker with Replica ID as Client ID

Created a manual replica via API:
```bash
curl -X POST "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/<runner-id>/replicas" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Then ran Docker with the replica ID:
```bash
docker run -d \
  --name runner \
  -e RUNNER_RUNDECK_SERVER_TOKEN="<replica-specific-token>" \
  -e RUNNER_RUNDECK_SERVER_URL="https://api.runbook.pagerduty.cloud" \
  -e RUNNER_RUNDECK_CLIENT_ID="019c24fa-022a-7eba-bc2b-e7d71fcb6cc3" \
  rundeckpro/runner:5.19.0
```

**Result**: "Runner not found" errors initially, then "Bad Request" errors after reverting. Logs showed "Beginning to poll Rundeck" but replica stayed in "New" status.

### Attempt 3: Various Token Combinations

Tried combinations of:
- Original runner token with runner ID
- Original runner token with replica ID
- Replica-specific token with runner ID
- Replica-specific token with replica ID

**Result**: All combinations failed with the Docker container.

### Attempt 4: Connectivity Verification

Verified EC2 instance can reach PagerDuty:
```bash
curl -s -o /dev/null -w "%{http_code}" https://api.runbook.pagerduty.cloud/health
# Result: 200
```

**Conclusion**: Network connectivity was not the issue.

---

## The Working Solution

### Key Discovery

When creating a manual replica via API, the response includes a `downloadTk` field:

```json
{
  "id": "019c24fa-022a-7eba-bc2b-e7d71fcb6cc3",
  "runnerId": "c144f57c-b026-4174-88b9-d65b06a6d7cc",
  "status": "New",
  "downloadTk": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."
}
```

This `downloadTk` is a JWT that allows downloading a **custom runner JAR** with embedded credentials specific to this replica.

### The Working Approach: Direct JAR Execution

Instead of using the Docker container, download and run the replica-specific JAR directly:

1. **Create a manual replica** via API to get the `downloadTk`
2. **Download the custom JAR** using the download token
3. **Run the JAR directly** with Java (not Docker)

### Why This Works

The custom JAR downloaded via `downloadTk`:
- Contains embedded authentication credentials for the specific replica
- Has the correct runner ID and replica ID pre-configured
- Uses a different authentication flow than environment variables
- Properly handles the manual replica registration

---

## Step-by-Step Setup Guide

### Prerequisites

- AWS EC2 instance (Amazon Linux 2 or similar)
- Instance role with SSM access (for management)
- Outbound HTTPS (443) access to `*.runbook.pagerduty.cloud`
- Java 17+ runtime
- PagerDuty RBA API token (from Automation > Runners > API Tokens)

### Step 1: Create the Runner in PagerDuty

Via PagerDuty UI:
1. Navigate to **Automation** > **Runners**
2. Click **New Runner**
3. Enter runner name (e.g., `aws-ec2-runner`)
4. Select the project (e.g., `pagerduty-demo`)
5. Note the **Runner ID** from the created runner

Or via API:
```bash
curl -X POST "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aws-ec2-runner",
    "description": "AWS EC2 Runner for automation",
    "assignedProjects": {
      "default": ["<PROJECT_ID>"]
    },
    "tagNames": ["aws", "ec2"],
    "replicaType": "manual"
  }'
```

### Step 2: Create a Manual Replica

```bash
RUNNER_ID="c144f57c-b026-4174-88b9-d65b06a6d7cc"
API_TOKEN="<your-api-token>"

curl -X POST "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/${RUNNER_ID}/replicas" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -o replica_response.json

# Extract the download token
DOWNLOAD_TK=$(jq -r '.downloadTk' replica_response.json)
REPLICA_ID=$(jq -r '.id' replica_response.json)

echo "Replica ID: ${REPLICA_ID}"
echo "Download Token: ${DOWNLOAD_TK}"
```

**IMPORTANT**: Save the `downloadTk` - it's only provided once at replica creation!

### Step 3: Download the Custom Runner JAR

```bash
curl -X GET "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/download/runner" \
  -H "Authorization: Bearer ${DOWNLOAD_TK}" \
  -o runner.jar
```

The downloaded JAR is approximately 227 MB and contains:
- The runner application
- Embedded plugins (SSH, Docker, Ansible, AWS, Azure, etc.)
- Pre-configured credentials for this replica

### Step 4: Upload JAR to S3 (Optional but Recommended)

```bash
# Create S3 bucket for runner artifacts
aws s3 mb s3://pagerduty-demo-runner-bucket --region us-east-1

# Upload the JAR
aws s3 cp runner.jar s3://pagerduty-demo-runner-bucket/runner.jar

# Ensure EC2 instance role has S3 read permissions
aws iam put-role-policy --role-name rba-runner-role \
  --policy-name S3RunnerBucketAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::pagerduty-demo-runner-bucket",
        "arn:aws:s3:::pagerduty-demo-runner-bucket/*"
      ]
    }]
  }'
```

### Step 5: Install Java on EC2

```bash
# Via SSM or direct SSH
sudo yum install -y java-17-amazon-corretto-headless
```

### Step 6: Download and Run the JAR on EC2

```bash
# Download from S3
aws s3 cp s3://pagerduty-demo-runner-bucket/runner.jar /opt/runner.jar

# Run as background process
nohup java -jar /opt/runner.jar > /var/log/runner.log 2>&1 &
```

### Step 7: Verify Runner is Connected

Check the logs:
```bash
tail -f /usr/bin/runner/logs/runner.log
```

Expected output:
```
INFO  com.rundeck.sidecar.agent.comm.rundeck.HttpPollingOperationListenerService - Beginning to poll Rundeck for operations
INFO  com.rundeck.runner.agent.ReplicaService - Connecting to the rundeck server
INFO  com.rundeck.sidecar.agent.services.AgentStatusEvents - Runner started. Version: 5.20-RBA-20260128-2c35e1f-1989440
Operations registered: [RundeckWorkflowStep, Ping, RundeckFileCopy, CancelInvocation, 
                        RundeckWorkflowNodeStep, RbaScript, RundeckCommand, GetNodesInvocation, 
                        RundeckStorageConfiguration, rundeck-storage-lookup]
INFO  io.micronaut.runtime.Micronaut - Startup completed in 8315ms.
```

Verify network connection:
```bash
netstat -an | grep ESTABLISHED | grep 443
# Should show connection to PagerDuty IP (e.g., 98.88.14.39:443)
```

### Step 8: Set Up as Systemd Service (Production)

Create `/etc/systemd/system/pagerduty-runner.service`:
```ini
[Unit]
Description=PagerDuty RBA Runner
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/java -jar /opt/runner.jar
Restart=always
RestartSec=10
StandardOutput=append:/var/log/runner-stdout.log
StandardError=append:/var/log/runner-stderr.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pagerduty-runner
sudo systemctl start pagerduty-runner
sudo systemctl status pagerduty-runner
```

---

## Resources and References

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners` | List/Create runners |
| `https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/{id}/replicas` | Manage replicas |
| `https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/download/runner` | Download custom JAR |

### Log File Locations (on EC2)

| File | Purpose |
|------|---------|
| `/var/log/runner.log` | Main stdout/stderr from nohup |
| `/usr/bin/runner/logs/runner.log` | Detailed runner application logs |
| `/usr/bin/runner/logs/operations.log` | Operation execution logs |

### Key Configuration Values

| Item | Value |
|------|-------|
| Runner ID | `c144f57c-b026-4174-88b9-d65b06a6d7cc` |
| Replica ID | `019c24fa-022a-7eba-bc2b-e7d71fcb6cc3` |
| EC2 Instance | `i-03ab4fd5f509a8342` |
| S3 Bucket | `pagerduty-demo-runner-bucket` |
| IAM Role | `rba-runner-role` |
| Instance Profile | `rba-runner-profile` |

### Useful Commands

```bash
# Check runner process
ps aux | grep java

# Check runner logs
tail -f /usr/bin/runner/logs/runner.log

# Check network connections
netstat -an | grep ESTABLISHED | grep 443

# Restart runner
sudo systemctl restart pagerduty-runner

# View runner status via API
curl -X GET "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/<RUNNER_ID>/replicas" \
  -H "Authorization: Bearer <API_TOKEN>"
```

### AWS Resources

- **EC2 Instance**: `i-03ab4fd5f509a8342` (us-east-1)
- **Security Group**: Requires outbound HTTPS (443) to internet
- **IAM Role**: `rba-runner-role` with SSM and S3 permissions
- **S3 Bucket**: `pagerduty-demo-runner-bucket`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PagerDuty Cloud                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Runbook Automation (RBA)                        │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │   │
│  │  │   Project   │    │   Runner    │    │   Replica   │     │   │
│  │  │ pagerduty-  │───▶│ aws-ec2-    │───▶│ 019c24fa... │     │   │
│  │  │   demo      │    │   runner    │    │  (Active)   │     │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▲                                      │
│                              │ HTTPS (443)                          │
│                              │ Outbound polling                     │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                         AWS VPC                                     │
│                              │                                      │
│  ┌───────────────────────────┼─────────────────────────────────┐   │
│  │                    EC2 Instance                              │   │
│  │                 i-03ab4fd5f509a8342                          │   │
│  │                                                              │   │
│  │   ┌──────────────────────────────────────────────────────┐  │   │
│  │   │                Java Process                           │  │   │
│  │   │         java -jar /opt/runner.jar                     │  │   │
│  │   │                                                       │  │   │
│  │   │  • Polls PagerDuty for pending operations             │  │   │
│  │   │  • Executes commands/scripts locally                  │  │   │
│  │   │  • Reports results back to PagerDuty                  │  │   │
│  │   │  • Embedded credentials (no env vars needed)          │  │   │
│  │   └──────────────────────────────────────────────────────┘  │   │
│  │                                                              │   │
│  │   Log Files:                                                 │   │
│  │   • /var/log/runner.log                                      │   │
│  │   • /usr/bin/runner/logs/runner.log                          │   │
│  │   • /usr/bin/runner/logs/operations.log                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    S3 Bucket                                  │  │
│  │           pagerduty-demo-runner-bucket                        │  │
│  │                                                               │  │
│  │   • runner.jar (227 MB, custom JAR with credentials)          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Runner Shows "New" Status

**Cause**: The runner is not connecting properly.

**Solution**: 
1. Verify using the custom JAR (not Docker with env vars)
2. Check the `downloadTk` was used to download the JAR
3. Verify Java 17+ is installed
4. Check outbound HTTPS connectivity

### "RecoveryInterceptor" Errors

**Cause**: Docker container authentication failure with manual replicas.

**Solution**: Use the direct JAR approach instead of Docker.

### "Bad Request" Errors

**Cause**: Incorrect authentication or client ID mismatch.

**Solution**: Use the custom JAR which has embedded credentials.

### No Network Connection

**Cause**: Security group or network ACL blocking outbound HTTPS.

**Solution**: Ensure outbound TCP 443 is allowed to `0.0.0.0/0` or PagerDuty IPs.

### JAR Download Fails

**Cause**: `downloadTk` expired or invalid.

**Solution**: Create a new replica to get a fresh `downloadTk`.

---

## Critical Gotchas and Workarounds

This section documents the critical lessons learned during the RBA runner setup process. These are non-obvious behaviors that can cause significant troubleshooting time if not understood upfront.

### GOTCHA #1: Docker Container Does NOT Work for Manual Replicas

**The Problem:**
The official PagerDuty documentation and many examples show using the Docker container with environment variables:
```bash
docker run -d \
  -e RUNNER_RUNDECK_SERVER_TOKEN="..." \
  -e RUNNER_RUNDECK_SERVER_URL="https://api.runbook.pagerduty.cloud" \
  -e RUNNER_RUNDECK_CLIENT_ID="..." \
  rundeckpro/runner:5.19.0
```

This approach **ONLY works for automatic replicas**. When you create a runner via the PagerDuty UI or API without specifying `replicaType: manual`, the Docker container can self-register as a replica.

**However**, if the runner is configured with `replicaType: manual` (which is common in enterprise environments for control/auditing), the Docker container authentication completely fails with cryptic errors like:
- `RecoveryInterceptor: Connection not established`
- `Bad Request (400)`
- Replica stuck in "New" status forever

**The Workaround:**
You MUST use the custom JAR downloaded via the `downloadTk` JWT token, not the Docker container. This is the only way to authenticate a manual replica.

**Time Lost to This Issue:** Approximately 4+ hours of troubleshooting

---

### GOTCHA #2: The downloadTk is ONLY Available at Replica Creation

**The Problem:**
When you create a manual replica via the API:
```bash
POST /api/v1/runnerManagement/runners/{runner-id}/replicas
```

The response includes a `downloadTk` field which is a JWT token for downloading the custom runner JAR. This token is:
- Only returned ONCE at creation time
- NOT stored or retrievable later
- NOT visible in the PagerDuty UI
- Has a limited validity period

If you lose this token or forget to save it, you must:
1. Delete the replica
2. Create a new replica
3. Immediately save the new `downloadTk`

**The Workaround:**
ALWAYS save the full API response when creating a replica:
```bash
curl -X POST "https://api.runbook.pagerduty.cloud/api/v1/runnerManagement/runners/${RUNNER_ID}/replicas" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -o replica_response.json  # SAVE THE FULL RESPONSE!
```

---

### GOTCHA #3: EC2 Instance Needs S3 Permissions You Might Not Expect

**The Problem:**
If you store the runner JAR in S3 (recommended for reproducibility), your EC2 instance role needs explicit S3 read permissions for that specific bucket. The default Amazon SSM managed policy does NOT include S3 access.

**Symptoms:**
```
fatal error: An error occurred (403) when calling the HeadObject operation: Forbidden
```

**The Workaround:**
Add an inline policy to your EC2 instance role:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::your-bucket-name",
      "arn:aws:s3:::your-bucket-name/*"
    ]
  }]
}
```

---

### GOTCHA #4: The Runner Creates Its Own Log Directory Structure

**The Problem:**
The runner JAR creates its own directory structure at runtime:
```
/usr/bin/runner/
├── logs/
│   ├── runner.log
│   └── operations.log
├── .db/
└── runner.log
```

This is NOT in `/var/log` by default. If you redirect stdout/stderr to a log file, you'll have TWO sets of logs:
1. Your redirected logs (e.g., `/var/log/runner.log`)
2. The runner's internal logs (`/usr/bin/runner/logs/runner.log`)

**The Workaround:**
For troubleshooting, always check BOTH locations:
```bash
tail -f /usr/bin/runner/logs/runner.log  # The detailed application logs
tail -f /var/log/runner.log               # The stdout/stderr redirect
```

---

### GOTCHA #5: Lambda Environment Variable Updates Have a Command-Line Length Limit

**The Problem:**
When updating Lambda function environment variables via AWS CLI, passing all variables as a JSON string in the command line can exceed shell command length limits (typically 128KB).

**Symptoms:**
```
argument list too long
```

**The Workaround:**
Use a JSON file and the `file://` prefix:
```bash
# Get current config and modify
aws lambda get-function-configuration --function-name my-func \
  --query 'Environment' --output json | jq '.Variables.NEW_VAR = "value"' > /tmp/env.json

# Update using file reference
aws lambda update-function-configuration --function-name my-func \
  --environment file:///tmp/env.json
```

**CRITICAL**: The `--environment` parameter expects the structure `{"Variables": {...}}`, so use jq to modify `.Variables.*` not the top level.

---

### GOTCHA #6: Slack Bot Token Scopes are Workspace-Specific

**The Problem:**
When using Slack in an Enterprise Grid environment, bot tokens can be either:
- **Workspace-scoped**: Only works in specific workspaces
- **Org-scoped**: Works across all workspaces in the org

The PagerDuty Slack integration typically requires org-level tokens. If you reinstall the Slack app or modify permissions, you must:
1. Ensure the app is installed at the org level
2. Update the token in ALL locations (Lambda functions, PagerDuty UI, local scripts)

**Symptoms:**
- `missing_scope` errors
- `channel_not_found` errors even for channels that exist
- `not_in_channel` errors

**The Workaround:**
Always verify the token scopes after any Slack app reinstallation:
```bash
curl -H "Authorization: Bearer xoxb-..." https://slack.com/api/auth.test
```

Check the response includes `"is_enterprise_install": true` for org-wide access.

---

### GOTCHA #7: PagerDuty Workflow Steps Require API Keys, Not User Tokens

**The Problem:**
When programmatically updating PagerDuty incident workflow steps (via API), you MUST use an API Key, not a User OAuth Token.

**Symptoms:**
- `403 Forbidden` errors
- Empty responses
- Partial updates that silently fail

**The Workaround:**
Always use an API Key (starts with `u+` and is longer) for workflow management scripts:
```bash
export PAGERDUTY_TOKEN="YOUR_PAGERDUTY_TOKEN"  # API Key, not user token
python scripts/populate_workflow_steps.py --apply
```

---

## Lessons Learned Summary

| Lesson | Impact | Prevention |
|--------|--------|------------|
| Docker + manual replicas = broken | 4+ hours | Always use custom JAR for manual replicas |
| downloadTk is ephemeral | 1+ hours | ALWAYS save full replica creation response |
| S3 permissions not automatic | 30 min | Add S3 policy to EC2 role upfront |
| Multiple log locations | 30 min | Check both /var/log and /usr/bin/runner/logs |
| CLI length limits for Lambda | 30 min | Always use file:// for env updates |
| Slack token scope issues | 1+ hours | Verify org-level install after changes |
| API Key vs User Token | 30 min | Use API Keys for workflow automation |

**Total Estimated Time Lost to These Issues:** 8+ hours

By documenting these gotchas, future developers should be able to avoid these pitfalls entirely.

---

## Summary

| Approach | Works? | Notes |
|----------|--------|-------|
| Docker + env vars (automatic replica) | Maybe | Only if runner configured for automatic replicas |
| Docker + env vars (manual replica) | **NO** | Authentication fails |
| Custom JAR via downloadTk | **YES** | The working solution for manual replicas |

**Key Takeaway**: For manual replica types, you MUST use the custom JAR downloaded via the `downloadTk` token. The generic Docker container with environment variables does not work.

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-03 | AI Assistant | Initial documentation of issue and solution |
| 2026-02-03 | AI Assistant | Added Critical Gotchas and Workarounds section with 7 detailed gotchas |
| 2026-02-03 | AI Assistant | Added Lessons Learned Summary table |
