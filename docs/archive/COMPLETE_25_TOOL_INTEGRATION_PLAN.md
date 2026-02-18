# COMPLETE 25-TOOL INTEGRATION PLAN

**Purpose:** Direct integration plan for ALL tools with synthetic data generation for realistic demo scenarios

---

## MASTER TOOL LIST (25 Tools + PagerDuty Core)

| # | Tool | Category | Integration Type | Free Tier | Status |
|---|------|----------|-----------------|-----------|--------|
| 1 | **PagerDuty** | Core Platform | N/A | Trial/NFP | DEPLOYED |
| 2 | **Slack** | Collaboration | Native Extension | Free | PARTIAL |
| 3 | **Jira Cloud** | ITSM | Native Extension | Free | PARTIAL |
| 4 | **Confluence** | Documentation | Via Jira/API | Free | NOT STARTED |
| 5 | **Prometheus** | Monitoring | Events API v2 | Free (self-host) | ROUTING KEY READY |
| 6 | **Grafana** | Visualization | Events API v2 | Free Cloud | ROUTING KEY READY |
| 7 | **Datadog** | APM/Monitoring | Native Integration | Free Forever | ROUTING KEY READY |
| 8 | **New Relic** | APM/Monitoring | Native Integration | Free Forever | ROUTING KEY READY |
| 9 | **Splunk** | Log Management | Events API v2 | Free (dev) | ROUTING KEY READY |
| 10 | **Elasticsearch** | Search/Logs | Events API v2 | Free (self-host) | NEEDS SETUP |
| 11 | **Sentry** | Error Tracking | Native Integration | Free | ROUTING KEY READY |
| 12 | **UptimeRobot** | Uptime Monitoring | Webhook | Free | ROUTING KEY READY |
| 13 | **GitHub Actions** | CI/CD | Events API v2 | Free | ROUTING KEY READY |
| 14 | **AWS CloudWatch** | Cloud Monitoring | Native Integration | Free Tier | ROUTING KEY READY |
| 15 | **Azure Monitor** | Cloud Monitoring | Native Integration | Free Tier | NEEDS SETUP |
| 16 | **GCP Cloud Monitoring** | Cloud Monitoring | Native Integration | Free Tier | NEEDS SETUP |
| 17 | **ServiceNow** | ITSM | Native (PDI) | Developer Instance | NOT STARTED |
| 18 | **Salesforce** | CRM | Native Extension | Developer Edition | NOT STARTED |
| 19 | **Zoom** | Conferencing | Native Extension | Free | NOT CONNECTED |
| 20 | **Microsoft Teams** | Collaboration | Native Extension | Free | NOT STARTED |
| 21 | **Google Meet** | Conferencing | Native Extension | Free (Workspace) | NOT STARTED |
| 22 | **StatusPage** | Status Communication | Native | Included | NOT CONFIGURED |
| 23 | **Nagios** | Legacy Monitoring | Events API v2 | Free (XI free) | NOT STARTED |
| 24 | **Rundeck** | Automation | Native (RBA) | Free OSS | NOT STARTED |
| 25 | **Power BI** | Analytics | Indirect (API/Export) | Free | INDIRECT ONLY |

---

## CRITICAL NOTES

### Incident Workflow Creation Process

Due to a known issue with the PagerDuty Terraform provider (404 errors when creating incident workflows with steps), workflows must be built via the PagerDuty API.

**Create workflow with steps in a single API call:**
```bash
curl -X POST "https://api.pagerduty.com/incident_workflows" \
  -H "Authorization: Token token=${PAGERDUTY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_workflow": {
      "name": "Workflow Name",
      "description": "Description",
      "team": {"id": "TEAM_ID", "type": "team_reference"},
      "steps": [
        {
          "name": "Add Note",
          "configuration": {
            "action_id": "pagerduty.add-incident-note",
            "inputs": [{"name": "note", "value": "Incident protocol activated"}]
          }
        },
        {
          "name": "Create Slack Channel",
          "configuration": {
            "action_id": "pagerduty.create-slack-channel",
            "inputs": [
              {"name": "channel_name", "value": "inc-{{incident.id}}"},
              {"name": "is_private", "value": "false"},
              {"name": "connection_id", "value": "SLACK_CONNECTION_ID"}
            ]
          }
        },
        {
          "name": "Add Responders",
          "configuration": {
            "action_id": "pagerduty.add-responders",
            "inputs": [{"name": "responders", "value": "[{\"type\":\"escalation_policy\",\"id\":\"EP_ID\"}]"}]
          }
        }
      ]
    }
  }'
```

**Available workflow actions:**
- `pagerduty.add-incident-note` - Add note to incident
- `pagerduty.create-slack-channel` - Create Slack channel (requires `slack_connection_id`)
- `pagerduty.archive-slack-channel` - Archive Slack channel
- `pagerduty.add-responders` - Add responders from escalation policy
- `pagerduty.create-conference-bridge` - Create Zoom/Teams bridge
- `pagerduty.run-automation-action` - Run automation action
- `pagerduty.post-to-status-page` - Post status update
- `pagerduty.create-jira-issue` - Create Jira ticket

**Automation Script:** `scripts/data-generators/build_workflows_via_api.py`
```bash
export PAGERDUTY_TOKEN=your_admin_token
export SLACK_CONNECTION_ID=your_slack_connection_id
python scripts/data-generators/build_workflows_via_api.py --apply
```

---

## PART 1: MONITORING TOOLS (Inbound Alerts)

### 1.1 Prometheus + Alertmanager

**Integration Type:** Events API v2 via Alertmanager webhook
**Free Tier:** Self-hosted (completely free)

**Setup Steps:**
```bash
# Deploy Prometheus stack (Docker Compose or K8s)
# Alertmanager config to send to PagerDuty:

receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: '${prometheus_routing_key}'  # From terraform output
        severity: critical
        description: '{{ .CommonAnnotations.summary }}'
        details:
          alertname: '{{ .CommonLabels.alertname }}'
          instance: '{{ .CommonLabels.instance }}'
          
  - name: 'pagerduty-warning'
    pagerduty_configs:
      - routing_key: '${prometheus_routing_key}'
        severity: warning
```

**Synthetic Data Generation:**
```yaml
# prometheus/demo_metrics.yml - Fake metrics for demo scenarios
groups:
  - name: demo_application_metrics
    rules:
      # Simulate high CPU
      - record: demo:cpu_usage_percent
        expr: 50 + (sin(time() / 300) * 30) + (random() * 10)
      
      # Simulate memory leak (gradually increasing)
      - record: demo:memory_usage_percent  
        expr: 60 + (time() % 3600) / 60  # Increases over 1 hour
      
      # Simulate request latency spikes
      - record: demo:request_latency_seconds
        expr: 0.1 + (sin(time() / 120) > 0.8 ? 2.5 : 0)
      
      # Simulate error rate
      - record: demo:error_rate_percent
        expr: 2 + (random() * 3) + (hour() >= 14 and hour() <= 16 ? 15 : 0)

  - name: demo_alerting_rules
    rules:
      - alert: HighCPUUsage
        expr: demo:cpu_usage_percent > 85
        for: 2m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          
      - alert: MemoryLeak
        expr: demo:memory_usage_percent > 90
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Memory leak detected - usage at {{ $value }}%"
```

