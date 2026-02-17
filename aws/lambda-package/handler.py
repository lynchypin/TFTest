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
CONALL_SLACK_USER_ID_PERSONAL = 'U0A9GBYT999'
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

# PagerDuty API Configuration and Stubs
PAGERDUTY_API_ENDPOINTS = {
    'incidents': '/incidents',
    'incident_detail': '/incidents/{incident_id}',
    'incident_acknowledge': '/incidents/{incident_id}/acknowledge',
    'incident_resolve': '/incidents/{incident_id}/resolve',
    'incident_escalate': '/incidents/{incident_id}/escalate',
    'incident_urgency': '/incidents/{incident_id}',
    'incident_status': '/incidents/{incident_id}/status_updates',
    'incident_body': '/incidents/{incident_id}/body',
    'incident_assignments': '/incidents/{incident_id}/responders',
    'users': '/users',
    'user_detail': '/users/{user_id}',
    'services': '/services',
    'service_detail': '/services/{service_id}',
    'teams': '/teams',
    'schedules': '/schedules',
    'escalation_policies': '/escalation_policies',
    'event_orchestration': '/event_orchestrations',
    'automation_actions': '/automation_actions',
    'response_plays': '/response_plays',
    'webhooks': '/webhooks',
    'webhook_subscriptions': '/webhook_subscriptions',
    'integrations': '/integrations',
}

DEMO_CONFIG = {
    'ack_delay_min': 30,
    'ack_delay_max': 120,
    'action_delay_min': 60,
    'action_delay_max': 180,
    'resolve_delay_min': 120,
    'resolve_delay_max': 300,
    'escalation_ack_delay_min': 15,
    'escalation_ack_delay_max': 45,
    'max_ack_attempts': 3,
    'force_ack_after_minutes': 10,
    'enable_slack_population': True,
    'enable_jira_sync': True,
    'enable_status_page_updates': False,
    'enable_conference_bridge': True,
    'demo_prefix': '[DEMO]',
}

