#!/usr/bin/env python3
"""
Setup script to configure Datadog and New Relic integrations with PagerDuty.
This creates monitors/alerts that trigger PagerDuty when metrics exceed thresholds.
"""

import os
import sys
import json
import requests
from typing import Optional

DATADOG_API_KEY = os.environ.get("DATADOG_API_KEY", "29bd7e2c438d43f329b2980ddb1ec747")
DATADOG_APP_KEY = os.environ.get("DATADOG_APP_KEY", "")
DATADOG_SITE = os.environ.get("DATADOG_SITE", "us5.datadoghq.com")

NEWRELIC_API_KEY = os.environ.get("NEWRELIC_API_KEY", "")
NEWRELIC_ACCOUNT_ID = os.environ.get("NEWRELIC_ACCOUNT_ID", "6576386")

PAGERDUTY_ROUTING_KEY = os.environ.get("PAGERDUTY_ROUTING_KEY", "R02HFHFV8Z3RZBCUIWLKN5NBDM0YXWDR")


class DatadogSetup:
    def __init__(self, api_key: str, app_key: str, site: str):
        self.api_key = api_key
        self.app_key = app_key
        self.base_url = f"https://api.{site}"
        self.headers = {
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }
    
    def create_pagerduty_integration(self, routing_key: str) -> dict:
        url = f"{self.base_url}/api/v1/integration/pagerduty"
        payload = {
            "services": [
                {
                    "service_name": "demo-simulator-alerts",
                    "service_key": routing_key
                }
            ],
            "subdomain": "demo-simulator"
        }
        resp = requests.put(url, headers=self.headers, json=payload)
        print(f"Datadog PagerDuty integration: {resp.status_code}")
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    
    def create_monitor(self, name: str, query: str, message: str, thresholds: dict) -> dict:
        url = f"{self.base_url}/api/v1/monitor"
        payload = {
            "name": f"[DEMO] {name}",
            "type": "metric alert",
            "query": query,
            "message": message,
            "tags": ["demo:true", "env:demo-simulator"],
            "priority": 3,
            "options": {
                "thresholds": thresholds,
                "notify_no_data": False,
                "renotify_interval": 0,
                "include_tags": True,
                "notify_audit": False,
                "new_host_delay": 0,
                "evaluation_delay": 0
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        print(f"Datadog monitor '{name}': {resp.status_code}")
        if resp.status_code in [200, 201]:
            return resp.json()
        else:
            print(f"  Error: {resp.text}")
            return {"error": resp.text}

    def update_monitor(self, monitor_id: int, name: str, query: str, message: str, thresholds: dict) -> dict:
        url = f"{self.base_url}/api/v1/monitor/{monitor_id}"
        payload = {
            "name": f"[DEMO] {name}",
            "type": "metric alert",
            "query": query,
            "message": message,
            "tags": ["demo:true", "env:demo-simulator"],
            "priority": 3,
            "options": {
                "thresholds": thresholds,
                "notify_no_data": False,
                "renotify_interval": 0,
                "include_tags": True,
                "notify_audit": False,
                "new_host_delay": 0,
                "evaluation_delay": 0
            }
        }
        resp = requests.put(url, headers=self.headers, json=payload)
        print(f"Datadog monitor '{name}' update: {resp.status_code}")
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  Error: {resp.text}")
            return {"error": resp.text}

    def get_existing_monitors(self) -> dict:
        url = f"{self.base_url}/api/v1/monitor"
        resp = requests.get(url, headers=self.headers)
        if resp.ok:
            monitors = resp.json()
            return {m['name']: m['id'] for m in monitors if '[DEMO]' in m.get('name', '')}
        return {}

    def setup_monitors(self):
        existing = self.get_existing_monitors()
        print(f"Found {len(existing)} existing DEMO monitors")

        monitors = [
            {
                "name": "API Response Time High",
                "query": "avg(last_1m):avg:demo.api.response_time{*} > 500",
                "message": "@pagerduty-demo-simulator-alerts API response time exceeded 500ms threshold. Check API gateway and backend services.",
                "thresholds": {"critical": 500, "warning": 300}
            },
            {
                "name": "Database Connection Pool Exhausted",
                "query": "avg(last_1m):avg:demo.database.connections{*} > 90",
                "message": "@pagerduty-demo-simulator-alerts Database connection pool above 90%. Risk of connection exhaustion.",
                "thresholds": {"critical": 90, "warning": 75}
            },
            {
                "name": "Error Rate High",
                "query": "avg(last_1m):avg:demo.api.error_rate{*} > 5",
                "message": "@pagerduty-demo-simulator-alerts Error rate exceeded 5%. Investigate recent deployments.",
                "thresholds": {"critical": 5, "warning": 2}
            },
            {
                "name": "Memory Usage Critical",
                "query": "avg(last_1m):avg:demo.system.memory_usage{*} > 85",
                "message": "@pagerduty-demo-simulator-alerts Memory usage above 85%. Services may become unstable.",
                "thresholds": {"critical": 85, "warning": 70}
            },
            {
                "name": "Queue Depth High",
                "query": "avg(last_1m):avg:demo.queue.depth{*} > 1000",
                "message": "@pagerduty-demo-simulator-alerts Message queue depth exceeded 1000. Processing backlog detected.",
                "thresholds": {"critical": 1000, "warning": 500}
            }
        ]

        results = []
        for m in monitors:
            full_name = f"[DEMO] {m['name']}"
            if full_name in existing:
                result = self.update_monitor(existing[full_name], m["name"], m["query"], m["message"], m["thresholds"])
            else:
                result = self.create_monitor(m["name"], m["query"], m["message"], m["thresholds"])
            results.append(result)
        return results


class NewRelicSetup:
    def __init__(self, api_key: str, account_id: str):
        self.api_key = api_key
        self.account_id = account_id
        self.graphql_url = "https://api.newrelic.com/graphql"
        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def graphql_query(self, query: str, variables: dict = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(self.graphql_url, headers=self.headers, json=payload)
        return resp.json()
    
    def create_alert_policy(self, name: str) -> Optional[int]:
        query = """
        mutation($accountId: Int!, $name: String!) {
            alertsPolicyCreate(accountId: $accountId, policy: {
                name: $name,
                incidentPreference: PER_CONDITION
            }) {
                id
                name
            }
        }
        """
        variables = {"accountId": int(self.account_id), "name": name}
        result = self.graphql_query(query, variables)
        print(f"New Relic policy '{name}': {json.dumps(result, indent=2)}")

        if "data" in result and result["data"].get("alertsPolicyCreate"):
            return result["data"]["alertsPolicyCreate"]["id"]
        return None

    def create_nrql_condition(self, policy_id: int, name: str, nrql: str, threshold: float) -> dict:
        query = """
        mutation($accountId: Int!, $policyId: ID!, $condition: AlertsNrqlConditionStaticInput!) {
            alertsNrqlConditionStaticCreate(
                accountId: $accountId,
                policyId: $policyId,
                condition: $condition
            ) {
                id
                name
            }
        }
        """
        variables = {
            "accountId": int(self.account_id),
            "policyId": str(policy_id),
            "condition": {
                "name": f"[DEMO] {name}",
                "enabled": True,
                "nrql": {"query": nrql},
                "signal": {
                    "aggregationWindow": 60,
                    "aggregationMethod": "EVENT_FLOW",
                    "aggregationDelay": 120
                },
                "terms": [{
                    "threshold": threshold,
                    "thresholdOccurrences": "AT_LEAST_ONCE",
                    "thresholdDuration": 300,
                    "operator": "ABOVE",
                    "priority": "CRITICAL"
                }],
                "violationTimeLimitSeconds": 86400
            }
        }
        result = self.graphql_query(query, variables)
        print(f"New Relic condition '{name}': {json.dumps(result, indent=2)}")
        return result
    
    def create_pagerduty_destination(self, routing_key: str) -> Optional[str]:
        query = """
        mutation($accountId: Int!, $destination: AiNotificationsDestinationInput!) {
            aiNotificationsCreateDestination(accountId: $accountId, destination: $destination) {
                destination {
                    id
                    name
                }
                error {
                    description
                }
            }
        }
        """
        variables = {
            "accountId": int(self.account_id),
            "destination": {
                "type": "PAGERDUTY_SERVICE_INTEGRATION",
                "name": "Demo Simulator PagerDuty",
                "properties": [{
                    "key": "routingKey",
                    "value": routing_key
                }]
            }
        }
        result = self.graphql_query(query, variables)
        print(f"New Relic PagerDuty destination: {json.dumps(result, indent=2)}")
        
        if "data" in result and result["data"].get("aiNotificationsCreateDestination"):
            dest = result["data"]["aiNotificationsCreateDestination"].get("destination")
            if dest:
                return dest["id"]
        return None
    
    def create_notification_channel(self, destination_id: str, policy_id: int) -> dict:
        query = """
        mutation($accountId: Int!, $channel: AiNotificationsChannelInput!) {
            aiNotificationsCreateChannel(accountId: $accountId, channel: $channel) {
                channel {
                    id
                    name
                }
                error {
                    description
                }
            }
        }
        """
        variables = {
            "accountId": int(self.account_id),
            "channel": {
                "type": "PAGERDUTY_SERVICE_INTEGRATION",
                "name": "Demo Simulator Alerts",
                "destinationId": destination_id,
                "product": "IINT",
                "properties": []
            }
        }
        result = self.graphql_query(query, variables)
        print(f"New Relic notification channel: {json.dumps(result, indent=2)}")
        return result
    
    def setup_alerts(self, routing_key: str):
        policy_id = self.create_alert_policy("[DEMO] Demo Simulator Alerts")
        if not policy_id:
            print("Failed to create alert policy")
            return
        
        conditions = [
            {
                "name": "API Response Time High",
                "nrql": "SELECT average(value) FROM Metric WHERE metricName = 'demo.api.response_time'",
                "threshold": 500
            },
            {
                "name": "Database Connections High",
                "nrql": "SELECT average(value) FROM Metric WHERE metricName = 'demo.database.connections'",
                "threshold": 90
            },
            {
                "name": "Error Rate High",
                "nrql": "SELECT average(value) FROM Metric WHERE metricName = 'demo.api.error_rate'",
                "threshold": 5
            },
            {
                "name": "Memory Usage High",
                "nrql": "SELECT average(value) FROM Metric WHERE metricName = 'demo.system.memory_usage'",
                "threshold": 85
            }
        ]
        
        for c in conditions:
            self.create_nrql_condition(policy_id, c["name"], c["nrql"], c["threshold"])
        
        dest_id = self.create_pagerduty_destination(routing_key)
        if dest_id:
            self.create_notification_channel(dest_id, policy_id)


def main():
    print("=" * 60)
    print("Setting up Datadog and New Relic integrations with PagerDuty")
    print("=" * 60)
    
    if not DATADOG_APP_KEY:
        print("\nWARNING: DATADOG_APP_KEY not set. Skipping Datadog setup.")
        print("  To set up Datadog monitors, you need an Application Key.")
        print("  Create one at: https://app.datadoghq.com/organization-settings/application-keys")
    else:
        print("\n--- Datadog Setup ---")
        dd = DatadogSetup(DATADOG_API_KEY, DATADOG_APP_KEY, DATADOG_SITE)
        dd.create_pagerduty_integration(PAGERDUTY_ROUTING_KEY)
        dd.setup_monitors()
    
    if not NEWRELIC_API_KEY:
        print("\nWARNING: NEWRELIC_API_KEY not set. Skipping New Relic setup.")
        print("  To set up New Relic alerts, you need a User API Key.")
        print("  Create one at: https://one.newrelic.com/api-keys")
    else:
        print("\n--- New Relic Setup ---")
        nr = NewRelicSetup(NEWRELIC_API_KEY, NEWRELIC_ACCOUNT_ID)
        nr.setup_alerts(PAGERDUTY_ROUTING_KEY)
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