**Scenarios Using This Tool:**
- P1: Multi-channel alerting (CPU/Memory alerts)
- P3: Escalation path demo (tiered severity)
- B2: Event correlation (multiple related alerts)

---

### 1.2 Grafana Cloud

**Integration Type:** Native PagerDuty contact point
**Free Tier:** 10k metrics, 50GB logs, 50GB traces

**Setup Steps:**
```
1. Sign up: https://grafana.com/products/cloud/
2. In Grafana Cloud: Alerting > Contact points
3. Add new contact point:
   - Name: PagerDuty
   - Type: PagerDuty
   - Integration Key: ${grafana_cloud_routing_key}
4. Create notification policy routing to PagerDuty
```

**Synthetic Data Generation:**
```javascript
// Grafana Cloud - Synthetic data via k6 or Telegraf

// Option 1: Push metrics via Prometheus remote write
// Configure Prometheus to remote_write to Grafana Cloud

// Option 2: Use Grafana Agent to scrape demo endpoints
// grafana-agent.yaml
metrics:
  configs:
    - name: demo
      scrape_configs:
        - job_name: 'demo-app'
          static_configs:
            - targets: ['demo-app:8080']
          metrics_path: /metrics
      remote_write:
        - url: https://prometheus-prod-us-central.grafana.net/api/prom/push
          basic_auth:
            username: ${GRAFANA_CLOUD_USER}
            password: ${GRAFANA_CLOUD_API_KEY}
```

**Dashboards to Create:**
- Application Performance Overview
- Infrastructure Health
- Business Metrics (order volume, revenue)

---

### 1.3 Datadog

**Integration Type:** Native bidirectional integration
**Free Tier:** Free Forever plan (5 hosts, 1-day retention)

**Setup Steps:**
```
1. Sign up: https://app.datadoghq.com (select Free Forever)
2. In Datadog: Integrations > PagerDuty
3. Add integration:
   - Service name: Map to PagerDuty services
   - Integration key: ${datadog_routing_key}
4. Enable bidirectional sync (optional)
```

**Synthetic Data Generation:**
```python
# datadog_synthetic_data.py
from datadog_api_client import Configuration, ApiClient
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_series import MetricSeries
from datadog_api_client.v2.model.metric_point import MetricPoint
import time
import random
import math

configuration = Configuration()
configuration.api_key["apiKeyAuth"] = os.environ["DATADOG_API_KEY"]
configuration.api_key["appKeyAuth"] = os.environ["DATADOG_APP_KEY"]

def generate_demo_metrics():
    """Generate realistic metrics for demo scenarios"""
    with ApiClient(configuration) as api_client:
        api = MetricsApi(api_client)
        
        timestamp = int(time.time())
        
        # Simulate payment service latency (normal ~100ms, spikes to 2s)
        latency = 0.1 + (0.05 * random.random())
        if random.random() > 0.95:  # 5% chance of spike
            latency = 2.0 + random.random()
        
        # Simulate error rate (normal ~1%, incident ~15%)
        error_rate = 1.0 + random.random()
        if os.environ.get("SIMULATE_INCIDENT"):
            error_rate = 15.0 + (5 * random.random())
        
        series = [
            MetricSeries(
                metric="demo.payment.latency",
                type=MetricSeries.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=latency)],
                tags=["service:payment", "env:demo"]
            ),
            MetricSeries(
                metric="demo.payment.error_rate",
                type=MetricSeries.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=error_rate)],
                tags=["service:payment", "env:demo"]
            ),
            MetricSeries(
                metric="demo.orders.per_minute",
                type=MetricSeries.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=100 + 50*math.sin(timestamp/1800))],
                tags=["service:orders", "env:demo"]
            )
        ]
        
        api.submit_metrics(MetricPayload(series=series))

# Datadog Monitors to create:
MONITORS = [
    {
        "name": "[Demo] Payment Service High Latency",
        "type": "metric alert",
        "query": "avg(last_5m):avg:demo.payment.latency{service:payment} > 1",
        "message": "Payment service latency is above 1s. @pagerduty-payment-service",
        "priority": 1
    },
    {
        "name": "[Demo] High Error Rate",
        "type": "metric alert", 
        "query": "avg(last_5m):avg:demo.payment.error_rate{*} > 10",
        "message": "Error rate exceeded 10%. @pagerduty-platform",
        "priority": 2
    }
]
```

**Scenarios Using This Tool:**
- P1: Multi-channel alerting (APM metrics)
- B3: Service orchestration (service-level alerts)
- D1: AIOps correlation (multiple services)

---

### 1.4 New Relic

**Integration Type:** Native integration via Alerts & AI
**Free Tier:** 100GB/month ingest, unlimited users

**Setup Steps:**
```
1. Sign up: https://newrelic.com/signup (no credit card)
2. In New Relic: Alerts & AI > Destinations
3. Add destination: PagerDuty
   - Integration key: ${new_relic_routing_key}
4. Create alert policies with PagerDuty notification
```

**Synthetic Data Generation:**
```python
# new_relic_synthetic_data.py
import requests
import os
import time
import random

NEW_RELIC_INSERT_KEY = os.environ["NEW_RELIC_INSIGHTS_KEY"]
NEW_RELIC_ACCOUNT_ID = os.environ["NEW_RELIC_ACCOUNT_ID"]

def send_custom_events():
    """Send custom events to New Relic for demo scenarios"""
    
    events = [
        {
            "eventType": "DemoTransaction",
            "service": "payment-service",
            "duration": 0.1 + random.random() * 0.5,
            "statusCode": random.choices([200, 200, 200, 500, 503], weights=[85, 5, 5, 3, 2])[0],
            "endpoint": "/api/v1/payment/process",
            "customerId": f"CUST-{random.randint(1000, 9999)}"
        },
        {
            "eventType": "DemoTransaction",
            "service": "user-service",
            "duration": 0.05 + random.random() * 0.2,
            "statusCode": 200,
            "endpoint": "/api/v1/users/profile"
        },
        {
            "eventType": "DemoInfrastructure",
            "host": f"prod-web-{random.randint(1,5)}",
            "cpuPercent": 40 + random.random() * 30,
            "memoryPercent": 60 + random.random() * 20,
            "diskPercent": 70 + random.random() * 10
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Api-Key": NEW_RELIC_INSERT_KEY
    }
    
    url = f"https://insights-collector.newrelic.com/v1/accounts/{NEW_RELIC_ACCOUNT_ID}/events"
    response = requests.post(url, json=events, headers=headers)
    return response.status_code

# NRQL Alerts to create:
ALERT_CONDITIONS = [
    {
        "name": "[Demo] High Transaction Error Rate",
        "nrql": "SELECT percentage(count(*), WHERE statusCode >= 500) FROM DemoTransaction WHERE service = 'payment-service'",
        "threshold": 5,
        "priority": "critical"
    },
    {
        "name": "[Demo] Slow Transaction Response",
        "nrql": "SELECT percentile(duration, 95) FROM DemoTransaction WHERE service = 'payment-service'",
        "threshold": 2,
        "priority": "warning"
    }
]
```

