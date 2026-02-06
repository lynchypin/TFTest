#!/usr/bin/env python3
"""
Populate PagerDuty Incident Workflow Steps.

This script adds steps to workflows created by Terraform. The Terraform provider
limitation prevents creating workflows with steps directly, so we use this script
to populate steps via the API after terraform apply.

Usage:
    export PAGERDUTY_TOKEN=your_token
    python scripts/populate_workflow_steps.py
"""
import os
import sys
import json
import subprocess
import requests

PAGERDUTY_API_BASE = "https://api.pagerduty.com"

WORKFLOW_STEPS = {
    "standard_incident_response": {
        "steps": [
            {
                "name": "Create incident Slack channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "inc-{{incident.incident_number}}-{{incident.service.name | downcase | replace: ' ', '-'}}"
                        },
                        "channel_description": {
                            "value": "Incident #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            }
        ]
    },
    "major_incident_mobilization": {
        "steps": [
            {
                "name": "Create major incident Slack channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "major-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "MAJOR INCIDENT #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            },
            {
                "name": "Add note about channel creation",
                "configuration": {
                    "action_id": "pagerduty.com:incident-workflows:add-note",
                    "inputs": {
                        "note": {
                            "value": "Slack channel created for this incident. Team members are being mobilized."
                        }
                    }
                }
            }
        ]
    },
    "security_incident_response": {
        "steps": [
            {
                "name": "Create security incident channel (private)",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "sec-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "SECURITY INCIDENT #{{incident.incident_number}}: {{incident.title}} - CONFIDENTIAL"
                        },
                        "is_private": {
                            "value": "true"
                        }
                    }
                }
            },
            {
                "name": "Add security handling note",
                "configuration": {
                    "action_id": "pagerduty.com:incident-workflows:add-note",
                    "inputs": {
                        "note": {
                            "value": "[CONFIDENTIAL] Security incident handling initiated. Private Slack channel created. Follow security incident response procedures."
                        }
                    }
                }
            }
        ]
    },
    "customer_impacting": {
        "steps": [
            {
                "name": "Create customer impact channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "cust-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "Customer-Impacting Incident #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            }
        ]
    },
    "p1_critical": {
        "steps": [
            {
                "name": "Create P1 critical incident channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "p1-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "P1 CRITICAL #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            },
            {
                "name": "Add P1 escalation note",
                "configuration": {
                    "action_id": "pagerduty.com:incident-workflows:add-note",
                    "inputs": {
                        "note": {
                            "value": "P1 Critical Response Protocol activated. Slack channel created, responders being mobilized."
                        }
                    }
                }
            }
        ]
    },
    "database_emergency": {
        "steps": [
            {
                "name": "Create database incident channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "db-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "Database Emergency #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            }
        ]
    },
    "payments_outage": {
        "steps": [
            {
                "name": "Create payments incident channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "pay-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "Payments Outage #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            }
        ]
    },
    "data_pipeline_failure": {
        "steps": [
            {
                "name": "Create data pipeline incident channel",
                "configuration": {
                    "action_id": "slack.com:incident-workflows:create-channel",
                    "inputs": {
                        "channel_name": {
                            "value": "data-inc-{{incident.incident_number}}"
                        },
                        "channel_description": {
                            "value": "Data Pipeline Alert #{{incident.incident_number}}: {{incident.title}}"
                        },
                        "is_private": {
                            "value": "false"
                        }
                    }
                }
            }
        ]
    }
}

def get_token():
    token = os.environ.get('PAGERDUTY_TOKEN')
    if not token:
        print('='*60)
        print('ERROR: PAGERDUTY_TOKEN not set in environment.')
        print('')
        print('Set it with:')
        print('  export PAGERDUTY_TOKEN=your_api_token')
        print('='*60)
        sys.exit(1)
    return token

def get_headers(token):
    return {
        'Authorization': f'Token token={token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def list_workflows(token):
    headers = get_headers(token)
    resp = requests.get(f"{PAGERDUTY_API_BASE}/incident_workflows", headers=headers)
    if resp.status_code != 200:
        print(f"Error listing workflows: {resp.status_code} - {resp.text}")
        sys.exit(1)
    return resp.json().get('incident_workflows', [])

def get_workflow(token, workflow_id):
    headers = get_headers(token)
    resp = requests.get(f"{PAGERDUTY_API_BASE}/incident_workflows/{workflow_id}", headers=headers)
    if resp.status_code != 200:
        print(f"Error getting workflow {workflow_id}: {resp.status_code} - {resp.text}")
        return None
    return resp.json().get('incident_workflow')

def update_workflow_steps(token, workflow_id, workflow_name, steps):
    headers = get_headers(token)
    
    workflow = get_workflow(token, workflow_id)
    if not workflow:
        print(f"  Could not fetch workflow {workflow_id}")
        return False
    
    existing_steps = workflow.get('steps', [])
    if existing_steps:
        print(f"  Workflow already has {len(existing_steps)} steps - skipping")
        return True
    
    payload = {
        "incident_workflow": {
            "name": workflow_name,
            "steps": steps
        }
    }
    
    resp = requests.put(
        f"{PAGERDUTY_API_BASE}/incident_workflows/{workflow_id}",
        headers=headers,
        json=payload
    )
    
    if resp.status_code == 200:
        print(f"  Successfully added {len(steps)} steps")
        return True
    else:
        print(f"  Error updating: {resp.status_code} - {resp.text}")
        return False

def main():
    token = get_token()
    workflows = list_workflows(token)
    
    print(f"Found {len(workflows)} workflows in PagerDuty\n")
    
    name_to_key = {
        'Standard Incident Response': 'standard_incident_response',
        'Major Incident Full Mobilization': 'major_incident_mobilization',
        'Security Incident Response (Confidential)': 'security_incident_response',
        'Customer Impact Communication': 'customer_impacting',
        'P1 Critical Response Protocol': 'p1_critical',
        'Database Emergency Response': 'database_emergency',
        'Payments System Outage': 'payments_outage',
        'Data Pipeline Alert': 'data_pipeline_failure',
    }
    
    updated = 0
    skipped = 0
    errors = 0
    
    for wf in workflows:
        wf_id = wf['id']
        wf_name = wf['name']
        step_count = len(wf.get('steps', []))
        
        key = name_to_key.get(wf_name)
        if not key:
            continue
        
        if key not in WORKFLOW_STEPS:
            continue
        
        print(f"Processing: {wf_name} ({wf_id})")
        
        steps_config = WORKFLOW_STEPS[key]['steps']
        
        if update_workflow_steps(token, wf_id, wf_name, steps_config):
            if step_count == 0:
                updated += 1
            else:
                skipped += 1
        else:
            errors += 1
    
    print(f"\nSummary: {updated} updated, {skipped} skipped (already had steps), {errors} errors")

if __name__ == '__main__':
    main()
