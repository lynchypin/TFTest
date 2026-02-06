import json
import os
import random
import time
import requests
from datetime import datetime

DATADOG_API_KEY = os.environ.get('DATADOG_API_KEY', '')
DATADOG_SITE = os.environ.get('DATADOG_SITE', 'us5.datadoghq.com')
NEW_RELIC_LICENSE_KEY = os.environ.get('NEW_RELIC_LICENSE_KEY', '')
NEW_RELIC_ACCOUNT_ID = os.environ.get('NEW_RELIC_ACCOUNT_ID', '')
PAGERDUTY_ROUTING_KEY = os.environ.get('PAGERDUTY_ROUTING_KEY', '')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '')

SERVICES = ['api-gateway', 'user-service', 'payment-service', 'inventory-service', 'auth-service']
HOSTS = ['prod-web-01', 'prod-web-02', 'prod-api-01', 'prod-db-01', 'prod-cache-01']

METRIC_DEFINITIONS = {
    'api.response_time': {'normal': (50, 200), 'spike': (800, 2500), 'threshold': 500},
    'api.error_rate': {'normal': (0.1, 2.0), 'spike': (8, 25), 'threshold': 5},
    'database.connections': {'normal': (10, 50), 'spike': (92, 99), 'threshold': 90},
    'system.memory_usage': {'normal': (40, 70), 'spike': (88, 96), 'threshold': 85},
    'system.cpu_usage': {'normal': (20, 60), 'spike': (85, 98), 'threshold': 80},
    'queue.depth': {'normal': (0, 100), 'spike': (1500, 3000), 'threshold': 1000},
    'cache.hit_rate': {'normal': (85, 99), 'spike': (20, 50), 'threshold': 60},
}

INCIDENT_TRIGGERS = {
    'api.response_time': {
        'title': '[DEMO] API Latency Degradation - {service}',
        'description': 'P95 latency for {service} has exceeded 500ms. Current: {value}ms',
        'severity': 'error',
    },
    'api.error_rate': {
        'title': '[DEMO] Elevated Error Rate - {service}',
        'description': 'Error rate for {service} is at {value}%, exceeding 5% threshold',
        'severity': 'critical',
    },
    'database.connections': {
        'title': '[DEMO] Database Connection Pool Exhaustion',
        'description': 'Active DB connections: {value}%. Connection pool near exhaustion.',
        'severity': 'critical',
    },
    'system.memory_usage': {
        'title': '[DEMO] Memory Pressure Alert on {host}',
        'description': 'Memory usage critical on {host}. Current: {value}%, Threshold: 85%',
        'severity': 'error',
    },
    'system.cpu_usage': {
        'title': '[DEMO] High CPU Usage on {host}',
        'description': 'CPU utilization has exceeded 80% threshold on {host}. Current value: {value}%',
        'severity': 'warning',
    },
    'queue.depth': {
        'title': '[DEMO] Message Queue Backlog Critical',
        'description': 'Queue depth has grown to {value} messages. Processing may be stalled.',
        'severity': 'error',
    },
    'cache.hit_rate': {
        'title': '[DEMO] Cache Performance Degradation',
        'description': 'Cache hit rate dropped to {value}%. Increased database load expected.',
        'severity': 'warning',
    },
}


