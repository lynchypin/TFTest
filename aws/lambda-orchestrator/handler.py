#!/usr/bin/env python3
import os
import json
import random
import logging
import time
from typing import Optional, Dict, Any, List

from shared import PagerDutyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCENARIOS_FILE = os.environ.get('SCENARIOS_FILE', '/var/task/scenarios.json')

SERVICE_TO_ROUTING_KEY = {
    "Platform - DBRE": os.getenv("ROUTING_KEY_DBRE", ""),
    "Database - DBRE Team": os.getenv("ROUTING_KEY_DBRE", ""),
    "Platform - Kubernetes/Platform": os.getenv("ROUTING_KEY_K8S", ""),
    "App - Backend API": os.getenv("ROUTING_KEY_API", ""),
    "App - Orders API Team": os.getenv("ROUTING_KEY_API", ""),
    "App - Checkout Team": os.getenv("ROUTING_KEY_API", ""),
    "Platform - Networking": os.getenv("ROUTING_KEY_K8S", ""),
    "Platform - Network": os.getenv("ROUTING_KEY_K8S", ""),
    "SecOps": os.getenv("ROUTING_KEY_K8S", ""),
    "OT Operations - Factory Floor": os.getenv("ROUTING_KEY_K8S", ""),
    "Payments Ops": os.getenv("ROUTING_KEY_API", ""),
    "Platform - Frontend": os.getenv("ROUTING_KEY_K8S", ""),
    "Clinical Systems - EMR": os.getenv("ROUTING_KEY_K8S", ""),
    "Grid Operations Center": os.getenv("ROUTING_KEY_K8S", ""),
    "Network Operations - Core": os.getenv("ROUTING_KEY_K8S", ""),
    "Retail Systems - POS": os.getenv("ROUTING_KEY_API", ""),
    "Payment Processing - Gateway": os.getenv("ROUTING_KEY_API", ""),
    "DevOps - CI/CD Platform": os.getenv("ROUTING_KEY_K8S", ""),
    "Quality Control - Manufacturing": os.getenv("ROUTING_KEY_K8S", ""),
    "Mining Operations - Equipment": os.getenv("ROUTING_KEY_K8S", ""),
    "Safety Operations": os.getenv("ROUTING_KEY_K8S", ""),
}

_cached_scenarios = None


def load_scenarios_from_file() -> List[Dict]:
    global _cached_scenarios
    if _cached_scenarios is not None:
        return _cached_scenarios
    
    try:
        with open(SCENARIOS_FILE, 'r') as f:
            data = json.load(f)
            _cached_scenarios = data.get("scenarios", [])
            logger.info(f"Loaded {len(_cached_scenarios)} scenarios from {SCENARIOS_FILE}")
            return _cached_scenarios
    except FileNotFoundError:
        scenarios_alt = os.path.join(os.path.dirname(__file__), 'scenarios.json')
        try:
            with open(scenarios_alt, 'r') as f:
                data = json.load(f)
                _cached_scenarios = data.get("scenarios", [])
                logger.info(f"Loaded {len(_cached_scenarios)} scenarios from {scenarios_alt}")
                return _cached_scenarios
        except Exception as e:
            logger.warning(f"Could not load scenarios from file: {e}, using built-in scenarios")
            return []
    except Exception as e:
        logger.warning(f"Error loading scenarios: {e}, using built-in scenarios")
        return []


BUILTIN_SCENARIOS = [
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
]


def get_all_scenarios() -> List[Dict]:
    file_scenarios = load_scenarios_from_file()
    if file_scenarios:
        return file_scenarios
    return BUILTIN_SCENARIOS


def get_scenario_by_id(scenario_id: str) -> Optional[Dict]:
    all_scenarios = get_all_scenarios()
    for scenario in all_scenarios:
        if scenario.get("id") == scenario_id:
            return scenario
    return None


def convert_file_scenario_to_payload(scenario: Dict) -> Dict:
    if "payload" in scenario and "summary" in scenario.get("payload", {}):
        return scenario
    
    payload_wrapper = scenario.get("payload", {})
    inner_payload = payload_wrapper.get("payload", payload_wrapper)
    
    return {
        "id": scenario.get("id"),
        "name": scenario.get("name"),
        "payload": {
            "summary": inner_payload.get("summary", scenario.get("description", "Demo incident")),
            "source": inner_payload.get("source", "demo-orchestrator"),
            "severity": inner_payload.get("severity", scenario.get("severity", "warning")),
            "custom_details": {
                **inner_payload.get("custom_details", {}),
                "pd_service": inner_payload.get("custom_details", {}).get("pd_service", scenario.get("target_service", "")),
            }
        }
    }


def spawn_incident(scenario_id: Optional[str] = None, probability: float = 1.0) -> Dict[str, Any]:
    if random.random() > probability:
        return {"status": "skipped", "reason": f"probability check failed ({probability})"}

    all_scenarios = get_all_scenarios()
    
    if scenario_id:
        scenario = get_scenario_by_id(scenario_id)
        if not scenario:
            logger.warning(f"Scenario {scenario_id} not found, selecting random")
            scenario = random.choice(all_scenarios) if all_scenarios else None
    else:
        scenario = random.choice(all_scenarios) if all_scenarios else None
    
    if not scenario:
        return {"status": "error", "reason": "No scenarios available"}
    
    scenario = convert_file_scenario_to_payload(scenario)
    
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

    return {
        "status": "triggered" if result.get("success") else "error",
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "dedup_key": dedup_key,
        "pd_service": pd_service,
        "pagerduty_response": result,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    action = event.get("action")
    
    if action == "list_scenarios":
        scenarios = get_all_scenarios()
        scenario_list = [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "description": s.get("description", ""),
                "severity": s.get("severity"),
                "target_service": s.get("target_service", s.get("payload", {}).get("custom_details", {}).get("pd_service", "")),
            }
            for s in scenarios
        ]
        return {
            "statusCode": 200,
            "body": json.dumps({"scenarios": scenario_list, "count": len(scenario_list)}),
        }
    
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
    
    result = lambda_handler({"action": "list_scenarios"}, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