---

### 1.5 Splunk

**Integration Type:** Events API v2 via Splunk Alert Action
**Free Tier:** Splunk Free (500MB/day), Splunk Dev License

**Setup Steps:**
```
1. Splunk Cloud trial OR Splunk Free download
2. Install PagerDuty Alert Action app:
   - Splunkbase: https://splunkbase.splunk.com/app/3013
3. Configure with routing key: ${splunk_routing_key}
4. Create saved searches with alert actions
```

**Synthetic Data Generation:**
```python
# splunk_synthetic_data.py
import requests
import os
import json
import time
import random
from datetime import datetime

SPLUNK_HEC_URL = os.environ["SPLUNK_HEC_URL"]
SPLUNK_HEC_TOKEN = os.environ["SPLUNK_HEC_TOKEN"]

def generate_demo_logs():
    """Generate realistic log events for Splunk"""
    
    log_templates = [
        {
            "source": "payment-service",
            "sourcetype": "application:json",
            "event": {
                "level": "INFO",
                "message": "Payment processed successfully",
                "transaction_id": f"TXN-{random.randint(100000, 999999)}",
                "amount": round(random.uniform(10, 500), 2),
                "duration_ms": random.randint(50, 200)
            }
        },
        {
            "source": "payment-service", 
            "sourcetype": "application:json",
            "event": {
                "level": "ERROR",
                "message": "Payment gateway timeout",
                "transaction_id": f"TXN-{random.randint(100000, 999999)}",
                "error_code": "GATEWAY_TIMEOUT",
                "retry_count": random.randint(1, 3)
            }
        },
        {
            "source": "api-gateway",
            "sourcetype": "nginx:access",
            "event": f'192.168.1.{random.randint(1,255)} - - [{datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")}] "POST /api/v1/payments HTTP/1.1" {random.choice([200, 200, 200, 500, 502, 503])} {random.randint(100, 5000)} "-" "Demo-Client/1.0"'
        },
        {
            "source": "kubernetes",
            "sourcetype": "kube:events",
            "event": {
                "type": random.choice(["Normal", "Normal", "Warning"]),
                "reason": random.choice(["Scheduled", "Pulled", "Started", "OOMKilled", "BackOff"]),
                "object": f"pod/payment-service-{random.randint(1000,9999)}",
                "message": "Container started" if random.random() > 0.1 else "Container exceeded memory limit"
            }
        }
    ]
    
    # Select weighted random log (mostly success, some errors)
    weights = [70, 10, 15, 5]
    log = random.choices(log_templates, weights=weights)[0]
    
    headers = {
        "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "time": time.time(),
        "host": "demo-cluster",
        "source": log["source"],
        "sourcetype": log["sourcetype"],
        "event": log["event"]
    }
    
    requests.post(SPLUNK_HEC_URL, json=payload, headers=headers, verify=False)

# Splunk Saved Searches (Alerts):
SAVED_SEARCHES = """
[Demo - High Error Rate]
search = sourcetype="application:json" level=ERROR | stats count as errors by source | where errors > 10
alert.severity = 4
action.pagerduty = 1
action.pagerduty.param.integration_key = ${splunk_routing_key}

[Demo - Payment Gateway Failures]
search = sourcetype="application:json" error_code="GATEWAY_TIMEOUT" | stats count | where count > 5
alert.severity = 5
action.pagerduty = 1

[Demo - Pod OOMKilled Events]
search = sourcetype="kube:events" reason="OOMKilled" | stats count by object
alert.severity = 4
action.pagerduty = 1
"""
```

---

### 1.6 Elasticsearch + Elastalert

**Integration Type:** Elastalert to Events API v2
**Free Tier:** Self-hosted (completely free)

**Setup Steps:**
```bash
# Deploy Elasticsearch (Docker)
docker run -d --name elasticsearch \
  -e "discovery.type=single-node" \
  -p 9200:9200 \
  elasticsearch:8.11.0

# Deploy Elastalert2
pip install elastalert2

# elastalert_config.yaml
es_host: elasticsearch
es_port: 9200
rules_folder: /opt/elastalert/rules
run_every:
  minutes: 1
buffer_time:
  minutes: 15
```

**Elastalert Rules:**
```yaml
# rules/payment_errors.yaml
name: Payment Service Error Spike
type: spike
index: demo-logs-*
query_key: service
threshold: 3
spike_height: 3
spike_type: up
timeframe:
  minutes: 10

alert:
  - pagerduty
pagerduty_service_key: ${elasticsearch_routing_key}
pagerduty_client_name: Elastalert
pagerduty_event_type: trigger
```

**Synthetic Data Generation:**
```python
# elasticsearch_synthetic_data.py
from elasticsearch import Elasticsearch
from datetime import datetime
import random
import time

es = Elasticsearch([os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")])

def generate_demo_documents():
    """Generate demo log documents in Elasticsearch"""
    
    services = ["payment-service", "user-service", "api-gateway", "order-service"]
    levels = ["INFO", "INFO", "INFO", "INFO", "WARN", "ERROR"]  # Weighted toward INFO
    
    doc = {
        "@timestamp": datetime.utcnow().isoformat(),
        "service": random.choice(services),
        "level": random.choice(levels),
        "message": random.choice([
            "Request processed successfully",
            "Database query completed",
            "Cache hit for user session",
            "Connection timeout to downstream service",
            "Rate limit exceeded",
            "Null pointer exception in payment handler"
        ]),
        "response_time_ms": random.randint(10, 500) if random.random() > 0.1 else random.randint(2000, 10000),
        "status_code": random.choices([200, 201, 400, 500, 503], weights=[80, 5, 5, 7, 3])[0],
        "trace_id": f"trace-{random.randint(100000, 999999)}",
        "host": f"prod-{random.choice(services)}-{random.randint(1, 3)}"
    }
    
    index_name = f"demo-logs-{datetime.utcnow().strftime('%Y.%m.%d')}"
    es.index(index=index_name, document=doc)
```

---

### 1.7 Sentry

**Integration Type:** Native PagerDuty integration
**Free Tier:** 5K errors/month, 1 user

