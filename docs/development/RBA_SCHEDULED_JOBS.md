# RBA Background Scheduled Jobs

This document describes the Rundeck/RBA scheduled jobs that provide continuous background activity for the demo environment.

## Overview

These jobs run entirely in RBA (Runbook Automation) on schedules - they do NOT require a local runner connection. They are defined in `rundeck/jobs/background-scheduled-jobs.yaml`.

## Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| **background-metric-generator** | Every 5 min | Sends synthetic metrics to Datadog/New Relic |
| **background-log-generator** | Every 10 min | Generates application logs with INFO/WARN/ERROR levels |
| **background-user-activity-simulator** | Every 15 min (business hours) | Simulates user actions (ack, notes) using demo user tokens |
| **background-incident-lifecycle-simulator** | Hourly (business hours) | Creates new incidents with 30% probability |
| **background-integration-health-check** | Daily at 8am | Verifies all integration connectivity |
| **demo-reset-quick** | Manual | Resolves all open incidents |
| **demo-reset-full** | Manual | Full environment reset with baseline metrics |
| **scheduled-event-generator** | Hourly at :30 (business hours) | Probability-based event generation |

## Environment Variables Required

The jobs expect these environment variables to be configured in RBA:

```bash
# PagerDuty
PAGERDUTY_API_KEY=<api-key>
PAGERDUTY_EVENTS_KEY=<events-routing-key>

# Monitoring
DATADOG_API_KEY=<datadog-api-key>
DATADOG_SITE=us5.datadoghq.com
NEW_RELIC_LICENSE_KEY=<newrelic-license-key>
NEW_RELIC_API_KEY=<newrelic-api-key>

# Integrations (for health checks)
JIRA_API_TOKEN=<jira-token>
JIRA_EMAIL=<jira-email>
JIRA_SITE_URL=https://losandes.atlassian.net
SENTRY_AUTH_TOKEN=<sentry-token>
SENTRY_ORG_SLUG=alan-xl
GRAFANA_API_KEY=<grafana-api-key>
GRAFANA_URL=https://conalllynch88.grafana.net

# User Tokens (for activity simulator)
USER_TOKEN_Jack=u+4xuQWzuwJ4ujyzz4WQ
USER_TOKEN_Arthur=u+rRnDx15Dpsdsy8iM1Q
USER_TOKEN_Ginny=u+5AUE9uQnCViN8PPxQg
USER_TOKEN_James=u+86hjucXAiKSeukYKog
USER_TOKEN_Jameson=u+eYxgz9yDQWG2oGsMRA
USER_TOKEN_Jim=u+97_sCG8G9zWUVGyXSQ
USER_TOKEN_Jose=u+Udjo1HbtNfPG8howMQ
USER_TOKEN_Kaptin=u+js-oGZPr61sg8rzoAg
USER_TOKEN_Paddy=u+4dGyoxoZiJoaqHMvog
USER_TOKEN_Uisce=u+uawtsftsy4vW_KkNcA
```

## Deploying to RBA

1. Import the job definitions from `rundeck/jobs/background-scheduled-jobs.yaml`
2. Configure the environment variables as RBA project keys
3. Enable the scheduled jobs

## Difference from Automation Actions

| Automation Actions | RBA Scheduled Jobs |
|-------------------|-------------------|
| User-triggered during incidents | Run automatically on schedule |
| Require PD Runner connected | Run in RBA cloud |
| For diagnostics/remediation | For background demo activity |
| Defined in `automation_actions.tf` | Defined in `rundeck/jobs/` |
