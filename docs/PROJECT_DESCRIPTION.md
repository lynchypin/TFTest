# PagerDuty Demo Environment - Project Description

## Executive Summary

This project creates a **fully automated, realistic PagerDuty demo environment** that showcases the complete incident management lifecycle. Unlike static demos or manual walkthroughs, this environment simulates actual user behavior, enabling prospects and customers to see PagerDuty's capabilities "in action" without requiring manual intervention during demonstrations.

---

## The Problem This Solves

### Traditional Demo Challenges

1. **Manual Effort**: Presenters must click through UI, type notes, acknowledge incidents manually
2. **Timing Issues**: Difficult to show realistic response times (30 seconds feels like forever in a demo)
3. **Complexity**: Hard to demonstrate multi-responder scenarios, escalations, and coordination
4. **Integration Depth**: Challenging to show Slack/Jira integration without pre-staging
5. **Reproducibility**: Every demo is different, hard to ensure consistency

### This Solution

1. **Automated Lifecycle**: Incidents progress automatically from trigger to resolution
2. **Simulated Responders**: Multiple "users" acknowledge, add notes, collaborate
3. **Real Integrations**: Actually creates Slack channels, Jira tickets, runs automation
4. **Controllable Timing**: Configurable delays between actions (demo-friendly speeds)
5. **Pause/Resume**: Can pause automation to deep-dive on specific features
6. **Reproducible**: Same triggers produce same demo flow every time

---

## Key Design Decisions & Rationale

### Why Terraform for PagerDuty Resources?

**Decision**: Use Terraform to define all PagerDuty configuration as code.

**Rationale**:
- **Reproducibility**: Can recreate entire environment from scratch
- **Version Control**: Changes are tracked, reviewable, revertable
- **Documentation**: The `.tf` files ARE the documentation
- **Multi-environment**: Easy to create staging/production variants

**Trade-off**: Terraform provider limitations (e.g., no workflow steps), requiring API workarounds.

---

### Why Two-Phase Workflow Deployment?

**Decision**: Create empty workflow shells via Terraform, then populate steps via API script.

**Rationale**:
- PagerDuty Terraform provider cannot create workflows WITH steps in single operation
- Workaround maintains "infrastructure as code" principle while working within limitations

**Trade-off**: Extra deployment step, potential for drift if script not run.

---

### Why External Orchestrator (Lambda) Instead of Pure PagerDuty?

**Decision**: Use AWS Lambda to orchestrate demo behavior rather than relying solely on PagerDuty workflows.

**Rationale**:
- **Slack Population**: PagerDuty workflows CREATE channels but don't INVITE users or POST messages
- **Timing Control**: Workflows execute immediately; Lambda can introduce realistic delays
- **Action Simulation**: Workflows can't simulate a user acknowledging or adding notes
- **State Management**: Need to track which responders have acted, demo pause state
- **Flexibility**: Can add demo-specific logic (random responder selection, conversation library)

**Trade-off**: Additional infrastructure to deploy and maintain.

**Evolution (February 12, 2026):** The original approach used a webhook-driven `demo-simulator-orchestrator-v2` Lambda with EventBridge Scheduler for delayed actions. This was replaced by the `demo-simulator-controller` Lambda which is self-contained — it triggers the event, waits inline (using `time.sleep()`), discovers channels, and runs all phases within a single 15-minute Lambda invocation. This eliminated timing issues with EventBridge and webhook delivery.

---

### Why DynamoDB for State?

**Decision**: Store demo state (incident progress, responders, pause status) in DynamoDB.

**Rationale**:
- **Serverless**: No servers to manage, scales automatically
- **TTL**: Records auto-expire after 24 hours (cleanup handled)
- **Low Latency**: Fast reads/writes for webhook processing
- **Cost**: Pay-per-request pricing suits sporadic demo usage

**Trade-off**: AWS lock-in, requires AWS credentials.

**Note (February 12, 2026):** The `demo-simulator-controller` Lambda does NOT use DynamoDB — it manages state in-memory during its single invocation. DynamoDB is still used by the legacy webhook-driven `demo-simulator-orchestrator-v2`.

---

### Why Inline Delays Instead of EventBridge Scheduler?