class DatadogClient:
    def __init__(self, api_key: str, site: str):
        self.api_key = api_key
        self.site = site
        self.metrics_url = f'https://api.{site}/api/v2/series'
        self.logs_url = f'https://http-intake.logs.{site}/api/v2/logs'
    
    def send_metrics(self, metrics: list) -> dict:
        if not self.api_key:
            return {'status': 'skipped', 'reason': 'no api key'}
        
        payload = {'series': metrics}
        headers = {
            'DD-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            resp = requests.post(self.metrics_url, json=payload, headers=headers, timeout=10)
            return {'status': 'success' if resp.ok else 'error', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def send_logs(self, logs: list) -> dict:
        if not self.api_key:
            return {'status': 'skipped', 'reason': 'no api key'}
        
        headers = {
            'DD-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            resp = requests.post(self.logs_url, json=logs, headers=headers, timeout=10)
            return {'status': 'success' if resp.ok else 'error', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class NewRelicClient:
    def __init__(self, license_key: str, account_id: str):
        self.license_key = license_key
        self.account_id = account_id
        self.metrics_url = 'https://metric-api.newrelic.com/metric/v1'
        self.logs_url = 'https://log-api.newrelic.com/log/v1'
    
    def send_metrics(self, metrics: list) -> dict:
        if not self.license_key:
            return {'status': 'skipped', 'reason': 'no license key'}
        
        payload = [{'metrics': metrics}]
        headers = {
            'Api-Key': self.license_key,
            'Content-Type': 'application/json'
        }
        
        try:
            resp = requests.post(self.metrics_url, json=payload, headers=headers, timeout=10)
            return {'status': 'success' if resp.ok else 'error', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def send_logs(self, logs: list) -> dict:
        if not self.license_key:
            return {'status': 'skipped', 'reason': 'no license key'}
        
        headers = {
            'Api-Key': self.license_key,
            'Content-Type': 'application/json'
        }
        
        try:
            resp = requests.post(self.logs_url, json=logs, headers=headers, timeout=10)
            return {'status': 'success' if resp.ok else 'error', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class PagerDutyClient:
    def __init__(self, routing_key: str):
        self.routing_key = routing_key
        self.events_url = 'https://events.pagerduty.com/v2/enqueue'
    
    def trigger(self, title: str, description: str, severity: str, source: str, dedup_key: str) -> dict:
        if not self.routing_key:
            return {'status': 'skipped', 'reason': 'no routing key'}
        
        payload = {
            'routing_key': self.routing_key,
            'event_action': 'trigger',
            'dedup_key': dedup_key,
            'payload': {
                'summary': title,
                'source': source,
                'severity': severity,
                'custom_details': {'description': description, 'triggered_by': 'datadog_monitor'}
            }
        }
        
        try:
            resp = requests.post(self.events_url, json=payload, timeout=10)
            return resp.json() if resp.ok else {'status': 'error', 'code': resp.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class SlackClient:
    def __init__(self, token: str, channel: str):
        self.token = token
        self.channel = channel
    
    def post(self, message: str) -> dict:
        if not self.token or not self.channel:
            return {'status': 'skipped', 'reason': 'no token or channel'}
        
        try:
            resp = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                json={'channel': self.channel, 'text': message},
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def generate_metrics(spike_probability: float = 0.1) -> tuple:
    now = int(time.time())
    dd_metrics = []
    nr_metrics = []
    spikes = []
    
    for metric_name, config in METRIC_DEFINITIONS.items():
        for service in random.sample(SERVICES, 2):
            for host in random.sample(HOSTS, 2):
                is_spike = random.random() < spike_probability
                
                if is_spike:
                    value = random.uniform(*config['spike'])
                    spikes.append({
                        'metric': metric_name,
                        'value': round(value, 2),
                        'host': host,
                        'service': service,
                        'threshold': config['threshold']
                    })
                else:
                    value = random.uniform(*config['normal'])
                
                dd_metrics.append({
                    'metric': f'demo.{metric_name}',
                    'type': 0,
                    'points': [{'timestamp': now, 'value': round(value, 2)}],
                    'tags': [f'service:{service}', f'host:{host}', 'env:demo', 'source:lambda']
                })
                
                nr_metrics.append({
                    'name': f'demo.{metric_name}',
                    'type': 'gauge',
                    'value': round(value, 2),
                    'timestamp': now,
                    'attributes': {'service': service, 'host': host, 'env': 'demo'}
                })
    
    return dd_metrics, nr_metrics, spikes


def generate_logs(spikes: list) -> tuple:
    dd_logs = []
    nr_logs = []
    now = datetime.utcnow().isoformat() + 'Z'
    
    log_templates = [
        {'level': 'INFO', 'message': 'Request processed successfully', 'service': random.choice(SERVICES)},
        {'level': 'INFO', 'message': 'Cache hit for user session', 'service': 'auth-service'},
        {'level': 'DEBUG', 'message': 'Database query completed', 'service': 'user-service'},
        {'level': 'WARN', 'message': 'Slow response detected', 'service': random.choice(SERVICES)},
    ]
    
    for _ in range(random.randint(5, 15)):
        template = random.choice(log_templates)
        dd_logs.append({
            'ddsource': 'demo-lambda',
            'ddtags': f"service:{template['service']},env:demo",
            'hostname': random.choice(HOSTS),
            'message': json.dumps({
                'timestamp': now,
                'level': template['level'],
                'message': template['message'],
                'service': template['service']
            }),
            'service': template['service'],
            'status': template['level'].lower()
        })
        
        nr_logs.append({
            'timestamp': int(time.time() * 1000),
            'message': template['message'],
            'attributes': {
                'level': template['level'],
                'service': template['service'],
                'host': random.choice(HOSTS),
                'env': 'demo'
            }
        })
    
    for spike in spikes:
        error_msg = f"ALERT: {spike['metric']} exceeded threshold ({spike['value']} > {spike['threshold']}) on {spike['host']}"
        dd_logs.append({
            'ddsource': 'demo-lambda',
            'ddtags': f"service:{spike['service']},env:demo,alert:true",
            'hostname': spike['host'],
            'message': json.dumps({
                'timestamp': now,
                'level': 'ERROR',
                'message': error_msg,
                'metric': spike['metric'],
                'value': spike['value'],
                'threshold': spike['threshold']
            }),
            'service': spike['service'],
            'status': 'error'
        })
    
    return dd_logs, nr_logs


def trigger_incident_for_spike(spike: dict, pd_client: PagerDutyClient, slack_client: SlackClient) -> dict:
    trigger_config = INCIDENT_TRIGGERS.get(spike['metric'])
    if not trigger_config:
        return {'status': 'skipped', 'reason': 'no trigger config'}
    
    title = trigger_config['title'].format(
        host=spike['host'],
        service=spike['service'],
        value=spike['value']
    )
    description = trigger_config['description'].format(
        host=spike['host'],
        service=spike['service'],
        value=spike['value']
    )
    
    dedup_key = f"demo-{spike['metric']}-{spike['host']}-{int(time.time() // 3600)}"
    
    pd_result = pd_client.trigger(
        title=title,
        description=description,
        severity=trigger_config['severity'],
        source=f"Datadog Monitor: demo.{spike['metric']}",
        dedup_key=dedup_key
    )
    
    if pd_result.get('status') == 'success':
        slack_msg = f":rotating_light: *Datadog Alert Triggered*\n>{title}\n_Metric: {spike['metric']} = {spike['value']} (threshold: {spike['threshold']})_"
        slack_client.post(slack_msg)
    
    return {'spike': spike, 'pagerduty': pd_result, 'dedup_key': dedup_key}


def lambda_handler(event, context):
    spike_probability = float(event.get('spike_probability', 0.05))
    force_spike = event.get('force_spike', False)
    trigger_pagerduty = event.get('trigger_pagerduty', False)

    if force_spike:
        spike_probability = 1.0

    datadog = DatadogClient(DATADOG_API_KEY, DATADOG_SITE)
    newrelic = NewRelicClient(NEW_RELIC_LICENSE_KEY, NEW_RELIC_ACCOUNT_ID)
    pagerduty = PagerDutyClient(PAGERDUTY_ROUTING_KEY)
    slack = SlackClient(SLACK_BOT_TOKEN, SLACK_CHANNEL)

    dd_metrics, nr_metrics, spikes = generate_metrics(spike_probability)
    dd_logs, nr_logs = generate_logs(spikes)

    results = {
        'datadog_metrics': datadog.send_metrics(dd_metrics),
        'datadog_logs': datadog.send_logs(dd_logs),
        'newrelic_metrics': newrelic.send_metrics(nr_metrics),
        'newrelic_logs': newrelic.send_logs(nr_logs),
        'metrics_sent': len(dd_metrics),
        'logs_sent': len(dd_logs),
        'spikes_detected': len(spikes),
        'spike_details': spikes[:3] if spikes else []
    }

    if trigger_pagerduty and spikes:
        pd_results = []
        for spike in spikes[:1]:
            pd_result = trigger_incident_for_spike(spike, pagerduty, slack)
            pd_results.append(pd_result)
        results['pagerduty_triggers'] = pd_results

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
