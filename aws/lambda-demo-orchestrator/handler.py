import os
import json
import logging
import random
import hashlib
import hmac
import boto3
import requests
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGERDUTY_API_URL = 'https://api.pagerduty.com'
PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue'

CONALL_EMAIL = 'clynch@pagerduty.com'
CONALL_SLACK_USER_ID = 'U0A9KAMT0BF'
CONALL_PD_USER_ID = 'PSLR7NC'

DEMO_USERS = [
    {'id': 'PG6UTES', 'email': 'jbeam@losandesgaa.onmicrosoft.com', 'name': 'Jim Beam', 'slack_id': 'U0AA1LZSYHX'},
    {'id': 'PR0E7IK', 'email': 'jdaniels@losandesgaa.onmicrosoft.com', 'name': 'Jack Daniels', 'slack_id': 'U0A9GC08EV9'},
    {'id': 'PCX6T22', 'email': 'jcasker@losandesgaa.onmicrosoft.com', 'name': 'Jameson Casker', 'slack_id': 'U0AA1LYLH2M'},
    {'id': 'PVOXRAP', 'email': 'jcuervo@losandesgaa.onmicrosoft.com', 'name': 'Jose Cuervo', 'slack_id': 'U0A9LN3QVC6'},
    {'id': 'PNRT76X', 'email': 'gtonic@losandesgaa.onmicrosoft.com', 'name': 'Ginny Tonic', 'slack_id': 'U0A9KANFCLV'},
    {'id': 'PYKISPC', 'email': 'aguiness@losandesgaa.onmicrosoft.com', 'name': 'Arthur Guinness', 'slack_id': 'U0A9SBF3MTN'},
]

PAUSE_TIMEOUT_MINUTES = 15

ACTION_TYPES = [
    ('add_note', 30),
    ('status_update', 15),
    ('run_automation', 10),
    ('trigger_workflow', 5),
    ('update_custom_fields', 10),
    ('change_priority', 10),
    ('add_responder', 5),
    ('update_incident_type', 5),
    ('add_task', 10),
]

CONVERSATION_LIBRARY = {
    'investigating': [
        "Looking into this now, checking the logs...",
        "I'm on it. Pulling up the monitoring dashboards.",
        "Investigating the root cause, one moment.",
        "Checking the recent deployments to see if anything changed.",
    ],
    'found_issue': [
        "Found something - there's a spike in the error logs around the time this started.",
        "I think I see the issue. The connection pool is exhausted.",
        "Looks like a memory leak is causing the degradation.",
        "Found it - there's a deadlock in the database queries.",
    ],
    'working_fix': [
        "Working on a fix now, should have something shortly.",
        "Deploying a hotfix to address this.",
        "Running the remediation playbook.",
        "Scaling up the instances to handle the load.",
    ],
    'resolved': [
        "Fix deployed, monitoring for stability. Looks good so far.",
        "Issue resolved. Root cause was identified and addressed.",
        "All systems back to normal. Will follow up with a post-incident review.",
        "Resolved! The automated remediation worked. Incident closed.",
    ],
}

dynamodb = boto3.resource('dynamodb')
scheduler = boto3.client('scheduler')
TABLE_NAME = os.environ.get('DEMO_STATE_TABLE', 'demo-incident-state')


