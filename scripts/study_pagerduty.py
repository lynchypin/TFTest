#!/usr/bin/env python3
import os
import json
import requests

PD_TOKEN = os.getenv("PAGERDUTY_ADMIN_TOKEN", "")
PD_HEADERS = {
    "Authorization": f"Token token={PD_TOKEN}",
    "Content-Type": "application/json"
}

output = []

def log(msg):
    output.append(msg)
    print(msg)

def get_event_orchestration_rules():
    r = requests.get(
        "https://api.pagerduty.com/event_orchestrations/94e4c195-79d1-44ca-b649-548acbf08ea2/router",
        headers=PD_HEADERS
    )
    data = r.json()
    rules = data['orchestration_path']['sets'][0]['rules']
    
    log(f"=== EVENT ORCHESTRATION ROUTING RULES ===")
    log(f"Total routing rules: {len(rules)}\n")
    
    for i, r in enumerate(rules, 1):
        label = r.get('label', 'No label')
        route_to = r['actions'].get('route_to', 'N/A')
        cond = r['conditions'][0]['expression'] if r.get('conditions') else 'No conditions'
        log(f"{i}. {label}")
        log(f"   Route to: {route_to}")
        log(f"   Condition: {cond[:100]}...")
        log("")
    return rules

def get_incident_workflows():
    r = requests.get(
        "https://api.pagerduty.com/incident_workflows?limit=100",
        headers=PD_HEADERS
    )
    data = r.json()
    workflows = data.get('incident_workflows', [])
    
    log(f"\n=== INCIDENT WORKFLOWS ===")
    log(f"Total workflows: {len(workflows)}\n")
    
    results = []
    for wf in workflows:
        r2 = requests.get(
            f"https://api.pagerduty.com/incident_workflows/{wf['id']}",
            headers=PD_HEADERS
        )
        wf_detail = r2.json().get('incident_workflow', {})
        steps = wf_detail.get('steps', [])
        
        step_names = []
        for step in steps:
            action = step.get('configuration', {}).get('action_type', step.get('name', 'N/A'))
            step_names.append(action)
        
        results.append({
            'id': wf['id'],
            'name': wf['name'],
            'description': wf.get('description', ''),
            'steps': step_names
        })
        
        log(f"ID: {wf['id']}")
        log(f"Name: {wf['name']}")
        log(f"Description: {wf.get('description', 'N/A')[:80]}")
        log(f"Steps: {len(steps)}")
        for s in step_names:
            log(f"  - {s}")
        log("")
    return results

def get_workflow_triggers():
    r = requests.get(
        "https://api.pagerduty.com/incident_workflows/triggers?limit=100",
        headers=PD_HEADERS
    )
    data = r.json()
    triggers = data.get('triggers', [])
    
    log(f"\n=== WORKFLOW TRIGGERS ===")
    log(f"Total triggers: {len(triggers)}\n")
    
    results = []
    for t in triggers:
        workflow = t.get('workflow', {})
        results.append({
            'id': t['id'],
            'type': t['type'],
            'workflow_id': workflow.get('id', 'N/A'),
            'workflow_name': workflow.get('name', 'N/A'),
            'condition': t.get('condition', 'N/A'),
            'subscribed_to_all_services': t.get('is_subscribed_to_all_services', False),
            'services_count': len(t.get('services', []))
        })
        
        log(f"ID: {t['id']}")
        log(f"Type: {t['type']}")
        log(f"Workflow: {workflow.get('name', 'N/A')} ({workflow.get('id', 'N/A')})")
        log(f"Condition: {t.get('condition', 'N/A')}")
        log(f"Subscribed to all services: {t.get('is_subscribed_to_all_services', False)}")
        services = t.get('services', [])
        log(f"Services: {len(services)}")
        log("")
    return results

def get_services():
    r = requests.get(
        "https://api.pagerduty.com/services?limit=100",
        headers=PD_HEADERS
    )
    data = r.json()
    services = data.get('services', [])
    
    log(f"\n=== PAGERDUTY SERVICES ===")
    log(f"Total services: {len(services)}\n")
    
    results = []
    for s in services:
        ep = s.get('escalation_policy', {})
        results.append({
            'id': s['id'],
            'name': s['name'],
            'escalation_policy': ep.get('summary', 'N/A')
        })
        log(f"ID: {s['id']} - {s['name']}")
        log(f"  Escalation Policy: {ep.get('summary', 'N/A')}")
    return results

if __name__ == "__main__":
    rules = get_event_orchestration_rules()
    workflows = get_incident_workflows()
    triggers = get_workflow_triggers()
    services = get_services()
    
    summary = {
        'event_orchestration_rules': len(rules),
        'incident_workflows': len(workflows),
        'workflow_triggers': len(triggers),
        'services': len(services),
        'workflows': workflows,
        'triggers': triggers,
        'services_list': services
    }
    
    with open('docs/pagerduty_analysis.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    log(f"\n=== SUMMARY ===")
    log(f"Event Orchestration Rules: {len(rules)}")
    log(f"Incident Workflows: {len(workflows)}")
    log(f"Workflow Triggers: {len(triggers)}")
    log(f"Services: {len(services)}")
    log(f"\nSaved detailed analysis to docs/pagerduty_analysis.json")
