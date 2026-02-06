#!/usr/bin/env python3
import os
import json
import requests

GRAFANA_URL = os.environ.get('GRAFANA_URL', 'https://conalllynch88.grafana.net')
GRAFANA_API_KEY = os.environ.get('GRAFANA_API_KEY')
PAGERDUTY_CONTACT_POINT_UID = os.environ.get('PAGERDUTY_CONTACT_POINT_UID', 'cfbcjz992b474a')

if not GRAFANA_API_KEY:
    raise ValueError("GRAFANA_API_KEY environment variable required")

headers = {
    'Authorization': f'Bearer {GRAFANA_API_KEY}',
    'Content-Type': 'application/json'
}

def get_folders():
    response = requests.get(f'{GRAFANA_URL}/api/folders', headers=headers)
    return response.json()

def create_folder(title, uid):
    response = requests.post(
        f'{GRAFANA_URL}/api/folders',
        headers=headers,
        json={'title': title, 'uid': uid}
    )
    print(f"Create folder '{title}': {response.status_code}")
    return response.json() if response.ok else None

def get_datasources():
    response = requests.get(f'{GRAFANA_URL}/api/datasources', headers=headers)
    return response.json()

def update_notification_policy():
    policy = {
        "receiver": "PagerDuty",
        "group_by": ["grafana_folder", "alertname"],
        "routes": [
            {
                "receiver": "PagerDuty",
                "matchers": ["demo=true"],
                "continue": False
            }
        ]
    }
    response = requests.put(
        f'{GRAFANA_URL}/api/v1/provisioning/policies',
        headers=headers,
        json=policy
    )
    print(f"Update notification policy: {response.status_code}")
    if not response.ok:
        print(f"  Error: {response.text}")
    return response.ok

def create_alert_rule(folder_uid, title, condition_query, threshold):
    rule = {
        "title": title,
        "ruleGroup": "demo-alerts",
        "folderUID": folder_uid,
        "noDataState": "OK",
        "execErrState": "Error",
        "for": "1m",
        "annotations": {
            "summary": f"[DEMO] {title}",
            "description": "This is a demo alert for PagerDuty demonstration"
        },
        "labels": {
            "demo": "true",
            "severity": "critical"
        },
        "data": [
            {
                "refId": "A",
                "queryType": "",
                "relativeTimeRange": {
                    "from": 300,
                    "to": 0
                },
                "datasourceUid": "__expr__",
                "model": {
                    "conditions": [
                        {
                            "evaluator": {
                                "params": [threshold],
                                "type": "gt"
                            },
                            "operator": {"type": "and"},
                            "query": {"params": ["A"]},
                            "reducer": {"params": [], "type": "last"},
                            "type": "query"
                        }
                    ],
                    "datasource": {"type": "__expr__", "uid": "__expr__"},
                    "expression": str(threshold + 100),
                    "intervalMs": 1000,
                    "maxDataPoints": 43200,
                    "refId": "A",
                    "type": "math"
                }
            }
        ]
    }
    
    response = requests.post(
        f'{GRAFANA_URL}/api/v1/provisioning/alert-rules',
        headers={**headers, 'X-Disable-Provenance': 'true'},
        json=rule
    )
    print(f"Create alert rule '{title}': {response.status_code}")
    if not response.ok:
        print(f"  Error: {response.text}")
    return response.ok

def main():
    print("=" * 60)
    print("Setting up Grafana Cloud Alerts -> PagerDuty")
    print("=" * 60)
    
    print("\n--- Step 1: Check/Create Demo Folder ---")
    folders = get_folders()
    demo_folder = None
    for f in folders:
        if f.get('title') == 'Demo Alerts':
            demo_folder = f
            print(f"Found existing folder: {f['title']} (uid: {f['uid']})")
            break
    
    if not demo_folder:
        print("Creating Demo Alerts folder...")
        demo_folder = create_folder('Demo Alerts', 'demo-alerts')
    
    if not demo_folder:
        print("Failed to get/create folder")
        return
    
    folder_uid = demo_folder.get('uid', 'demo-alerts')
    
    print("\n--- Step 2: Update Notification Policy ---")
    update_notification_policy()
    
    print("\n--- Step 3: Check Datasources ---")
    datasources = get_datasources()
    print(f"Found {len(datasources)} datasources:")
    for ds in datasources:
        print(f"  - {ds.get('name')} ({ds.get('type')})")
    
    print("\n--- Step 4: Create Demo Alert Rules ---")
    alerts = [
        ("[DEMO] API Response Time High", "api.response_time", 500),
        ("[DEMO] Error Rate Critical", "api.error_rate", 5),
        ("[DEMO] Database Connections Exhausted", "database.connections", 90),
    ]

    for title, metric, threshold in alerts:
        create_alert_rule(folder_uid, title, metric, threshold)
    
    print("\n" + "=" * 60)
    print("Grafana alerting setup complete!")
    print("=" * 60)
    print("\nNote: Alert rules use math expressions for demo purposes.")
    print("To trigger alerts, you can modify the threshold expressions.")

if __name__ == '__main__':
    main()
