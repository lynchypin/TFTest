import json
import os
import logging
from datetime import datetime
import requests

from shared import SlackNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGERDUTY_TOKEN = os.environ.get('PAGERDUTY_TOKEN', '')
DATADOG_API_KEY = os.environ.get('DATADOG_API_KEY', '')
DATADOG_SITE = os.environ.get('DATADOG_SITE', 'us5.datadoghq.com')
NEW_RELIC_API_KEY = os.environ.get('NEW_RELIC_API_KEY', '')
GRAFANA_TOKEN = os.environ.get('GRAFANA_TOKEN', '')
GRAFANA_URL = os.environ.get('GRAFANA_URL', 'https://conalllynch88.grafana.net')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'C0A9GCXFSBD')
JIRA_URL = os.environ.get('JIRA_URL', 'https://losandes.atlassian.net')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL', '')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN', '')


class HealthChecker:
    def __init__(self):
        self.results = {}
        self.timeout = 10
    
    def check_pagerduty(self) -> dict:
        if not PAGERDUTY_TOKEN:
            return {'status': 'SKIPPED', 'reason': 'No token configured'}
        
        try:
            resp = requests.get(
                'https://api.pagerduty.com/users/me',
                headers={'Authorization': f'Token token={PAGERDUTY_TOKEN}'},
                timeout=self.timeout
            )
            if resp.ok:
                user = resp.json().get('user', {})
                return {'status': 'OK', 'user': user.get('email', 'Unknown')}
            return {'status': 'FAILED', 'code': resp.status_code, 'reason': resp.text[:100]}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def check_datadog(self) -> dict:
        if not DATADOG_API_KEY:
            return {'status': 'SKIPPED', 'reason': 'No API key configured'}
        
        try:
            resp = requests.get(
                f'https://api.{DATADOG_SITE}/api/v1/validate',
                headers={'DD-API-KEY': DATADOG_API_KEY},
                timeout=self.timeout
            )
            if resp.ok:
                return {'status': 'OK', 'valid': resp.json().get('valid', False)}
            return {'status': 'FAILED', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def check_newrelic(self) -> dict:
        if not NEW_RELIC_API_KEY:
            return {'status': 'SKIPPED', 'reason': 'No API key configured'}
        
        try:
            resp = requests.get(
                'https://api.newrelic.com/v2/users.json',
                headers={'Api-Key': NEW_RELIC_API_KEY},
                timeout=self.timeout
            )
            if resp.ok:
                return {'status': 'OK'}
            return {'status': 'FAILED', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def check_grafana(self) -> dict:
        if not GRAFANA_TOKEN:
            return {'status': 'SKIPPED', 'reason': 'No token configured'}
        
        try:
            resp = requests.get(
                f'{GRAFANA_URL}/api/health',
                headers={'Authorization': f'Bearer {GRAFANA_TOKEN}'},
                timeout=self.timeout
            )
            if resp.ok:
                return {'status': 'OK', 'version': resp.json().get('version', 'Unknown')}
            return {'status': 'FAILED', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def check_slack(self) -> dict:
        if not SLACK_BOT_TOKEN:
            return {'status': 'SKIPPED', 'reason': 'No token configured'}
        
        try:
            resp = requests.post(
                'https://slack.com/api/auth.test',
                headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'},
                timeout=self.timeout
            )
            data = resp.json()
            if data.get('ok'):
                return {'status': 'OK', 'team': data.get('team', 'Unknown'), 'user': data.get('user', 'Unknown')}
            return {'status': 'FAILED', 'error': data.get('error', 'Unknown error')}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def check_jira(self) -> dict:
        if not JIRA_EMAIL or not JIRA_TOKEN:
            return {'status': 'SKIPPED', 'reason': 'No credentials configured'}
        
        try:
            import base64
            auth = base64.b64encode(f'{JIRA_EMAIL}:{JIRA_TOKEN}'.encode()).decode()
            resp = requests.get(
                f'{JIRA_URL}/rest/api/3/myself',
                headers={'Authorization': f'Basic {auth}', 'Accept': 'application/json'},
                timeout=self.timeout
            )
            if resp.ok:
                return {'status': 'OK', 'user': resp.json().get('displayName', 'Unknown')}
            return {'status': 'FAILED', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'ERROR', 'reason': str(e)}
    
    def run_all_checks(self) -> dict:
        self.results = {
            'pagerduty': self.check_pagerduty(),
            'datadog': self.check_datadog(),
            'newrelic': self.check_newrelic(),
            'grafana': self.check_grafana(),
            'slack': self.check_slack(),
            'jira': self.check_jira(),
        }
        
        ok_count = sum(1 for r in self.results.values() if r.get('status') == 'OK')
        failed_count = sum(1 for r in self.results.values() if r.get('status') == 'FAILED')
        error_count = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')
        skipped_count = sum(1 for r in self.results.values() if r.get('status') == 'SKIPPED')
        
        self.results['summary'] = {
            'total': len(self.results) - 1,
            'ok': ok_count,
            'failed': failed_count,
            'error': error_count,
            'skipped': skipped_count,
            'overall': 'HEALTHY' if failed_count == 0 and error_count == 0 else 'DEGRADED'
        }
        
        return self.results
    
    def format_slack_message(self) -> str:
        lines = ['*Integration Health Check Report*', '```']

        for name, result in self.results.items():
            if name == 'summary':
                continue
            status = result.get('status', 'UNKNOWN')
            emoji = {'OK': '+', 'FAILED': '-', 'ERROR': '!', 'SKIPPED': '~'}.get(status, '?')
            lines.append(f"[{emoji}] {name.upper()}: {status}")

        lines.append('```')

        summary = self.results.get('summary', {})
        lines.append(f"*Overall: {summary.get('overall', 'UNKNOWN')}* | OK: {summary.get('ok', 0)} | Failed: {summary.get('failed', 0)} | Skipped: {summary.get('skipped', 0)}")

        return '\n'.join(lines)


def lambda_handler(event, context):
    logger.info(f"Integration Health Check invoked at {datetime.utcnow().isoformat()}")
    
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    for name, result in results.items():
        if name != 'summary':
            logger.info(f"{name}: {result.get('status', 'UNKNOWN')}")
    
    logger.info(f"Summary: {results.get('summary', {})}")
    
    post_to_slack = event.get('post_to_slack', True)
    if post_to_slack:
        slack = SlackNotifier(SLACK_BOT_TOKEN, SLACK_CHANNEL)
        message = checker.format_slack_message()
        slack_result = slack.post(message)
        results['slack_notification'] = slack_result
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Health check complete',
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        })
    }
