import json
import os
import random
import logging
from datetime import datetime

from shared import PagerDutyClient, DEMO_USERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGERDUTY_TOKEN = os.environ.get('PAGERDUTY_TOKEN', '')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'C0A9GCXFSBD')

INVESTIGATION_NOTES = [
    "Investigating the issue. Checking application logs for errors.",
    "Reviewing recent deployments that might have caused this.",
    "Checking database connection pool metrics.",
    "Analyzing CPU and memory utilization on affected hosts.",
    "Reviewing error rates in monitoring dashboards.",
    "Checking for any network connectivity issues.",
    "Correlating with recent change events.",
    "Running diagnostic scripts to gather more information.",
    "Checking downstream service dependencies.",
    "Reviewing alert thresholds and recent metric trends.",
    "Pulled thread dumps from affected JVMs for analysis.",
    "Checking Kubernetes pod health and restart counts.",
    "Reviewing recent config changes in the affected service.",
    "Querying distributed tracing for slow spans.",
    "Checking certificate expiration dates on affected endpoints.",
]

RESOLUTION_NOTES = [
    "Root cause identified: Memory leak in application. Restarted affected pods.",
    "Issue resolved: Database connection pool exhausted. Increased pool size.",
    "Fixed: Misconfigured load balancer health checks. Updated configuration.",
    "Resolved: Disk space issue on log volume. Cleaned up old logs.",
    "Issue was transient network blip. Monitoring shows recovery.",
    "Resolved by rolling back recent deployment v2.4.1 to v2.4.0.",
    "Fixed upstream dependency issue. Third-party service restored.",
    "Auto-scaling resolved the issue. Added capacity.",
    "Restarted the affected microservice. Memory pressure relieved.",
    "Applied hotfix for race condition in connection handling.",
    "DNS propagation complete. Service reachable from all regions.",
    "Cache invalidation completed. Stale data cleared.",
    "Rate limiter threshold adjusted. Traffic flowing normally.",
    "SSL certificate renewed. HTTPS connections restored.",
]

STATUS_UPDATES = [
    "Currently investigating. No customer impact confirmed yet.",
    "Identified potential root cause. Implementing fix.",
    "Fix deployed to staging. Testing before production rollout.",
    "Rolling out fix to production. Monitoring closely.",
    "Fix deployed. Monitoring for 15 minutes before closing.",
    "Partial mitigation in place. Full fix in progress.",
    "Escalated to platform team for assistance.",
    "Waiting on third-party vendor response.",
    "Customer communications sent. ETA for resolution: 30 minutes.",
]

RUNBOOK_ACTIONS = [
    "Executed runbook: Restart Application Pods",
    "Executed runbook: Clear Redis Cache",
    "Executed runbook: Rotate Database Credentials",
    "Executed runbook: Scale Up Worker Nodes",
    "Executed runbook: Enable Debug Logging",
    "Executed runbook: Failover to Secondary Database",
    "Executed runbook: Flush CDN Cache",
    "Executed runbook: Restart Message Queue Consumers",
]

DIAGNOSTIC_RESULTS = [
    "Diagnostics complete: High memory usage detected (92% utilized)",
    "Diagnostics complete: Database query latency elevated (avg 2.3s)",
    "Diagnostics complete: Network packet loss detected (3.2%)",
    "Diagnostics complete: CPU throttling observed on 4 pods",
    "Diagnostics complete: Connection pool at 95% capacity",
    "Diagnostics complete: Disk I/O wait times elevated",
    "Diagnostics complete: No anomalies detected in recent logs",
    "Diagnostics complete: Found 47 error entries in last 5 minutes",
]


def get_user_by_id(user_id: str) -> dict:
    for user in DEMO_USERS:
        if user['id'] == user_id:
            return user
    return None


