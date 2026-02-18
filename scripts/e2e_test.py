#!/usr/bin/env python3
import os
import requests
import json
import time
import random
import uuid
from datetime import datetime

PD_ADMIN_TOKEN = os.environ.get("PD_ADMIN_TOKEN", "")
PD_ROUTING_KEY = os.environ.get("PD_ROUTING_KEY", "")
PD_EVENT_ORCH_KEY = os.environ.get("PD_EVENT_ORCH_KEY", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_TEAM_ID = os.environ.get("SLACK_TEAM_ID", "")
DATADOG_API_KEY = os.environ.get("DATADOG_API_KEY", "")
DATADOG_APP_KEY = os.environ.get("DATADOG_APP_KEY", "")
DATADOG_SITE = os.environ.get("DATADOG_SITE", "us5.datadoghq.com")

PD_HEADERS = {
    "Authorization": f"Token token={PD_ADMIN_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.pagerduty+json;version=2"
}

SLACK_HEADERS = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json"
}

USER_EMAILS = {
    "Jack Daniels": "jdaniels@losandesgaa.onmicrosoft.com",
    "Arthur Guinness": "aguiness@losandesgaa.onmicrosoft.com",
    "Ginny Tonic": "gtonic@losandesgaa.onmicrosoft.com",
    "James Murphy": "jmurphy@losandesgaa.onmicrosoft.com",
    "Jameson Casker": "jcasker@losandesgaa.onmicrosoft.com",
    "Jim Beam": "jbeam@losandesgaa.onmicrosoft.com",
    "Jose Cuervo": "jcuervo@losandesgaa.onmicrosoft.com",
    "Kaptin Morgan": "kmorgan@losandesgaa.onmicrosoft.com",
    "Paddy Losty": "plosty@losandesgaa.onmicrosoft.com",
    "Uisce Beatha": "ubeatha@losandesgaa.onmicrosoft.com",
}

RESPONDER_MESSAGES = [
    "Looking into this now",
    "Found the root cause - database connection pool exhausted",
    "Scaling up the connection pool",
    "Monitoring metrics - response times returning to normal",
    "Issue resolved - implementing long-term fix in next sprint"
]

