#!/usr/bin/env python3
import json
import os

SCENARIOS_FILE = "docs/demo-scenarios/src/data/scenarios.json"
PD_ANALYSIS_FILE = "docs/pagerduty_analysis.json"

with open(SCENARIOS_FILE) as f:
    scenarios = json.load(f)['scenarios']

with open(PD_ANALYSIS_FILE) as f:
    pd_data = json.load(f)

workflows = {w['name'].lower(): w for w in pd_data['workflows']}
services = {s['name']: s for s in pd_data['services_list']}
triggers = pd_data['triggers']

FEATURE_TO_WORKFLOW_MAP = {
    'slack_channel_creation': ['Demo Incident Channel Setup', 'Standard Incident Response', 'Major Incident Full Mobilization'],
    'slack_incident_channel': ['Demo Incident Channel Setup', 'Standard Incident Response'],
    'conference_bridge': ['Demo Incident Channel Setup'],
    'response_mobilizer': ['Major Incident Full Mobilization', 'P1 Critical Response Protocol'],
    'post_incident_review': ['Incident Closeout and PIR Scheduling', 'Incident Resolution Cleanup'],
    'post_incident_reviews': ['Incident Closeout and PIR Scheduling', 'Incident Resolution Cleanup'],
    'jira_integration': ['Standard Incident Response'],
    'servicenow_integration': [],
    'status_page': ['Customer Impact Communication'],
    'stakeholder_updates': ['Customer Impact Communication', 'Initiate Customer Communication (Manual)'],
    'stakeholder_notifications': ['Customer Impact Communication', 'Initiate Customer Communication (Manual)'],
    'alert_grouping': [],
    'alert_suppression': [],
    'auto_pause': [],
    'event_orchestration': [],
    'schedule_routing': [],
    'change_correlation': [],
    'global_event_orchestration': [],
    'global_alert_grouping': [],
    'probable_origin': [],
    'outlier_detection': [],
    'incident_tasks': [],
    'incident_roles': [],
    'incident_types': [],
    'advanced_slack_actions': [],
    'custom_fields': [],
    'automated_diagnostics': ['Run Comprehensive Diagnostics (Manual)', 'Automated Service Health Check'],
    'automated_remediation': [],
    'runbook_automation': [],
    'external_status_page': ['Customer Impact Communication'],
    'incident_workflow_page': ['P1 Critical Response Protocol', 'Major Incident Full Mobilization'],
    'incident_workflow_full': ['Standard Incident Response', 'Major Incident Full Mobilization'],
    'incident_workflows': ['Standard Incident Response', 'Major Incident Full Mobilization', 'Demo Incident Channel Setup'],
    'advanced_workflow': [],
    'security_response': ['Security Incident Response (Confidential)', 'Data Breach Response'],
    'database_response': ['Database Emergency Response'],
    'payments_response': ['Payments System Outage'],
    'capacity_response': ['Capacity Emergency Response'],
    'identity_response': ['Identity/Authentication Crisis'],
    'vendor_escalation': ['Third-Party Vendor Escalation'],
    'compliance_handler': ['Compliance Incident Handler'],
    'maintenance_handling': ['Maintenance Window Incident'],
    'ic_handoff': ['Incident Commander Handoff'],
    'data_pipeline': ['Data Pipeline Alert'],
    'escalation_timeout': ['Escalation Timeout Handler'],
}

INTEGRATION_STATUS = {
    'datadog': {'status': 'READY', 'monitors': 14, 'routing': 'Event Orchestration'},
    'prometheus': {'status': 'READY', 'notes': 'Via Grafana Cloud'},
    'grafana': {'status': 'READY', 'url': 'https://conalllynch88.grafana.net'},
    'cloudwatch': {'status': 'READY', 'region': 'us-east-1'},
    'newrelic': {'status': 'READY', 'policy': 'Demo Simulator Alerts'},
    'github_actions': {'status': 'READY', 'workflow': 'pagerduty-demo.yml'},
    'sentry': {'status': 'FALLBACK', 'notes': 'Uses PagerDuty direct integration'},
    'splunk': {'status': 'FALLBACK', 'notes': 'No Splunk instance, uses PD direct'},
    'uptimerobot': {'status': 'FALLBACK', 'notes': 'Uses PagerDuty direct'},
    'slack': {'status': 'READY', 'scopes': 'Full'},
    'jira': {'status': 'OAUTH', 'notes': 'OAuth connected but no projects for demo'},
    'servicenow': {'status': 'NOT_CONFIGURED'},
    'zoom': {'status': 'OAUTH', 'notes': 'Connected via PD UI'},
    'ms_teams': {'status': 'OAUTH', 'notes': 'Connected via PD UI'},
}