FEATURE_FLAGS = {
    'incidents': True,
    'services': True,
    'users': True,
    'teams': True,
    'schedules': True,
    'escalation_policies': True,
    'incident_workflows': True,
    'event_orchestration': True,
    'automation_actions': True,
    'business_services': True,
    'status_dashboard': True,
    'analytics': True,
    'response_plays': True,
    'on_call': True,
    'notifications': True,
    'integrations': True,
    'webhooks': True,
    'custom_fields': True,
    'priorities': True,
    'tags': True,
    'maintenance_windows': True,
    'status_pages': False,
    'jeli_integration': False,
    'aiops': False,
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

    def list_services(self, team_ids: List[str] = None, limit: int = 100) -> List[Dict]:
        params = {'limit': limit}
        if team_ids:
            params['team_ids[]'] = team_ids
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/services', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('services', [])
        except Exception as e:
            logger.error(f"Error listing services: {e}")
        return []

    def get_service(self, service_id: str, include: List[str] = None) -> Optional[Dict]:
        params = {}
        if include:
            params['include[]'] = include
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/services/{service_id}', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('service')
        except Exception as e:
            logger.error(f"Error getting service: {e}")
        return None

    def create_service(self, name: str, escalation_policy_id: str, description: str = None, alert_grouping: str = None) -> Optional[Dict]:
        body = {
            'service': {
                'type': 'service',
                'name': name,
                'escalation_policy': {'id': escalation_policy_id, 'type': 'escalation_policy_reference'}
            }
        }
        if description:
            body['service']['description'] = description
        if alert_grouping:
            body['service']['alert_grouping_parameters'] = {'type': alert_grouping}
        try:
            resp = requests.post(f'{PAGERDUTY_API_URL}/services', headers=self.headers, json=body, timeout=10)
            if resp.ok:
                return resp.json().get('service')
        except Exception as e:
            logger.error(f"Error creating service: {e}")
        return None

    def update_service(self, service_id: str, updates: Dict) -> Optional[Dict]:
        body = {'service': {'type': 'service', **updates}}
        try:
            resp = requests.put(f'{PAGERDUTY_API_URL}/services/{service_id}', headers=self.headers, json=body, timeout=10)
            if resp.ok:
                return resp.json().get('service')
        except Exception as e:
            logger.error(f"Error updating service: {e}")
        return None

    def delete_service(self, service_id: str) -> bool:
        try:
            resp = requests.delete(f'{PAGERDUTY_API_URL}/services/{service_id}', headers=self.headers, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logger.error(f"Error deleting service: {e}")
            return False

    def list_users(self, team_ids: List[str] = None, include: List[str] = None, limit: int = 100) -> List[Dict]:
        params = {'limit': limit}
        if team_ids:
            params['team_ids[]'] = team_ids
        if include:
            params['include[]'] = include
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/users', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('users', [])
        except Exception as e:
            logger.error(f"Error listing users: {e}")
        return []

    def get_user(self, user_id: str, include: List[str] = None) -> Optional[Dict]:
        params = {}
        if include:
            params['include[]'] = include
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/users/{user_id}', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('user')
        except Exception as e:
            logger.error(f"Error getting user: {e}")
        return None

    def get_user_on_call(self, user_id: str) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/users/{user_id}/oncalls', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('oncalls', [])
        except Exception as e:
            logger.error(f"Error getting user on-call: {e}")
        return []

    def list_teams(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/teams', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('teams', [])
        except Exception as e:
            logger.error(f"Error listing teams: {e}")
        return []

    def get_team(self, team_id: str, include: List[str] = None) -> Optional[Dict]:
        params = {}
        if include:
            params['include[]'] = include
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/teams/{team_id}', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('team')
        except Exception as e:
            logger.error(f"Error getting team: {e}")
        return None

    def list_schedules(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/schedules', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('schedules', [])
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
        return []

    def get_schedule(self, schedule_id: str, since: str = None, until: str = None) -> Optional[Dict]:
        params = {}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/schedules/{schedule_id}', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('schedule')
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
        return None

    def get_oncalls(self, schedule_ids: List[str] = None, escalation_policy_ids: List[str] = None) -> List[Dict]:
        params = {}
        if schedule_ids:
            params['schedule_ids[]'] = schedule_ids
        if escalation_policy_ids:
            params['escalation_policy_ids[]'] = escalation_policy_ids
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/oncalls', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('oncalls', [])
        except Exception as e:
            logger.error(f"Error getting oncalls: {e}")
        return []

    def list_escalation_policies(self, team_ids: List[str] = None, limit: int = 100) -> List[Dict]:
        params = {'limit': limit}
        if team_ids:
            params['team_ids[]'] = team_ids
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/escalation_policies', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('escalation_policies', [])
        except Exception as e:
            logger.error(f"Error listing escalation policies: {e}")
        return []

    def get_escalation_policy(self, policy_id: str, include: List[str] = None) -> Optional[Dict]:
        params = {}
        if include:
            params['include[]'] = include
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/escalation_policies/{policy_id}', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('escalation_policy')
        except Exception as e:
            logger.error(f"Error getting escalation policy: {e}")
        return None

    def list_priorities(self) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/priorities', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('priorities', [])
        except Exception as e:
            logger.error(f"Error listing priorities: {e}")
        return []

    def snooze_incident(self, incident_id: str, user_email: str, duration_seconds: int) -> bool:
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}/snooze',
                headers={**self.headers, 'From': user_email},
                json={'duration': duration_seconds},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error snoozing incident: {e}")
            return False

    def merge_incidents(self, parent_incident_id: str, user_email: str, incident_ids: List[str]) -> bool:
        try:
            source_incidents = [{'id': iid, 'type': 'incident_reference'} for iid in incident_ids]
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{parent_incident_id}/merge',
                headers={**self.headers, 'From': user_email},
                json={'source_incidents': source_incidents},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error merging incidents: {e}")
            return False

    def reassign_incident(self, incident_id: str, user_email: str, assignee_ids: List[str]) -> bool:
        try:
            assignments = [{'assignee': {'id': aid, 'type': 'user_reference'}} for aid in assignee_ids]
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json={'incident': {'type': 'incident_reference', 'assignments': assignments}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error reassigning incident: {e}")
            return False

    def run_response_play(self, incident_id: str, user_email: str, response_play_id: str) -> bool:
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/response_plays/{response_play_id}/run',
                headers={**self.headers, 'From': user_email},
                json={'incident': {'id': incident_id, 'type': 'incident_reference'}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error running response play: {e}")
            return False

    def list_response_plays(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/response_plays', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('response_plays', [])
        except Exception as e:
            logger.error(f"Error listing response plays: {e}")
        return []

    def list_incident_workflows(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incident_workflows', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('incident_workflows', [])
        except Exception as e:
            logger.error(f"Error listing incident workflows: {e}")
        return []

    def trigger_incident_workflow(self, workflow_id: str, incident_id: str) -> bool:
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/incident_workflows/{workflow_id}/instances',
                headers=self.headers,
                json={'incident_workflow_instance': {'incident': {'id': incident_id, 'type': 'incident_reference'}}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error triggering incident workflow: {e}")
            return False

    def list_business_services(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/business_services', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('business_services', [])
        except Exception as e:
            logger.error(f"Error listing business services: {e}")
        return []

    def get_business_service(self, service_id: str) -> Optional[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/business_services/{service_id}', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('business_service')
        except Exception as e:
            logger.error(f"Error getting business service: {e}")
        return None

    def update_business_service_impact(self, service_id: str, status: str, message: str = None) -> bool:
        try:
            body = {'impactor': {'type': 'incident_reference', 'status': status}}
            if message:
                body['impactor']['message'] = message
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/business_services/{service_id}/impactors',
                headers=self.headers,
                json=body,
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error updating business service impact: {e}")
            return False

    def list_maintenance_windows(self, service_ids: List[str] = None, filter_: str = 'ongoing') -> List[Dict]:
        params = {'filter': filter_}
        if service_ids:
            params['service_ids[]'] = service_ids
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/maintenance_windows', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json().get('maintenance_windows', [])
        except Exception as e:
            logger.error(f"Error listing maintenance windows: {e}")
        return []

    def create_maintenance_window(self, service_ids: List[str], start_time: str, end_time: str, description: str = None) -> Optional[Dict]:
        services = [{'id': sid, 'type': 'service_reference'} for sid in service_ids]
        body = {
            'maintenance_window': {
                'type': 'maintenance_window',
                'start_time': start_time,
                'end_time': end_time,
                'services': services
            }
        }
        if description:
            body['maintenance_window']['description'] = description
        try:
            resp = requests.post(f'{PAGERDUTY_API_URL}/maintenance_windows', headers=self.headers, json=body, timeout=10)
            if resp.ok:
                return resp.json().get('maintenance_window')
        except Exception as e:
            logger.error(f"Error creating maintenance window: {e}")
        return None

    def get_incident_alerts(self, incident_id: str) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incidents/{incident_id}/alerts', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('alerts', [])
        except Exception as e:
            logger.error(f"Error getting incident alerts: {e}")
        return []

    def update_incident_alert(self, incident_id: str, alert_id: str, status: str) -> bool:
        try:
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}/alerts/{alert_id}',
                headers=self.headers,
                json={'alert': {'type': 'alert', 'status': status}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error updating incident alert: {e}")
            return False

    def get_incident_timeline(self, incident_id: str) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incidents/{incident_id}/log_entries', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('log_entries', [])
        except Exception as e:
            logger.error(f"Error getting incident timeline: {e}")
        return []

    def list_tags(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/tags', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('tags', [])
        except Exception as e:
            logger.error(f"Error listing tags: {e}")
        return []

    def add_tags_to_entity(self, entity_type: str, entity_id: str, tag_ids: List[str]) -> bool:
        tags = [{'id': tid, 'type': 'tag_reference'} for tid in tag_ids]
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/{entity_type}/{entity_id}/tags',
                headers=self.headers,
                json={'tags': tags},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error adding tags: {e}")
            return False

    def get_analytics_incident_metrics(self, since: str, until: str, service_ids: List[str] = None) -> Optional[Dict]:
        params = {'since': since, 'until': until}
        if service_ids:
            params['service_ids[]'] = service_ids
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/analytics/metrics/incidents/all', headers=self.headers, params=params, timeout=10)
            if resp.ok:
                return resp.json()
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
        return None

    def send_event(self, routing_key: str, event_action: str, dedup_key: str, payload: Dict) -> bool:
        body = {
            'routing_key': routing_key,
            'event_action': event_action,
            'dedup_key': dedup_key,
            'payload': payload
        }
        try:
            resp = requests.post('https://events.pagerduty.com/v2/enqueue', json=body, timeout=10)
            return resp.ok
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            return False

    def create_change_event(self, routing_key: str, summary: str, source: str, custom_details: Dict = None) -> bool:
        body = {
            'routing_key': routing_key,
            'payload': {
                'summary': summary,
                'source': source,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        if custom_details:
            body['payload']['custom_details'] = custom_details
        try:
            resp = requests.post('https://events.pagerduty.com/v2/change/enqueue', json=body, timeout=10)
            return resp.ok
        except Exception as e:
            logger.error(f"Error creating change event: {e}")
            return False

    def list_custom_fields(self) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/incidents/custom_fields', headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('fields', [])
        except Exception as e:
            logger.error(f"Error listing custom fields: {e}")
        return []

    def update_incident_custom_fields(self, incident_id: str, user_email: str, custom_fields: List[Dict]) -> bool:
        try:
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json={'incident': {'type': 'incident_reference', 'custom_fields': custom_fields}},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error updating custom fields: {e}")
            return False

    def list_automation_actions(self, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f'{PAGERDUTY_API_URL}/automation_actions/actions', headers=self.headers, params={'limit': limit}, timeout=10)
            if resp.ok:
                return resp.json().get('actions', [])
        except Exception as e:
            logger.error(f"Error listing automation actions: {e}")
        return []

    def invoke_automation_action(self, action_id: str, incident_id: str = None) -> Optional[Dict]:
        body = {}
        if incident_id:
            body = {'incident': {'id': incident_id, 'type': 'incident_reference'}}
        try:
            resp = requests.post(
                f'{PAGERDUTY_API_URL}/automation_actions/actions/{action_id}/invocations',
                headers=self.headers,
                json=body,
                timeout=10
            )
            if resp.ok:
                return resp.json()
        except Exception as e:
            logger.error(f"Error invoking automation action: {e}")
        return None

    def get_current_oncall_user(self, escalation_policy_id: str) -> Optional[Dict]:
        oncalls = self.get_oncalls(escalation_policy_ids=[escalation_policy_id])
        for oncall in oncalls:
            if oncall.get('escalation_level') == 1:
                return oncall.get('user')
        return None

    def escalate_incident(self, incident_id: str, user_email: str, escalation_level: int = None) -> bool:
        try:
            body = {'incident': {'type': 'incident_reference', 'escalation_level': escalation_level or 2}}
            resp = requests.put(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers={**self.headers, 'From': user_email},
                json=body,
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error escalating incident: {e}")
            return False


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
    
    def invite_users_to_channel(self, channel_id: str, user_ids: List[str]) -> int:
        success_count = 0
        for user_id in user_ids:
            if not user_id:
                continue
            try:
                resp = requests.post(
                    'https://slack.com/api/conversations.invite',
                    headers=self.headers,
                    json={'channel': channel_id, 'users': user_id},
                    timeout=10
                )
                data = resp.json()
                if data.get('ok'):
                    logger.info(f"Invited user {user_id} to channel {channel_id}")
                    success_count += 1
                elif data.get('error') == 'already_in_channel':
                    logger.info(f"User {user_id} already in channel {channel_id}")
                    success_count += 1
                elif data.get('error') == 'cant_invite_self':
                    logger.info(f"Bot is {user_id}, skipping self-invite")
                    success_count += 1
                else:
                    logger.warning(f"Failed to invite {user_id} to {channel_id}: {data.get('error')}")
            except Exception as e:
                logger.error(f"Error inviting user {user_id}: {e}")
        logger.info(f"Invited {success_count}/{len(user_ids)} users to channel {channel_id}")
        return success_count
    
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
        'incident.unacknowledged': lambda: on_incident_unacknowledged(incident_id, incident_data, state),
        'incident.delegated': lambda: on_incident_delegated(incident_id, incident_data, state),
        'incident.escalated': lambda: on_incident_escalated(incident_id, incident_data, state),
        'incident.reassigned': lambda: on_incident_reassigned(incident_id, incident_data, state),
        'incident.responder.added': lambda: on_responder_added(incident_id, event_data, state),
        'incident.responder.replied': lambda: on_responder_replied(incident_id, event_data, state),
        'incident.annotated': lambda: on_action_completed(incident_id, 'add_note', state),
        'incident.status_update_published': lambda: on_action_completed(incident_id, 'status_update', state),
        'incident.priority_updated': lambda: on_priority_updated(incident_id, event_data, state),
        'incident.reopened': lambda: on_incident_reopened(incident_id, incident_data, state),
        'incident.urgency_updated': lambda: on_urgency_updated(incident_id, event_data, state),
        'workflow.completed': lambda: on_workflow_completed(incident_id, event_data, state),
        'service.created': lambda: on_service_event('created', event_data),
        'service.updated': lambda: on_service_event('updated', event_data),
        'service.deleted': lambda: on_service_event('deleted', event_data),
    }

    handler = handlers.get(event_type)
    if handler:
        handler()
    else:
        logger.info(f"Unhandled event type: {event_type}")

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
        'acknowledged_at': datetime.now(timezone.utc).isoformat(),
        'ack_attempts': 0
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


def on_incident_escalated(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident escalated: {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        logger.warning(f"No demo state for {incident_id}, creating new state for escalated incident")
        on_incident_triggered(incident_id, incident_data, state)
        return

    if demo.get('paused'):
        logger.info(f"Demo {incident_id} is paused, skipping escalation handling")
        return

    current_level = incident_data.get('escalation_level', 1)
    ack_attempts = demo.get('ack_attempts', 0) + 1

    assignments = incident_data.get('assignments', [])
    new_assignee_id = None
    if assignments:
        new_assignee_id = assignments[0].get('assignee', {}).get('id')

    state.update(incident_id, {
        'escalation_level': current_level,
        'ack_attempts': ack_attempts,
        'last_escalation_at': datetime.now(timezone.utc).isoformat()
    })

    if new_assignee_id:
        new_responder = next((u for u in DEMO_USERS if u['id'] == new_assignee_id), None)
        if new_responder:
            responders = demo.get('responders', [])
            if new_responder not in responders:
                responders.insert(0, new_responder)
                state.update(incident_id, {'responders': responders})

    config = DEMO_CONFIG
    max_attempts = config.get('max_ack_attempts', 3)

    if ack_attempts >= max_attempts:
        logger.info(f"Max ack attempts ({max_attempts}) reached for {incident_id}, forcing acknowledgment")
        schedule_action(incident_id, 'force_acknowledge', 5, new_assignee_id)
    else:
        delay = random.randint(
            config.get('escalation_ack_delay_min', 15),
            config.get('escalation_ack_delay_max', 45)
        )
        schedule_action(incident_id, 'acknowledge', delay, new_assignee_id)
        logger.info(f"Escalated to level {current_level}, scheduled ack in {delay}s (attempt {ack_attempts + 1})")


def on_incident_unacknowledged(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident unacknowledged (timeout): {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        return

    if demo.get('paused'):
        return

    state.update(incident_id, {
        'state': 'triggered',
        'acknowledged_at': None
    })

    responders = demo.get('responders', [])
    if responders:
        delay = random.randint(15, 45)
        schedule_action(incident_id, 'acknowledge', delay, responders[0]['id'])
        logger.info(f"Incident timed out, rescheduling ack in {delay}s")


def on_incident_delegated(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident delegated: {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        return

    assignments = incident_data.get('assignments', [])
    if assignments:
        new_assignee = assignments[0].get('assignee', {})
        new_id = new_assignee.get('id')

        demo_user = next((u for u in DEMO_USERS if u['id'] == new_id), None)
        if demo_user:
            responders = demo.get('responders', [])
            responders = [demo_user] + [r for r in responders if r['id'] != new_id]
            state.update(incident_id, {'responders': responders})

            if demo.get('state') == 'triggered':
                delay = random.randint(30, 90)
                schedule_action(incident_id, 'acknowledge', delay, new_id)


def on_incident_reassigned(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident reassigned: {incident_id}")
    on_incident_delegated(incident_id, incident_data, state)


def on_incident_reopened(incident_id: str, incident_data: Dict, state: DemoState):
    logger.info(f"Incident reopened: {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        on_incident_triggered(incident_id, incident_data, state)
        return

    state.update(incident_id, {
        'state': 'triggered',
        'acknowledged_at': None,
        'resolver_id': None
    })

    responders = demo.get('responders', [])
    if responders:
        delay = random.randint(20, 60)
        schedule_action(incident_id, 'acknowledge', delay, responders[0]['id'])


def on_responder_replied(incident_id: str, event_data: Dict, state: DemoState):
    logger.info(f"Responder replied to {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        return

    responder = event_data.get('data', {}).get('responder', {})
    responder_id = responder.get('id', '')
    reply_type = event_data.get('data', {}).get('responder_request_response', {}).get('response', '')

    responder_actions = demo.get('responder_actions', {})
    if responder_id in responder_actions:
        responder_actions[responder_id]['replied'] = True
        responder_actions[responder_id]['reply_type'] = reply_type
        state.update(incident_id, {'responder_actions': responder_actions})


def on_priority_updated(incident_id: str, event_data: Dict, state: DemoState):
    logger.info(f"Priority updated for {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        return

    priority = event_data.get('data', {}).get('priority', {})
    state.update(incident_id, {
        'priority_id': priority.get('id'),
        'priority_name': priority.get('summary')
    })


def on_urgency_updated(incident_id: str, event_data: Dict, state: DemoState):
    logger.info(f"Urgency updated for {incident_id}")

    demo = state.get(incident_id)
    if not demo:
        return

    urgency = event_data.get('data', {}).get('urgency')
    state.update(incident_id, {'urgency': urgency})


def on_service_event(action: str, event_data: Dict):
    logger.info(f"Service {action}: {event_data.get('data', {}).get('id')}")


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
    user_ids = [CONALL_SLACK_USER_ID, CONALL_SLACK_USER_ID_PERSONAL]
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
        incident = pd.get_incident(incident_id)
        if incident and incident.get('status') == 'triggered':
            pd.acknowledge_incident(incident_id, user_email)
            if slack_channel:
                slack.post_message(slack_channel, f"{user['name']}: {get_conversation_message('investigating')}")
        else:
            logger.info(f"Incident {incident_id} not in triggered state, skipping ack")

    elif action == 'force_acknowledge':
        incident = pd.get_incident(incident_id)
        if incident and incident.get('status') == 'triggered':
            pd.acknowledge_incident(incident_id, user_email)
            logger.info(f"Force acknowledged {incident_id} after max escalation attempts")
            pd.add_note(incident_id, user_email, "[Auto-Response] Incident acknowledged after escalation timeout.")
            if slack_channel:
                slack.post_message(slack_channel, f"[System] Incident auto-acknowledged after escalation. {user['name']} is now responding.")

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


def trigger_datadog(scenario: Dict) -> Dict:
    api_key = os.environ.get('DATADOG_API_KEY', '')
    site = os.environ.get('DATADOG_SITE', 'us5.datadoghq.com')

    if not api_key:
        return {'success': False, 'error': 'DATADOG_API_KEY not configured'}

    scenario_id = scenario.get('id', '').lower()
    title = scenario.get('title', '')

    metric_configs = {
        'api-latency': {'metric': 'demo.api.response_time', 'value': 650, 'threshold': 500},
        'database-connection': {'metric': 'demo.database.connections', 'value': 95, 'threshold': 90},
        'high-error-rate': {'metric': 'demo.api.error_rate', 'value': 8, 'threshold': 5},
        'memory-exhaustion': {'metric': 'demo.memory.usage', 'value': 98, 'threshold': 95},
        'queue-backlog': {'metric': 'demo.queue.depth', 'value': 1500, 'threshold': 1000},
    }

    config = None
    for key, cfg in metric_configs.items():
        if key in scenario_id or key in title.lower():
            config = cfg
            break

    if not config:
        config = metric_configs['api-latency']

    now = int(datetime.now(timezone.utc).timestamp())
    points = [[now - i * 10, config['value'] + (i % 3) * 10] for i in range(6)]

    series_payload = {
        'series': [{
            'metric': config['metric'],
            'points': points,
            'type': 'gauge',
            'tags': [
                f"scenario:{scenario.get('id', 'unknown')}",
                f"integration:datadog",
                'demo:true',
                'env:demo-simulator'
            ]
        }]
    }

    try:
        resp = requests.post(
            f'https://api.{site}/api/v1/series',
            headers={'DD-API-KEY': api_key, 'Content-Type': 'application/json'},
            json=series_payload,
            timeout=15
        )
        if resp.ok:
            return {
                'success': True,
                'metric': config['metric'],
                'value': config['value'],
                'threshold': config['threshold'],
                'message': f"Sent metric {config['metric']}={config['value']} (threshold: {config['threshold']}). Monitor will trigger shortly."
            }
        return {'success': False, 'error': f'Datadog API returned {resp.status_code}: {resp.text}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def trigger_grafana(scenario: Dict) -> Dict:
    api_key = os.environ.get('GRAFANA_API_KEY', '')
    url = os.environ.get('GRAFANA_URL', '')

    if not api_key or not url:
        return {'success': False, 'error': 'GRAFANA_API_KEY or GRAFANA_URL not configured'}

    annotation = {
        'text': f"[DEMO] {scenario.get('title', 'Demo Incident')}: {scenario.get('description', '')}",
        'tags': ['demo', 'pagerduty', scenario.get('id', 'unknown')],
        'time': int(datetime.now(timezone.utc).timestamp() * 1000)
    }

    try:
        resp = requests.post(
            f'{url}/api/annotations',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json=annotation,
            timeout=15
        )
        if resp.ok:
            return {'success': True, 'response': resp.json()}
        return {'success': False, 'error': f'Grafana API returned {resp.status_code}: {resp.text}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def trigger_newrelic(scenario: Dict) -> Dict:
    api_key = os.environ.get('NEWRELIC_API_KEY', '')
    account_id = os.environ.get('NEWRELIC_ACCOUNT_ID', '')

    if not api_key:
        return {'success': False, 'error': 'NEWRELIC_API_KEY not configured'}

    event = {
        'eventType': 'PagerDutyDemo',
        'title': f"[DEMO] {scenario.get('title', 'Demo Incident')}",
        'description': scenario.get('description', 'Demo incident triggered'),
        'scenarioId': scenario.get('id', 'unknown'),
        'integration': scenario.get('integration', 'newrelic'),
        'demo': True
    }

    try:
        url = f'https://insights-collector.newrelic.com/v1/accounts/{account_id}/events' if account_id else 'https://insights-collector.newrelic.com/v1/events'
        resp = requests.post(
            url,
            headers={'Api-Key': api_key, 'Content-Type': 'application/json'},
            json=event,
            timeout=15
        )
        if resp.ok:
            return {'success': True, 'response': resp.json() if resp.text else {'status': 'accepted'}}
        return {'success': False, 'error': f'New Relic API returned {resp.status_code}: {resp.text}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def trigger_cloudwatch(scenario: Dict) -> Dict:
    try:
        cloudwatch = boto3.client('cloudwatch')
        metric_name = scenario.get('metric_name', 'DemoIncidentMetric')
        namespace = os.environ.get('CLOUDWATCH_NAMESPACE', 'PagerDutyDemo')

        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[{
                'MetricName': metric_name,
                'Value': scenario.get('metric_value', 100),
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ScenarioId', 'Value': scenario.get('id', 'unknown')},
                    {'Name': 'Demo', 'Value': 'true'}
                ]
            }]
        )
        return {'success': True, 'message': f'Published metric {metric_name} to {namespace}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def trigger_pagerduty_events(scenario: Dict) -> Dict:
    routing_key = scenario.get('routing_key') or os.environ.get('PAGERDUTY_ROUTING_KEY', '')

    if not routing_key:
        return {'success': False, 'error': 'No routing key provided or configured'}

    payload = {
        'routing_key': routing_key,
        'event_action': 'trigger',
        'dedup_key': f"demo-{scenario.get('id', 'unknown')}-{int(datetime.now().timestamp())}",
        'payload': {
            'summary': f"[DEMO] {scenario.get('title', 'Demo Incident')}",
            'severity': scenario.get('severity', 'error'),
            'source': scenario.get('integration', 'demo-picker'),
            'custom_details': {
                'scenario_id': scenario.get('id'),
                'scenario_name': scenario.get('title'),
                'description': scenario.get('description', ''),
                'triggered_by': 'Demo Picker UI'
            }
        }
    }

    if scenario.get('service_key'):
        payload['payload']['custom_details']['service_key'] = scenario.get('service_key')

    try:
        resp = requests.post(
            PAGERDUTY_EVENTS_URL,
            json=payload,
            timeout=15
        )
        if resp.ok:
            return {'success': True, 'response': resp.json()}
        return {'success': False, 'error': f'PagerDuty Events API returned {resp.status_code}: {resp.text}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def handle_trigger(body: Dict) -> Dict:
    integration = body.get('integration', '').lower()
    scenario = body.get('scenario', {})
    use_fallback = body.get('use_fallback', False)

    if not scenario:
        return {'success': False, 'error': 'No scenario provided'}

    result = {'integration': integration, 'fallback_used': False}

    if use_fallback:
        trigger_result = trigger_pagerduty_events(scenario)
        result['fallback_used'] = True
    else:
        triggers = {
            'datadog': trigger_datadog,
            'grafana': trigger_grafana,
            'newrelic': trigger_newrelic,
            'cloudwatch': trigger_cloudwatch,
            'pagerduty': trigger_pagerduty_events,
        }

        trigger_fn = triggers.get(integration)
        if trigger_fn:
            trigger_result = trigger_fn(scenario)
            if not trigger_result.get('success'):
                logger.warning(f"Integration {integration} failed: {trigger_result.get('error')}. Using fallback.")
                trigger_result = trigger_pagerduty_events(scenario)
                result['fallback_used'] = True
                result['original_error'] = trigger_result.get('error')
        else:
            trigger_result = trigger_pagerduty_events(scenario)
            result['fallback_used'] = True
            result['reason'] = f'Integration {integration} not supported, using PagerDuty Events API'

    result.update(trigger_result)
    return result


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

    elif '/trigger' in path and method == 'POST':
        result = handle_trigger(body)
        status_code = 200 if result.get('success') else 400
        return {'statusCode': status_code, 'headers': cors_headers, 'body': json.dumps(result)}

    elif '/integrations' in path and method == 'GET':
        integrations = {
            'datadog': {'configured': bool(os.environ.get('DATADOG_API_KEY')), 'site': os.environ.get('DATADOG_SITE', 'us5.datadoghq.com')},
            'grafana': {'configured': bool(os.environ.get('GRAFANA_API_KEY') and os.environ.get('GRAFANA_URL'))},
            'newrelic': {'configured': bool(os.environ.get('NEWRELIC_API_KEY'))},
            'cloudwatch': {'configured': True},
            'pagerduty': {'configured': bool(os.environ.get('PAGERDUTY_ROUTING_KEY'))}
        }
        return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'integrations': integrations})}

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