**Setup Steps:**
```
1. Sign up: https://sentry.io/signup/
2. Create project for each demo service
3. In Sentry: Settings > Integrations > PagerDuty
4. Configure with routing key: ${sentry_routing_key}
5. Set alert rules to notify PagerDuty
```

**Synthetic Data Generation:**
```python
# sentry_synthetic_errors.py
import sentry_sdk
import random
import traceback

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    traces_sample_rate=1.0,
    environment="demo"
)

def simulate_errors():
    """Generate realistic errors for Sentry"""
    
    error_scenarios = [
        ("PaymentProcessingError", "Payment gateway returned unexpected response"),
        ("DatabaseConnectionError", "Connection pool exhausted"),
        ("ValidationError", "Invalid card number format"),
        ("TimeoutError", "Request to inventory service timed out"),
        ("AuthenticationError", "JWT token expired"),
    ]
    
    error_class, message = random.choice(error_scenarios)
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("service", random.choice(["payment", "order", "user"]))
        scope.set_tag("environment", "demo")
        scope.set_user({"id": f"user-{random.randint(1000, 9999)}"})
        scope.set_context("transaction", {
            "id": f"TXN-{random.randint(100000, 999999)}",
            "amount": round(random.uniform(10, 500), 2)
        })
        
        try:
            raise Exception(f"{error_class}: {message}")
        except Exception as e:
            sentry_sdk.capture_exception(e)
```

---

### 1.8 UptimeRobot

**Integration Type:** Webhook to Events API v2
**Free Tier:** 50 monitors, 5-minute intervals

**Setup Steps:**
```
1. Sign up: https://uptimerobot.com/
2. Create monitors for demo endpoints:
   - https://demo-api.example.com/health
   - https://demo-payment.example.com/status
   - https://demo-frontend.example.com
3. Add Alert Contact:
   - Type: Webhook
   - URL: https://events.pagerduty.com/v2/enqueue
   - POST Data (JSON):
```

```json
{
  "routing_key": "${uptime_robot_routing_key}",
  "event_action": "*monitorFriendlyName* is *alertTypeFriendlyName*",
  "dedup_key": "uptimerobot-*monitorID*",
  "payload": {
    "summary": "*monitorFriendlyName* is *alertTypeFriendlyName*",
    "source": "UptimeRobot",
    "severity": "critical",
    "custom_details": {
      "monitor_url": "*monitorURL*",
      "alert_type": "*alertType*",
      "alert_details": "*alertDetails*"
    }
  }
}
```

**Demo Endpoints to Monitor:**
```python
# Create simple health endpoints that can be toggled
# demo_health_server.py
from flask import Flask, jsonify
import os

app = Flask(__name__)

# Toggle via environment variable or file
HEALTHY = True

@app.route('/health')
def health():
    if os.path.exists('/tmp/unhealthy') or not HEALTHY:
        return jsonify({"status": "unhealthy"}), 503
    return jsonify({"status": "healthy"}), 200

@app.route('/toggle-health')
def toggle():
    global HEALTHY
    HEALTHY = not HEALTHY
    return jsonify({"healthy": HEALTHY})
```

---

### 1.9 GitHub Actions

**Integration Type:** Events API v2 via action
**Free Tier:** 2000 minutes/month (public repos unlimited)

**Setup Steps:**
```yaml
# .github/workflows/demo-pipeline.yml
name: Demo CI/CD Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      simulate_failure:
        description: 'Simulate deployment failure'
        required: false
        default: 'false'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build
        run: echo "Building..."
        
      - name: Test
        run: |
          if [[ "${{ github.event.inputs.simulate_failure }}" == "true" ]]; then
            echo "Simulating test failure!"
            exit 1
          fi
          echo "Tests passed!"

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: echo "Deploying..."
        
      - name: Notify PagerDuty on Failure
        if: failure()
        uses: pagerduty/pagerduty-events-action@v1
        with:
          routing-key: ${{ secrets.PAGERDUTY_ROUTING_KEY }}
          event-action: trigger
          dedup-key: github-deploy-${{ github.run_id }}
          summary: "Deployment failed for ${{ github.repository }}"
          severity: critical
          source: GitHub Actions
          custom-details: |
            {
              "repository": "${{ github.repository }}",
              "workflow": "${{ github.workflow }}",
              "run_id": "${{ github.run_id }}",
              "commit": "${{ github.sha }}",
              "actor": "${{ github.actor }}"
            }
```

---

### 1.10 AWS CloudWatch

**Integration Type:** SNS to EventBridge to PagerDuty
**Free Tier:** 10 custom metrics, 10 alarms, 1M API requests

**Setup Steps:**
```hcl
# terraform/aws_cloudwatch.tf

# SNS Topic for PagerDuty
resource "aws_sns_topic" "pagerduty_alerts" {
  name = "pagerduty-demo-alerts"
}

# SNS Subscription to PagerDuty Events API
resource "aws_sns_topic_subscription" "pagerduty" {
  topic_arn = aws_sns_topic.pagerduty_alerts.arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/${var.aws_cloudwatch_routing_key}/enqueue"
}

# Demo CloudWatch Alarm
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "demo-high-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This alarm fires when CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.pagerduty_alerts.arn]
  
  dimensions = {
    InstanceId = aws_instance.demo.id
  }
}
```

**Synthetic Data (Custom Metrics):**
```python
# aws_cloudwatch_synthetic.py
import boto3
import random
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def put_demo_metrics():
    """Push custom metrics to CloudWatch for demo"""
    
    cloudwatch.put_metric_data(
        Namespace='Demo/Application',
        MetricData=[
            {
                'MetricName': 'RequestLatency',
                'Value': random.uniform(0.1, 0.5) if random.random() > 0.1 else random.uniform(2, 5),
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'Service', 'Value': 'PaymentService'},
                    {'Name': 'Environment', 'Value': 'Demo'}
                ]
            },
            {
                'MetricName': 'ErrorCount',
                'Value': random.randint(0, 5) if random.random() > 0.05 else random.randint(50, 100),
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Service', 'Value': 'PaymentService'}
                ]
            },
            {
                'MetricName': 'OrdersProcessed',
                'Value': random.randint(80, 120),
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Service', 'Value': 'OrderService'}
                ]
            }
        ]
    )
```

---

### 1.11 Azure Monitor

**Integration Type:** Action Groups to PagerDuty webhook
**Free Tier:** 1M standard web calls, 1GB logs/month

**Setup Steps:**
```hcl
# terraform/azure_monitor.tf

resource "azurerm_monitor_action_group" "pagerduty" {
  name                = "pagerduty-alerts"
  resource_group_name = azurerm_resource_group.demo.name
  short_name          = "pd-alerts"

  webhook_receiver {
    name                    = "pagerduty"
    service_uri             = "https://events.pagerduty.com/integration/${var.azure_routing_key}/enqueue"
    use_common_alert_schema = true
  }
}

resource "azurerm_monitor_metric_alert" "high_cpu" {
  name                = "demo-high-cpu"
  resource_group_name = azurerm_resource_group.demo.name
  scopes              = [azurerm_linux_virtual_machine.demo.id]
  description         = "Alert when CPU exceeds 80%"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.pagerduty.id
  }
}
```