SERVICE_MAPPING = {
    "Platform - Kubernetes/Platform": "P639GQH",
    "Platform - DBRE": "PPAQBDV",
    "Platform - Network": "PTL6IUK",
    "Platform - Networking": "PTL6IUK",
    "Platform - Frontend": "P35TLDW",
    "App - Backend API": "P35TLDW",
    "App - Checkout Team": "PISRLOQ",
    "App - Orders API Team": "PEG3KZ0",
    "SecOps": "PR0R0HZ",
    "Payments Ops": "PBYI8CS",
    "Clinical Systems - EMR": "P639GQH",
    "Grid Operations Center": "P639GQH",
    "Network Operations - Core": "PTL6IUK",
    "Retail Systems - POS": "P639GQH",
    "Payment Processing - Gateway": "PBYI8CS",
    "DevOps - CI/CD Platform": "P639GQH",
    "Quality Control - Manufacturing": "P639GQH",
    "Mining Operations - Equipment": "P639GQH",
    "Safety Operations": "P639GQH",
    "OT Operations - Factory Floor": "P639GQH",
    "Database - DBRE Team": "PPAQBDV",
}

def check_scenario_readiness(scenario):
    scenario_id = scenario['id']
    name = scenario['name']
    features_required = scenario.get('required_features', [])
    features_demonstrated = scenario.get('features_demonstrated', [])
    target_service = scenario.get('target_service', '')
    integration = scenario.get('tags', {}).get('integration', 'unknown')
    
    readiness = {
        'id': scenario_id,
        'name': name,
        'target_service': target_service,
        'integration': integration,
        'status': 'UNKNOWN',
        'missing': [],
        'ready': [],
        'notes': []
    }
    
    int_status = INTEGRATION_STATUS.get(integration, {'status': 'UNKNOWN'})
    if int_status['status'] == 'NOT_CONFIGURED':
        readiness['missing'].append(f'Integration not configured: {integration}')
    elif int_status['status'] == 'FALLBACK':
        readiness['notes'].append(f'Integration uses fallback: {integration}')
        readiness['ready'].append(f'Integration available (fallback): {integration}')
    elif int_status['status'] in ['READY', 'OAUTH']:
        readiness['ready'].append(f'Integration available: {integration}')
    
    if target_service:
        if target_service in SERVICE_MAPPING or target_service in services:
            readiness['ready'].append(f'Service exists: {target_service}')
        else:
            readiness['missing'].append(f'Service not found: {target_service}')
    
    all_features = set(features_required + features_demonstrated)
    for feature in all_features:
        feature_lower = feature.lower().replace(' ', '_').replace('-', '_')
        
        workflow_matches = FEATURE_TO_WORKFLOW_MAP.get(feature_lower, None)
        
        if workflow_matches is None:
            if any(kw in feature_lower for kw in ['orchestration', 'grouping', 'suppression', 'auto_pause', 'correlation', 'service_rules', 'threshold_conditions', 'schedule_conditions']):
                readiness['notes'].append(f'Feature requires AIOps/Event Intelligence: {feature}')
                readiness['ready'].append(f'Event Orchestration configured: Demo Global Event Orchestration')
            elif any(kw in feature_lower for kw in ['task', 'role', 'type', 'custom_field']):
                readiness['notes'].append(f'Feature requires Enterprise features: {feature}')
            elif any(kw in feature_lower for kw in ['runbook', 'remediation', 'automation', 'rba_runner']):
                readiness['notes'].append(f'RBA feature: {feature}')
                readiness['ready'].append('RBA runner deployed on EC2')
            elif any(kw in feature_lower for kw in ['priority', 'priority_assignment', 'severity']):
                readiness['ready'].append(f'Priority configured: P1-P5 available')
            elif any(kw in feature_lower for kw in ['service_graph', 'impact_metrics', 'business_services', 'related_incidents', 'past_incidents', 'change_events', 'outlier']):
                readiness['notes'].append(f'Feature requires AIOps/Service Graph: {feature}')
                readiness['ready'].append('Service dependencies configured')
            elif any(kw in feature_lower for kw in ['status_pages', 'status_update_templates', 'external_status']):
                readiness['notes'].append(f'StatusPage feature: {feature}')
                readiness['ready'].append('StatusPage integration available')
            elif any(kw in feature_lower for kw in ['slack_actions', 'slack_advanced']):
                readiness['ready'].append('Slack integration configured')
            elif any(kw in feature_lower for kw in ['incident_workflows_advanced', 'advanced_workflow']):
                readiness['notes'].append(f'Advanced workflow feature: {feature}')
                readiness['ready'].append('21 workflows configured')
            elif 'basic' in feature_lower or 'routing' in feature_lower or 'escalation' in feature_lower or 'on_call' in feature_lower:
                readiness['ready'].append(f'Basic PD feature: {feature}')
            else:
                readiness['missing'].append(f'Feature mapping unknown: {feature}')
        elif len(workflow_matches) == 0:
            readiness['missing'].append(f'No workflow for feature: {feature}')
        else:
            found = False
            for wf_name in workflow_matches:
                if wf_name.lower() in workflows:
                    wf = workflows[wf_name.lower()]
                    if len(wf['steps']) > 0:
                        readiness['ready'].append(f'Workflow configured: {wf_name}')
                        found = True
                        break
                    else:
                        readiness['notes'].append(f'Workflow exists but empty: {wf_name}')
            if not found and len(workflow_matches) > 0:
                readiness['notes'].append(f'Workflow not fully configured: {workflow_matches[0]}')
    
    if not readiness['missing']:
        if len(readiness['notes']) == 0:
            readiness['status'] = 'READY'
        else:
            readiness['status'] = 'PARTIAL'
    else:
        if len(readiness['ready']) > len(readiness['missing']):
            readiness['status'] = 'PARTIAL'
        else:
            readiness['status'] = 'NEEDS_WORK'
    
    return readiness