def perform_single_action(pd_client: PagerDutyClient, incident: dict, current_assignee: dict, action_type: str) -> dict:
    incident_id = incident['id']
    incident_status = incident.get('status', 'triggered')

    if action_type == 'acknowledge':
        response = pd_client.acknowledge_incident(incident_id, current_assignee['email'])
        return {
            'action': 'acknowledge',
            'response': response,
            'description': f"{current_assignee['name']} acknowledged incident"
        }

    elif action_type == 'add_note':
        note = random.choice(INVESTIGATION_NOTES)
        response = pd_client.add_note(incident_id, note, current_assignee['email'])
        return {
            'action': 'add_note',
            'response': response,
            'note': note,
            'description': f"{current_assignee['name']} added investigation note"
        }

    elif action_type == 'snooze':
        duration = random.choice([1800, 3600, 7200])
        response = pd_client.snooze_incident(incident_id, duration, current_assignee['email'])
        return {
            'action': 'snooze',
            'response': response,
            'duration_minutes': duration // 60,
            'description': f"{current_assignee['name']} snoozed incident for {duration // 60} minutes"
        }

    elif action_type == 'reassign':
        other_users = [u for u in DEMO_USERS if u['id'] != current_assignee['id']]
        new_assignee = random.choice(other_users)
        response = pd_client.reassign_incident(incident_id, new_assignee['id'], current_assignee['email'])
        return {
            'action': 'reassign',
            'response': response,
            'reassigned_to': new_assignee['name'],
            'new_assignee': new_assignee,
            'description': f"{current_assignee['name']} escalated incident to {new_assignee['name']}"
        }

    elif action_type == 'add_responders':
        other_users = [u for u in DEMO_USERS if u['id'] != current_assignee['id']]
        num_responders = random.randint(1, 2)
        responders = random.sample(other_users, min(num_responders, len(other_users)))
        responder_ids = [r['id'] for r in responders]
        responder_names = [r['name'] for r in responders]
        response = pd_client.add_responders(incident_id, responder_ids, current_assignee['email'])
        return {
            'action': 'add_responders',
            'response': response,
            'responders': responder_names,
            'description': f"{current_assignee['name']} requested help from {', '.join(responder_names)}"
        }

    elif action_type == 'change_urgency':
        new_urgency = 'high'
        response = pd_client.update_urgency(incident_id, new_urgency, current_assignee['email'])
        return {
            'action': 'change_urgency',
            'response': response,
            'new_urgency': new_urgency,
            'description': f"{current_assignee['name']} escalated urgency to {new_urgency}"
        }

    elif action_type == 'run_diagnostic':
        diagnostic_note = random.choice(DIAGNOSTIC_RESULTS)
        response = pd_client.add_note(incident_id, diagnostic_note, current_assignee['email'])
        return {
            'action': 'run_diagnostic',
            'response': response,
            'diagnostic_result': diagnostic_note,
            'description': f"{current_assignee['name']} ran diagnostics"
        }

    elif action_type == 'status_update':
        status = random.choice(STATUS_UPDATES)
        response = pd_client.add_note(incident_id, f"STATUS UPDATE: {status}", current_assignee['email'])
        return {
            'action': 'status_update',
            'response': response,
            'status': status,
            'description': f"{current_assignee['name']} posted status update"
        }

    elif action_type == 'run_runbook':
        runbook_action = random.choice(RUNBOOK_ACTIONS)
        response = pd_client.add_note(incident_id, runbook_action, current_assignee['email'])
        return {
            'action': 'run_runbook',
            'response': response,
            'runbook_action': runbook_action,
            'description': f"{current_assignee['name']} {runbook_action.lower()}"
        }

    elif action_type == 'resolve':
        resolution_note = random.choice(RESOLUTION_NOTES)
        note_response = pd_client.add_note(incident_id, resolution_note, current_assignee['email'])
        resolve_response = pd_client.resolve_incident(incident_id, current_assignee['email'])
        return {
            'action': 'resolve',
            'note_response': note_response,
            'resolve_response': resolve_response,
            'resolution_note': resolution_note,
            'resolved_by': current_assignee['name'],
            'description': f"{current_assignee['name']} resolved incident: {resolution_note[:50]}..."
        }

    return {'action': 'unknown', 'description': 'Unknown action type'}