---

### 1.12 GCP Cloud Monitoring

**Integration Type:** Notification Channels
**Free Tier:** 150MB logs, monitoring for most GCP services

**Setup Steps:**
```hcl
# terraform/gcp_monitoring.tf

resource "google_monitoring_notification_channel" "pagerduty" {
  display_name = "PagerDuty Demo"
  type         = "pagerduty"
  
  labels = {
    service_key = var.gcp_routing_key
  }
}

resource "google_monitoring_alert_policy" "high_cpu" {
  display_name = "Demo - High CPU Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "CPU utilization > 80%"
    
    condition_threshold {
      filter          = "resource.type = \"gce_instance\" AND metric.type = \"compute.googleapis.com/instance/cpu/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.pagerduty.name]
}
```

---

### 1.13 Nagios (Legacy Monitoring)

**Integration Type:** Events API v2 via notification command
**Free Tier:** Nagios Core (open source), Nagios XI free trial

**Setup Steps:**
```bash
# /usr/local/nagios/etc/objects/commands.cfg

define command {
    command_name    notify-pagerduty
    command_line    /usr/local/bin/pagerduty_nagios.py \
                    --routing-key "${nagios_routing_key}" \
                    --notification-type "$NOTIFICATIONTYPE$" \
                    --host-name "$HOSTNAME$" \
                    --host-state "$HOSTSTATE$" \
                    --service-description "$SERVICEDESC$" \
                    --service-state "$SERVICESTATE$" \
                    --output "$SERVICEOUTPUT$"
}

define contact {
    contact_name                    pagerduty
    service_notification_commands   notify-pagerduty
    host_notification_commands      notify-pagerduty
}
```

---

## PART 2: ITSM & COLLABORATION TOOLS (Bidirectional)

### 2.1 Slack (CRITICAL - Partially Configured)

**Integration Type:** Native PagerDuty extension (bidirectional)
**Status:** Workspace ID configured, Connection ID MISSING

**IMMEDIATE USER ACTIONS:**
```
1. Get Slack Connection ID:
   - PagerDuty > Integrations > Extensions > Slack
   - Click on your workspace
   - Copy Connection ID from URL or settings

2. Add to terraform.tfvars:
   slack_connection_id = "YOUR_CONNECTION_ID"
```

**Synthetic Slack Activity:**
```python
# slack_activity_simulator.py
from slack_sdk import WebClient
import os
import random
import time

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

DEMO_USERS = {
    "Ginny Tonic": "https://i.pravatar.cc/150?u=ginny",
    "Arthur Guiness": "https://i.pravatar.cc/150?u=arthur",
    "Jim Beam": "https://i.pravatar.cc/150?u=jim",
}

INCIDENT_MESSAGES = [
    "Looking into this now...",
    "Checking the logs, seeing elevated error rates",
    "Identified the issue - database connection pool exhausted",
    "Rolling back the last deployment",
    "Services recovering, monitoring closely",
    "All clear, incident resolved. Will follow up with RCA.",
]

def simulate_incident_response(channel_id, incident_title):
    """Simulate team responding to incident in Slack"""
    
    # Initial alert (usually from PagerDuty integration)
    client.chat_postMessage(
        channel=channel_id,
        text=f":rotating_light: *INCIDENT TRIGGERED*: {incident_title}",
        username="PagerDuty Bot",
        icon_url="https://www.pagerduty.com/favicon.ico"
    )
    
    time.sleep(30)  # Wait 30 seconds
    
    # Team member acknowledges
    user, avatar = random.choice(list(DEMO_USERS.items()))
    client.chat_postMessage(
        channel=channel_id,
        text="I've got this, acknowledging now :eyes:",
        username=user,
        icon_url=avatar
    )
    
    # Simulate investigation messages
    for i in range(4):
        time.sleep(random.randint(60, 180))
        user, avatar = random.choice(list(DEMO_USERS.items()))
        message = INCIDENT_MESSAGES[min(i+1, len(INCIDENT_MESSAGES)-1)]
        client.chat_postMessage(
            channel=channel_id,
            text=message,
            username=user,
            icon_url=avatar
        )
```

---

### 2.2 Jira Cloud (Bidirectional)

**Integration Type:** Native PagerDuty extension
**Status:** Site URL configured, projects may not exist

**REQUIRED JIRA PROJECTS:**
| Key | Name | Issue Types Needed |
|-----|------|-------------------|
| KAN | General Incidents | Incident, Task |
| SECOPS | Security Operations | Security Incident, Task |
| COMPLIANCE | Compliance | Data Breach, Audit, Task |
| INFRA | Infrastructure | Incident, Change Request |
| PIR | Post-Incident Reviews | Post-Mortem, Action Item |
| PAYMENTS | Payment System | Incident, Bug |
| DATA | Data Platform | Incident, Data Issue |

**Jira Project Setup Script:**
```python
# jira_project_setup.py
from jira import JIRA
import os

jira = JIRA(
    server=os.environ["JIRA_BASE_URL"],
    basic_auth=(os.environ["JIRA_USER_EMAIL"], os.environ["JIRA_API_TOKEN"])
)

PROJECTS_TO_CREATE = [
    {"key": "SECOPS", "name": "Security Operations", "template": "com.pyxis.greenhopper.jira:gh-simplified-kanban"},
    {"key": "COMPLIANCE", "name": "Compliance", "template": "com.pyxis.greenhopper.jira:gh-simplified-kanban"},
    {"key": "INFRA", "name": "Infrastructure", "template": "com.pyxis.greenhopper.jira:gh-simplified-scrum"},
    {"key": "PIR", "name": "Post-Incident Reviews", "template": "com.pyxis.greenhopper.jira:gh-simplified-kanban"},
    {"key": "PAYMENTS", "name": "Payment System", "template": "com.pyxis.greenhopper.jira:gh-simplified-scrum"},
    {"key": "DATA", "name": "Data Platform", "template": "com.pyxis.greenhopper.jira:gh-simplified-kanban"},
]

def setup_projects():
    existing = {p.key for p in jira.projects()}
    
    for project in PROJECTS_TO_CREATE:
        if project["key"] not in existing:
            print(f"Creating project: {project['key']}")
            jira.create_project(
                key=project["key"],
                name=project["name"],
                template_name=project["template"],
                lead="admin"  # Your Jira admin username
            )
        else:
            print(f"Project {project['key']} already exists")

# Create custom issue types
def setup_issue_types():
    """Ensure required issue types exist"""
    # Note: Issue type creation requires Jira admin
    # Usually done via UI: Project Settings > Issue Types
    pass
```