**Decision**: The current `demo-simulator-controller` uses `time.sleep()` with random delays between actions, running the entire scenario within a single Lambda invocation (900-second timeout).

**Rationale**:
- **Simplicity**: No external scheduler coordination, no webhook delivery issues
- **Reliability**: Eliminates timing bugs from EventBridge/webhook race conditions
- **Debuggability**: Entire scenario flow visible in a single CloudWatch log stream
- **Configurability**: Pass `"action_delay": N` to override timing for testing vs demos

**Trade-off**: Lambda runs for 8-12 minutes during a real demo (billed for full duration). Cost is minimal for demo usage.

**Previous Approach**: EventBridge Scheduler (`ActionAfterCompletion: DELETE`) was used in the orchestrator Lambda. This is documented for reference but is no longer the primary execution path.

---

## Nuanced Behaviors & Edge Cases

### Incident Acknowledgment

**Requirement**: Every demo incident MUST be acknowledged.

**Implementation (Controller — current)**:
1. Controller triggers the event and polls for incident creation
2. Controller directly acknowledges the incident as the first responder using the admin token with `From:` header
3. No delay needed — acknowledgment happens immediately after incident is found
4. If the controller fails mid-run, PagerDuty's native escalation policy eventually escalates to next responder

**Legacy Implementation (Orchestrator — not actively used)**:
1. On `incident.triggered` webhook, schedule acknowledgment via EventBridge Scheduler (30-120s delay)
2. If acknowledgment doesn't happen, PagerDuty escalation kicks in
3. Escalation to next level triggers new acknowledgment attempt

**Why This Matters**: Unacknowledged incidents break the demo narrative and look unprofessional.

---

### Multi-Responder Coordination

**Behavior**: Some incidents have multiple responders (1-4, weighted probability).

**Flow**:
1. Determine responder count (65% single, 25% double, 8% triple, 2% quad)
2. Primary responder acknowledges first
3. On acknowledgment, ADD additional responders to incident
4. Each responder performs one action (note, status update, etc.)
5. Resolution only after all responders have acted

**Why Weighted**: Most real incidents are handled by single responder; multi-responder scenarios are less common but impactful to demonstrate.

---

### Pause/Resume Mechanism

**Purpose**: Allow the presenter to pause automated demo progression and spend more time explaining specific features or steps.

**Use Cases**:
- Pause to deep-dive on a specific PagerDuty feature during a demo
- Allow more time for audience questions at a specific step
- Temporarily halt the demo while explaining complex concepts
- Presenter-controlled pacing (NOT automatic real incident detection)

**Behavior**:
- `POST /pause`: Sets `paused: true` in demo state
- While paused: Scheduled actions check state and skip execution
- `POST /resume`: Sets `paused: false`, schedules next action immediately
- **Timeout**: If paused > 15 minutes, auto-resolve incident (prevents orphaned demos)

**Why Timeout**: Presenters sometimes forget to resume; orphaned incidents clutter PagerDuty.

---

### Demo vs. Real Incident Detection

**Mechanism**: Demo incidents have `[DEMO]` prefix in title.

**Why**: 
- Lambda only processes incidents with `[DEMO]` in title
- Prevents demo automation from interfering with real incidents
- Allows demo environment to coexist with production PagerDuty

---

### Slack Channel Naming

**Pattern**: `demo-{incident_number}-{service_name_truncated}`

**Examples**:
- `demo-718-demo-e2e-workflow-`
- `demo-314-demo-e2e-workflow-`

**Why `demo-` prefix**: PagerDuty's Incident Workflow "Create Slack Channel" step generates channels with the `demo-` prefix based on the configured channel name template.

**Why Truncate Service Name**: Slack channel names have 80-character limit.

---

### Conversation Library

**Purpose**: Make Slack messages feel realistic, not robotic.

**Categories** (10 as of Feb 12, 2026):
- `database`: "Running SHOW PROCESSLIST to identify slow queries..."
- `kubernetes`: "OOMKilled events on several pods - checking resource limits..."
- `api`: "Circuit breaker opened to downstream payment service..."
- `security`: "Analyzing suspicious login patterns from multiple geos..."
- `network`: "Packet loss between us-east and us-west regions..."
- `automation`: "Runbook execution completed, checking results..."
- `manufacturing`: "Checking OT sensor readings on line 4..."
- `workflow`: "Pipeline stage completed, moving to next phase..."
- `integration`: "API health check returning degraded status..."
- `observability`: "Trace analysis shows latency spike in service mesh..."

