#!/usr/bin/env python3
import os
import json
import random
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACK_TEMPLATES = [
    "On it, looking into this now",
    "Ack - checking dashboards",
    "Got it, investigating",
    "Taking a look now",
    "On this - pulling up metrics",
    "Acknowledged, digging in",
]

TRIAGE_TEMPLATES = [
    "Seeing elevated error rates in the logs. Checking if this correlates with the recent deploy.",
    "Found some connection timeouts in the traces. Looks like it might be hitting the DB.",
    "Metrics show a spike starting ~10 mins ago. Checking what changed around that time.",
    "CPU looks fine but memory is climbing. Could be a leak, checking heap dumps.",
    "Seeing 503s from the upstream service. Going to check their status page.",
    "Looks like this started after the config change. Rolling back to confirm.",
]

UPDATE_TEMPLATES = [
    "Still investigating. Narrowed it down to the {component} layer.",
    "Making progress - found a suspicious pattern in the logs. Digging deeper.",
    "Confirmed the issue is related to {component}. Working on a fix.",
    "Escalated to {team} team for additional context.",
    "Deployed a temporary mitigation. Monitoring to see if it helps.",
]

RESOLUTION_TEMPLATES = [
    "Root cause identified and fixed. The issue was {cause}. Monitoring for recurrence.",
    "Resolved - turned out to be {cause}. Added alerting to catch this earlier next time.",
    "Fixed! {cause}. Will follow up with a post-mortem.",
    "All clear now. Issue was {cause}. Metrics back to normal.",
]

CAUSES = [
    "a connection pool exhaustion due to slow queries",
    "a memory leak in the cache layer",
    "a misconfigured timeout after the last deploy",
    "an upstream dependency degradation",
    "a spike in traffic from a retry storm",
    "a certificate expiration we missed",
]

COMPONENTS = ["database", "cache", "API gateway", "message queue", "auth service"]
TEAMS = ["platform", "SRE", "backend", "infrastructure"]


class PagerDutyClient:
    def __init__(self):
        self.admin_token = os.getenv("PAGERDUTY_ADMIN_TOKEN", "")
        self.api_base = "https://api.pagerduty.com"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Token token={self.admin_token}",
            "Content-Type": "application/json",
        }
    
    def list_incidents(self, statuses: List[str]) -> List[Dict]:
        params = {
            "statuses[]": statuses,
            "sort_by": "created_at:asc",
            "limit": 25,
        }
        try:
            response = requests.get(
                f"{self.api_base}/incidents",
                headers=self._headers(),
                params=params,
            )
            if response.status_code == 200:
                return response.json().get("incidents", [])
            logger.error(f"Failed to list incidents: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error listing incidents: {e}")
        return []
    
    def acknowledge_incident(self, incident_id: str) -> bool:
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "acknowledged",
            }
        }
        try:
            response = requests.put(
                f"{self.api_base}/incidents/{incident_id}",
                headers=self._headers(),
                json=payload,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error acknowledging incident: {e}")
            return False
    
    def resolve_incident(self, incident_id: str) -> bool:
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "resolved",
            }
        }
        try:
            response = requests.put(
                f"{self.api_base}/incidents/{incident_id}",
                headers=self._headers(),
                json=payload,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error resolving incident: {e}")
            return False
    
    def add_note(self, incident_id: str, content: str) -> bool:
        payload = {"note": {"content": content}}
        try:
            response = requests.post(
                f"{self.api_base}/incidents/{incident_id}/notes",
                headers=self._headers(),
                json=payload,
            )
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False


class SlackClient:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.api_base = "https://slack.com/api"
    
    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "error": "no_token"}
        response = requests.post(
            f"{self.api_base}/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"channel": channel, "text": text}
        )
        return response.json()


def get_incident_age_minutes(incident: Dict) -> float:
    created_at = incident.get("created_at", "")
    if not created_at:
        return 0
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 60
    except Exception:
        return 0


def process_incidents() -> Dict[str, Any]:
    pd = PagerDutyClient()
    slack = SlackClient()
    channel = os.getenv("SLACK_CHANNEL_ACTIVE_INCIDENTS", "")
    
    results = {
        "acknowledged": [],
        "notes_added": [],
        "resolved": [],
        "skipped": [],
    }
    
    triggered = pd.list_incidents(["triggered"])
    for incident in triggered:
        age = get_incident_age_minutes(incident)
        incident_id = incident["id"]
        title = incident.get("title", "Unknown")
        
        if "[DEMO]" not in title:
            results["skipped"].append({"id": incident_id, "reason": "not a demo incident"})
            continue
        
        if age >= 3:
            if pd.acknowledge_incident(incident_id):
                results["acknowledged"].append(incident_id)
                msg = random.choice(ACK_TEMPLATES)
                if channel:
                    slack.post_message(channel, f":eyes: {msg}")
                pd.add_note(incident_id, f"[Automated] {msg}")
                logger.info(f"Acknowledged incident {incident_id} (age: {age:.1f}m)")
        else:
            results["skipped"].append({"id": incident_id, "reason": f"too new ({age:.1f}m)"})
    
    acknowledged = pd.list_incidents(["acknowledged"])
    for incident in acknowledged:
        age = get_incident_age_minutes(incident)
        incident_id = incident["id"]
        title = incident.get("title", "Unknown")
        
        if "[DEMO]" not in title:
            results["skipped"].append({"id": incident_id, "reason": "not a demo incident"})
            continue
        
        if age >= 30:
            if pd.resolve_incident(incident_id):
                results["resolved"].append(incident_id)
                cause = random.choice(CAUSES)
                msg = random.choice(RESOLUTION_TEMPLATES).format(cause=cause)
                if channel:
                    slack.post_message(channel, f":white_check_mark: {msg}")
                pd.add_note(incident_id, f"[Automated] {msg}")
                logger.info(f"Resolved incident {incident_id} (age: {age:.1f}m)")
        elif age >= 10 and random.random() < 0.5:
            component = random.choice(COMPONENTS)
            team = random.choice(TEAMS)
            if random.random() < 0.5:
                msg = random.choice(TRIAGE_TEMPLATES)
            else:
                msg = random.choice(UPDATE_TEMPLATES).format(component=component, team=team)
            if pd.add_note(incident_id, f"[Automated] {msg}"):
                results["notes_added"].append(incident_id)
                if channel:
                    slack.post_message(channel, f":mag: {msg}")
                logger.info(f"Added note to incident {incident_id}")
        else:
            results["skipped"].append({"id": incident_id, "reason": f"waiting ({age:.1f}m)"})
    
    return results


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Lifecycle Lambda invoked")
    
    results = process_incidents()
    
    logger.info(f"Results: {results}")
    
    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../scripts/demo-simulator/.env")
    
    result = lambda_handler({}, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