**Synthetic Jira Data:**
```python
# jira_synthetic_data.py

def create_incident_ticket(incident_data):
    """Create Jira ticket matching PagerDuty incident"""
    
    issue_dict = {
        "project": {"key": incident_data.get("project_key", "KAN")},
        "summary": f"[INC-{incident_data['number']}] {incident_data['title']}",
        "description": f"""
            h2. Incident Details
            
            *PagerDuty Link:* {incident_data['html_url']}
            *Service:* {incident_data['service']}
            *Priority:* {incident_data['priority']}
            *Status:* {incident_data['status']}
            
            h2. Description
            {incident_data.get('description', 'No description provided')}
            
            h2. Timeline
            * Created: {incident_data['created_at']}
        """,
        "issuetype": {"name": "Incident"},
        "priority": {"name": map_priority(incident_data['priority'])},
        "labels": ["pagerduty", "auto-created"],
    }
    
    return jira.create_issue(fields=issue_dict)

def map_priority(pd_priority):
    """Map PagerDuty priority to Jira priority"""
    mapping = {
        "P1": "Highest",
        "P2": "High", 
        "P3": "Medium",
        "P4": "Low",
        "P5": "Lowest"
    }
    return mapping.get(pd_priority, "Medium")
```

---

### 2.3 Confluence (Documentation Hub)

**Integration Type:** Confluence API + embedded PagerDuty widgets
**Status:** Same Atlassian instance as Jira

**Setup:**
```python
# confluence_setup.py
from atlassian import Confluence
import os

confluence = Confluence(
    url=os.environ["JIRA_BASE_URL"].replace("atlassian.net", "atlassian.net/wiki"),
    username=os.environ["JIRA_USER_EMAIL"],
    password=os.environ["JIRA_API_TOKEN"]
)

# Create runbook space
def setup_runbook_space():
    space_key = "RUNBOOKS"
    
    # Check if space exists
    try:
        confluence.get_space(space_key)
        print(f"Space {space_key} exists")
    except:
        confluence.create_space(
            space_key=space_key,
            space_name="Engineering Runbooks",
            space_description="Incident response runbooks and procedures"
        )
        print(f"Created space {space_key}")
    
    # Create runbook pages
    runbooks = [
        ("Major Incident Response", "major_incident_runbook.md"),
        ("Database Failover", "database_failover_runbook.md"),
        ("Payment Service Troubleshooting", "payment_service_runbook.md"),
        ("Security Incident Response", "security_incident_runbook.md"),
        ("On-Call Handoff Checklist", "oncall_handoff_runbook.md"),
    ]
    
    for title, source_file in runbooks:
        with open(f"docs/confluence-runbooks/{source_file}") as f:
            content = f.read()
        
        # Convert markdown to Confluence storage format
        # (simplified - use confluence-markup converter for full support)
        storage_content = markdown_to_confluence(content)
        
        confluence.create_page(
            space=space_key,
            title=title,
            body=storage_content
        )
```

**Embedded PagerDuty Widgets:**
```html
<!-- Confluence page with PagerDuty widget -->
<ac:structured-macro ac:name="html">
  <ac:plain-text-body><![CDATA[
    <iframe 
      src="https://losandes.pagerduty.com/embed/service/PXXXXXX" 
      width="100%" 
      height="400" 
      frameborder="0">
    </iframe>
  ]]></ac:plain-text-body>
</ac:structured-macro>
```

---

### 2.4 ServiceNow (Enterprise ITSM)

**Integration Type:** PagerDuty Integration (PDI) - Bidirectional
**Free Tier:** ServiceNow Developer Instance (free forever)

**Setup Steps:**
```
1. Get Developer Instance:
   - https://developer.servicenow.com/dev.do
   - Request Personal Developer Instance (free)
   - Instance URL: https://devXXXXX.service-now.com

2. Install PagerDuty Integration:
   - In ServiceNow: System Applications > All Available Applications
   - Search "PagerDuty"
   - Install "PagerDuty Integration"

3. Configure Integration:
   - Navigate to: PagerDuty > Configuration
   - Enter PagerDuty API token
   - Map ServiceNow assignment groups to PagerDuty services

4. Enable Bidirectional Sync:
   - ServiceNow incidents create PagerDuty incidents
   - PagerDuty incidents create/update ServiceNow incidents
```

**ServiceNow Configuration:**
```javascript
// ServiceNow Business Rule: Create PagerDuty Incident
(function executeRule(current, previous) {
    // Only for P1/P2 incidents
    if (current.priority <= 2) {
        var pd = new PagerDutyIntegration();
        pd.createIncident({
            title: current.short_description,
            service_id: getServiceMapping(current.assignment_group),
            urgency: mapPriority(current.priority),
            body: {
                type: "incident_body",
                details: current.description
            }
        });
    }
})(current, previous);
```

**Synthetic ServiceNow Data:**
```python
# servicenow_synthetic_data.py
import requests
import os

SNOW_INSTANCE = os.environ["SERVICENOW_INSTANCE"]
SNOW_USER = os.environ["SERVICENOW_USER"]
SNOW_PASSWORD = os.environ["SERVICENOW_PASSWORD"]

def create_servicenow_incident(data):
    """Create incident in ServiceNow"""
    
    url = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    payload = {
        "short_description": data["title"],
        "description": data["description"],
        "urgency": data.get("urgency", "2"),  # 1=High, 2=Medium, 3=Low
        "impact": data.get("impact", "2"),
        "assignment_group": data.get("assignment_group", "Service Desk"),
        "category": data.get("category", "Inquiry / Help"),
        "caller_id": "demo.user"
    }
    
    response = requests.post(
        url,
        auth=(SNOW_USER, SNOW_PASSWORD),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload
    )
    
    return response.json()

# Keep ServiceNow instance active (they hibernate after 10 days)
def keepalive():
    """Ping ServiceNow instance to prevent hibernation"""
    url = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/sys_user?sysparm_limit=1"
    requests.get(url, auth=(SNOW_USER, SNOW_PASSWORD))
```

---

### 2.5 Salesforce (Customer Context)

**Integration Type:** PagerDuty Salesforce Extension
**Free Tier:** Salesforce Developer Edition (free forever)

**Setup Steps:**
```
1. Get Developer Edition:
   - https://developer.salesforce.com/signup
   - Free, permanent org for development

2. Install PagerDuty Package:
   - In Salesforce: Setup > AppExchange Marketplace
   - Search "PagerDuty"
   - Install "PagerDuty for Salesforce"

3. Configure Connected App:
   - Setup > App Manager > New Connected App
   - Enable OAuth
   - Add required scopes: api, refresh_token

4. Configure in PagerDuty:
   - Integrations > Extensions > Salesforce
   - Connect with OAuth
   - Map fields for customer context
```

