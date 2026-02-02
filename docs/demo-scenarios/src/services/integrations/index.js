import { sendDatadogEvent, hasDatadogCredentials } from './datadog.js';
import { sendSentryError, hasSentryCredentials } from './sentry.js';
import { triggerGitHubWorkflow, hasGitHubCredentials } from './github.js';
import { sendNewRelicEvent, hasNewRelicCredentials } from './newrelic.js';
import { sendSplunkEvent, hasSplunkCredentials } from './splunk.js';
import { sendCloudWatchMetric, hasCloudWatchCredentials } from './cloudwatch.js';
import { sendAlertmanagerAlert, hasPrometheusCredentials } from './prometheus.js';
import { sendGrafanaAnnotation, hasGrafanaCredentials } from './grafana.js';
import { triggerUptimeRobotAlert, hasUptimeRobotCredentials } from './uptimerobot.js';
import { triggerPagerDutyDirect, hasPagerDutyCredentials } from './pagerduty.js';

export * from './datadog.js';
export * from './sentry.js';
export * from './github.js';
export * from './newrelic.js';
export * from './splunk.js';
export * from './cloudwatch.js';
export * from './prometheus.js';
export * from './grafana.js';
export * from './uptimerobot.js';
export * from './pagerduty.js';

const FULL_FLOW_INTEGRATIONS = ['datadog', 'grafana', 'cloudwatch', 'newrelic', 'github_actions', 'prometheus'];

const integrationTriggers = {
  datadog: { trigger: sendDatadogEvent, hasCredentials: hasDatadogCredentials, fullFlow: true },
  sentry: { trigger: sendSentryError, hasCredentials: hasSentryCredentials, fullFlow: false },
  github_actions: { trigger: triggerGitHubWorkflow, hasCredentials: hasGitHubCredentials, fullFlow: true },
  newrelic: { trigger: sendNewRelicEvent, hasCredentials: hasNewRelicCredentials, fullFlow: true },
  splunk: { trigger: sendSplunkEvent, hasCredentials: hasSplunkCredentials, fullFlow: false },
  cloudwatch: { trigger: sendCloudWatchMetric, hasCredentials: hasCloudWatchCredentials, fullFlow: true },
  prometheus: { trigger: sendAlertmanagerAlert, hasCredentials: hasPrometheusCredentials, fullFlow: true },
  grafana: { trigger: sendGrafanaAnnotation, hasCredentials: hasGrafanaCredentials, fullFlow: true },
  uptimerobot: { trigger: triggerUptimeRobotAlert, hasCredentials: hasUptimeRobotCredentials, fullFlow: false }
};

export function getIntegrationStatus() {
  const status = {};
  for (const [name, { hasCredentials, fullFlow }] of Object.entries(integrationTriggers)) {
    status[name] = {
      configured: hasCredentials(),
      name: formatIntegrationName(name),
      fullFlow: fullFlow,
      pdFallbackAvailable: hasPagerDutyCredentials()
    };
  }
  status.pagerduty_direct = {
    configured: hasPagerDutyCredentials(),
    name: 'PagerDuty Direct',
    fullFlow: true,
    pdFallbackAvailable: false
  };
  return status;
}

export function isIntegrationConfigured(integration) {
  if (integration === 'pagerduty_direct') {
    return hasPagerDutyCredentials();
  }
  const config = integrationTriggers[integration];
  return config ? config.hasCredentials() : false;
}

export async function triggerNativeIntegration(scenario) {
  const integration = scenario.tags?.integration;
  
  if (!integration) {
    return await triggerWithPagerDutyFallback(scenario, null, 'No integration specified');
  }

  const config = integrationTriggers[integration];
  
  if (!config) {
    return await triggerWithPagerDutyFallback(scenario, integration, `Unknown integration: ${integration}`);
  }

  try {
    let nativeResult = null;
    let nativeError = null;
    
    if (config.hasCredentials()) {
      try {
        nativeResult = await config.trigger(scenario);
      } catch (error) {
        nativeError = error.message;
      }
    }

    if (config.fullFlow && nativeResult && !nativeResult.requiresFallback) {
      return { 
        ...nativeResult, 
        nativeTriggered: true,
        integration,
        flow: 'native -> tool -> PagerDuty'
      };
    }

    const pdResult = await triggerWithPagerDutyFallback(
      scenario, 
      integration, 
      nativeError || (nativeResult?.reason) || 'Integration does not support full flow'
    );

    return {
      ...pdResult,
      nativeAttempted: !!nativeResult || !!nativeError,
      nativeResult: nativeResult,
      nativeError: nativeError
    };

  } catch (error) {
    return await triggerWithPagerDutyFallback(scenario, integration, error.message);
  }
}

async function triggerWithPagerDutyFallback(scenario, integration, reason) {
  if (!hasPagerDutyCredentials()) {
    return { 
      success: false, 
      error: 'PagerDuty routing key not configured for fallback',
      originalReason: reason,
      integration 
    };
  }

  try {
    const result = await triggerPagerDutyDirect(scenario);
    return {
      ...result,
      success: true,
      fallbackUsed: true,
      fallbackReason: reason,
      originalIntegration: integration,
      flow: `${integration || 'unknown'} (fallback) -> PagerDuty Direct`
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      fallbackUsed: true,
      originalReason: reason,
      integration
    };
  }
}

function formatIntegrationName(integration) {
  const names = {
    datadog: 'Datadog',
    sentry: 'Sentry',
    github_actions: 'GitHub Actions',
    newrelic: 'New Relic',
    splunk: 'Splunk',
    cloudwatch: 'CloudWatch',
    prometheus: 'Prometheus',
    grafana: 'Grafana',
    uptimerobot: 'UptimeRobot',
    pagerduty_direct: 'PagerDuty Direct'
  };
  return names[integration] || integration;
}