def simulate_user_activity(pd_client: PagerDutyClient) -> dict:
    if random.random() < 0.15:
        idle_user = random.choice(DEMO_USERS)
        idle_reasons = [
            "in a meeting",
            "on a call",
            "reviewing documentation",
            "on break",
            "handling another issue",
            "waiting for more information",
        ]
        return {
            'action': 'idle',
            'user': idle_user['name'],
            'reason': random.choice(idle_reasons),
            'description': f"{idle_user['name']} is {random.choice(idle_reasons)} - no action taken"
        }

    incidents = pd_client.get_demo_incidents()

    if not incidents:
        return {'action': 'none', 'reason': 'No [DEMO] incidents found'}

    incident = random.choice(incidents)
    incident_id = incident['id']
    incident_status = incident.get('status', 'triggered')
    incident_title = incident.get('title', 'Unknown')

    current_assignee = pd_client.get_incident_assignee(incident)

    num_actions = random.choices(
        [1, 2, 3, 4],
        weights=[0.40, 0.35, 0.15, 0.10]
    )[0]

    actions_taken = []
    simulated_delays = []
    total_simulated_time = 0

    result = {
        'incident_id': incident_id,
        'incident_title': incident_title,
        'incident_status': incident_status,
        'current_assignee': current_assignee['name'],
        'planned_actions': num_actions,
    }

    if incident_status == 'triggered':
        ack_result = perform_single_action(pd_client, incident, current_assignee, 'acknowledge')
        actions_taken.append(ack_result)

        delay = random.randint(30, 180)
        simulated_delays.append(delay)
        total_simulated_time += delay

        remaining_actions = num_actions - 1

        available_actions = ['add_note', 'snooze', 'reassign', 'add_responders', 'change_urgency', 'run_diagnostic', 'status_update']
        action_weights = [0.25, 0.10, 0.15, 0.15, 0.10, 0.15, 0.10]

        for i in range(remaining_actions):
            action_type = random.choices(available_actions, weights=action_weights)[0]
            action_result = perform_single_action(pd_client, incident, current_assignee, action_type)
            actions_taken.append(action_result)

            if action_type == 'reassign' and 'new_assignee' in action_result:
                current_assignee = action_result['new_assignee']
                result['escalated_to'] = current_assignee['name']

            if i < remaining_actions - 1:
                delay = random.randint(60, 300)
                simulated_delays.append(delay)
                total_simulated_time += delay

    else:
        available_actions = ['add_note', 'resolve', 'run_runbook', 'add_responders', 'status_update', 'run_diagnostic']
        action_weights = [0.15, 0.40, 0.15, 0.10, 0.10, 0.10]

        for i in range(num_actions):
            if i == num_actions - 1 and not any(a['action'] == 'resolve' for a in actions_taken):
                if random.random() < 0.6:
                    action_type = 'resolve'
                else:
                    action_type = random.choices(available_actions, weights=action_weights)[0]
            else:
                action_type = random.choices(available_actions, weights=action_weights)[0]

            if action_type == 'resolve' and any(a['action'] == 'resolve' for a in actions_taken):
                action_type = random.choice(['add_note', 'status_update', 'run_diagnostic'])

            action_result = perform_single_action(pd_client, incident, current_assignee, action_type)
            actions_taken.append(action_result)

            if action_type == 'resolve':
                break

            if i < num_actions - 1:
                delay = random.randint(60, 300)
                simulated_delays.append(delay)
                total_simulated_time += delay

    result['actions'] = actions_taken
    result['actions_performed'] = len(actions_taken)
    result['simulated_delays_seconds'] = simulated_delays
    result['total_simulated_time_seconds'] = total_simulated_time
    result['total_simulated_time_minutes'] = round(total_simulated_time / 60, 1)
    result['description'] = '; '.join([a['description'] for a in actions_taken])

    return result


def lambda_handler(event, context):
    logger.info(f"User Activity Simulator invoked at {datetime.utcnow().isoformat()}")

    if not PAGERDUTY_TOKEN:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'PAGERDUTY_TOKEN not configured'})
        }

    pd_client = PagerDutyClient(PAGERDUTY_TOKEN)

    num_invocations = event.get('num_invocations', 1)
    results = []

    for _ in range(num_invocations):
        result = simulate_user_activity(pd_client)
        results.append(result)
        logger.info(f"Action result: {result.get('description', 'No action taken')}")

    total_actions = sum(r.get('actions_performed', 0) for r in results)
    idle_count = sum(1 for r in results if r.get('action') == 'idle')

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'User activity simulation complete',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'invocations': num_invocations,
                'total_actions_performed': total_actions,
                'idle_users': idle_count,
            },
            'results': results
        })
    }