class DemoState:
    def __init__(self):
        self.table = dynamodb.Table(TABLE_NAME)
    
    def create(self, incident_id: str, data: Dict) -> Dict:
        item = {
            'incident_id': incident_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'ttl': int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
            **data
        }
        self.table.put_item(Item=json.loads(json.dumps(item), parse_float=Decimal))
        return item
    
    def get(self, incident_id: str) -> Optional[Dict]:
        try:
            response = self.table.get_item(Key={'incident_id': incident_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting demo state: {e}")
            return None
    
    def update(self, incident_id: str, updates: Dict) -> bool:
        try:
            update_expr = 'SET ' + ', '.join([f'#{k} = :{k}' for k in updates.keys()])
            expr_names = {f'#{k}': k for k in updates.keys()}
            expr_values = {f':{k}': v for k, v in updates.items()}
            self.table.update_item(
                Key={'incident_id': incident_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=json.loads(json.dumps(expr_values), parse_float=Decimal)
            )
            return True
        except Exception as e:
            logger.error(f"Error updating demo state: {e}")
            return False
    
    def delete(self, incident_id: str) -> bool:
        try:
            self.table.delete_item(Key={'incident_id': incident_id})
            return True
        except Exception as e:
            logger.error(f"Error deleting demo state: {e}")
            return False
    
    def get_active_demos(self) -> List[Dict]:
        try:
            response = self.table.scan(
                FilterExpression='#state <> :resolved',
                ExpressionAttributeNames={'#state': 'state'},
                ExpressionAttributeValues={':resolved': 'resolved'}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error scanning demos: {e}")
            return []


class PagerDutyClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('PAGERDUTY_TOKEN', '')
        self.headers = {
            'Authorization': f'Token token={self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incidents/{incident_id}', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('incident')
        except Exception as e:
            logger.error(f"Error getting incident: {e}")
        return None
    
    def acknowledge_incident(self, incident_id: str, user_email: str) -> bool:
        try:
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json={'incident': {'type': 'incident_reference', 'status': 'acknowledged'}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error acknowledging incident: {e}")
            return False
    
    def resolve_incident(self, incident_id: str, user_email: str, resolution: str = None) -> bool:
        try:
            body = {'incident': {'type': 'incident_reference', 'status': 'resolved'}}
            if resolution:
                body['incident']['resolution'] = resolution
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json=body,
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error resolving incident: {e}")
            return False
    
    def add_note(self, incident_id: str, user_email: str, content: str) -> bool:
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}/notes',
                headers={**self.headers, 'From': user_email},
                json={'note': {'content': content}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False
    
    def add_responders(self, incident_id: str, requester_email: str, responder_ids: List[str], message: str = None) -> bool:
        try:
            responders = [{'responder_request_target': {'id': rid, 'type': 'user_reference'}} for rid in responder_ids]
            body = {'requester_id': self._get_user_id_by_email(requester_email), 'responder_request_targets': responders}
            if message:
                body['message'] = message
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}/responder_requests',
                headers={**self.headers, 'From': requester_email},
                json=body,
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error adding responders: {e}")
            return False
    
    def post_status_update(self, incident_id: str, user_email: str, message: str) -> bool:
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}/status_updates',
                headers={**self.headers, 'From': user_email},
                json={'message': message},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error posting status update: {e}")
            return False
    
    def change_priority(self, incident_id: str, user_email: str, priority_id: str) -> bool:
        try:
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json={'incident': {'type': 'incident_reference', 'priority': {'id': priority_id, 'type': 'priority_reference'}}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error changing priority: {e}")
            return False
    
    def get_demo_incidents(self, statuses: List[str] = None) -> List[Dict]:
        if statuses is None:
            statuses = ['triggered', 'acknowledged']
        params = '&'.join([f'statuses[]={s}' for s in statuses])
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incidents?{params}&limit=100', headers=self.headers, timeout=10)
            if resp.ok:
                incidents = resp.json().get('incidents', [])
                return [i for i in incidents if i.get('title', '').startswith('[DEMO]')]
        except Exception as e:
            logger.error(f"Error getting demo incidents: {e}")
        return []
    
    def _get_user_id_by_email(self, email: str) -> str:
        for user in DEMO_USERS:
            if user['email'] == email:
                return user['id']
        return ''


class SlackClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('SLACK_BOT_TOKEN', '')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def post_message(self, channel_id: str, text: str, username: str = None) -> bool:
        try:
            body = {'channel': channel_id, 'text': text}
            if username:
                body['username'] = username
            resp = requests.post('https://slack.com/api/chat.postMessage', headers=self.headers, json=body, timeout=10)
            return resp.ok and resp.json().get('ok')
        except Exception as e:
            logger.error(f"Error posting message: {e}")
            return False
    
    def invite_users_to_channel(self, channel_id: str, user_ids: List[str]) -> bool:
        try:
            resp = requests.post(
                'https://slack.com/api/conversations.invite',
                headers=self.headers,
                json={'channel': channel_id, 'users': ','.join(user_ids)},
                timeout=10
            )
            data = resp.json()
            return data.get('ok') or data.get('error') == 'already_in_channel'
        except Exception as e:
            logger.error(f"Error inviting users: {e}")
            return False
    
    def find_channel_by_pattern(self, pattern: str) -> Optional[str]:
        try:
            resp = requests.get(
                'https://slack.com/api/conversations.list',
                headers=self.headers,
                params={'types': 'public_channel,private_channel', 'limit': 200},
                timeout=10
            )
            if resp.ok:
                channels = resp.json().get('channels', [])
                for ch in channels:
                    if pattern.lower() in ch.get('name', '').lower():
                        return ch['id']
        except Exception as e:
            logger.error(f"Error finding channel: {e}")
        return None


def determine_responder_count() -> int:
    roll = random.random() * 100
    if roll < 65:
        return 1
    elif roll < 90:
        return 2
    elif roll < 97:
        return 3
    else:
        return 4


def select_responders(primary_user_id: str, count: int) -> List[Dict]:
    available = [u for u in DEMO_USERS if u['id'] != primary_user_id]
    additional_count = min(count - 1, len(available))
    additional = random.sample(available, additional_count) if additional_count > 0 else []
    primary = next((u for u in DEMO_USERS if u['id'] == primary_user_id), DEMO_USERS[0])
    return [primary] + additional


def select_action() -> str:
    total = sum(weight for _, weight in ACTION_TYPES)
    roll = random.random() * total
    cumulative = 0
    for action, weight in ACTION_TYPES:
        cumulative += weight
        if roll < cumulative:
            return action
    return 'add_note'


def get_conversation_message(category: str) -> str:
    messages = CONVERSATION_LIBRARY.get(category, CONVERSATION_LIBRARY['investigating'])
    return random.choice(messages)


def schedule_action(incident_id: str, action: str, delay_seconds: int, user_id: str = None):
    schedule_name = f"demo-{incident_id}-{action}-{int(datetime.now().timestamp())}"
    try:
        scheduler.create_schedule(
            Name=schedule_name,
            ScheduleExpression=f"at({(datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)).strftime('%Y-%m-%dT%H:%M:%S')})",
            FlexibleTimeWindow={'Mode': 'OFF'},
            Target={
                'Arn': os.environ.get('SELF_LAMBDA_ARN', ''),
                'RoleArn': os.environ.get('SCHEDULER_ROLE_ARN', ''),
                'Input': json.dumps({
                    'source': 'scheduler',
                    'action': action,
                    'incident_id': incident_id,
                    'user_id': user_id
                })
            },
            ActionAfterCompletion='DELETE'
        )
        logger.info(f"Scheduled {action} for {incident_id} in {delay_seconds}s")
        return True
    except Exception as e:
        logger.error(f"Error scheduling action: {e}")
        return False


def verify_webhook_signature(body: str, signature: str, secret: str) -> bool:
    if not secret:
        return True
    expected = 'v1=' + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_webhook(event: Dict) -> Dict:
    body = event.get('body', '{}')
    signature = event.get('headers', {}).get('x-pagerduty-signature', '')
    webhook_secret = os.environ.get('WEBHOOK_SECRET', '')
    
    if webhook_secret and not verify_webhook_signature(body, signature, webhook_secret):
        logger.warning("Invalid webhook signature")
        return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid signature'})}
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON'})}
    
    event_data = payload.get('event', {})
    event_type = event_data.get('event_type', '')
    
    if event_type == 'pagey.ping':
        return {'statusCode': 200, 'body': json.dumps({'message': 'pong'})}
    
    incident_data = event_data.get('data', {})
    if incident_data.get('type') != 'incident':
        incident_data = event_data.get('data', {}).get('incident', {})
    
    incident_id = incident_data.get('id', '')
    title = incident_data.get('title', '')
    
    if not incident_id or '[DEMO]' not in title:
        logger.info(f"Ignoring non-demo incident: {incident_id} - {title}")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Not a demo incident'})}
    
    logger.info(f"Processing webhook: {event_type} for incident {incident_id}")
    
    state = DemoState()
    handlers = {
        'incident.triggered': lambda: on_incident_triggered(incident_id, incident_data, state),
        'incident.acknowledged': lambda: on_incident_acknowledged(incident_id, incident_data, state),
        'incident.resolved': lambda: on_incident_resolved(incident_id, state),
        'incident.responder.added': lambda: on_responder_added(incident_id, event_data, state),
        'incident.annotated': lambda: on_action_completed(incident_id, 'add_note', state),
        'incident.status_update_published': lambda: on_action_completed(incident_id, 'status_update', state),
        'workflow.completed': lambda: on_workflow_completed(incident_id, event_data, state),
    }
    
    handler = handlers.get(event_type)
    if handler:
        handler()
    
    return {'statusCode': 200, 'body': json.dumps({'message': 'Processed', 'event_type': event_type})}


def on_incident_triggered(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident triggered: {incident_id}")
    
    existing = state.get(incident_id)
    if existing:
        logger.info(f"Demo state already exists for {incident_id}")
        return
    
    custom_details = incident_data.get('custom_fields', {}) or {}
    if isinstance(custom_details, list):
        custom_details = {f.get('name'): f.get('value') for f in custom_details if f.get('name')}
    
    service = incident_data.get('service', {})
    assignees = incident_data.get('assignments', [])
    primary_user_id = assignees[0].get('assignee', {}).get('id') if assignees else DEMO_USERS[0]['id']
    
    responder_count = determine_responder_count()
    responders = select_responders(primary_user_id, responder_count)
    
    demo_data = {
        'state': 'triggered',
        'scenario_id': custom_details.get('scenario_id', 'unknown'),
        'scenario_name': custom_details.get('scenario_name', incident_data.get('title', '')),
        'service_id': service.get('id', ''),
        'service_name': service.get('summary', ''),
        'responders': responders,
        'responder_actions': {r['id']: {'acted': False, 'action': None} for r in responders},
        'paused': False,
        'pause_started_at': None,
        'slack_channel_id': None,
        'acknowledged_at': None,
        'resolver_id': None,
    }
    
    state.create(incident_id, demo_data)
    logger.info(f"Created demo state for {incident_id} with {len(responders)} responders")
    
    primary_email = responders[0]['email']
    delay = random.randint(30, 120)
    schedule_action(incident_id, 'acknowledge', delay, responders[0]['id'])
    logger.info(f"Scheduled acknowledgment in {delay}s by {primary_email}")


def on_incident_acknowledged(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident acknowledged: {incident_id}")
    
    demo = state.get(incident_id)
    if not demo:
        logger.warning(f"No demo state for {incident_id}")
        return
    
    if demo.get('paused'):
        logger.info(f"Demo {incident_id} is paused, skipping actions")
        return
    
    state.update(incident_id, {
        'state': 'acknowledged',
        'acknowledged_at': datetime.now(timezone.utc).isoformat()
    })
    
    responders = demo.get('responders', [])
    if len(responders) > 1:
        pd = PagerDutyClient()
        additional_ids = [r['id'] for r in responders[1:]]
        primary_email = responders[0]['email']
        pd.add_responders(incident_id, primary_email, additional_ids, "Requesting additional support for this incident")
        logger.info(f"Added {len(additional_ids)} responders to {incident_id}")
    
    delay = random.randint(60, 180)
    schedule_action(incident_id, 'responder_action', delay, responders[0]['id'])


def on_responder_added(incident_id: str, event_data: Dict, state: DemoState):
    logger.info(f"Responder added to {incident_id}")
    
    demo = state.get(incident_id)
    if not demo or demo.get('paused'):
        return
    
    slack_channel = demo.get('slack_channel_id')
    if slack_channel:
        responder = event_data.get('data', {}).get('responder', {})
        responder_id = responder.get('id', '')
        user = next((u for u in DEMO_USERS if u['id'] == responder_id), None)
        if user:
            slack = SlackClient()
            slack.invite_users_to_channel(slack_channel, [user['slack_id']])
            slack.post_message(slack_channel, f"{user['name']} has joined to help with this incident.")


def on_workflow_completed(incident_id: str, event_data: Dict, state: DemoState):
    logger.info(f"Workflow completed for {incident_id}")
    
    demo = state.get(incident_id)
    if not demo:
        return
    
    pd = PagerDutyClient()
    incident = pd.get_incident(incident_id)
    if not incident:
        return
    
    conference = incident.get('conference_bridge', {})
    slack_channel_url = conference.get('url', '') if conference else ''
    
    if not slack_channel_url:
        slack = SlackClient()
        service_name = demo.get('service_name', 'incident').lower().replace(' ', '-')[:20]
        incident_number = incident.get('incident_number', incident_id[-6:])
        pattern = f"inc-{incident_number}"
        channel_id = slack.find_channel_by_pattern(pattern)
        if channel_id:
            state.update(incident_id, {'slack_channel_id': channel_id})
            invite_to_slack_channel(channel_id, demo, slack)
            return
    
    if 'slack.com' in slack_channel_url:
        parts = slack_channel_url.split('/')
        channel_id = parts[-1] if parts else None
        if channel_id and channel_id.startswith('C'):
            state.update(incident_id, {'slack_channel_id': channel_id})
            slack = SlackClient()
            invite_to_slack_channel(channel_id, demo, slack)


def invite_to_slack_channel(channel_id: str, demo: Dict, slack: SlackClient):
    user_ids = [CONALL_SLACK_USER_ID]
    for r in demo.get('responders', []):
        if r.get('slack_id'):
            user_ids.append(r['slack_id'])
    
    slack.invite_users_to_channel(channel_id, user_ids)
    slack.post_message(channel_id, "Team assembled for incident response. Let's investigate.")
    logger.info(f"Invited {len(user_ids)} users to channel {channel_id}")


def on_action_completed(incident_id: str, action_type: str, state: DemoState):
    logger.info(f"Action {action_type} completed for {incident_id}")
    
    demo = state.get(incident_id)
    if not demo or demo.get('paused'):
        return
    
    responder_actions = demo.get('responder_actions', {})
    all_acted = all(ra.get('acted') for ra in responder_actions.values())
    
    if all_acted:
        delay = random.randint(120, 300)
        schedule_action(incident_id, 'resolve', delay)
        logger.info(f"All responders acted, scheduled resolution in {delay}s")
    else:
        not_acted = [rid for rid, ra in responder_actions.items() if not ra.get('acted')]
        if not_acted:
            next_user = random.choice(not_acted)
            delay = random.randint(60, 180)
            schedule_action(incident_id, 'responder_action', delay, next_user)


def on_incident_resolved(incident_id: str, state: DemoState):
    logger.info(f"Incident resolved: {incident_id}")
    
    demo = state.get(incident_id)
    if not demo:
        return
    
    slack_channel = demo.get('slack_channel_id')
    if slack_channel:
        slack = SlackClient()
        slack.post_message(slack_channel, get_conversation_message('resolved'))
    
    state.update(incident_id, {'state': 'resolved'})


def handle_scheduled_action(event: Dict) -> Dict:
    action = event.get('action')
    incident_id = event.get('incident_id')
    user_id = event.get('user_id')
    
    logger.info(f"Handling scheduled action: {action} for {incident_id}")
    
    state = DemoState()
    demo = state.get(incident_id)
    
    if not demo:
        logger.warning(f"No demo state for {incident_id}")
        return {'statusCode': 200, 'body': json.dumps({'message': 'No demo state'})}
    
    if demo.get('paused'):
        pause_started = demo.get('pause_started_at')
        if pause_started:
            pause_time = datetime.fromisoformat(pause_started.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - pause_time > timedelta(minutes=PAUSE_TIMEOUT_MINUTES):
                logger.info(f"Pause timeout reached for {incident_id}, resolving")
                action = 'resolve'
            else:
                logger.info(f"Demo {incident_id} is paused, skipping action")
                return {'statusCode': 200, 'body': json.dumps({'message': 'Demo paused'})}
    
    if demo.get('state') == 'resolved':
        logger.info(f"Demo {incident_id} already resolved")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Already resolved'})}
    
    pd = PagerDutyClient()
    slack = SlackClient()
    slack_channel = demo.get('slack_channel_id')
    
    user = next((u for u in DEMO_USERS if u['id'] == user_id), DEMO_USERS[0])
    user_email = user['email']
    
    if action == 'acknowledge':
        pd.acknowledge_incident(incident_id, user_email)
        if slack_channel:
            slack.post_message(slack_channel, f"{user['name']}: {get_conversation_message('investigating')}")
    
    elif action == 'responder_action':
        action_type = select_action()
        perform_responder_action(incident_id, user, action_type, pd, slack, slack_channel, demo, state)
    
    elif action == 'resolve':
        responders = demo.get('responders', [])
        resolver = random.choice(responders) if responders else user
        resolution = f"Issue resolved by {resolver['name']}. Root cause identified and addressed."
        pd.resolve_incident(incident_id, resolver['email'], resolution)
        if slack_channel:
            slack.post_message(slack_channel, f"{resolver['name']}: {get_conversation_message('resolved')}")
        state.update(incident_id, {'state': 'resolved', 'resolver_id': resolver['id']})
    
    return {'statusCode': 200, 'body': json.dumps({'message': f'Executed {action}'})}


def perform_responder_action(incident_id: str, user: Dict, action_type: str, pd: PagerDutyClient, 
                              slack: SlackClient, slack_channel: str, demo: Dict, state: DemoState):
    user_email = user['email']
    
    if action_type == 'add_note':
        content = get_conversation_message('found_issue')
        pd.add_note(incident_id, user_email, content)
        if slack_channel:
            slack.post_message(slack_channel, f"{user['name']}: {content}")
    
    elif action_type == 'status_update':
        message = get_conversation_message('working_fix')
        pd.post_status_update(incident_id, user_email, message)
        if slack_channel:
            slack.post_message(slack_channel, f"{user['name']} posted status update: {message}")
    
    elif action_type == 'add_responder':
        current_responders = demo.get('responders', [])
        current_ids = [r['id'] for r in current_responders]
        available = [u for u in DEMO_USERS if u['id'] not in current_ids]
        if available:
            new_responder = random.choice(available)
            pd.add_responders(incident_id, user_email, [new_responder['id']], "Need additional expertise")
            current_responders.append(new_responder)
            responder_actions = demo.get('responder_actions', {})
            responder_actions[new_responder['id']] = {'acted': False, 'action': None}
            state.update(incident_id, {'responders': current_responders, 'responder_actions': responder_actions})
            if slack_channel:
                slack.post_message(slack_channel, f"{user['name']} is requesting help from {new_responder['name']}")
    
    else:
        content = get_conversation_message('investigating')
        pd.add_note(incident_id, user_email, f"[{action_type}] {content}")
        if slack_channel:
            slack.post_message(slack_channel, f"{user['name']}: {content}")
    
    responder_actions = demo.get('responder_actions', {})
    if user['id'] in responder_actions:
        responder_actions[user['id']] = {'acted': True, 'action': action_type}
        state.update(incident_id, {'responder_actions': responder_actions})


def handle_api_request(event: Dict) -> Dict:
    path = event.get('rawPath', event.get('path', ''))
    method = event.get('requestContext', {}).get('http', {}).get('method', event.get('httpMethod', 'GET'))
    
    try:
        body = json.loads(event.get('body', '{}') or '{}')
    except json.JSONDecodeError:
        body = {}
    
    logger.info(f"API request: {method} {path}")
    
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors_headers, 'body': ''}
    
    state = DemoState()
    pd = PagerDutyClient()
    
    if '/cleanup' in path and method == 'POST':
        demos = pd.get_demo_incidents(['triggered', 'acknowledged'])
        resolved = 0
        for inc in demos:
            if pd.resolve_incident(inc['id'], DEMO_USERS[0]['email'], 'Cleanup before new demo'):
                state.delete(inc['id'])
                resolved += 1
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': f'Resolved {resolved} demo incidents', 'resolved': resolved})
        }
    
    elif '/pause' in path and method == 'POST':
        incident_id = body.get('incident_id')
        if incident_id:
            state.update(incident_id, {'paused': True, 'pause_started_at': datetime.now(timezone.utc).isoformat()})
            schedule_action(incident_id, 'pause_timeout', PAUSE_TIMEOUT_MINUTES * 60)
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'message': 'Demo paused', 'timeout_minutes': PAUSE_TIMEOUT_MINUTES})}
        else:
            active = state.get_active_demos()
            for demo in active:
                state.update(demo['incident_id'], {'paused': True, 'pause_started_at': datetime.now(timezone.utc).isoformat()})
                schedule_action(demo['incident_id'], 'pause_timeout', PAUSE_TIMEOUT_MINUTES * 60)
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'message': f'Paused {len(active)} demos', 'timeout_minutes': PAUSE_TIMEOUT_MINUTES})}
    
    elif '/resume' in path and method == 'POST':
        incident_id = body.get('incident_id')
        if incident_id:
            demo = state.get(incident_id)
            if demo:
                state.update(incident_id, {'paused': False, 'pause_started_at': None})
                delay = random.randint(30, 90)
                not_acted = [rid for rid, ra in demo.get('responder_actions', {}).items() if not ra.get('acted')]
                if not_acted:
                    schedule_action(incident_id, 'responder_action', delay, random.choice(not_acted))
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'message': 'Demo resumed'})}
        else:
            active = state.get_active_demos()
            for demo in active:
                state.update(demo['incident_id'], {'paused': False, 'pause_started_at': None})
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'message': f'Resumed {len(active)} demos'})}
    
    elif '/status' in path and method == 'GET':
        incident_id = event.get('queryStringParameters', {}).get('incident_id')
        if incident_id:
            demo = state.get(incident_id)
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'demo': demo})}
        else:
            active = state.get_active_demos()
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'active_demos': active, 'count': len(active)})}
    
    elif '/health' in path:
        return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})}
    
    return {'statusCode': 404, 'headers': cors_headers, 'body': json.dumps({'error': 'Not found'})}


def lambda_handler(event: Dict, context: Any) -> Dict:
    logger.info(f"Event received: {json.dumps(event)[:500]}")
    
    if event.get('source') == 'scheduler':
        return handle_scheduled_action(event)
    
    headers = event.get('headers', {})
    if headers.get('x-pagerduty-signature') or 'webhook' in event.get('rawPath', '').lower():
        return handle_webhook(event)
    
    return handle_api_request(event)
