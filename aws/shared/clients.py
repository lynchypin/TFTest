import os
import logging
import requests
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

PAGERDUTY_API_URL = 'https://api.pagerduty.com'
PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue'

CONALL_EMAIL = 'clynch@pagerduty.com'
CONALL_SLACK_USER_ID = 'U0A9KAMT0BF'
SLACK_WORKSPACE_ID = 'T0A9LN53CPQ'

DEMO_USERS = [
    {'id': 'PG6UTES', 'email': 'jbeam@losandesgaa.onmicrosoft.com', 'name': 'Jim Beam', 'slack_id': 'U0AA1LZSYHX'},
    {'id': 'PR0E7IK', 'email': 'jdaniels@losandesgaa.onmicrosoft.com', 'name': 'Jack Daniels', 'slack_id': 'U0A9GC08EV9'},
    {'id': 'PCX6T22', 'email': 'jcasker@losandesgaa.onmicrosoft.com', 'name': 'Jameson Casker', 'slack_id': 'U0AA1LYLH2M'},
    {'id': 'PVOXRAP', 'email': 'jcuervo@losandesgaa.onmicrosoft.com', 'name': 'Jose Cuervo', 'slack_id': 'U0A9LN3QVC6'},
    {'id': 'PNRT76X', 'email': 'gtonic@losandesgaa.onmicrosoft.com', 'name': 'Ginny Tonic', 'slack_id': 'U0A9KANFCLV'},
    {'id': 'PYKISPC', 'email': 'aguiness@losandesgaa.onmicrosoft.com', 'name': 'Arthur Guinness', 'slack_id': 'U0A9SBF3MTN'},
]

PAGERDUTY_TO_SLACK_USER_MAP = {user['email']: user['slack_id'] for user in DEMO_USERS}

_cached_users = None


class PagerDutyClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('PAGERDUTY_TOKEN') or os.environ.get('PAGERDUTY_ADMIN_TOKEN', '')
        self.headers = {
            'Authorization': f'Token token={self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def trigger_incident(
        self,
        routing_key: str,
        summary: str,
        severity: str,
        source: str,
        dedup_key: str,
        custom_details: Optional[Dict] = None,
        add_demo_prefix: bool = True,
    ) -> Dict[str, Any]:
        title = f"[DEMO] {summary}" if add_demo_prefix and not summary.startswith('[DEMO]') else summary
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": title,
                "severity": severity,
                "source": source,
                "custom_details": custom_details or {},
            },
        }
        logger.info(f"Triggering incident: routing_key={routing_key[:8]}..., summary={summary}")
        try:
            response = requests.post(PAGERDUTY_EVENTS_URL, json=payload, timeout=10)
            logger.info(f"PagerDuty response: status={response.status_code}")
            if response.status_code != 202:
                return {"success": False, "error": response.text, "status_code": response.status_code}
            return {"success": True, **response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_demo_incidents(self, statuses: list = None) -> list:
        if statuses is None:
            statuses = ['triggered', 'acknowledged']
        
        params = '&'.join([f'statuses[]={s}' for s in statuses])
        url = f'{PAGERDUTY_API_URL}/incidents?{params}&limit=100'
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.ok:
                incidents = resp.json().get('incidents', [])
                return [i for i in incidents if i.get('title', '').startswith('[DEMO]')]
            logger.error(f"Failed to get incidents: {resp.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error getting incidents: {e}")
            return []
    
    def list_recent_incidents(self, minutes: int = 15, statuses: list = None) -> List[Dict]:
        if statuses is None:
            statuses = ['triggered', 'acknowledged']
        since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/incidents',
                headers=self.headers,
                params={'statuses[]': statuses, 'since': since},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('incidents', [])
        except Exception as e:
            logger.error(f"Error listing incidents: {e}")
        return []
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/incidents/{incident_id}',
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('incident')
        except Exception as e:
            logger.error(f"Error getting incident: {e}")
        return None
    
    def list_users(self) -> List[Dict]:
        global _cached_users
        if _cached_users is not None:
            return _cached_users
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/users',
                headers=self.headers,
                params={'limit': 100},
                timeout=10
            )
            if response.status_code == 200:
                users = response.json().get('users', [])
                _cached_users = [
                    {
                        'id': u.get('id'),
                        'name': u.get('name'),
                        'email': u.get('email', ''),
                        'role': u.get('role', 'user'),
                        'job_title': u.get('job_title', ''),
                    }
                    for u in users
                ]
                logger.info(f"Fetched {len(_cached_users)} PagerDuty users")
                return _cached_users
            logger.error(f"Failed to list users: {response.status_code}")
        except Exception as e:
            logger.error(f"Error listing users: {e}")
        return []
    
    def resolve_incident(self, incident_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'status': 'resolved'
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def acknowledge_incident(self, incident_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'status': 'acknowledged'
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_note(self, incident_id: str, content: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/notes'
        payload = {'note': {'content': content}}
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_windows(self, filter_type: str = 'ongoing') -> list:
        url = f'{PAGERDUTY_API_URL}/maintenance_windows?filter={filter_type}'
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.ok:
                return resp.json().get('maintenance_windows', [])
            return []
        except Exception as e:
            logger.error(f"Error getting maintenance windows: {e}")
            return []
    
    def delete_maintenance_window(self, window_id: str) -> dict:
        url = f'{PAGERDUTY_API_URL}/maintenance_windows/{window_id}'
        
        try:
            resp = requests.delete(url, headers=self.headers, timeout=10)
            return {'success': resp.status_code in [200, 204], 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def snooze_incident(self, incident_id: str, duration_seconds: int = 3600, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/snooze'
        payload = {'duration': duration_seconds}
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reassign_incident(self, incident_id: str, assignee_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'assignments': [{'assignee': {'id': assignee_id, 'type': 'user_reference'}}]
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def change_priority(self, incident_id: str, priority_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'priority': {'id': priority_id, 'type': 'priority_reference'}
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email

        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_responders(self, incident_id: str, responder_ids: list, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/responder_requests'
        payload = {
            'requester_id': user_email or 'unknown',
            'message': 'Requesting assistance with this incident',
            'responder_request_targets': [
                {'responder_request_target': {'id': rid, 'type': 'user_reference'}}
                for rid in responder_ids
            ]
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_urgency(self, incident_id: str, urgency: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'urgency': urgency
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email

        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_incident_assignee(self, incident: dict, demo_users: list = None) -> dict:
        users = demo_users or DEMO_USERS
        assignments = incident.get('assignments', [])
        if assignments:
            assignee_ref = assignments[0].get('assignee', {})
            assignee_id = assignee_ref.get('id')
            for user in users:
                if user['id'] == assignee_id:
                    return user
        return random.choice(users)
    
    def get_incident_responders(self, incident: Dict) -> List[Dict]:
        responders = []
        for assignment in incident.get('assignments', []):
            assignee = assignment.get('assignee', {})
            if assignee.get('type') == 'user_reference':
                user_id = assignee.get('id')
                user_name = assignee.get('summary', 'Unknown')
                for user in DEMO_USERS:
                    if user['id'] == user_id:
                        responders.append(user)
                        break
                else:
                    responders.append({'id': user_id, 'name': user_name, 'email': '', 'slack_id': ''})
        return responders

    def trigger_sample_incident(self, routing_key: str, title: str, severity: str = 'warning') -> dict:
        return self.trigger_incident(
            routing_key=routing_key,
            summary=title,
            severity=severity,
            source='demo-simulator',
            dedup_key=f'demo-sample-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            custom_details={
                'created_by': 'Demo Simulator Lambda',
                'purpose': 'Sample incident for demo'
            }
        )

    def list_incidents(self, statuses: List[str], limit: int = 25, sort_by: str = 'created_at:asc') -> List[Dict]:
        params = {
            'statuses[]': statuses,
            'sort_by': sort_by,
            'limit': limit,
        }
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/incidents',
                headers=self.headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('incidents', [])
            logger.error(f"Failed to list incidents: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error listing incidents: {e}")
        return []

    def list_escalation_policies(self) -> List[Dict]:
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/escalation_policies',
                headers=self.headers,
                params={'limit': 100},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('escalation_policies', [])
            logger.error(f"Failed to list escalation policies: {response.status_code}")
        except Exception as e:
            logger.error(f"Error listing escalation policies: {e}")
        return []

    def escalate_incident(self, incident_id: str, escalation_level: int = 2, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        payload = {
            'incident': {
                'type': 'incident_reference',
                'escalation_level': escalation_level,
            }
        }
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Escalated incident {incident_id} to level {escalation_level}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_priorities(self) -> List[Dict]:
        try:
            response = requests.get(
                f'{PAGERDUTY_API_URL}/priorities',
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('priorities', [])
        except Exception as e:
            logger.error(f"Error listing priorities: {e}")
        return []

    def post_status_update(self, incident_id: str, message: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/status_updates'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'status_update': {
                'message': message
            }
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Posted status update to incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def run_automation_action(self, action_id: str, incident_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/automation_actions/invocations'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'invocation': {
                'action': {'id': action_id, 'type': 'action_reference'},
                'incident': {'id': incident_id, 'type': 'incident_reference'}
            }
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Invoked automation action {action_id} on incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code, 'data': resp.json() if resp.ok else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_workflow(self, workflow_id: str, incident_id: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incident_workflows/instances'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'incident_workflow_instance': {
                'incident_workflow': {'id': workflow_id, 'type': 'incident_workflow_reference'},
                'incident': {'id': incident_id, 'type': 'incident_reference'}
            }
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Triggered workflow {workflow_id} on incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code, 'data': resp.json() if resp.ok else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_custom_fields(self, incident_id: str, field_values: Dict[str, Any], user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        custom_fields = [
            {'id': field_id, 'value': value}
            for field_id, value in field_values.items()
        ]
        payload = {
            'incident': {
                'type': 'incident_reference',
                'custom_fields': custom_fields
            }
        }
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Updated custom fields on incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_incident_type(self, incident_id: str, incident_type: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'incident': {
                'type': 'incident_reference',
                'incident_type': {'type': 'incident_type_reference', 'name': incident_type}
            }
        }
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Updated incident type to {incident_type} on {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def resolve_via_events_api(self, routing_key: str, dedup_key: str) -> dict:
        payload = {
            'routing_key': routing_key,
            'event_action': 'resolve',
            'dedup_key': dedup_key
        }
        try:
            resp = requests.post(PAGERDUTY_EVENTS_URL, json=payload, timeout=10)
            if resp.status_code == 202:
                logger.info(f"Resolved incident via Events API, dedup_key={dedup_key[:20]}...")
            return {'success': resp.status_code == 202, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_subscriber(self, incident_id: str, subscriber_id: str, subscriber_type: str = 'user', user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/subscribers'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'subscribers': [{'subscriber_id': subscriber_id, 'subscriber_type': subscriber_type}]
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Added subscriber {subscriber_id} to incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_subscriber_notification(self, incident_id: str, message: str, user_email: str = None) -> dict:
        url = f'{PAGERDUTY_API_URL}/incidents/{incident_id}/status_updates/subscribers'
        headers = {**self.headers}
        if user_email:
            headers['From'] = user_email
        payload = {
            'status_update': {'message': message}
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logger.info(f"Sent subscriber notification for incident {incident_id}")
            return {'success': resp.ok, 'status_code': resp.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class SlackClient:
    def __init__(self, token: str = None, default_channel: str = None):
        self.token = token or os.environ.get('SLACK_BOT_TOKEN', '')
        self.default_channel = default_channel or os.environ.get('SLACK_CHANNEL', '')
        self.api_base = 'https://slack.com/api'
    
    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def post_message(self, text: str, channel: str = None, blocks: List[Dict] = None) -> Dict[str, Any]:
        if not self.token:
            return {'ok': False, 'error': 'no_token'}
        
        target_channel = channel or self.default_channel
        if not target_channel:
            return {'ok': False, 'error': 'no_channel'}
        
        payload = {'channel': target_channel, 'text': text}
        if blocks:
            payload['blocks'] = blocks
        
        try:
            resp = requests.post(
                f'{self.api_base}/chat.postMessage',
                headers=self._headers(),
                json=payload,
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def send_dm(self, user_id: str, text: str, blocks: List[Dict] = None) -> Dict[str, Any]:
        if not self.token:
            return {'ok': False, 'error': 'no_token'}
        
        try:
            open_resp = requests.post(
                f'{self.api_base}/conversations.open',
                headers=self._headers(),
                json={'users': user_id},
                timeout=10
            )
            open_data = open_resp.json()
            if not open_data.get('ok'):
                logger.error(f"Failed to open DM: {open_data}")
                return open_data
            dm_channel = open_data['channel']['id']
            return self.post_message(text, dm_channel, blocks)
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def get_recent_channels(self, minutes: int = 10) -> List[Dict]:
        if not self.token:
            return []
        try:
            response = requests.get(
                f'{self.api_base}/conversations.list',
                headers=self._headers(),
                params={'types': 'public_channel,private_channel', 'limit': 100},
                timeout=10
            )
            data = response.json()
            if not data.get('ok'):
                logger.error(f"Failed to list channels: {data.get('error')}")
                return []
            
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            recent = []
            for ch in data.get('channels', []):
                created = datetime.fromtimestamp(ch.get('created', 0), tz=timezone.utc)
                if created > cutoff:
                    recent.append(ch)
            return recent
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return []
    
    def get_channel_messages(self, channel_id: str, limit: int = 5) -> List[Dict]:
        if not self.token:
            return []
        try:
            response = requests.get(
                f'{self.api_base}/conversations.history',
                headers=self._headers(),
                params={'channel': channel_id, 'limit': limit},
                timeout=10
            )
            data = response.json()
            if data.get('ok'):
                return data.get('messages', [])
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
        return []
    
    def invite_user_to_channel(self, channel_id: str, user_id: str) -> Dict[str, Any]:
        if not self.token:
            return {'ok': False, 'error': 'no_token'}
        try:
            response = requests.post(
                f'{self.api_base}/conversations.invite',
                headers=self._headers(),
                json={'channel': channel_id, 'users': user_id},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        if not self.token:
            return {'ok': False, 'error': 'no_token'}
        try:
            response = requests.post(
                f'{self.api_base}/conversations.create',
                headers=self._headers(),
                json={'name': name, 'is_private': is_private},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def find_channel_by_pattern(self, pattern: str) -> Optional[str]:
        if not self.token:
            return None
        try:
            response = requests.get(
                f'{self.api_base}/conversations.list',
                headers=self._headers(),
                params={'types': 'public_channel,private_channel', 'limit': 200},
                timeout=10
            )
            data = response.json()
            if data.get('ok'):
                import re
                for channel in data.get('channels', []):
                    if re.search(pattern, channel.get('name', '')):
                        return channel['id']
        except Exception as e:
            logger.error(f"Error finding channel: {e}")
        return None

    def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        if not self.token:
            return None
        try:
            response = requests.get(
                f'{self.api_base}/conversations.info',
                headers=self._headers(),
                params={'channel': channel_id},
                timeout=10
            )
            data = response.json()
            if data.get('ok'):
                return data.get('channel')
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
        return None

    def invite_users_to_channel(self, channel_id: str, user_ids: List[str]) -> Dict[str, Any]:
        if not self.token:
            return {'ok': False, 'error': 'no_token'}
        if not user_ids:
            return {'ok': True, 'already_in_channel': True}
        try:
            response = requests.post(
                f'{self.api_base}/conversations.invite',
                headers=self._headers(),
                json={'channel': channel_id, 'users': ','.join(user_ids)},
                timeout=10
            )
            data = response.json()
            if data.get('ok'):
                logger.info(f"Invited {len(user_ids)} users to channel {channel_id}")
            elif data.get('error') == 'already_in_channel':
                logger.info(f"Users already in channel {channel_id}")
                return {'ok': True, 'already_in_channel': True}
            else:
                logger.error(f"Failed to invite users: {data.get('error')}")
            return data
        except Exception as e:
            logger.error(f"Error inviting users to channel: {e}")
            return {'ok': False, 'error': str(e)}


class SlackNotifier(SlackClient):
    def __init__(self, token: str = None, channel: str = None):
        super().__init__(token, channel)
    
    def post(self, message: str, channel: str = None) -> dict:
        result = self.post_message(message, channel)
        if result.get('ok'):
            return result
        return {'status': 'error' if 'error' in result else 'skipped', 'reason': result.get('error', 'unknown')}
