#!/usr/bin/env python3
import os
import json
import logging
import re
from typing import Optional, Dict, Any, List

from shared import PagerDutyClient, SlackClient, CONALL_SLACK_USER_ID, SLACK_WORKSPACE_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_notified_channels = set()


def is_demo_scenario_channel(channel_name: str) -> bool:
    return channel_name.startswith("inc-") and "[demo]" not in channel_name.lower()


def extract_incident_number(channel_name: str) -> Optional[str]:
    match = re.match(r"inc-(\d+)", channel_name)
    return match.group(1) if match else None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    global _notified_channels
    
    logger.info("Demo Scenario Notifier Lambda invoked")
    
    slack = SlackClient()
    pd = PagerDutyClient()
    
    results = {
        "channels_checked": 0,
        "dm_sent": [],
        "skipped": [],
    }
    
    recent_channels = slack.get_recent_channels(minutes=10)
    results["channels_checked"] = len(recent_channels)
    logger.info(f"Found {len(recent_channels)} recently created channels")
    
    for channel in recent_channels:
        channel_name = channel.get("name", "")
        channel_id = channel.get("id", "")
        
        if channel_id in _notified_channels:
            results["skipped"].append({"channel": channel_name, "reason": "already_notified"})
            continue
        
        if not is_demo_scenario_channel(channel_name):
            results["skipped"].append({"channel": channel_name, "reason": "not_demo_scenario"})
            continue
        
        incident_num = extract_incident_number(channel_name)
        incident_info = ""
        if incident_num:
            incidents = pd.list_recent_incidents(minutes=30)
            for inc in incidents:
                if str(inc.get("incident_number")) == incident_num:
                    title = inc.get("title", "Unknown")
                    service = inc.get("service", {}).get("summary", "Unknown Service")
                    status = inc.get("status", "unknown")
                    incident_info = f"\n*Incident:* {title}\n*Service:* {service}\n*Status:* {status.upper()}"
                    break
        
        channel_link = f"https://pdtlosandes.slack.com/archives/{channel_id}"
        
        message = (
            f":rotating_light: *Demo Scenario Started*\n\n"
            f"A new incident channel has been created for your demo scenario.\n"
            f"*Channel:* <#{channel_id}|{channel_name}>"
            f"{incident_info}\n\n"
            f":point_right: <{channel_link}|Click here to join the channel>"
        )
        
        result = slack.send_dm(CONALL_SLACK_USER_ID, message)
        
        if result.get("ok"):
            _notified_channels.add(channel_id)
            results["dm_sent"].append(channel_name)
            logger.info(f"Sent DM notification for channel: {channel_name}")
        else:
            logger.error(f"Failed to send DM: {result}")
            results["skipped"].append({"channel": channel_name, "reason": f"dm_failed: {result.get('error')}"})
    
    logger.info(f"Results: {results}")
    
    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../scripts/demo-simulator/.env")
    
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))