**Phase-Based Selection**: Messages are selected based on the current incident phase (investigating, found_issue, working_fix, resolved), with different tones appropriate to each phase.

**Why Multiple Per Category**: Avoids repetitive messages; random selection adds variety. A `used_messages` set prevents the same message appearing twice in a scenario.

---

## Integration-Specific Nuances

### Slack Integration

**PagerDuty Native**: Creates channels via Incident Workflow steps
**Lambda Controller**: Bot joins channels, invites observers + responders, posts conversation messages with user impersonation

**User Impersonation (Added February 8, 2026)**:
The Lambda now posts Slack messages that visually appear as individual users (Jim Beam, Jack Daniels, etc.) rather than as the bot:
- Uses `users.info` API to fetch user's display name and avatar URL
- Caches profiles to avoid repeated API calls
- Posts with `username` and `icon_url` parameters
- **Limitation**: Messages still show "APP" badge (Slack API limitation)

**Order of Operations (Updated February 18, 2026)**:
1. Controller triggers PagerDuty event via Events API v2
2. PagerDuty creates incident, workflow fires
3. Workflow creates Slack channel, stores URL in `conference_bridge`
4. Controller runs **Slack health check** (`verify_token()`) at startup — logs `SLACK TOKEN INVALID` if broken, preventing silent failures
5. Controller polls `GET /incidents/{id}?include[]=conference_bridge`
6. Controller extracts channel ID from `conference_bridge.conference_url`
7. Bot calls `conversations.join` on the channel
8. Bot invites observers — **both** Conall Slack accounts: `U0A9GBYT999` (personal) and `U0A9KAMT0BF` (work/PagerDuty)
9. Bot invites responders (handles `user_is_restricted` gracefully)
10. Responder actions post messages with user impersonation — **errors are now logged** if `post_as_user` or `invite_user_to_channel` fails

**Key Gotcha — Bot Must Self-Join**: The bot is NOT automatically a member of channels created by PagerDuty's native Slack integration. You MUST call `conversations.join` before posting or inviting. Without this, all Slack API calls fail with `not_in_channel`.

**Key Gotcha — `conference_bridge` Not Included by Default**: The `conference_bridge` field is NOT returned by `GET /incidents/{id}` unless you pass `include[]=conference_bridge`. The channel ID is in `conference_url` (not `url`).

**Key Gotcha — Observer Restrictions**: Some Slack users (e.g., `clynch@pagerduty.com`) are restricted guest users and cannot be invited to channels. The controller handles this gracefully with a warning log. Both `conalllynch88@gmail.com` and `clynch@pagerduty.com` are in the default observer list as of February 18, 2026.

---

### Jira Integration

**Workflow Step**: Creates ticket with incident details
**Project Mapping**: Different workflows target different Jira projects

| Workflow Type | Jira Project | Issue Type |
|--------------|--------------|------------|
| Security Incident | SECOPS | Security Incident |
| Data Breach | COMPLIANCE | Data Breach |
| Infrastructure | INFRA | Incident |
| Post-Incident Review | PIR | Post-Incident Review |
| Payment Outage | PAYMENTS | Outage |
| Data Pipeline | DATA | Pipeline Issue |

**Manual Prerequisite**: Jira projects must exist before workflow can create tickets.

---

### Monitoring Tool Triggers

**Datadog**: Send metric data points → trigger monitor → fire PagerDuty event
**Grafana**: Create annotation → trigger alert rule → fire PagerDuty event
**New Relic**: Send custom event → trigger NRQL alert → fire PagerDuty event
**CloudWatch**: Put metric data → trigger alarm → fire PagerDuty event

**Fallback**: If monitoring tool integration fails, Lambda falls back to PagerDuty Events API v2 (direct trigger).

---

## Performance Considerations

### Controller Lambda Duration

**Current Approach**: The controller runs the entire scenario within a single Lambda invocation (up to 900 seconds / 15 minutes).

**Typical Durations**:
- Testing mode (`action_delay: 2`): ~70 seconds
- Demo mode (default 30-60s delays): ~8-12 minutes