**Synthetic Salesforce Data:**
```python
# salesforce_synthetic_data.py
from simple_salesforce import Salesforce
import os
import random

sf = Salesforce(
    instance_url=os.environ["SALESFORCE_INSTANCE_URL"],
    session_id=os.environ["SALESFORCE_ACCESS_TOKEN"]
)

def create_demo_accounts():
    """Create demo customer accounts in Salesforce"""
    
    accounts = [
        {"Name": "Acme Corporation", "Type": "Enterprise", "Industry": "Technology", "AnnualRevenue": 50000000},
        {"Name": "Global Finance Ltd", "Type": "Enterprise", "Industry": "Financial Services", "AnnualRevenue": 100000000},
        {"Name": "HealthCare Plus", "Type": "Customer", "Industry": "Healthcare", "AnnualRevenue": 25000000},
        {"Name": "Retail Giants Inc", "Type": "Enterprise", "Industry": "Retail", "AnnualRevenue": 75000000},
        {"Name": "StartupXYZ", "Type": "Customer", "Industry": "Technology", "AnnualRevenue": 5000000},
    ]
    
    for account in accounts:
        sf.Account.create(account)

def create_demo_cases():
    """Create support cases for demo scenarios"""
    
    accounts = sf.query("SELECT Id, Name FROM Account LIMIT 10")
    
    for record in accounts["records"]:
        case = {
            "AccountId": record["Id"],
            "Subject": f"Performance issue reported by {record['Name']}",
            "Description": "Customer reporting slow response times on payment processing",
            "Status": "New",
            "Priority": random.choice(["High", "Medium", "Low"]),
            "Origin": "Phone"
        }
        sf.Case.create(case)
```

**PagerDuty Workflow with Salesforce Context:**
```hcl
# In incident workflow, add step to fetch customer context
step {
  name   = "Fetch Customer Context"
  action = "pagerduty.get-salesforce-context"
  input {
    name  = "lookup_field"
    value = "{{incident.custom_fields.customer_id}}"
  }
}

step {
  name   = "Add Customer Context Note"
  action = "pagerduty.add-incident-note"
  input {
    name  = "note"
    value = <<-EOT
      Customer Context from Salesforce:
      - Account: {{salesforce.account.name}}
      - Type: {{salesforce.account.type}}
      - Annual Revenue: {{salesforce.account.annual_revenue}}
      - Open Cases: {{salesforce.open_cases_count}}
    EOT
  }
}
```

---

### 2.6 Microsoft Teams (Alternative to Slack)

**Integration Type:** Native PagerDuty extension
**Free Tier:** Microsoft Teams Free (limited features)

**Setup Steps:**
```
1. In PagerDuty: Integrations > Extensions > Microsoft Teams
2. Sign in with Microsoft account
3. Select Teams/Channels to connect
4. Configure notification preferences
```

**Note:** Can run in parallel with Slack for organizations using both.

---

### 2.7 Google Meet (Alternative Conferencing)

**Integration Type:** Native PagerDuty extension
**Free Tier:** Google Workspace free tier or personal Google account

**Setup Steps:**
```
1. In PagerDuty: Integrations > Extensions > Google Meet
2. Authorize with Google account
3. Available in incident workflows as alternative to Zoom
```

---

## PART 3: CONFERENCING & STATUS

### 3.1 Zoom

**Integration Type:** Native PagerDuty extension
**Status:** NOT CONNECTED (blocks Major Incident workflow)

**USER ACTION REQUIRED:**
```
1. In PagerDuty: Integrations > Extensions > Zoom
2. Click "Connect to Zoom"
3. Authorize with Zoom account (free account works)
4. Configure default meeting settings
```

---

### 3.2 PagerDuty Status Page

**Integration Type:** Native PagerDuty feature
**Status:** NOT CONFIGURED

**USER ACTION REQUIRED:**
```
1. In PagerDuty: Status Pages
2. Create new status page:
   - Name: "Demo Service Status"
   - Subdomain: losandes-status (or similar)
3. Add services to track:
   - Payment Service
   - API Gateway
   - User Service
4. Configure public URL and branding
```

**Automated Status Updates:**
```python
# status_page_automation.py
import requests
import os

PD_API_TOKEN = os.environ["PAGERDUTY_ADMIN_TOKEN"]
STATUS_PAGE_ID = os.environ["STATUS_PAGE_ID"]

def post_status_update(component_id, status, message):
    """Post update to PagerDuty Status Page"""
    
    headers = {
        "Authorization": f"Token token={PD_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Update component status
    requests.put(
        f"https://api.pagerduty.com/status_pages/{STATUS_PAGE_ID}/components/{component_id}",
        headers=headers,
        json={
            "component": {
                "status": status  # operational, degraded_performance, partial_outage, major_outage
            }
        }
    )
    
    # Post incident update
    requests.post(
        f"https://api.pagerduty.com/status_pages/{STATUS_PAGE_ID}/incidents",
        headers=headers,
        json={
            "incident": {
                "name": message,
                "status": "investigating",
                "impact": "minor"
            }
        }
    )
```

---

## PART 4: AUTOMATION TOOLS

### 4.1 Rundeck (Runbook Automation)

**Integration Type:** PagerDuty Rundeck integration (bidirectional)
**Free Tier:** Rundeck Community Edition (open source)

**Setup:**
```bash
# Docker deployment
docker run -d --name rundeck \
  -p 4440:4440 \
  -e RUNDECK_GRAILS_URL=http://localhost:4440 \
  rundeck/rundeck:4.x

# Install PagerDuty plugin
# Download from: https://github.com/rundeck-plugins/pagerduty-notification
```

**Rundeck Jobs for Demo:**
```yaml
# rundeck_jobs.yaml
- name: Restart Payment Service
  description: Safely restart payment service pods
  sequence:
    - command: kubectl rollout restart deployment/payment-service -n production
    - command: kubectl rollout status deployment/payment-service -n production --timeout=300s
  notification:
    onsuccess:
      - plugin: pagerduty
        config:
          api_key: ${PAGERDUTY_TOKEN}
          action: resolve
    onfailure:
      - plugin: pagerduty
        config:
          api_key: ${PAGERDUTY_TOKEN}
          action: trigger
          severity: critical

- name: Database Health Check
  description: Check database connectivity and replication
  sequence:
    - script: |
        psql -h ${DB_HOST} -c "SELECT pg_is_in_recovery();"
        psql -h ${DB_HOST} -c "SELECT count(*) FROM pg_stat_replication;"
```

---

## PART 5: POWER BI (INDIRECT INTEGRATION)

**Integration Type:** Indirect (no native PagerDuty integration)
**Approach:** Export PagerDuty data to Power BI via API