results = []
for scenario in scenarios:
    result = check_scenario_readiness(scenario)
    results.append(result)

ready_count = sum(1 for r in results if r['status'] == 'READY')
partial_count = sum(1 for r in results if r['status'] == 'PARTIAL')
needs_work_count = sum(1 for r in results if r['status'] == 'NEEDS_WORK')

summary = {
    'total_scenarios': len(results),
    'ready': ready_count,
    'partial': partial_count,
    'needs_work': needs_work_count,
    'scenarios': results,
    'infrastructure_summary': {
        'event_orchestration_rules': pd_data['event_orchestration_rules'],
        'incident_workflows': pd_data['incident_workflows'],
        'workflow_triggers': pd_data['workflow_triggers'],
        'services': pd_data['services'],
        'integrations': INTEGRATION_STATUS
    }
}

with open('docs/scenario_readiness_analysis.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("=" * 80)
print("SCENARIO READINESS ANALYSIS")
print("=" * 80)
print(f"\nTotal Scenarios: {len(results)}")
print(f"  READY: {ready_count}")
print(f"  PARTIAL: {partial_count}")
print(f"  NEEDS_WORK: {needs_work_count}")

print("\n" + "=" * 80)
print("SCENARIOS BY STATUS")
print("=" * 80)

for status in ['READY', 'PARTIAL', 'NEEDS_WORK']:
    print(f"\n=== {status} ({sum(1 for r in results if r['status'] == status)}) ===")
    for r in results:
        if r['status'] == status:
            print(f"\n{r['id']}: {r['name']}")
            print(f"  Integration: {r['integration']}")
            print(f"  Target Service: {r['target_service']}")
            if r['ready']:
                print(f"  Ready: {', '.join(r['ready'][:3])}...")
            if r['missing']:
                print(f"  Missing: {', '.join(r['missing'])}")
            if r['notes']:
                print(f"  Notes: {', '.join(r['notes'][:2])}...")

print("\n" + "=" * 80)
print("SUMMARY BY TIER")
print("=" * 80)

tiers = {}
for r in results:
    tier = r['id'].split('-')[0]
    if tier not in tiers:
        tiers[tier] = {'READY': 0, 'PARTIAL': 0, 'NEEDS_WORK': 0}
    tiers[tier][r['status']] += 1

for tier, counts in sorted(tiers.items()):
    total = sum(counts.values())
    print(f"\n{tier} ({total} scenarios):")
    print(f"  READY: {counts['READY']}, PARTIAL: {counts['PARTIAL']}, NEEDS_WORK: {counts['NEEDS_WORK']}")

print(f"\nDetailed analysis saved to: docs/scenario_readiness_analysis.json")