**Cost**: Lambda is billed per 1ms of execution. A 10-minute Lambda invocation at 256MB costs ~$0.025. Minimal for demo usage.

**Limits**: Lambda max timeout is 900 seconds (15 minutes). Scenarios with many actions + max delays could approach this limit. Monitor CloudWatch for timeout errors.

### Legacy Architecture Performance (For Reference)

The webhook-driven orchestrator (`demo-simulator-orchestrator-v2`) used:
- DynamoDB single-table design for state (< 3s webhook processing target)
- EventBridge Scheduler for delayed actions (auto-delete after execution)
- DynamoDB on-demand capacity (sufficient for < 100 incidents/day)

These are not actively used by the controller but remain deployed.

---

## Security Considerations

### API Token Storage

**DO NOT**:
- Commit tokens to repository
- Log tokens in CloudWatch
- Pass tokens in query strings

**DO**:
- Store in AWS Secrets Manager or Parameter Store
- Reference via environment variables
- Use IAM roles for AWS services

---

### Webhook Signature Verification

**Mechanism**: PagerDuty signs webhooks with HMAC-SHA256.

**Implementation**: Lambda verifies `x-pagerduty-signature` header against shared secret.

**In Demo**: Can be disabled for simplicity, but MUST be enabled in production-like setups.

---

### Slack Token Scope

**Required Scopes**:
- `channels:read` - List channels
- `channels:join` - Join public channels (bot self-joins PD-created channels)
- `channels:manage` - Manage channel settings
- `chat:write` - Post messages
- `chat:write.customize` - Post with custom username/icon (user impersonation)
- `users:read` - Get user profiles for impersonation

**NOT Available** (and not needed):
- ~~`groups:read`~~ - Cannot list private channels; use `types=public_channel` only
- ~~`channels:write`~~ - Cannot create channels; PagerDuty workflows handle this

**Bot vs. User Token**: Use Bot token (starts with `xoxb-`), not User token.

---

## Extensibility Points

### Adding New Demo Scenarios

1. Add the scenario to `docs/demo-scenarios/src/data/scenarios.json`
2. Ensure the scenario's service has a routing key mapping in `SERVICE_TO_ROUTING_KEY` (`aws/lambda-demo-controller/handler.py`)
3. Ensure the event payload includes `class`/`component`/`custom_details` fields matching an Event Orchestration routing rule
4. Add conversation categories if the scenario type is new (in `CONVERSATION_LIBRARY`)
5. Test: `aws lambda invoke --function-name demo-simulator-controller --payload '{"action": "run_scenario", "scenario_id": "NEW-001", "action_delay": 2}' --cli-binary-format raw-in-base64-out /dev/stdout`

### Adding New Responder Actions

1. Add action type to the `action_type` selection in `select_actions_for_phase()` (`aws/lambda-demo-controller/handler.py`)
2. Implement the action handler in `perform_action()`
3. Add any new PagerDuty API methods to `aws/shared/clients.py`
4. Add conversation messages to `CONVERSATION_LIBRARY` if needed
5. Redeploy Lambda (see `docs/NEXT_DEVELOPER_PROMPT.md` for deployment commands)

### Customizing Timing

| Parameter | Default | Location |
|-----------|---------|----------|
| Action delay (between steps) | 30-60s random | `DEFAULT_ACTION_DELAY_MIN/MAX` env vars or `"action_delay"` in payload |
| Incident creation wait | 10s | `run_scenario()` in handler.py |
| Channel discovery timeout | 90s | `wait_for_incident_channel()` timeout_seconds param |
| Lambda timeout | 900s (15 min) | `aws/main.tf` controller Lambda config |

---

## Known Limitations

### Design Limitations

1. **Terraform Provider**: Cannot create workflow steps (requires API script)
2. **Single PagerDuty Account**: Designed for one account; multi-account would need refactoring
3. **Demo Prefix Required**: Only processes `[DEMO]` incidents; can't demo on real incidents
4. **Slack App Required**: Need Slack app with correct scopes; can't use legacy webhooks
5. **Jira Projects Manual**: Must create Jira projects manually before using workflows
6. **US Region Focus**: API URLs hardcoded for US; EU customers need adjustment
7. **Single Scenario at a Time**: Controller runs one scenario per invocation; no built-in multi-scenario orchestration yet
8. **Lambda Duration Cost**: Each demo scenario occupies a Lambda for 8-12 minutes; cost is minimal but could add up with frequent use