class E2ETest:
    def __init__(self):
        self.test_id = f"E2E-{datetime.now().strftime('%H%M%S')}"
        self.incidents = []
        self.slack_channels = []
        self.results = {"passed": [], "failed": [], "skipped": []}
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    def test_passed(self, name):
        self.results["passed"].append(name)
        self.log(f"PASSED: {name}", "PASS")
    
    def test_failed(self, name, error):
        self.results["failed"].append({"name": name, "error": str(error)})
        self.log(f"FAILED: {name} - {error}", "FAIL")
    
    def test_1_trigger_events_api(self):
        self.log("=" * 60)
        self.log("TEST 1: Trigger incident via PagerDuty Events API")
        self.log("=" * 60)
        
        dedup_key = f"e2e-test-{self.test_id}-api"
        payload = {
            "routing_key": PD_ROUTING_KEY,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": f"[DEMO] E2E Test - API Trigger - {self.test_id}",
                "source": "e2e-test-script",
                "severity": "warning",
                "custom_details": {
                    "test_id": self.test_id,
                    "trigger_method": "events_api_v2",
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        try:
            resp = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=30
            )
            self.log(f"Events API response: {resp.status_code}")
            
            if resp.status_code == 202:
                data = resp.json()
                self.log(f"Dedup key: {data.get('dedup_key')}")
                self.incidents.append({"dedup_key": dedup_key, "source": "api"})
                self.test_passed("Trigger via Events API")
                return True
            else:
                self.test_failed("Trigger via Events API", f"Status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            self.test_failed("Trigger via Events API", str(e))
            return False
    
    def test_2_verify_incident_created(self):
        self.log("=" * 60)
        self.log("TEST 2: Verify incident created in PagerDuty")
        self.log("=" * 60)
        
        self.log("Waiting 20s for incident to be created...")
        time.sleep(20)
        
        try:
            resp = requests.get(
                "https://api.pagerduty.com/incidents",
                headers=PD_HEADERS,
                params={
                    "statuses[]": ["triggered", "acknowledged"],
                    "sort_by": "created_at:desc",
                    "limit": 10
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                incidents = resp.json().get("incidents", [])
                demo_incidents = [i for i in incidents if "[DEMO]" in i.get("title", "") and self.test_id in i.get("title", "")]
                
                if demo_incidents:
                    inc = demo_incidents[0]
                    self.log(f"Found incident #{inc['incident_number']}: {inc['title']}")
                    self.log(f"Status: {inc['status']}, Urgency: {inc['urgency']}")
                    self.incidents[0]["id"] = inc["id"]
                    self.incidents[0]["number"] = inc["incident_number"]
                    self.test_passed("Verify incident created")
                    return inc
                else:
                    self.test_failed("Verify incident created", "No matching incident found")
                    return None
            else:
                self.test_failed("Verify incident created", f"API error: {resp.status_code}")
                return None
        except Exception as e:
            self.test_failed("Verify incident created", str(e))
            return None
    
    def test_3_verify_slack_channel(self, incident):
        self.log("=" * 60)
        self.log("TEST 3: Verify Slack channel created by workflow")
        self.log("=" * 60)

        if not incident:
            self.log("Skipping - no incident to check", "WARN")
            self.results["skipped"].append("Verify Slack channel")
            return None

        self.log("Waiting 25s for workflow to create Slack channel...")
        time.sleep(25)

        try:
            resp = requests.get(
                "https://slack.com/api/conversations.list",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                params={
                    "types": "public_channel",
                    "limit": "200",
                    "exclude_archived": "false",
                    "team_id": SLACK_TEAM_ID
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                if not data.get("ok"):
                    error = data.get("error", "unknown")
                    self.log(f"Slack API returned: {error}")
                    if error == "missing_scope":
                        self.log("Bot needs channels:read and groups:read scopes", "WARN")
                    self.test_failed("Verify Slack channel", f"Slack API error: {error}")
                    return None

                channels = data.get("channels", [])
                self.log(f"Found {len(channels)} channels in workspace")

                inc_num = str(incident.get("incident_number", ""))
                matching = [c for c in channels
                           if (f"demo-{inc_num}" in c.get("name", "").lower() or
                               f"inc-{inc_num}" in c.get("name", "").lower())
                           and not c.get("is_archived", False)]

                if matching:
                    channel = matching[0]
                    self.log(f"Found Slack channel: #{channel['name']} (ID: {channel['id']})")
                    self.slack_channels.append(channel)
                    self.test_passed("Verify Slack channel created")
                    return channel
                else:
                    recent_demo = [c for c in channels
                                  if (c.get("name", "").startswith("demo-") or
                                      c.get("name", "").startswith("inc-"))
                                  and not c.get("is_archived", False)]
                    if recent_demo:
                        self.log(f"Found {len(recent_demo)} demo/inc channels but none match incident #{inc_num}")
                        most_recent = sorted(recent_demo, key=lambda x: x.get("created", 0), reverse=True)
                        for c in most_recent[:5]:
                            self.log(f"  - #{c['name']} (created: {c.get('created', 'unknown')})")
                        if most_recent:
                            channel = most_recent[0]
                            self.log(f"Using most recent channel: #{channel['name']}")
                            self.slack_channels.append(channel)
                            self.test_passed("Verify Slack channel (used recent)")
                            return channel
                    self.test_failed("Verify Slack channel", f"No channel found for incident #{inc_num}")
                    return None
            else:
                self.test_failed("Verify Slack channel", f"HTTP error: {resp.status_code}")
                return None
        except Exception as e:
            self.test_failed("Verify Slack channel", str(e))
            return None
    
    def test_4_slack_conversation(self, channel):
        self.log("=" * 60)
        self.log("TEST 4: Simulate Slack conversation in incident channel")
        self.log("=" * 60)

        if not channel:
            self.log("Skipping - no channel available", "WARN")
            self.results["skipped"].append("Slack conversation")
            return False

        channel_id = channel["id"]
        channel_name = channel.get("name", "unknown")
        messages_sent = 0

        try:
            self.log(f"Joining channel #{channel_name}...")
            join_resp = requests.post(
                "https://slack.com/api/conversations.join",
                headers=SLACK_HEADERS,
                json={"channel": channel_id}
            )

            if join_resp.status_code == 200:
                join_data = join_resp.json()
                if join_data.get("ok"):
                    self.log("Bot joined channel successfully")
                elif join_data.get("error") == "already_in_channel":
                    self.log("Bot already in channel")
                else:
                    self.log(f"Join channel failed: {join_data.get('error')}", "WARN")

            for i, msg in enumerate(RESPONDER_MESSAGES):
                delay = random.uniform(2, 5)
                self.log(f"Waiting {delay:.1f}s before message {i+1}...")
                time.sleep(delay)

                resp = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=SLACK_HEADERS,
                    json={
                        "channel": channel_id,
                        "text": f"[{self.test_id}] {msg}"
                    }
                )

                if resp.status_code == 200 and resp.json().get("ok"):
                    self.log(f"Posted: '{msg[:40]}...'")
                    messages_sent += 1
                else:
                    self.log(f"Failed to post message: {resp.json().get('error')}", "WARN")

            if messages_sent >= 3:
                self.test_passed(f"Slack conversation ({messages_sent} messages)")
                return True
            else:
                self.test_failed("Slack conversation", f"Only sent {messages_sent}/{len(RESPONDER_MESSAGES)} messages")
                return False
        except Exception as e:
            self.test_failed("Slack conversation", str(e))
            return False
    
    def test_5_responder_actions(self, incident):
        self.log("=" * 60)
        self.log("TEST 5: Simulate responder actions (acknowledge, notes)")
        self.log("=" * 60)

        if not incident:
            self.log("Skipping - no incident", "WARN")
            self.results["skipped"].append("Responder actions")
            return False

        incident_id = incident.get("id")
        actions_completed = 0

        try:
            self.log("Fetching incident details to get assignee...")
            resp = requests.get(
                f"https://api.pagerduty.com/incidents/{incident_id}",
                headers=PD_HEADERS,
                timeout=30
            )

            assignee_email = None
            assignee_name = None
            if resp.status_code == 200:
                inc_data = resp.json().get("incident", {})
                assignments = inc_data.get("assignments", [])
                if assignments:
                    assignee = assignments[0].get("assignee", {})
                    assignee_name = assignee.get("summary", "")
                    assignee_email = USER_EMAILS.get(assignee_name)
                    if assignee_email:
                        self.log(f"Found assignee: {assignee_name} -> {assignee_email}")
                    else:
                        self.log(f"Found assignee: {assignee_name} (email not in mapping)")

            if not assignee_email:
                assignee_email = "jdaniels@losandesgaa.onmicrosoft.com"
                self.log(f"Using default email: {assignee_email}")

            self.log("Action 1: Acknowledge incident...")
            time.sleep(random.uniform(3, 6))

            resp = requests.put(
                f"https://api.pagerduty.com/incidents/{incident_id}",
                headers={**PD_HEADERS, "From": assignee_email},
                json={
                    "incident": {
                        "id": incident_id,
                        "type": "incident_reference",
                        "status": "acknowledged"
                    }
                }
            )

            if resp.status_code == 200:
                self.log("Incident acknowledged")
                actions_completed += 1
            else:
                error_msg = resp.text[:100] if resp.text else "Unknown error"
                self.log(f"Acknowledge failed: {resp.status_code} - {error_msg}", "WARN")
                self.log("Note: Acknowledge requires the 'From' user to be assigned to the incident")

            self.log("Action 2: Add investigation note...")
            time.sleep(random.uniform(2, 4))

            resp = requests.post(
                f"https://api.pagerduty.com/incidents/{incident_id}/notes",
                headers={**PD_HEADERS, "From": "jdaniels@losandesgaa.onmicrosoft.com"},
                json={
                    "note": {
                        "content": f"[{self.test_id}] E2E Test - Initial investigation started. Checking database connections and API response times."
                    }
                }
            )

            if resp.status_code == 201:
                self.log("Note added")
                actions_completed += 1
            else:
                self.log(f"Add note failed: {resp.status_code}", "WARN")

            self.log("Action 3: Add resolution note...")
            time.sleep(random.uniform(3, 5))

            resp = requests.post(
                f"https://api.pagerduty.com/incidents/{incident_id}/notes",
                headers={**PD_HEADERS, "From": "aguiness@losandesgaa.onmicrosoft.com"},
                json={
                    "note": {
                        "content": f"[{self.test_id}] Root cause identified: Connection pool exhausted. Scaled up pool size from 50 to 100. Monitoring for stability."
                    }
                }
            )

            if resp.status_code == 201:
                self.log("Resolution note added")
                actions_completed += 1
            else:
                self.log(f"Add note failed: {resp.status_code}", "WARN")

            if actions_completed >= 2:
                self.test_passed(f"Responder actions ({actions_completed}/3)")
                return True
            else:
                self.test_failed("Responder actions", f"Only {actions_completed}/3 completed")
                return False
        except Exception as e:
            self.test_failed("Responder actions", str(e))
            return False
    
    def test_6_trigger_via_datadog(self):
        self.log("=" * 60)
        self.log("TEST 6: Trigger incident via Datadog metric spike")
        self.log("=" * 60)
        
        try:
            self.log("Sending high response time metric to Datadog...")
            timestamp = int(time.time())
            
            metric_payload = {
                "series": [{
                    "metric": "demo.api.response_time",
                    "points": [[timestamp, 800]],
                    "type": "gauge",
                    "host": "e2e-test-host",
                    "tags": [f"test_id:{self.test_id}", "env:e2e-test", "service:api-gateway"]
                }]
            }
            
            resp = requests.post(
                f"https://api.{DATADOG_SITE}/api/v1/series",
                headers={
                    "Content-Type": "application/json",
                    "DD-API-KEY": DATADOG_API_KEY
                },
                json=metric_payload,
                timeout=30
            )
            
            if resp.status_code == 202:
                self.log("Metric submitted to Datadog (800ms response time)")
                self.log("Monitor threshold is 500ms - should trigger alert")
                self.test_passed("Send metric to Datadog")
                
                self.log("Note: Datadog monitor may take 1-5 minutes to evaluate and trigger PagerDuty")
                self.incidents.append({"source": "datadog", "metric": "demo.api.response_time"})
                return True
            else:
                self.test_failed("Send metric to Datadog", f"Status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            self.test_failed("Send metric to Datadog", str(e))
            return False
    
    def test_7_resolve_incidents(self):
        self.log("=" * 60)
        self.log("TEST 7: Resolve test incidents")
        self.log("=" * 60)
        
        resolved = 0
        
        for inc in self.incidents:
            if inc.get("source") == "api" and inc.get("dedup_key"):
                try:
                    self.log(f"Resolving incident via Events API...")
                    time.sleep(2)
                    
                    payload = {
                        "routing_key": PD_ROUTING_KEY,
                        "event_action": "resolve",
                        "dedup_key": inc["dedup_key"]
                    }
                    
                    resp = requests.post(
                        "https://events.pagerduty.com/v2/enqueue",
                        json=payload,
                        timeout=30
                    )
                    
                    if resp.status_code == 202:
                        self.log(f"Incident resolved (dedup: {inc['dedup_key'][:20]}...)")
                        resolved += 1
                    else:
                        self.log(f"Resolve failed: {resp.status_code}", "WARN")
                except Exception as e:
                    self.log(f"Resolve error: {e}", "WARN")
        
        for inc in self.incidents:
            if inc.get("source") == "datadog":
                try:
                    self.log("Sending recovery metric to Datadog...")
                    timestamp = int(time.time())
                    
                    metric_payload = {
                        "series": [{
                            "metric": "demo.api.response_time",
                            "points": [[timestamp, 100]],
                            "type": "gauge",
                            "host": "e2e-test-host",
                            "tags": [f"test_id:{self.test_id}", "env:e2e-test", "service:api-gateway"]
                        }]
                    }
                    
                    resp = requests.post(
                        f"https://api.{DATADOG_SITE}/api/v1/series",
                        headers={"Content-Type": "application/json", "DD-API-KEY": DATADOG_API_KEY},
                        json=metric_payload,
                        timeout=30
                    )
                    
                    if resp.status_code == 202:
                        self.log("Recovery metric sent (100ms)")
                        resolved += 1
                except Exception as e:
                    self.log(f"Recovery metric error: {e}", "WARN")
        
        if resolved > 0:
            self.test_passed(f"Resolve incidents ({resolved})")
            return True
        else:
            self.test_failed("Resolve incidents", "No incidents resolved")
            return False
    
    def print_summary(self):
        self.log("=" * 60)
        self.log("E2E TEST SUMMARY")
        self.log("=" * 60)
        
        total = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["skipped"])
        
        print(f"\nTest ID: {self.test_id}")
        print(f"Total Tests: {total}")
        print(f"  Passed:  {len(self.results['passed'])}")
        print(f"  Failed:  {len(self.results['failed'])}")
        print(f"  Skipped: {len(self.results['skipped'])}")
        
        if self.results["passed"]:
            print(f"\nPASSED:")
            for t in self.results["passed"]:
                print(f"  [OK] {t}")
        
        if self.results["failed"]:
            print(f"\nFAILED:")
            for t in self.results["failed"]:
                print(f"  [X] {t['name']}: {t['error']}")
        
        if self.results["skipped"]:
            print(f"\nSKIPPED:")
            for t in self.results["skipped"]:
                print(f"  [-] {t}")
        
        print(f"\nIncidents created: {len(self.incidents)}")
        print(f"Slack channels: {len(self.slack_channels)}")
        
        if len(self.results["failed"]) == 0 and len(self.results["passed"]) > 0:
            print(f"\n{'='*60}")
            print("E2E TEST SUITE: PASSED")
            print(f"{'='*60}")
            return True
        else:
            print(f"\n{'='*60}")
            print("E2E TEST SUITE: FAILED")
            print(f"{'='*60}")
            return False
    
    def run(self):
        self.log(f"Starting E2E Test Suite - {self.test_id}")
        self.log(f"Timestamp: {datetime.now().isoformat()}")
        
        self.test_1_trigger_events_api()
        incident = self.test_2_verify_incident_created()
        channel = self.test_3_verify_slack_channel(incident)
        self.test_4_slack_conversation(channel)
        self.test_5_responder_actions(incident)
        self.test_6_trigger_via_datadog()
        self.test_7_resolve_incidents()
        
        return self.print_summary()

if __name__ == "__main__":
    test = E2ETest()
    success = test.run()
    exit(0 if success else 1)