**Setup:**
```python
# powerbi_export.py - Export PagerDuty data for Power BI
import requests
import pandas as pd
import os
from datetime import datetime, timedelta

PD_API_TOKEN = os.environ["PAGERDUTY_ADMIN_TOKEN"]

def export_incidents_for_powerbi(days=30):
    """Export incident data for Power BI analysis"""
    
    headers = {
        "Authorization": f"Token token={PD_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    response = requests.get(
        "https://api.pagerduty.com/incidents",
        headers=headers,
        params={
            "since": since,
            "until": datetime.utcnow().isoformat(),
            "limit": 100
        }
    )
    
    incidents = response.json()["incidents"]
    
    # Transform to DataFrame
    df = pd.DataFrame([{
        "incident_number": i["incident_number"],
        "title": i["title"],
        "status": i["status"],
        "urgency": i["urgency"],
        "priority": i.get("priority", {}).get("summary", "None"),
        "service": i["service"]["summary"],
        "created_at": i["created_at"],
        "resolved_at": i.get("resolved_at"),
        "team": i.get("teams", [{}])[0].get("summary", "Unknown")
    } for i in incidents])
    
    # Calculate MTTR
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"])
    df["time_to_resolve_minutes"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 60
    
    # Export to CSV for Power BI
    df.to_csv("pagerduty_incidents.csv", index=False)
    
    # Or push to Power BI streaming dataset
    # push_to_powerbi_streaming(df)
    
    return df
```

**Power BI Dashboard Elements:**
- Incidents by Service (bar chart)
- MTTR trends (line chart)
- Priority distribution (pie chart)
- On-call load by team (heatmap)

---

## PART 6: DATA GENERATION ORCHESTRATOR

**Master Script to Generate Data Across All Tools:**

```python
# demo_data_orchestrator.py
"""
Master orchestrator to generate synthetic data across all integrated tools.
Run this continuously or on-demand for demos.
"""

import schedule
import time
import threading
from datadog_synthetic import generate_demo_metrics as datadog_metrics
from splunk_synthetic import generate_demo_logs as splunk_logs
from elasticsearch_synthetic import generate_demo_documents as es_docs
from newrelic_synthetic import send_custom_events as newrelic_events
from sentry_synthetic import simulate_errors as sentry_errors
from slack_activity import simulate_activity as slack_activity
from jira_synthetic import create_ticket_activity as jira_activity
from aws_cloudwatch_synthetic import put_demo_metrics as aws_metrics

class DemoDataOrchestrator:
    def __init__(self):
        self.running = True
        
    def start(self):
        # Schedule regular data generation
        schedule.every(30).seconds.do(self.generate_monitoring_data)
        schedule.every(5).minutes.do(self.generate_log_data)
        schedule.every(10).minutes.do(self.generate_error_data)
        schedule.every(30).minutes.do(self.generate_itsm_activity)
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def generate_monitoring_data(self):
        """Push metrics to all monitoring tools"""
        threads = [
            threading.Thread(target=datadog_metrics),
            threading.Thread(target=newrelic_events),
            threading.Thread(target=aws_metrics),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    
    def generate_log_data(self):
        """Generate logs in Splunk and Elasticsearch"""
        for _ in range(10):
            splunk_logs()
            es_docs()
    
    def generate_error_data(self):
        """Occasionally generate errors in Sentry"""
        import random
        if random.random() < 0.3:  # 30% chance
            sentry_errors()
    
    def generate_itsm_activity(self):
        """Simulate ITSM ticket updates"""
        jira_activity()
    
    def trigger_incident_scenario(self, scenario_type):
        """
        Trigger a coordinated incident across multiple tools.
        Used during live demos.
        """
        if scenario_type == "payment_outage":
            # 1. Spike metrics in monitoring tools
            self._spike_payment_metrics()
            # 2. Generate errors in Sentry
            self._generate_payment_errors()
            # 3. Create alerts (triggers PagerDuty)
            self._trigger_payment_alerts()
            
        elif scenario_type == "database_degradation":
            self._simulate_db_degradation()
            
        elif scenario_type == "security_breach":
            self._simulate_security_incident()

if __name__ == "__main__":
    orchestrator = DemoDataOrchestrator()
    orchestrator.start()
```

---

## PART 7: INTEGRATION CHECKLIST BY PRIORITY

### PRIORITY 1: Critical for Basic Demo (Do First)
- [ ] Slack Connection ID
- [ ] Zoom connection
- [ ] Status Page creation
- [ ] Jira projects (all 7)

### PRIORITY 2: Rich Monitoring Demo
- [ ] Datadog account + integration
- [ ] New Relic account + integration  
- [ ] Grafana Cloud + integration
- [ ] Sentry account + integration

### PRIORITY 3: Log Management Demo
- [ ] Splunk (dev instance or cloud trial)
- [ ] Elasticsearch + Elastalert

### PRIORITY 4: Cloud Provider Integration
- [ ] AWS CloudWatch (if using AWS)
- [ ] Azure Monitor (if using Azure)
- [ ] GCP Cloud Monitoring (if using GCP)

### PRIORITY 5: Enterprise Features
- [ ] ServiceNow developer instance
- [ ] Salesforce developer edition
- [ ] Confluence runbook space

### PRIORITY 6: Automation & Analytics
- [ ] Rundeck Community Edition
- [ ] Power BI data export setup

### PRIORITY 7: Alternative Channels
- [ ] Microsoft Teams (optional)
- [ ] Google Meet (optional)
- [ ] Nagios (legacy demo only)

---

## APPENDIX: FREE TIER SUMMARY

| Tool | Free Tier | Limitations | Signup URL |
|------|-----------|-------------|------------|
| Datadog | Forever Free | 5 hosts, 1-day retention | datadoghq.com |
| New Relic | Forever Free | 100GB/month | newrelic.com |
| Grafana Cloud | Forever Free | 10k metrics | grafana.com |
| Sentry | Free | 5k errors/month | sentry.io |
| Splunk | Free | 500MB/day | splunk.com |
| UptimeRobot | Free | 50 monitors | uptimerobot.com |
| ServiceNow | Dev Instance | Hibernates after 10 days | developer.servicenow.com |
| Salesforce | Dev Edition | Full features | developer.salesforce.com |
| AWS | Free Tier | 12 months, limits | aws.amazon.com |
| Azure | Free Tier | 12 months, limits | azure.microsoft.com |
| GCP | Free Tier | Always free limits | cloud.google.com |
| Prometheus | Open Source | Self-hosted | prometheus.io |
| Elasticsearch | Open Source | Self-hosted | elastic.co |
| Rundeck | Community | Open source | rundeck.com |
| Slack | Free | Limited history | slack.com |
| Zoom | Free | 40-min meetings | zoom.us |

---

**Total Integration Count:** 25 tools
**Direct Integrations:** 24 tools
**Indirect (API only):** 1 tool (Power BI)
