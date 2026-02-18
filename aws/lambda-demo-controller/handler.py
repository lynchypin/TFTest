#!/usr/bin/env python3
import os
import json
import time
import random
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import boto3

from shared import (
    PagerDutyClient, SlackClient, SlackNotifier,
    DEMO_USERS, PAGERDUTY_TO_SLACK_USER_MAP,
    CONALL_EMAIL, CONALL_SLACK_USER_ID, CONALL_SLACK_USER_ID_PERSONAL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.getLogger().setLevel(logging.INFO)

SCENARIOS_FILE = os.environ.get('SCENARIOS_FILE', '/var/task/scenarios.json')
DEFAULT_ACTION_DELAY_MIN = int(os.environ.get('ACTION_DELAY_MIN', 15))
DEFAULT_ACTION_DELAY_MAX = int(os.environ.get('ACTION_DELAY_MAX', 30))
SSM_RECENT_SCENARIOS_PARAM = os.environ.get('SSM_RECENT_SCENARIOS_PARAM', '/demo-simulator/recent-scenarios')
RECENT_SCENARIO_LIMIT = 10

SERVICE_TO_ROUTING_KEY = {
    "Platform - DBRE": os.getenv("ROUTING_KEY_DBRE", ""),
    "Database - DBRE Team": os.getenv("ROUTING_KEY_DBRE", ""),
    "Platform - Kubernetes/Platform": os.getenv("ROUTING_KEY_K8S", ""),
    "App - Backend API": os.getenv("ROUTING_KEY_API", ""),
    "App - Orders API Team": os.getenv("ROUTING_KEY_API", ""),
    "App - Checkout Team": os.getenv("ROUTING_KEY_API", ""),
    "Platform - Networking": os.getenv("ROUTING_KEY_K8S", ""),
    "Platform - Network": os.getenv("ROUTING_KEY_K8S", ""),
    "SecOps": os.getenv("ROUTING_KEY_K8S", ""),
    "OT Operations - Factory Floor": os.getenv("ROUTING_KEY_K8S", ""),
    "Payments Ops": os.getenv("ROUTING_KEY_API", ""),
}

CONVERSATION_LIBRARY = {
    "database": [
        "Just got paged - pulling up the monitoring dashboards now",
        "Seeing elevated query latency across the primary",
        "Connection pool looks saturated, let me check the app side",
        "Running SHOW PROCESSLIST to identify slow queries",
        "Found a runaway query from the analytics job - killing it",
        "Replication lag is spiking, checking binary log positions",
        "Primary CPU is pegged at 98%, likely the bulk import job",
        "Failover to replica completed successfully",
        "Verifying all app connections have reconnected",
    ],
    "kubernetes": [
        "Checking pod status across affected namespace",
        "OOMKilled events on several pods - checking resource limits",
        "Running kubectl describe on the crashlooping pods",
        "HPA is maxed out but still can't meet demand",
        "Node pressure detected - cordoning problematic nodes",
        "Rolling restart of the deployment in progress",
        "PVC stuck in Pending - checking storage class",
        "Service mesh sidecar injection failed on new pods",
        "Ingress controller logs show 502s to backend",
    ],
    "api": [
        "API latency p99 jumped from 200ms to 3s",
        "Checking upstream dependencies for bottlenecks",
        "Rate limiter tripped - legit traffic spike or attack?",
        "Circuit breaker opened to downstream payment service",
        "Retrying failed requests manually to isolate the issue",
        "Cache miss rate spiked - Redis cluster healthy?",
        "Feature flag rollout causing increased load - rolling back",
        "Memory leak in latest deploy - reverting to previous build",
        "Load balancer health checks passing but users still timing out",
    ],
    "security": [
        "Analyzing suspicious login patterns from multiple geos",
        "Blocking IP range associated with the brute force attempts",
        "Rotating compromised API keys as a precaution",
        "Running audit log export for forensics",
        "WAF rules updated to block the attack vector",
        "No evidence of data exfiltration in initial analysis",
        "Credential stuffing attack mitigated - monitoring continues",
        "Suspicious outbound traffic - isolating affected hosts",
        "MFA bypass attempt detected and blocked",
    ],
    "network": [
        "Packet loss between us-east and us-west regions",
        "BGP route flap causing intermittent connectivity",
        "DNS resolution failures to external dependencies",
        "MTU mismatch causing fragmentation issues",
        "VPN tunnel to partner datacenter is down",
        "Load balancer draining but not removing unhealthy targets",
        "CDN cache purge in progress for affected assets",
        "Firewall rule change caused unintended traffic drop",
        "NAT gateway capacity exceeded - spinning up additional",
    ],
    "general": [
        "Looking into this now, will update shortly",
        "Confirming scope of impact - checking all affected services",
        "Customer support reports increase in tickets related to this",
        "Looping in the on-call manager for visibility",
        "Drafting customer communication while we investigate",
        "This might be related to the change deployed at 14:30 UTC",
        "Rollback in progress, ETA 5 minutes",
        "Mitigation applied, monitoring for recovery",
        "Systems recovering, will keep monitoring for 15 more minutes",
    ],
}

ACTION_TYPES = [
    "status_update",
    "add_note",
    "run_automation",
    "trigger_workflow",
    "change_priority",
    "change_urgency",
    "add_subscriber",
    "escalate",
]


class DemoState(Enum):
    IDLE = "idle"
    RESETTING = "resetting"
    TRIGGERING = "triggering"
    WAITING_ACK = "waiting_ack"
    INVESTIGATING = "investigating"
    PROGRESSING = "progressing"
    RESOLVING = "resolving"
    COMPLETED = "completed"
    PAUSED = "paused"


_demo_state = {
    "state": DemoState.IDLE.value,
    "scenario_id": None,
    "incident_id": None,
    "dedup_key": None,
    "channel_id": None,
    "current_step": 0,
    "total_steps": 0,
    "paused": False,
    "started_at": None,
    "actions_taken": [],
    "responders": [],
}


DEFAULT_INTER_SCENARIO_DELAY = int(os.environ.get('INTER_SCENARIO_DELAY', 30))

PLAYLISTS = {
    "quick_overview": {
        "name": "Quick Overview (3 scenarios)",
        "description": "Fast tour of core PagerDuty capabilities: routing, Slack integration, and automation.",
        "scenario_ids": ["FREE-001", "BUS-002", "AUTO-001"],
    },
    "sales_executive": {
        "name": "Executive Sales Demo (5 scenarios)",
        "description": "High-impact demo for executive buyers: incident routing, Slack channels, Jira integration, status pages, and AIOps correlation.",
        "scenario_ids": ["PRO-001", "BUS-002", "PRO-003", "CSO-001", "SRE-004"],
    },
    "platform_engineering": {
        "name": "Platform Engineering (5 scenarios)",
        "description": "Kubernetes-focused: alert routing, response mobilization, automated diagnostics, workflows, and correlation.",
        "scenario_ids": ["FREE-001", "BUS-001", "AUTO-001", "WF-002", "SRE-004"],
    },
    "full_lifecycle": {
        "name": "Full Incident Lifecycle (4 scenarios)",
        "description": "End-to-end incident management: trigger, acknowledge, investigate with Slack + Jira, resolve, and post-incident review.",
        "scenario_ids": ["PRO-001", "BUS-002", "PRO-003", "PRO-002"],
    },
    "automation_showcase": {
        "name": "Automation Showcase (4 scenarios)",
        "description": "Automation capabilities: diagnostics, remediation, runbook integration, and advanced workflows.",
        "scenario_ids": ["AUTO-001", "AUTO-002", "AUTO-003", "WF-003"],
    },
    "industry_verticals": {
        "name": "Industry Verticals (5 scenarios)",
        "description": "Cross-industry demo: manufacturing, mining safety, retail POS, fintech payments, and healthcare.",
        "scenario_ids": ["IND-001", "IND-002", "IND-003", "IND-004", "IND-007"],
    },
    "enterprise_features": {
        "name": "Enterprise Features (6 scenarios)",
        "description": "Enterprise-grade capabilities: response mobilizer, service graph, stakeholder updates, custom fields, status page, and AIOps.",
        "scenario_ids": ["BUS-001", "BUS-003", "BUS-005", "BUS-007", "CSO-001", "SRE-004"],
    },
    "aiops_intelligence": {
        "name": "AIOps & Intelligence (3 scenarios)",
        "description": "AI-powered operations: multi-service correlation, learning from past incidents, and advanced workflows.",
        "scenario_ids": ["SRE-004", "SRE-006", "WF-003"],
    },
}


def load_scenarios() -> Dict:
    try:
        with open(SCENARIOS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        scenarios_alt = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'demo-scenarios', 'src', 'data', 'scenarios.json')
        try:
            with open(scenarios_alt, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load scenarios: {e}")
            return {"scenarios": []}


def get_scenario_by_id(scenario_id: str, scenarios_data: Dict) -> Optional[Dict]:
    for scenario in scenarios_data.get("scenarios", []):
        if scenario.get("id") == scenario_id:
            return scenario
    return None


def determine_responder_count() -> int:
    roll = random.random() * 100
    if roll < 3:
        return 4
    elif roll < 10:
        return 3
    elif roll < 35:
        return 2
    return 1


def select_responders(count: int, primary_email: str = None) -> List[Dict]:
    available = [u for u in DEMO_USERS if u.get('email') != CONALL_EMAIL]
    if primary_email:
        primary = next((u for u in available if u.get('email') == primary_email), None)
        if primary:
            available.remove(primary)
            selected = [primary]
            if count > 1:
                selected.extend(random.sample(available, min(count - 1, len(available))))
            return selected
    return random.sample(available, min(count, len(available)))


def select_resolver(responders: List[Dict]) -> Dict:
    return random.choice(responders)


def get_conversation_category(scenario: Dict) -> str:
    service = scenario.get("target_service", "").lower()
    if any(x in service for x in ["database", "dbre", "postgres", "mysql"]):
        return "database"
    elif any(x in service for x in ["kubernetes", "k8s", "platform", "container"]):
        return "kubernetes"
    elif any(x in service for x in ["api", "backend", "checkout", "orders"]):
        return "api"
    elif any(x in service for x in ["security", "secops", "soc"]):
        return "security"
    elif any(x in service for x in ["network", "dns", "cdn"]):
        return "network"
    return "general"


def get_conversation_message(category: str, used_messages: set) -> str:
    messages = CONVERSATION_LIBRARY.get(category, CONVERSATION_LIBRARY["general"])
    available = [m for m in messages if m not in used_messages]
    if not available:
        available = messages
    message = random.choice(available)
    used_messages.add(message)
    return message


def reset_demo_incidents(pd: PagerDutyClient) -> Dict[str, Any]:
    logger.info("Resetting all [DEMO] incidents...")
    results = {"resolved": [], "failed": []}
    
    demo_incidents = pd.get_demo_incidents(statuses=['triggered', 'acknowledged'])
    logger.info(f"Found {len(demo_incidents)} [DEMO] incidents to resolve")
    
    for incident in demo_incidents:
        incident_id = incident['id']
        result = pd.resolve_incident(incident_id, CONALL_EMAIL)
        if result.get('success'):
            results["resolved"].append(incident_id)
            logger.info(f"Resolved demo incident {incident_id}")
        else:
            results["failed"].append(incident_id)
            logger.error(f"Failed to resolve incident {incident_id}: {result}")
    
    return results


def trigger_scenario(pd: PagerDutyClient, scenario: Dict) -> Dict[str, Any]:
    payload = scenario.get("payload", {})
    inner_payload = payload.get("payload", payload)
    
    pd_service = inner_payload.get("custom_details", {}).get("pd_service", scenario.get("target_service", ""))
    routing_key = SERVICE_TO_ROUTING_KEY.get(pd_service)
    
    if not routing_key:
        routing_key = os.getenv("ROUTING_KEY_K8S", "")
        logger.warning(f"No routing key for service '{pd_service}', using default K8S key")
    
    summary = inner_payload.get("summary", scenario.get("description", "Demo incident"))
    severity = inner_payload.get("severity", scenario.get("severity", "warning"))
    source = inner_payload.get("source", "demo-controller")
    
    dedup_key = f"demo-{scenario['id']}-{int(time.time())}"
    
    custom_details = inner_payload.get("custom_details", {}).copy()
    custom_details["scenario_id"] = scenario["id"]
    custom_details["scenario_name"] = scenario.get("name", "")
    custom_details["triggered_by"] = "demo-controller"
    custom_details["features_demonstrated"] = scenario.get("features_demonstrated", [])
    
    result = pd.trigger_incident(
        routing_key=routing_key,
        summary=summary,
        severity=severity,
        source=source,
        dedup_key=dedup_key,
        custom_details=custom_details,
    )
    
    return {
        "success": result.get("success", False),
        "scenario_id": scenario["id"],
        "scenario_name": scenario.get("name"),
        "dedup_key": dedup_key,
        "routing_key": routing_key,
        "pd_service": pd_service,
        "response": result,
    }


def wait_for_incident(pd: PagerDutyClient, dedup_key: str, timeout_seconds: int = 30) -> Optional[Dict]:
    start = time.time()
    while time.time() - start < timeout_seconds:
        incidents = pd.list_recent_incidents(minutes=5)
        for inc in incidents:
            title = inc.get("title", "")
            if dedup_key in title or "[DEMO]" in title:
                alerts = inc.get("alerts", [])
                for alert in alerts:
                    if alert.get("alert_key") == dedup_key:
                        return inc
                custom_details = inc.get("body", {}).get("details", {})
                if custom_details.get("scenario_id") and dedup_key.startswith(f"demo-{custom_details['scenario_id']}"):
                    return inc
        time.sleep(2)
    return None


def get_random_delay(min_delay: int = None, max_delay: int = None) -> int:
    return random.randint(
        min_delay or DEFAULT_ACTION_DELAY_MIN,
        max_delay or DEFAULT_ACTION_DELAY_MAX
    )


def extract_channel_id_from_url(url: str) -> Optional[str]:
    import re
    match = re.search(r'/archives/([A-Z0-9]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'channel=([A-Z0-9]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'(C[A-Z0-9]{8,})', url)
    if match:
        return match.group(1)
    return None


def wait_for_incident_channel(pd: PagerDutyClient, slack: SlackClient, incident: Dict, timeout_seconds: int = 90, poll_interval: int = 5) -> Dict[str, Any]:
    incident_id = incident.get("id")
    number = incident.get("incident_number", "0")

    logger.info(f"Waiting for PD workflow to create Slack channel for incident {number}...")
    start = time.time()

    while time.time() - start < timeout_seconds:
        inc_data = pd.get_incident(incident_id, include=['conference_bridge'])
        if inc_data:
            cb = inc_data.get('conference_bridge')
            if cb:
                conf_url = cb.get('conference_url') or cb.get('url') or ''
                if conf_url and 'slack' in conf_url.lower():
                    channel_id = extract_channel_id_from_url(conf_url)
                    if channel_id:
                        slack.join_channel(channel_id)
                        channel_info = slack.get_channel_info(channel_id)
                        channel_name = channel_info.get('name', 'unknown') if channel_info else 'unknown'
                        logger.info(f"Found channel via conference_bridge: {channel_name} ({channel_id})")
                        return {"success": True, "channel_id": channel_id, "channel_name": channel_name, "created_by": "pd_workflow"}

        channel_id = slack.find_channel_by_pattern(f"^demo-{number}-")
        if channel_id:
            slack.join_channel(channel_id)
            channel_info = slack.get_channel_info(channel_id)
            channel_name = channel_info.get('name', 'unknown') if channel_info else 'unknown'
            logger.info(f"Found channel via pattern search: {channel_name} ({channel_id})")
            return {"success": True, "channel_id": channel_id, "channel_name": channel_name, "created_by": "pd_workflow"}

        time.sleep(poll_interval)

    logger.warning(f"Timeout waiting for PD workflow to create channel for incident {number}")
    return {"success": False, "error": "timeout_waiting_for_channel", "incident_number": number}


def invite_responders_to_slack_channel(slack: SlackClient, channel_id: str, responders: List[Dict],
                                        observer_slack_ids: List[str] = None) -> Dict[str, Any]:
    if observer_slack_ids is None:
        observer_slack_ids = [CONALL_SLACK_USER_ID_PERSONAL, CONALL_SLACK_USER_ID]

    invited = []
    failed = []

    for obs_id in observer_slack_ids:
        observer_result = slack.invite_user_to_channel(channel_id, obs_id)
        if observer_result.get('ok') or observer_result.get('error') == 'already_in_channel':
            invited.append(f"Observer ({obs_id[:6]}...)")
            logger.info(f"Added observer {obs_id} to Slack channel {channel_id}")
        else:
            logger.warning(f"Failed to add observer {obs_id} to channel: {observer_result.get('error')}")
            failed.append(f"Observer ({obs_id[:6]}...)")

    return {"invited": invited, "failed": failed}


def perform_action(pd: PagerDutyClient, slack: SlackClient, incident_id: str, channel_id: str,
                   responder: Dict, action_type: str, scenario: Dict, used_messages: set) -> Dict[str, Any]:
    category = get_conversation_category(scenario)
    result = {"action": action_type, "user": responder['name'], "success": False}

    if action_type == "status_update":
        message = get_conversation_message(category, used_messages)
        pd_result = pd.post_status_update(incident_id, message, responder['email'])
        result["success"] = pd_result.get('success', False)
        result["message"] = message
        if channel_id:
            slack.post_as_user(f":mega: *{responder['name']}* posted status update:\n_{message}_", responder, channel_id)

    elif action_type == "add_note":
        message = get_conversation_message(category, used_messages)
        pd_result = pd.add_note(incident_id, message, responder['email'])
        result["success"] = pd_result.get('success', False)
        result["message"] = message
        if channel_id:
            slack.post_as_user(f":memo: *{responder['name']}*: {message}", responder, channel_id)

    elif action_type == "run_automation":
        automations = pd.list_automation_actions()
        if automations:
            action = random.choice(automations)
            pd_result = pd.run_automation_action(action['id'], incident_id, responder['email'])
            result["success"] = pd_result.get('success', False)
            result["automation"] = action.get('name', action['id'])
            if channel_id:
                slack.post_as_user(f":robot_face: *{responder['name']}* triggered automation: {action.get('name', 'Unknown')}", responder, channel_id)
        else:
            message = "Ran diagnostic automation - results in notes"
            pd.add_note(incident_id, message, responder['email'])
            result["success"] = True
            result["message"] = message

    elif action_type == "trigger_workflow":
        workflows = pd.list_workflows()
        if workflows:
            workflow = random.choice(workflows)
            pd_result = pd.trigger_workflow(workflow['id'], incident_id, responder['email'])
            result["success"] = pd_result.get('success', False)
            result["workflow"] = workflow.get('name', workflow['id'])
            if channel_id:
                slack.post_as_user(f":gear: *{responder['name']}* triggered workflow: {workflow.get('name', 'Unknown')}", responder, channel_id)
        else:
            result["success"] = True
            result["message"] = "No workflows available"

    elif action_type == "change_priority":
        priorities = pd.list_priorities()
        if priorities:
            priority = random.choice(priorities)
            pd_result = pd.change_priority(incident_id, priority['id'], responder['email'])
            result["success"] = pd_result.get('success', False)
            result["priority"] = priority.get('name', priority['id'])
            if channel_id:
                slack.post_as_user(f":arrow_up_down: *{responder['name']}* changed priority to {priority.get('name', 'Unknown')}", responder, channel_id)
        else:
            result["success"] = True

    elif action_type == "change_urgency":
        urgency = random.choice(["high", "low"])
        pd_result = pd.update_urgency(incident_id, urgency, responder['email'])
        result["success"] = pd_result.get('success', False)
        result["urgency"] = urgency
        if channel_id:
            slack.post_as_user(f":bell: *{responder['name']}* changed urgency to {urgency}", responder, channel_id)

    elif action_type == "add_subscriber":
        manager = random.choice([u for u in DEMO_USERS if u != responder])
        pd_result = pd.add_subscriber(incident_id, manager['id'], 'user', responder['email'])
        result["success"] = pd_result.get('success', False)
        result["subscriber"] = manager['name']
        if channel_id:
            slack.post_as_user(f":eyes: *{responder['name']}* added {manager['name']} as subscriber for visibility", responder, channel_id)

    elif action_type == "escalate":
        pd_result = pd.escalate_incident(incident_id, 2, responder['email'])
        result["success"] = pd_result.get('success', False)
        if channel_id:
            slack.post_as_user(f":arrow_double_up: *{responder['name']}* escalated the incident", responder, channel_id)

    return result


def run_responder_actions(pd: PagerDutyClient, slack: SlackClient, incident_id: str, channel_id: str,
                          responders: List[Dict], scenario: Dict, delay_func) -> List[Dict]:
    actions_taken = []
    used_messages = set()
    responder_actions = {r['id']: [] for r in responders}
    
    total_actions = random.randint(3, 7)
    actions_per_responder = max(1, total_actions // len(responders))
    
    for i in range(total_actions):
        available_responders = [r for r in responders if len(responder_actions[r['id']]) < actions_per_responder + 1]
        if not available_responders:
            available_responders = responders
        
        responder = random.choice(available_responders)
        action_type = random.choice(ACTION_TYPES)
        
        if i == 0:
            action_type = "add_note"
        
        time.sleep(delay_func())
        
        result = perform_action(pd, slack, incident_id, channel_id, responder, action_type, scenario, used_messages)
        actions_taken.append(result)
        responder_actions[responder['id']].append(result)
        
        logger.info(f"Action {i+1}/{total_actions}: {result.get('action')} by {result.get('user')} - success={result.get('success')}")
    
    for responder in responders:
        if not responder_actions[responder['id']]:
            time.sleep(delay_func())
            result = perform_action(pd, slack, incident_id, channel_id, responder, "add_note", scenario, used_messages)
            actions_taken.append(result)
            logger.info(f"Ensuring action by {responder['name']}: {result.get('action')} - success={result.get('success')}")
    
    return actions_taken


def acknowledge_incident(pd: PagerDutyClient, slack: SlackClient, incident_id: str, channel_id: str, responder: Dict) -> Dict[str, Any]:
    result = pd.acknowledge_incident(incident_id, responder['email'])
    if channel_id:
        slack.post_as_user(f":white_check_mark: *{responder['name']}* acknowledged the incident", responder, channel_id)
    return {
        "action": "acknowledge",
        "user": responder['name'],
        "email": responder['email'],
        "success": result.get('success', False),
    }


def resolve_incident(pd: PagerDutyClient, slack: SlackClient, incident_id: str, channel_id: str,
                     responder: Dict, scenario: Dict, trigger_result: Dict) -> Dict[str, Any]:
    orchestration_trace = scenario.get("orchestration_trace", [])

    if orchestration_trace:
        last_stage = orchestration_trace[-1] if orchestration_trace else {}
        note = f"[Resolution] {last_stage.get('result', last_stage.get('action', 'Issue resolved.'))}"
    else:
        note = "Root cause identified and fixed. Incident resolved."

    pd.add_note(incident_id, note, responder['email'])

    routing_key = trigger_result.get("routing_key")
    dedup_key = trigger_result.get("dedup_key")
    if routing_key and dedup_key:
        pd.resolve_via_events_api(routing_key, dedup_key)

    result = pd.resolve_incident(incident_id, responder['email'])
    if not result.get('success'):
        logger.error(f"Failed to resolve incident {incident_id} as {responder['email']}: status={result.get('status_code')}, error={result.get('error')}")
        time.sleep(3)
        result = pd.resolve_incident(incident_id, responder['email'])
        if not result.get('success'):
            logger.error(f"Retry failed to resolve incident {incident_id}: status={result.get('status_code')}, error={result.get('error')}")

    if channel_id:
        resolve_post = slack.post_as_user(f":tada: *{responder['name']}*: {note}\n\n:white_check_mark: Incident resolved!", responder, channel_id)
        if not resolve_post.get('ok'):
            logger.error(f"Failed to post resolve message to Slack: {resolve_post.get('error')}")

    return {
        "action": "resolve",
        "user": responder['name'],
        "note": note,
        "success": result.get('success', False),
    }


def run_demo_flow(scenario_id: str, action_delay: int = None) -> Dict[str, Any]:
    global _demo_state

    pd = PagerDutyClient()
    slack = SlackClient()

    slack_health = slack.verify_token()
    if not slack_health.get('ok'):
        logger.error(f"SLACK TOKEN INVALID: {slack_health.get('error', 'unknown')} - all Slack operations will fail")
    else:
        logger.info(f"Slack token valid: team={slack_health.get('team')}, user={slack_health.get('user')}")

    delay_func = lambda: action_delay if action_delay else get_random_delay()

    results = {
        "scenario_id": scenario_id,
        "steps": [],
        "success": False,
        "incident_id": None,
        "channel_id": None,
        "responders": [],
    }

    scenarios_data = load_scenarios()
    scenario = get_scenario_by_id(scenario_id, scenarios_data)

    if not scenario:
        logger.error(f"Scenario {scenario_id} not found")
        return {"error": f"Scenario {scenario_id} not found", "success": False}

    _demo_state["state"] = DemoState.RESETTING.value
    _demo_state["scenario_id"] = scenario_id
    _demo_state["started_at"] = datetime.now(timezone.utc).isoformat()

    reset_result = reset_demo_incidents(pd)
    results["steps"].append({"step": "reset", "result": reset_result})
    logger.info(f"Reset complete: {len(reset_result['resolved'])} incidents resolved")

    if _demo_state.get("paused"):
        return {"status": "paused", "steps": results["steps"]}

    time.sleep(5)

    _demo_state["state"] = DemoState.TRIGGERING.value
    trigger_result = trigger_scenario(pd, scenario)
    results["steps"].append({"step": "trigger", "result": trigger_result})

    if not trigger_result.get("success"):
        logger.error(f"Failed to trigger scenario: {trigger_result}")
        return {"error": "Failed to trigger scenario", "steps": results["steps"], "success": False}

    _demo_state["dedup_key"] = trigger_result["dedup_key"]
    logger.info(f"Triggered scenario {scenario_id}, waiting for incident...")

    time.sleep(delay_func())

    _demo_state["state"] = DemoState.WAITING_ACK.value
    incident = wait_for_incident(pd, trigger_result["dedup_key"])

    if not incident:
        logger.warning("Incident not found after trigger, checking for any recent demo incidents...")
        recent = pd.list_recent_incidents(minutes=5)
        demo_incidents = [i for i in recent if "[DEMO]" in i.get("title", "")]
        if demo_incidents:
            incident = demo_incidents[0]

    if not incident:
        logger.error("Failed to find triggered incident")
        return {"error": "Incident not found", "steps": results["steps"], "success": False}

    incident_id = incident["id"]
    _demo_state["incident_id"] = incident_id
    results["incident_id"] = incident_id
    logger.info(f"Found incident {incident_id}")

    responder_count = determine_responder_count()
    responders = select_responders(responder_count)
    _demo_state["responders"] = [r['name'] for r in responders]
    results["responders"] = [r['name'] for r in responders]
    logger.info(f"Selected {len(responders)} responders: {[r['name'] for r in responders]}")

    if _demo_state.get("paused"):
        return {"status": "paused", "incident_id": incident_id, "steps": results["steps"]}

    primary_responder = responders[0]
    ack_result = acknowledge_incident(pd, slack, incident_id, None, primary_responder)
    results["steps"].append({"step": "acknowledge", "result": ack_result})
    logger.info(f"Acknowledged by {ack_result.get('user')} - this triggers PD workflow to create Slack channel")

    time.sleep(3)

    channel_result = wait_for_incident_channel(pd, slack, incident, timeout_seconds=90, poll_interval=5)
    results["steps"].append({"step": "wait_for_channel", "result": channel_result})
    channel_id = channel_result.get("channel_id")
    _demo_state["channel_id"] = channel_id
    results["channel_id"] = channel_id

    if channel_id:
        logger.info(f"Channel created by PD workflow, adding users via Slack API...")
        invite_result = invite_responders_to_slack_channel(slack, channel_id, [primary_responder])
        results["steps"].append({"step": "invite_primary_responder", "result": invite_result})
        if invite_result.get('failed'):
            logger.error(f"Failed to invite some users to Slack channel: {invite_result['failed']}")
        logger.info(f"Added to Slack channel: {invite_result['invited']}")

        ack_post = slack.post_as_user(f":white_check_mark: *{primary_responder['name']}* acknowledged the incident", primary_responder, channel_id)
        if not ack_post.get('ok'):
            logger.error(f"Failed to post ack message to Slack: {ack_post.get('error')}")
    else:
        logger.warning("No Slack channel found - continuing without Slack integration")

    if len(responders) > 1:
        additional = responders[1:]
        add_result = pd.add_responders(incident_id, [r['id'] for r in additional], primary_responder['email'])
        results["steps"].append({"step": "add_responders_to_pd", "result": {"added": [r['name'] for r in additional], "success": add_result.get('success')}})
        logger.info(f"Added {len(additional)} additional responders to PD incident")

        if channel_id:
            for resp in additional:
                slack_id = resp.get('slack_id') or PAGERDUTY_TO_SLACK_USER_MAP.get(resp.get('email'))
                if slack_id:
                    inv_result = slack.invite_user_to_channel(channel_id, slack_id)
                    if inv_result.get('ok') or inv_result.get('error') == 'already_in_channel':
                        logger.info(f"Added {resp['name']} to Slack channel via Slack API")
                    else:
                        logger.error(f"Failed to invite {resp['name']} to Slack channel: {inv_result.get('error')}")

            names = ", ".join([r['name'] for r in additional])
            slack.post_as_user(f":busts_in_silhouette: *{primary_responder['name']}* requested help from {names}", primary_responder, channel_id)

    if _demo_state.get("paused"):
        return {"status": "paused", "incident_id": incident_id, "channel_id": channel_id, "steps": results["steps"]}

    time.sleep(delay_func())

    _demo_state["state"] = DemoState.INVESTIGATING.value

    actions = run_responder_actions(pd, slack, incident_id, channel_id, responders, scenario, delay_func)
    results["steps"].append({"step": "responder_actions", "result": {"actions": actions, "count": len(actions)}})

    if _demo_state.get("paused"):
        return {"status": "paused", "incident_id": incident_id, "channel_id": channel_id, "steps": results["steps"]}

    _demo_state["state"] = DemoState.RESOLVING.value

    resolver = select_resolver(responders)
    time.sleep(delay_func())

    resolve_result = resolve_incident(pd, slack, incident_id, channel_id, resolver, scenario, trigger_result)
    results["steps"].append({"step": "resolve", "result": resolve_result})

    _demo_state["state"] = DemoState.COMPLETED.value
    results["success"] = True
    results["resolver"] = resolver['name']

    logger.info(f"Demo flow completed for scenario {scenario_id}, resolved by {resolver['name']}")
    return results


def pause_demo() -> Dict[str, Any]:
    global _demo_state
    _demo_state["paused"] = True
    _demo_state["state"] = DemoState.PAUSED.value
    return {"status": "paused", "state": _demo_state}


def resume_demo() -> Dict[str, Any]:
    global _demo_state
    _demo_state["paused"] = False
    return {"status": "resumed", "state": _demo_state}


def get_demo_status() -> Dict[str, Any]:
    global _demo_state
    return {"state": _demo_state}


def list_available_scenarios() -> List[Dict]:
    scenarios_data = load_scenarios()
    return [
        {
            "id": s.get("id"),
            "name": s.get("name"),
            "description": s.get("description"),
            "severity": s.get("severity"),
            "target_service": s.get("target_service"),
            "features_demonstrated": s.get("features_demonstrated", []),
        }
        for s in scenarios_data.get("scenarios", [])
    ]


def run_playlist(playlist_key: str = None, scenario_ids: List[str] = None,
                 action_delay: int = None, inter_scenario_delay: int = None) -> Dict[str, Any]:
    global _demo_state

    if not scenario_ids:
        if not playlist_key or playlist_key not in PLAYLISTS:
            return {"error": f"Unknown playlist: {playlist_key}. Use list_playlists to see available options.", "success": False}
        playlist = PLAYLISTS[playlist_key]
        scenario_ids = playlist["scenario_ids"]
        playlist_name = playlist["name"]
    else:
        playlist_name = f"Custom playlist ({len(scenario_ids)} scenarios)"

    if inter_scenario_delay is None:
        inter_scenario_delay = DEFAULT_INTER_SCENARIO_DELAY

    scenarios_data = load_scenarios()
    valid_ids = []
    for sid in scenario_ids:
        scenario = get_scenario_by_id(sid, scenarios_data)
        if not scenario:
            logger.warning(f"Playlist scenario {sid} not found, skipping")
            continue
        if not scenario.get("enabled", True):
            logger.warning(f"Playlist scenario {sid} is disabled, skipping")
            continue
        valid_ids.append(sid)

    if not valid_ids:
        return {"error": "No valid enabled scenarios in playlist", "success": False}

    playlist_results = {
        "playlist": playlist_name,
        "playlist_key": playlist_key,
        "requested_scenarios": scenario_ids,
        "valid_scenarios": valid_ids,
        "skipped_scenarios": [s for s in scenario_ids if s not in valid_ids],
        "scenario_results": [],
        "success": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "total": len(valid_ids),
        "passed": 0,
        "failed": 0,
    }

    logger.info(f"Starting playlist '{playlist_name}' with {len(valid_ids)} scenarios: {valid_ids}")

    for idx, sid in enumerate(valid_ids):
        if _demo_state.get("paused"):
            logger.info(f"Playlist paused before scenario {idx + 1}/{len(valid_ids)}: {sid}")
            playlist_results["scenario_results"].append({"scenario_id": sid, "status": "skipped_paused"})
            break

        logger.info(f"Playlist scenario {idx + 1}/{len(valid_ids)}: {sid}")

        result = run_demo_flow(sid, action_delay)
        scenario_success = result.get("success", False)

        playlist_results["scenario_results"].append({
            "scenario_id": sid,
            "index": idx + 1,
            "success": scenario_success,
            "incident_id": result.get("incident_id"),
            "resolver": result.get("resolver"),
            "error": result.get("error"),
        })

        if scenario_success:
            playlist_results["passed"] += 1
        else:
            playlist_results["failed"] += 1

        if idx < len(valid_ids) - 1 and not _demo_state.get("paused"):
            logger.info(f"Waiting {inter_scenario_delay}s before next scenario...")
            time.sleep(inter_scenario_delay)

    playlist_results["completed_at"] = datetime.now(timezone.utc).isoformat()
    playlist_results["success"] = playlist_results["failed"] == 0 and playlist_results["passed"] == len(valid_ids)

    logger.info(f"Playlist '{playlist_name}' complete: {playlist_results['passed']}/{len(valid_ids)} passed")
    return playlist_results


def list_playlists() -> List[Dict]:
    return [
        {
            "key": key,
            "name": p["name"],
            "description": p["description"],
            "scenario_ids": p["scenario_ids"],
            "scenario_count": len(p["scenario_ids"]),
        }
        for key, p in PLAYLISTS.items()
    ]


def _get_recent_scenarios() -> List[str]:
    try:
        ssm = boto3.client("ssm")
        resp = ssm.get_parameter(Name=SSM_RECENT_SCENARIOS_PARAM)
        return json.loads(resp["Parameter"]["Value"])
    except ssm.exceptions.ParameterNotFound:
        return []
    except Exception as e:
        logger.warning(f"Failed to read recent scenarios from SSM: {e}")
        return []


def _save_recent_scenarios(recent: List[str]) -> None:
    try:
        ssm = boto3.client("ssm")
        ssm.put_parameter(
            Name=SSM_RECENT_SCENARIOS_PARAM,
            Value=json.dumps(recent[-RECENT_SCENARIO_LIMIT:]),
            Type="String",
            Overwrite=True,
        )
    except Exception as e:
        logger.warning(f"Failed to save recent scenarios to SSM: {e}")


def run_random_scenario(action_delay: int = None) -> Dict[str, Any]:
    scenarios_data = load_scenarios()
    enabled = [s for s in scenarios_data.get("scenarios", []) if s.get("enabled", True)]
    if not enabled:
        return {"error": "No enabled scenarios found", "success": False}
    recent = _get_recent_scenarios()
    candidates = [s for s in enabled if s["id"] not in recent]
    if not candidates:
        logger.info("All enabled scenarios recently run, resetting history")
        candidates = enabled
        recent = []
    scenario = random.choice(candidates)
    logger.info(f"Randomly selected scenario: {scenario['id']} - {scenario.get('name', '')} (skipped {len(recent)} recent)")
    recent.append(scenario["id"])
    _save_recent_scenarios(recent)
    return run_demo_flow(scenario["id"], action_delay)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info(f"Demo Controller invoked with event: {json.dumps(event)}")
    
    action = event.get("action", "run")
    
    if action == "run":
        scenario_id = event.get("scenario_id")
        if not scenario_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "scenario_id is required"})
            }
        delay = event.get("action_delay")
        result = run_demo_flow(scenario_id, delay)
        return {
            "statusCode": 200 if result.get("success") else 500,
            "body": json.dumps(result)
        }
    
    elif action == "pause":
        result = pause_demo()
        return {"statusCode": 200, "body": json.dumps(result)}
    
    elif action == "resume":
        result = resume_demo()
        return {"statusCode": 200, "body": json.dumps(result)}
    
    elif action == "status":
        result = get_demo_status()
        return {"statusCode": 200, "body": json.dumps(result)}
    
    elif action == "list_scenarios":
        scenarios = list_available_scenarios()
        return {"statusCode": 200, "body": json.dumps({"scenarios": scenarios})}
    
    elif action == "reset":
        pd = PagerDutyClient()
        result = reset_demo_incidents(pd)
        return {"statusCode": 200, "body": json.dumps(result)}

    elif action == "run_playlist":
        playlist_key = event.get("playlist")
        scenario_ids = event.get("scenario_ids")
        if not playlist_key and not scenario_ids:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "playlist or scenario_ids is required"})
            }
        delay = event.get("action_delay")
        inter_delay = event.get("inter_scenario_delay")
        result = run_playlist(playlist_key, scenario_ids, delay, inter_delay)
        return {
            "statusCode": 200 if result.get("success") else 500,
            "body": json.dumps(result)
        }

    elif action == "list_playlists":
        playlists = list_playlists()
        return {"statusCode": 200, "body": json.dumps({"playlists": playlists})}

    elif action == "run_random":
        delay = event.get("action_delay")
        result = run_random_scenario(delay)
        return {
            "statusCode": 200 if result.get("success") else 500,
            "body": json.dumps(result)
        }

    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown action: {action}"})
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../scripts/demo-simulator/.env")
    
    result = lambda_handler({"action": "list_scenarios"}, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