### Remaining Issues (as of February 18, 2026)

1. **~~Incidents Not Auto-Acknowledging~~**: RESOLVED — Controller handles acknowledgment directly via API
2. **~~Demo Owner Not Added to Channels~~**: RESOLVED (Feb 18) — Both Conall Slack accounts (`U0A9GBYT999` personal, `U0A9KAMT0BF` work) now in default observer list. Controller also validates Slack token at startup.
3. **Event Routing**: 12 rules cover most scenarios, but some may fall through to default service
4. **~~60 Scenarios Not E2E Validated~~**: RESOLVED (Feb 14) — All 51 enabled scenarios (of 70 total) validated via `scripts/test_all_scenarios.py`; 19 disabled pending external integrations
5. **Status Page API**: `create_status_incident()` returns Invalid Input — enum values need fixing
6. **Terraform Lambda Deployment**: Does not reliably detect code changes; use direct CLI deployment as workaround
7. **~~Jim Beam Over-Scheduled~~**: RESOLVED (Feb 18) — Replaced Jim Beam with Arthur Guinness on "Business Ops" and "Manager Escalation" schedules. All users now have 2-3 schedule assignments.
8. **~~Slack Operations Failing Silently~~**: PARTIALLY RESOLVED (Feb 18) — `SlackClient.verify_token()` added; `run_demo_flow()` now validates token at startup and logs `SLACK TOKEN INVALID` if broken. Slack `post_as_user` and `invite_user_to_channel` errors are now logged. However, failures still don't halt the demo flow (by design — PagerDuty operations should still complete even if Slack is down).
9. **~~Incident Resolution Failures~~**: IMPROVED (Feb 18) — `resolve_incident()` in the controller now has retry logic with error logging. If the first resolve attempt fails, it waits 3 seconds and retries once, logging both attempts.
10. **Cache Variable TTL Tuning**: Cache variable TTLs (300-600s) are initial estimates. May need adjustment based on real demo usage patterns — see `docs/GOTCHAS_AND_WORKAROUNDS.md` for current settings.

See [GOTCHAS_AND_WORKAROUNDS.md](./GOTCHAS_AND_WORKAROUNDS.md) for detailed debugging steps.

---

## Glossary

| Term | Definition |
|------|------------|
| **Incident Workflow** | PagerDuty feature that automates actions when incidents meet conditions |
| **Event Orchestration** | Rules engine for processing incoming events before incident creation |
| **RBA** | Runbook Automation - PagerDuty's automation execution platform |
| **Automation Action** | A script or command executed by RBA runners |
| **Escalation Policy** | Rules defining who to notify and when to escalate |
| **Schedule** | On-call rotation defining who is available when |
| **Business Service** | High-level service representing business capability |
| **Technical Service** | Lower-level service representing infrastructure component |
| **Conference Bridge** | PagerDuty incident field that stores the Slack channel URL after workflow execution |
| **Demo Controller** | The `demo-simulator-controller` Lambda — primary scenario execution engine |
| **Workflow Trigger** | Condition that causes an Incident Workflow to fire (e.g., title contains `[DEMO]`) |
| **Slack Connection** | PagerDuty-side integration that enables Incident Workflows to create Slack channels |

---

## Related Documentation

- [NEXT_DEVELOPER_PROMPT.md](./NEXT_DEVELOPER_PROMPT.md) - Developer handover guide (start here)
- [GOTCHAS_AND_WORKAROUNDS.md](./GOTCHAS_AND_WORKAROUNDS.md) - Known issues and workarounds
- [SCENARIO_FLOWS.md](./SCENARIO_FLOWS.md) - Detailed scenario flows
- [ARCHITECTURE_BLUEPRINT.md](./ARCHITECTURE_BLUEPRINT.md) - Architecture with status tracking
- [E2E_TEST_DOCUMENTATION.md](./E2E_TEST_DOCUMENTATION.md) - E2E test results
- [setup/DEPLOYMENT.md](./setup/DEPLOYMENT.md) - Deployment guide with terraform procedures
