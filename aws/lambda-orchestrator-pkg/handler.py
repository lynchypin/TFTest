#!/usr/bin/env python3
import os
import json
import random
import logging
import time
from typing import Optional, Dict, Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PagerDutyClient:
    def __init__(self):
        self.admin_token = os.getenv("PAGERDUTY_ADMIN_TOKEN", "")
        self.events_url = "https://events.pagerduty.com/v2/enqueue"
    
    def trigger_incident(
        self,
        routing_key: str,
        summary: str,
        severity: str,
        source: str,
        dedup_key: str,
        custom_details: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": f"[DEMO] {summary}",
                "severity": severity,
                "source": source,
                "custom_details": custom_details or {},
            },
        }
        logger.info(f"Sending to PagerDuty: routing_key={routing_key[:8]}..., summary={summary}")
        response = requests.post(self.events_url, json=payload)
        logger.info(f"PagerDuty response: status={response.status_code}, body={response.text[:200]}")
        if response.status_code != 202:
            return {"error": response.text, "status_code": response.status_code}
        return response.json()


class SlackClient:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.api_base = "https://slack.com/api"
    
    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "error": "no_token"}
        payload = {"channel": channel, "text": text}
        response = requests.post(
            f"{self.api_base}/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload
        )
        return response.json()


SERVICE_TO_ROUTING_KEY = {
    "Platform - DBRE": os.getenv("ROUTING_KEY_DBRE", ""),
    "Database - DBRE Team": os.getenv("ROUTING_KEY_DBRE", ""),
    "Platform - Kubernetes/Platform": os.getenv("ROUTING_KEY_K8S", ""),
    "App - Backend API": os.getenv("ROUTING_KEY_API", ""),
    "App - Orders API Team": os.getenv("ROUTING_KEY_API", ""),
    "App - Checkout Team": os.getenv("ROUTING_KEY_API", ""),
    "Platform - Networking": os.getenv("ROUTING_KEY_K8S", ""),
    "Platform - Network": os.getenv("ROUTING_KEY_K8S", ""),
}

SCENARIOS = [
    {
        "id": "PRO-001",
        "name": "Priority-Based Incident Routing",
        "payload": {
            "summary": "Production database connection failures",
            "source": "datadog",
            "severity": "critical",
            "custom_details": {
                "pd_service": "Platform - DBRE",
                "env": "production",
                "database": "orders-db",
                "error": "Connection refused"
            }
        }
    },
    {
        "id": "BUS-001",
        "name": "Response Mobilizer - Major Incident",
        "payload": {
            "summary": "MAJOR: Complete production cluster failure affecting all services",
            "source": "datadog",
            "severity": "critical",
            "custom_details": {
                "pd_service": "Platform - Kubernetes/Platform",
                "env": "production",
                "cluster": "prod-us-east-1",
                "affected_services": 47
            }
        }
    },
    {
        "id": "DIGOPS-003",
        "name": "Auto-Pause Transient Incidents",
        "payload": {
            "summary": "Brief CPU spike on batch processor",
            "source": "datadog",
            "severity": "warning",
            "custom_details": {
                "pd_service": "Platform - Kubernetes/Platform",
                "env": "production",
                "host": "batch-processor-01",
                "cpu_percent": 92
            }
        }
    },
    {
        "id": "DIGOPS-007",
        "name": "Change Correlation",
        "payload": {
            "summary": "Orders API errors after deployment",
            "source": "datadog",
            "severity": "critical",
            "custom_details": {
                "pd_service": "App - Orders API Team",
                "env": "production",
                "service": "orders-api",
                "error_rate": 15.2,
                "recent_deploy": "orders-api-v2.4.1"
            }
        }
    },
    {
        "id": "EIM-001",
        "name": "Incident Tasks Assignment",
        "payload": {
            "summary": "MAJOR: Production database corruption detected",
            "source": "datadog",
            "severity": "critical",
            "custom_details": {
                "pd_service": "Platform - DBRE",
                "env": "production",
                "database": "users-db",
                "corruption_type": "index_corruption"
            }
        }
    },
    {
        "id": "FREE-001",
        "name": "Simple Alert Routing",
        "payload": {
            "summary": "High memory usage on web-server-01",
            "source": "prometheus-alertmanager",
            "severity": "warning",
            "custom_details": {
                "pd_service": "Platform - Kubernetes/Platform",
                "env": "production",
                "host": "web-server-01",
                "memory_percent": 85
            }
        }
    },
    {
        "id": "FREE-002",
        "name": "Basic Condition Routing",
        "payload": {
            "summary": "API error rate elevated on checkout service",
            "source": "grafana-cloud",
            "severity": "error",
            "custom_details": {
                "pd_service": "App - Checkout Team",
                "env": "production",
                "service": "checkout-api",
                "error_rate": 2.5
            }
        }
    },
    {
        "id": "BUS-005",
        "name": "Stakeholder Status Update",
        "payload": {
            "summary": "Payment processing degraded - customer impact",
            "source": "datadog",
            "severity": "critical",
            "custom_details": {
                "pd_service": "App - Checkout Team",
                "env": "production",
                "service": "payment-gateway",
                "success_rate": 87.3
            }
        }
    },
]


def spawn_incident(scenario_id: Optional[str] = None, probability: float = 1.0) -> Dict[str, Any]:
    if random.random() > probability:
        return {"status": "skipped", "reason": f"probability check failed ({probability})"}

    if scenario_id:
        scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
        if not scenario:
            scenario = random.choice(SCENARIOS)
    else:
        scenario = random.choice(SCENARIOS)

    payload = scenario["payload"]
    pd_service = payload.get("custom_details", {}).get("pd_service", "")
    routing_key = SERVICE_TO_ROUTING_KEY.get(pd_service)

    if not routing_key:
        routing_key = os.getenv("ROUTING_KEY_K8S", "")
        logger.warning(f"No routing key for service '{pd_service}', using default K8S key")

    pd_client = PagerDutyClient()
    dedup_key = f"demo-{scenario['id']}-{int(time.time())}"

    custom_details = payload.get("custom_details", {}).copy()
    custom_details["scenario_id"] = scenario["id"]
    custom_details["scenario_name"] = scenario["name"]
    custom_details["triggered_by"] = "aws-lambda-orchestrator"

    result = pd_client.trigger_incident(
        routing_key=routing_key,
        summary=payload["summary"],
        severity=payload["severity"],
        source=payload["source"],
        dedup_key=dedup_key,
        custom_details=custom_details,
    )

    slack_channel = os.getenv("SLACK_CHANNEL")
    if slack_channel:
        slack = SlackClient()
        slack.post_message(
            channel=slack_channel,
            text=f":rotating_light: *{scenario['name']}*\n>{payload['summary']}\n_Source: {payload['source']} | Severity: {payload['severity']}_"
        )

    return {
        "status": "triggered",
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "dedup_key": dedup_key,
        "pd_service": pd_service,
        "pagerduty_response": result,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    scenario_id = event.get("scenario_id") or event.get("scenario")
    probability = float(event.get("probability", 0.3))

    logger.info(f"Lambda invoked: scenario_id={scenario_id}, probability={probability}")

    result = spawn_incident(scenario_id=scenario_id, probability=probability)

    logger.info(f"Result: {result}")

    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../scripts/demo-simulator/.env")
    
    result = lambda_handler({"probability": 1.0}, None)
    print(json.dumps(result, indent=2))
