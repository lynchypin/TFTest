#!/usr/bin/env python3
import os
import json
import random
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from shared import (
    PagerDutyClient, SlackClient, 
    DEMO_USERS, PAGERDUTY_TO_SLACK_USER_MAP, CONALL_SLACK_USER_ID
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROLE_EMOJIS = {
    "sre": ":firefighter:",
    "engineer": ":male-technologist:",
    "manager": ":briefcase:",
    "lead": ":star:",
    "admin": ":gear:",
    "devops": ":rocket:",
    "platform": ":building_construction:",
    "default": ":bust_in_silhouette:",
}

ACK_MESSAGES = [
    ("On it, pulling up dashboards now", ":eyes:"),
    ("Ack - I've got this. Checking metrics", ":saluting_face:"),
    ("Taking point on this one. Looking into it", ":point_right:"),
    ("Got the page. Investigating now", ":mag:"),
    ("I'm here. Starting triage", ":muscle:"),
]

INVESTIGATION_MESSAGES = [
    ("Seeing elevated error rates in the logs around {timestamp}. Checking if this correlates with the recent deploy.", ":chart_with_upwards_trend:"),
    ("Found some connection timeouts in the traces. Looks like it might be hitting the {component}.", ":hourglass:"),
    ("Metrics show a spike starting ~{minutes} mins ago. Checking what changed around that time.", ":bar_chart:"),
    ("CPU looks fine but memory is climbing on {service}. Could be a leak.", ":thermometer:"),
    ("Seeing 5xx errors from the upstream service. Going to check their status.", ":warning:"),
    ("Pulled the logs - there's a pattern here. Let me dig deeper.", ":magnifying_glass_tilted_left:"),
]

COLLABORATION_MESSAGES = [
    ("{name}, can you check the {component} logs while I look at traces?", ":handshake:"),
    ("@here heads up - this might be related to the {change} we pushed earlier", ":mega:"),
    ("Good catch {name}! That explains the {metric} spike", ":bulb:"),
    ("I'm seeing the same thing on my end. Definitely related to {component}", ":dart:"),
    ("Let me loop in {team} team - they have more context on this service", ":phone:"),
    ("Can someone check if {dependency} is healthy? Might be upstream", ":thinking_face:"),
]

PROGRESS_MESSAGES = [
    ("Update: Narrowed it down to the {component} layer. Working on a fix.", ":hammer_and_wrench:"),
    ("Making progress - found a suspicious pattern. {detail}", ":detective:"),
    ("Confirmed the issue. It's {root_cause}. Preparing a rollback.", ":white_check_mark:"),
    ("Deployed a temporary mitigation. Monitoring to see if error rates drop.", ":rocket:"),
    ("Mitigation is holding. Error rates coming down from {high}% to {low}%", ":chart_with_downwards_trend:"),
]

RESOLUTION_MESSAGES = [
    ("All clear! Root cause was {cause}. Metrics back to normal.", ":tada:"),
    ("Resolved - {cause}. Will schedule a post-mortem for tomorrow.", ":memo:"),
    ("Fixed! Error rates at baseline. Nice work everyone :raised_hands:", ":star2:"),
    ("Incident resolved. {cause}. Added monitoring to catch this earlier.", ":white_check_mark:"),
]

ESCALATION_MESSAGES = [
    ("This is beyond my expertise - escalating to {team} team for help.", ":arrow_up:"),
    ("Need additional eyes on this. Escalating to on-call lead.", ":rotating_light:"),
    ("Impact is broader than expected. Bringing in {team} for support.", ":sos:"),
    ("Escalating - this requires {team} team involvement to resolve.", ":loudspeaker:"),
    ("Can't make progress solo. Escalating to get more resources.", ":raising_hand:"),
]

SNOOZE_MESSAGES = [
    ("Snoozing for 10 minutes while we wait for the deploy to complete.", ":zzz:"),
    ("Putting this on hold - waiting on {team} team response.", ":pause_button:"),
    ("Snoozing briefly - need to gather more context from logs.", ":hourglass_flowing_sand:"),
]

ROOT_CAUSES = [
    "a connection pool exhaustion from slow queries hitting the replica",
    "a memory leak in the cache layer introduced in v2.3.1",
    "a misconfigured timeout after the config deployment",
    "an upstream dependency rate limiting us",
    "a retry storm from the mobile clients",
    "an expired certificate on the internal load balancer",
    "a deadlock in the connection handling code",
    "a DNS resolution delay after the infrastructure change",
]

COMPONENTS = ["database", "cache", "API gateway", "message queue", "auth service", "payment processor", "CDN", "search cluster"]
SERVICES = ["user-service", "order-api", "inventory-svc", "notification-worker", "analytics-pipeline"]
TEAMS = ["platform", "SRE", "backend", "infrastructure", "data"]
CHANGES = ["config change", "feature flag update", "database migration", "dependency upgrade", "scaling event"]
DETAILS = [
    "Looks like a race condition in the connection handling",
    "The timeout was set too aggressively for the new endpoints",
    "Seeing correlation with the traffic spike from the marketing campaign",
]

STATUS_UPDATE_MESSAGES = [
    ("Investigation in progress. Initial assessment indicates {component} may be impacted.", ":mag:"),
    ("We have identified the root cause. Working on remediation for {component}.", ":bulb:"),
    ("Mitigation deployed. Monitoring for stability. Error rates decreasing.", ":chart_with_downwards_trend:"),
    ("Service is recovering. Estimated full recovery in {minutes} minutes.", ":hourglass:"),
    ("Incident resolved. All systems operational. Post-incident review scheduled.", ":white_check_mark:"),
    ("Update: {team} team is engaged and actively working on resolution.", ":busts_in_silhouette:"),
    ("Current status: Identified issue in {component}. ETA for fix: 15 minutes.", ":clock3:"),
]

ADD_RESPONDERS_MESSAGES = [
    ("Pulling in additional support from {team} team.", ":raising_hand:"),
    ("Adding {name} to help with investigation.", ":handshake:"),
    ("Requesting backup - this needs more eyes.", ":eyes:"),
    ("Looping in specialists for {component} expertise.", ":brain:"),
]

RBA_ACTION_MESSAGES = [
    ("Running automated diagnostics on {component}...", ":robot_face:"),
    ("Triggered runbook for {scenario} scenario.", ":book:"),
    ("Automation collecting logs and metrics from affected systems.", ":gear:"),
    ("Diagnostic script completed. Results attached to incident.", ":clipboard:"),
    ("Automated remediation initiated for {component}.", ":wrench:"),
]

SCENARIO_CONVERSATIONS = {
    "database": {
        "investigation": [
            ("Checking connection pool stats on the primary replica...", ":database:"),
            ("Running SHOW PROCESSLIST - seeing {count} blocked queries", ":mag:"),
            ("Slow query log shows queries taking {ms}ms+ on the users table", ":snail:"),
        ],
        "progress": [
            ("Found the problematic query - it's a full table scan on users table", ":bulb:"),
            ("Adding index should fix this. Preparing ALTER statement.", ":hammer_and_wrench:"),
            ("Index creation in progress. Will take ~5 minutes.", ":hourglass:"),
        ],
        "resolution": [
            ("Index created successfully. Query time dropped from {high}s to {low}ms", ":rocket:"),
            ("Connection pool recovered. All queries executing normally.", ":white_check_mark:"),
        ],
    },
    "memory": {
        "investigation": [
            ("Heap dump shows HashMap objects consuming 2GB", ":mag:"),
            ("GC logs indicate full GC every 30 seconds", ":recycle:"),
            ("Memory graph shows steady climb since last deploy", ":chart_with_upwards_trend:"),
        ],
        "progress": [
            ("Found the leak - unbounded cache growth in session handler", ":bulb:"),
            ("Deploying fix to cap cache size at 10k entries", ":hammer_and_wrench:"),
            ("Rolling restart in progress across the cluster", ":arrows_counterclockwise:"),
        ],
        "resolution": [
            ("Memory stable at 60% after fix. GC back to normal.", ":white_check_mark:"),
            ("All nodes healthy. Leak patched.", ":tada:"),
        ],
    },
    "network": {
        "investigation": [
            ("Packet loss at 5% between us-east-1a and us-east-1b", ":globe_with_meridians:"),
            ("Traceroute shows increased latency at hop 4", ":signal_strength:"),
            ("MTR showing intermittent drops to the load balancer", ":bar_chart:"),
        ],
        "progress": [
            ("AWS reporting degraded networking in us-east-1", ":warning:"),
            ("Failing over traffic to us-west-2", ":airplane:"),
            ("Traffic migration at 80% complete", ":hourglass:"),
        ],
        "resolution": [
            ("Failover complete. All traffic now routing through us-west-2.", ":white_check_mark:"),
            ("Latency back to normal. Monitoring AWS status.", ":eyes:"),
        ],
    },
    "cpu": {
        "investigation": [
            ("CPU pegged at 100% on 3 of 5 nodes", ":fire:"),
            ("Top shows runaway process in analytics worker", ":chart_with_upwards_trend:"),
            ("Profiler attached - seeing tight loop in data processing", ":mag:"),
        ],
        "progress": [
            ("Identified infinite loop in batch job - missing break condition", ":bulb:"),
            ("Killing runaway processes and deploying hotfix", ":hammer_and_wrench:"),
            ("Nodes recovering - CPU dropping to normal levels", ":chart_with_downwards_trend:"),
        ],
        "resolution": [
            ("All nodes healthy. Hotfix deployed to prevent recurrence.", ":white_check_mark:"),
            ("Added circuit breaker to catch this pattern.", ":shield:"),
        ],
    },
}


def get_incident_age_minutes(incident: Dict) -> float:
    created_at = incident.get("created_at", "")
    if not created_at:
        return 0
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 60
    except Exception:
        return 0


def get_incident_channel_name(incident: Dict) -> str:
    number = incident.get("incident_number", "0")
    title = incident.get("title", "incident").replace("[DEMO] ", "").lower()
    slug = re.sub(r'[^a-z0-9]+', '-', title)[:30].strip('-')
    return f"inc-{number}-{slug}"


def get_user_emoji(user: Dict) -> str:
    job_title = (user.get("job_title", "") or "").lower()
    role = (user.get("role", "") or "").lower()
    combined = f"{job_title} {role}"
    for key, emoji in ROLE_EMOJIS.items():
        if key in combined:
            return emoji
    return ROLE_EMOJIS["default"]


def pick_responders(pd_client: PagerDutyClient, incident: Dict, count: int = 2) -> List[Dict]:
    incident_responders = pd_client.get_incident_responders(incident)
    all_users = pd_client.list_users()
    
    responders = []
    for ir in incident_responders:
        full_user = next((u for u in all_users if u.get("id") == ir.get("id")), None)
        if full_user:
            responders.append(full_user)
        else:
            responders.append({"name": ir.get("name", "Unknown"), "job_title": "", "role": "user"})
    
    if len(responders) < count and all_users:
        remaining = [u for u in all_users if u not in responders]
        if remaining:
            responders.extend(random.sample(remaining, min(count - len(responders), len(remaining))))
    
    if not responders and all_users:
        responders = random.sample(all_users, min(count, len(all_users)))
    
    if not responders:
        responders = [random.choice(DEMO_USERS)]
    
    return responders


def format_message(template: str, responders: List[Dict], incident: Dict, all_users: List[Dict]) -> str:
    age = get_incident_age_minutes(incident)
    other_users = [u for u in all_users if u not in responders] or responders
    other = random.choice(other_users) if other_users else {"name": "team"}
    other_name = other.get("name", "team").split()[0]

    return template.format(
        other_name=other_name,
        name=other_name,
        component=random.choice(COMPONENTS),
        service=random.choice(SERVICES),
        team=random.choice(TEAMS),
        change=random.choice(CHANGES),
        detail=random.choice(DETAILS),
        dependency=random.choice(COMPONENTS),
        metric="latency",
        timestamp=f"{int(age)}m ago",
        minutes=int(age),
        root_cause=random.choice(ROOT_CAUSES)[:50],
        cause=random.choice(ROOT_CAUSES),
        high=random.randint(5, 15),
        low=random.randint(0, 2),
    )


def post_conversation(slack: SlackClient, channel_id: str, messages: List[tuple], responders: List[Dict], incident: Dict, all_users: List[Dict]):
    for i, (template, emoji) in enumerate(messages):
        responder = responders[i % len(responders)]
        text = format_message(template, responders, incident, all_users)
        user_emoji = get_user_emoji(responder)
        job_title = responder.get("job_title") or responder.get("role", "")
        title_display = f" ({job_title})" if job_title else ""
        full_text = f"{user_emoji} *{responder['name']}*{title_display}\n{text}"
        slack.post_message(full_text, channel_id)
        logger.info(f"Posted to {channel_id}: {responder['name']}: {text[:50]}...")


def check_for_real_scenario(pd: PagerDutyClient, all_incidents: List[Dict]) -> Optional[Dict]:
    for incident in all_incidents:
        title = incident.get("title", "")
        if "[DEMO]" not in title and incident.get("status") in ["triggered", "acknowledged"]:
            return incident
    return None


def pause_fake_activity(pd: PagerDutyClient, slack: SlackClient) -> Dict[str, Any]:
    logger.info("REAL SCENARIO DETECTED - Pausing fake activity")
    results = {"resolved_demo_incidents": [], "notified": False}

    demo_incidents = pd.list_incidents(["triggered", "acknowledged"])
    for incident in demo_incidents:
        title = incident.get("title", "")
        if "[DEMO]" in title:
            result = pd.resolve_incident(incident["id"])
            if result.get("success"):
                results["resolved_demo_incidents"].append(incident["id"])
                logger.info(f"Resolved demo incident {incident['id']} for real scenario")

    return results


def select_resolver(responders: List[Dict], all_users: List[Dict]) -> Dict:
    if random.random() < 0.5:
        return responders[0] if responders else {"name": "On-Call Engineer"}
    other_users = [u for u in all_users if u not in responders]
    if other_users:
        return random.choice(other_users)
    return responders[-1] if len(responders) > 1 else responders[0] if responders else {"name": "On-Call Engineer"}


def get_scenario_type(incident: Dict) -> str:
    title = incident.get("title", "").lower()
    if any(kw in title for kw in ["database", "db", "postgres", "mysql", "redis"]):
        return "database"
    if any(kw in title for kw in ["cpu", "memory", "resource", "spike", "leak"]):
        return "cpu_spike"
    if any(kw in title for kw in ["api", "timeout", "latency", "response"]):
        return "api_timeout"
    return "default"


def get_scenario_messages(incident: Dict, phase: str) -> List[tuple]:
    scenario_type = get_scenario_type(incident)
    if scenario_type in SCENARIO_CONVERSATIONS:
        return SCENARIO_CONVERSATIONS[scenario_type].get(phase, [])
    return []


def get_slack_user_ids_for_responders(responders: List[Dict]) -> List[str]:
    slack_ids = []
    for responder in responders:
        email = responder.get("email", "")
        if email and email in PAGERDUTY_TO_SLACK_USER_MAP:
            slack_ids.append(PAGERDUTY_TO_SLACK_USER_MAP[email])
    return slack_ids


def select_action_count() -> int:
    roll = random.random()
    if roll < 0.17:
        return 1
    elif roll < 0.44:
        return 2
    elif roll < 0.72:
        return 3
    else:
        return 4


def get_responder_actions(pd: PagerDutyClient, slack: SlackClient, incident: Dict,
                          responders: List[Dict], all_users: List[Dict],
                          channel_id: Optional[str]) -> Dict[str, Any]:
    action_count = select_action_count()
    actions_taken = {"count": action_count, "actions": [], "escalated": False, "snoozed": False, "reassigned": False, "responders_added": False, "status_updated": False, "rba_triggered": False}
    incident_id = incident["id"]

    if action_count == 1:
        result = pd.escalate_incident(incident_id, escalation_level=2)
        if result.get("success"):
            actions_taken["escalated"] = True
            actions_taken["actions"].append("escalate")
            msg = random.choice(ESCALATION_MESSAGES)[0].format(team=random.choice(TEAMS))
            pd.add_note(incident_id, f"[Automated] {msg}")
            if channel_id:
                post_conversation(slack, channel_id, [random.choice(ESCALATION_MESSAGES)],
                                responders, incident, all_users)
        return actions_taken

    available_actions = ["investigate", "collaborate", "progress", "snooze", "escalate", "reassign", "add_responders", "status_update", "trigger_rba"]
    selected_actions = random.sample(available_actions, min(action_count, len(available_actions)))

    must_escalate = random.random() < 0.35
    if must_escalate and "escalate" not in selected_actions:
        selected_actions[-1] = "escalate"

    for action in selected_actions:
        if action == "investigate":
            scenario_msgs = get_scenario_messages(incident, "investigation")
            if scenario_msgs:
                msg_template = random.choice(scenario_msgs)
            else:
                msg_template = random.choice(INVESTIGATION_MESSAGES)
            msg = msg_template[0].format(
                timestamp=f"{int(get_incident_age_minutes(incident))}m ago",
                component=random.choice(COMPONENTS),
                minutes=int(get_incident_age_minutes(incident)),
                service=random.choice(SERVICES),
                count=random.randint(10, 100),
                ms=random.randint(500, 5000),
                table="users",
            )
            pd.add_note(incident_id, f"[Automated] {msg}")
            if channel_id:
                post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
            actions_taken["actions"].append("investigate")

        elif action == "collaborate":
            msg_template = random.choice(COLLABORATION_MESSAGES)
            if channel_id:
                post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
            actions_taken["actions"].append("collaborate")

        elif action == "progress":
            scenario_msgs = get_scenario_messages(incident, "progress")
            if scenario_msgs:
                msg_template = random.choice(scenario_msgs)
            else:
                msg_template = random.choice(PROGRESS_MESSAGES)
            msg = msg_template[0].format(
                component=random.choice(COMPONENTS),
                detail=random.choice(DETAILS),
                root_cause=random.choice(ROOT_CAUSES)[:50],
                high=random.randint(5, 15),
                low=random.randint(0, 2),
                table="users",
                minutes=random.randint(2, 10),
            )
            pd.add_note(incident_id, f"[Automated] {msg}")
            if channel_id:
                post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
            actions_taken["actions"].append("progress")

        elif action == "snooze":
            result = pd.snooze_incident(incident_id, duration_seconds=600)
            if result.get("success"):
                actions_taken["snoozed"] = True
                msg = random.choice(SNOOZE_MESSAGES)[0].format(team=random.choice(TEAMS))
                pd.add_note(incident_id, f"[Automated] {msg}")
                if channel_id:
                    post_conversation(slack, channel_id, [random.choice(SNOOZE_MESSAGES)],
                                    responders, incident, all_users)
            actions_taken["actions"].append("snooze")

        elif action == "escalate":
            result = pd.escalate_incident(incident_id, escalation_level=2)
            if result.get("success"):
                actions_taken["escalated"] = True
                msg = random.choice(ESCALATION_MESSAGES)[0].format(team=random.choice(TEAMS))
                pd.add_note(incident_id, f"[Automated] {msg}")
                if channel_id:
                    post_conversation(slack, channel_id, [random.choice(ESCALATION_MESSAGES)],
                                    responders, incident, all_users)
            actions_taken["actions"].append("escalate")

        elif action == "reassign":
            if all_users and len(all_users) > 1:
                other_users = [u for u in all_users if u not in responders]
                if other_users:
                    new_assignee = random.choice(other_users)
                    result = pd.reassign_incident(incident_id, new_assignee["id"])
                    if result.get("success"):
                        actions_taken["reassigned"] = True
                        msg = f"Reassigning to {new_assignee['name']} for additional expertise."
                        pd.add_note(incident_id, f"[Automated] {msg}")
            actions_taken["actions"].append("reassign")

        elif action == "add_responders":
            other_users = [u for u in all_users if u not in responders and u.get("id")]
            if other_users:
                new_responders = random.sample(other_users, min(2, len(other_users)))
                new_responder_ids = [u["id"] for u in new_responders]
                msg_template = random.choice(ADD_RESPONDERS_MESSAGES)
                msg = msg_template[0].format(
                    team=random.choice(TEAMS),
                    name=new_responders[0]["name"] if new_responders else "team",
                    component=random.choice(COMPONENTS),
                )
                result = pd.add_responders(incident_id, new_responder_ids)
                if result.get("success"):
                    actions_taken["responders_added"] = True
                    pd.add_note(incident_id, f"[Automated] {msg}")
                    if channel_id:
                        post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
                        slack_ids = get_slack_user_ids_for_responders(new_responders)
                        if slack_ids:
                            slack.invite_users_to_channel(channel_id, slack_ids)
            actions_taken["actions"].append("add_responders")

        elif action == "status_update":
            msg_template = random.choice(STATUS_UPDATE_MESSAGES)
            msg = msg_template[0].format(
                component=random.choice(COMPONENTS),
                team=random.choice(TEAMS),
                minutes=int(get_incident_age_minutes(incident)),
            )
            requester_email = responders[0].get("email") if responders else None
            result = pd.post_status_update(incident_id, msg, requester_email)
            if result.get("success"):
                actions_taken["status_updated"] = True
                if channel_id:
                    post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
            actions_taken["actions"].append("status_update")

        elif action == "trigger_rba":
            scenario_type = get_scenario_type(incident)
            msg_template = random.choice(RBA_ACTION_MESSAGES)
            msg = msg_template[0].format(
                component=random.choice(COMPONENTS),
                scenario=scenario_type,
            )
            pd.add_note(incident_id, f"[Automated - RBA] {msg}")
            actions_taken["rba_triggered"] = True
            if channel_id:
                post_conversation(slack, channel_id, [msg_template], responders, incident, all_users)
            actions_taken["actions"].append("trigger_rba")

    return actions_taken


def ensure_all_responders_participate(
    slack: SlackClient,
    incident: Dict,
    responders: List[Dict],
    all_users: List[Dict],
    channel_id: Optional[str],
    responders_who_acted: set = None
) -> set:
    if not channel_id or not responders:
        return responders_who_acted or set()

    if responders_who_acted is None:
        responders_who_acted = set()

    for responder in responders:
        responder_id = responder.get("id", responder.get("name"))
        if responder_id not in responders_who_acted:
            action_type = random.choice(["investigate", "collaborate", "progress"])
            scenario_msgs = get_scenario_messages(incident, action_type if action_type != "investigate" else "investigation")
            if scenario_msgs:
                msg_template = random.choice(scenario_msgs)
            elif action_type == "investigate":
                msg_template = random.choice(INVESTIGATION_MESSAGES)
            elif action_type == "collaborate":
                msg_template = random.choice(COLLABORATION_MESSAGES)
            else:
                msg_template = random.choice(PROGRESS_MESSAGES)

            text = format_message(msg_template[0], responders, incident, all_users)
            emoji = get_user_emoji(responder)
            job_title = responder.get("job_title") or responder.get("role", "")
            title_display = f" ({job_title})" if job_title else ""
            full_text = f"{emoji} *{responder['name']}*{title_display}\n{text}"
            slack.post_message(full_text, channel_id)
            responders_who_acted.add(responder_id)
            logger.info(f"Ensured responder {responder['name']} participated in incident conversation")

    return responders_who_acted


def process_incidents() -> Dict[str, Any]:
    pd = PagerDutyClient()
    slack = SlackClient()

    all_users = pd.list_users()
    logger.info(f"Using {len(all_users)} PagerDuty users for simulation")

    results = {
        "acknowledged": [],
        "escalated": [],
        "snoozed": [],
        "reassigned": [],
        "notes_added": [],
        "resolved": [],
        "slack_posted": [],
        "skipped": [],
        "real_scenario_detected": False,
        "demo_paused": [],
        "dm_sent": [],
        "actions_taken": [],
    }

    all_open = pd.list_incidents(["triggered", "acknowledged"])

    real_scenario = check_for_real_scenario(pd, all_open)
    if real_scenario:
        results["real_scenario_detected"] = True
        pause_results = pause_fake_activity(pd, slack)
        results["demo_paused"] = pause_results["resolved_demo_incidents"]
        logger.info(f"Real scenario active: {real_scenario.get('title')} - paused {len(results['demo_paused'])} demo incidents")
        return results

    triggered = pd.list_incidents(["triggered"])
    for incident in triggered:
        age = get_incident_age_minutes(incident)
        incident_id = incident["id"]
        title = incident.get("title", "Unknown")

        if "[DEMO]" not in title:
            results["skipped"].append({"id": incident_id, "reason": "not a demo incident"})
            continue

        if age >= 2:
            result = pd.acknowledge_incident(incident_id)
            if result.get("success"):
                results["acknowledged"].append(incident_id)

                channel_name = get_incident_channel_name(incident)
                channel_id = slack.find_channel_by_pattern(f"^{channel_name[:20]}")

                if channel_id:
                    responders = pick_responders(pd, incident, 2)
                    slack_user_ids = get_slack_user_ids_for_responders(responders)
                    if slack_user_ids:
                        slack.invite_users_to_channel(channel_id, slack_user_ids)
                        logger.info(f"Auto-invited {len(slack_user_ids)} responders to channel {channel_name}")
                    ack_msg = random.choice(ACK_MESSAGES)
                    post_conversation(slack, channel_id, [ack_msg], responders, incident, all_users)
                    results["slack_posted"].append({"channel": channel_name, "type": "ack"})

                msg = random.choice(ACK_MESSAGES)[0]
                pd.add_note(incident_id, f"[Automated] {msg}")
                logger.info(f"Acknowledged incident {incident_id} (age: {age:.1f}m)")
        else:
            results["skipped"].append({"id": incident_id, "reason": f"too new ({age:.1f}m)"})

    acknowledged = pd.list_incidents(["acknowledged"])
    for incident in acknowledged:
        age = get_incident_age_minutes(incident)
        incident_id = incident["id"]
        title = incident.get("title", "Unknown")

        if "[DEMO]" not in title:
            results["skipped"].append({"id": incident_id, "reason": "not a demo incident"})
            continue

        channel_name = get_incident_channel_name(incident)
        channel_id = slack.find_channel_by_pattern(f"^{channel_name[:20]}")
        responders = pick_responders(pd, incident, 3)

        if age >= 20:
            result = pd.resolve_incident(incident_id)
            if result.get("success"):
                results["resolved"].append(incident_id)

                if channel_id:
                    resolver = select_resolver(responders, all_users)
                    scenario_msgs = get_scenario_messages(incident, "resolution")
                    if scenario_msgs:
                        resolution_template = random.choice(scenario_msgs)
                    else:
                        resolution_template = random.choice(RESOLUTION_MESSAGES)
                    resolution_msgs = [
                        random.choice(PROGRESS_MESSAGES),
                        resolution_template,
                    ]
                    ensure_all_responders_participate(slack, incident, responders, all_users, channel_id)
                    post_conversation(slack, channel_id, resolution_msgs, [resolver], incident, all_users)
                    results["slack_posted"].append({"channel": channel_name, "type": "resolution"})

                cause = random.choice(ROOT_CAUSES)
                msg = random.choice(RESOLUTION_MESSAGES)[0].format(cause=cause)
                pd.add_note(incident_id, f"[Automated] {msg}")
                logger.info(f"Resolved incident {incident_id} (age: {age:.1f}m)")

        elif age >= 5:
            action_results = get_responder_actions(pd, slack, incident, responders, all_users, channel_id)

            if channel_id and random.random() < 0.3:
                ensure_all_responders_participate(slack, incident, responders, all_users, channel_id)

            results["actions_taken"].append({
                "incident_id": incident_id,
                "age": age,
                "actions": action_results
            })

            if action_results.get("escalated"):
                results["escalated"].append(incident_id)
            if action_results.get("snoozed"):
                results["snoozed"].append(incident_id)
            if action_results.get("reassigned"):
                results["reassigned"].append(incident_id)
            if action_results.get("actions"):
                results["notes_added"].append(incident_id)

            logger.info(f"Took {action_results['count']} actions on incident {incident_id}: {action_results['actions']}")
        else:
            results["skipped"].append({"id": incident_id, "reason": f"waiting ({age:.1f}m)"})

    return results


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Lifecycle Lambda invoked")
    
    results = process_incidents()
    
    logger.info(f"Results: {results}")
    
    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../scripts/demo-simulator/.env")
    
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))
