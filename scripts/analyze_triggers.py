#!/usr/bin/env python3
import os
import requests

TOKEN = os.getenv("PAGERDUTY_TOKEN", "")
headers = {
    'Authorization': f'Token token={TOKEN}',
    'Content-Type': 'application/json',
}

r = requests.get("https://api.pagerduty.com/incident_workflows/triggers?limit=100", headers=headers)
triggers = r.json().get('triggers', [])

print(f"Total triggers: {len(triggers)}\n")

zero_services = []
not_all_services = []

for t in triggers:
    wf = t.get('workflow', {})
    services = t.get('services', [])
    is_all = t.get('is_subscribed_to_all_services', False)
    
    if is_all:
        print(f"ALL: {t['id'][:8]} - {wf.get('name', 'N/A')[:50]}")
    elif len(services) == 0:
        print(f"NONE: {t['id'][:8]} - {wf.get('name', 'N/A')[:50]}")
        zero_services.append(t)
    else:
        print(f"{len(services):2d}:  {t['id'][:8]} - {wf.get('name', 'N/A')[:50]}")

print(f"\nTriggers with ZERO services (won't fire): {len(zero_services)}")
for t in zero_services:
    print(f"  - {t['id']} : {t.get('workflow',{}).get('name', 'N/A')}")
