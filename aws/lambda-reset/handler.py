import json
import os
import logging
from datetime import datetime

from shared import PagerDutyClient, SlackNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGERDUTY_TOKEN = os.environ.get('PAGERDUTY_TOKEN', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'clynch@pagerduty.com')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'C0A9GCXFSBD')
ROUTING_KEY = os.environ.get('PAGERDUTY_ROUTING_KEY', '')


def reset_quick(pd_client: PagerDutyClient) -> dict:
    logger.info("Starting Quick Reset...")
    results = {
        'mode': 'quick',
        'incidents_resolved': 0,
        'incidents_failed': 0,
        'incident_ids': []
    }
    
    incidents = pd_client.get_demo_incidents()
    logger.info(f"Found {len(incidents)} [DEMO] incidents to resolve")
    
    for incident in incidents:
        incident_id = incident['id']
        response = pd_client.resolve_incident(incident_id, ADMIN_EMAIL)
        
        if response.get('success'):
            results['incidents_resolved'] += 1
            results['incident_ids'].append(incident_id)
            logger.info(f"Resolved incident {incident_id}")
        else:
            results['incidents_failed'] += 1
            logger.error(f"Failed to resolve incident {incident_id}: {response}")
    
    return results


def reset_full(pd_client: PagerDutyClient, create_samples: bool = False) -> dict:
    logger.info("Starting Full Reset...")
    
    quick_results = reset_quick(pd_client)
    
    results = {
        'mode': 'full',
        'incidents_resolved': quick_results['incidents_resolved'],
        'incidents_failed': quick_results['incidents_failed'],
        'maintenance_windows_deleted': 0,
        'samples_created': 0
    }
    
    maintenance_windows = pd_client.get_maintenance_windows('ongoing')
    logger.info(f"Found {len(maintenance_windows)} active maintenance windows")
    
    for mw in maintenance_windows:
        mw_id = mw['id']
        response = pd_client.delete_maintenance_window(mw_id)
        
        if response.get('success'):
            results['maintenance_windows_deleted'] += 1
            logger.info(f"Deleted maintenance window {mw_id}")
        else:
            logger.error(f"Failed to delete maintenance window {mw_id}: {response}")
    
    if create_samples and ROUTING_KEY:
        sample_incidents = [
            {'title': '[DEMO] Sample Database Alert - Ready for demo', 'severity': 'critical'},
            {'title': '[DEMO] Sample API Latency Warning - Monitoring', 'severity': 'warning'},
        ]
        
        for sample in sample_incidents:
            response = pd_client.trigger_sample_incident(ROUTING_KEY, sample['title'], sample['severity'])
            if response.get('success'):
                results['samples_created'] += 1
                logger.info(f"Created sample incident: {sample['title']}")
    
    return results


def lambda_handler(event, context):
    logger.info(f"Demo Reset Lambda invoked at {datetime.utcnow().isoformat()}")
    
    if not PAGERDUTY_TOKEN:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'PAGERDUTY_TOKEN not configured'})
        }
    
    pd_client = PagerDutyClient(PAGERDUTY_TOKEN)
    slack = SlackNotifier(SLACK_BOT_TOKEN, SLACK_CHANNEL)
    
    mode = event.get('mode', 'quick')
    create_samples = event.get('create_samples', False)
    notify_slack = event.get('notify_slack', True)
    
    if mode == 'full':
        results = reset_full(pd_client, create_samples)
        action_summary = f"Full Reset completed:\n- Resolved: {results['incidents_resolved']} incidents\n- Maintenance windows cleared: {results['maintenance_windows_deleted']}"
        if create_samples:
            action_summary += f"\n- Sample incidents created: {results['samples_created']}"
    else:
        results = reset_quick(pd_client)
        action_summary = f"Quick Reset completed:\n- Resolved: {results['incidents_resolved']} [DEMO] incidents"
    
    if notify_slack:
        slack_message = f"*Demo Reset ({mode.upper()})*\n{action_summary}"
        slack_result = slack.post(slack_message)
        results['slack_notification'] = slack_result
    
    logger.info(f"Reset complete: {results}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Demo reset ({mode}) complete',
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        })
    }
