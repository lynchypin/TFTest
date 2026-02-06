#!/usr/bin/env python3
"""
List PagerDuty workflows and generate Terraform import commands.

Usage:
    export PAGERDUTY_TOKEN=your_token
    python scripts/list_workflows.py

Or run with terraform show to extract from state (if available).
"""
import os
import sys
import json
import subprocess
import requests

def get_token_from_env():
    return os.environ.get('PAGERDUTY_TOKEN')

def get_token_from_terraform_state():
    try:
        result = subprocess.run(
            ['terraform', 'show', '-json'],
            capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)) or '.'
        )
        if result.returncode == 0:
            state = json.loads(result.stdout)
            return None
    except:
        pass
    return None

def main():
    token = get_token_from_env()
    
    if not token:
        print('='*60)
        print('PAGERDUTY_TOKEN not set in environment.')
        print('')
        print('Set it with:')
        print('  export PAGERDUTY_TOKEN=your_api_token')
        print('')
        print('Get your API token from:')
        print('  PagerDuty > Integrations > API Access Keys')
        print('='*60)
        sys.exit(1)

    headers = {
        'Authorization': f'Token token={token}',
        'Content-Type': 'application/json'
    }

    resp = requests.get('https://api.pagerduty.com/incident_workflows', headers=headers)
    if resp.status_code != 200:
        print(f'Error: {resp.status_code} - {resp.text}')
        sys.exit(1)
    
    workflows = resp.json().get('incident_workflows', [])
    print(f'Found {len(workflows)} existing workflows:\n')
    
    for wf in workflows:
        step_count = len(wf.get('steps', []))
        print(f'  {wf["id"]}: {wf["name"]} ({step_count} steps)')
    
    mapping = {
        'Major Incident Full Mobilization': 'major_incident_mobilization',
        'Security Incident Response (Confidential)': 'security_incident_response',
        'Customer Impact Communication': 'customer_impacting',
        'Platform Infrastructure Degradation': 'platform_infrastructure',
        'Incident Closeout and PIR Scheduling': 'incident_closeout',
        'Payments System Outage': 'payments_outage',
        'Data Pipeline Emergency Response': 'data_pipeline_failure',
        'Data Pipeline Alert': 'data_pipeline_failure',
        'Database Emergency Response': 'database_emergency',
        'P1 Critical Response Protocol': 'p1_critical',
        'Maintenance Window Incident': 'maintenance_window',
        'Data Breach Response': 'data_breach_response',
        'Identity/Authentication Crisis': 'identity_crisis',
        'Escalation Timeout Handler': 'escalation_timeout',
        'Run Comprehensive Diagnostics (Manual)': 'manual_diagnostics',
        'Initiate Customer Communication (Manual)': 'manual_customer_comms',
        'Automated Service Health Check': 'service_health_check',
        'Incident Commander Handoff': 'incident_commander_handoff',
        'Third-Party Vendor Escalation': 'vendor_escalation',
        'Capacity Emergency Response': 'capacity_emergency',
        'Compliance Incident Handler': 'compliance_incident',
    }
    
    print('\n' + '='*60)
    print('TERRAFORM IMPORT COMMANDS')
    print('='*60)
    print('# Run these commands to import existing workflows:\n')
    
    imported = []
    not_mapped = []
    
    for wf in workflows:
        name = wf['name']
        wf_id = wf['id']
        tf_name = mapping.get(name)
        if tf_name:
            print(f'terraform import pagerduty_incident_workflow.{tf_name} {wf_id}')
            imported.append(tf_name)
        else:
            not_mapped.append(f'{name} ({wf_id})')
    
    if not_mapped:
        print(f'\n# Workflows without Terraform mapping (will be created new):')
        for item in not_mapped:
            print(f'#   - {item}')
    
    print('\n' + '='*60)
    print(f'Total: {len(imported)} can be imported, {len(not_mapped)} unmapped')
    print('='*60)

if __name__ == '__main__':
    main()
