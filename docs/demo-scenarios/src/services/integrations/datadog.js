const DATADOG_EVENTS_URL = 'https://api.us5.datadoghq.com/api/v1/events';
const DATADOG_METRICS_URL = 'https://api.us5.datadoghq.com/api/v2/series';

const MONITOR_METRICS = {
  'api.response_time': { metric: 'demo.api.response_time', spikeValue: 2500, threshold: 500 },
  'database.connections': { metric: 'demo.database.connections', spikeValue: 98, threshold: 90 },
  'api.error_rate': { metric: 'demo.api.error_rate', spikeValue: 15, threshold: 5 },
  'system.memory_usage': { metric: 'demo.system.memory_usage', spikeValue: 95, threshold: 85 },
  'queue.depth': { metric: 'demo.queue.depth', spikeValue: 5000, threshold: 1000 }
};

function getMetricForScenario(scenario) {
  const summary = (scenario.payload?.payload?.summary || '').toLowerCase();
  const name = (scenario.name || '').toLowerCase();
  const details = scenario.payload?.payload?.custom_details || {};
  
  if (summary.includes('database') || summary.includes('connection') || details.database) {
    return MONITOR_METRICS['database.connections'];
  }
  if (summary.includes('error rate') || summary.includes('api error') || details.error_rate) {
    return MONITOR_METRICS['api.error_rate'];
  }
  if (summary.includes('memory') || summary.includes('mem') || details.memory_percent) {
    return MONITOR_METRICS['system.memory_usage'];
  }
  if (summary.includes('queue') || summary.includes('backlog') || summary.includes('processing')) {
    return MONITOR_METRICS['queue.depth'];
  }
  return MONITOR_METRICS['api.response_time'];
}

export function getDatadogCredentials() {
  return {
    apiKey: localStorage.getItem('datadog_api_key') || '',
    appKey: localStorage.getItem('datadog_app_key') || ''
  };
}

export function saveDatadogCredentials(apiKey, appKey) {
  if (apiKey) localStorage.setItem('datadog_api_key', apiKey);
  if (appKey) localStorage.setItem('datadog_app_key', appKey);
}

export function clearDatadogCredentials() {
  localStorage.removeItem('datadog_api_key');
  localStorage.removeItem('datadog_app_key');
}

export function hasDatadogCredentials() {
  const { apiKey } = getDatadogCredentials();
  return !!apiKey;
}

export async function sendDatadogEvent(scenario) {
  const { apiKey } = getDatadogCredentials();
  
  if (!apiKey) {
    throw new Error('Datadog API key not configured');
  }

  const payload = scenario.payload.payload;
  const metricConfig = getMetricForScenario(scenario);
  
  const eventResponse = await sendEvent(apiKey, scenario, payload);
  const metricResponse = await sendMetricSpike(apiKey, scenario, payload, metricConfig);

  return {
    status: 'success',
    message: `Event + metric spike (${metricConfig.metric}=${metricConfig.spikeValue}) sent to Datadog`,
    event_id: eventResponse.event?.id,
    metric: metricConfig.metric,
    spikeValue: metricConfig.spikeValue,
    threshold: metricConfig.threshold,
    integration: 'datadog'
  };
}

async function sendEvent(apiKey, scenario, payload) {
  const alertType = payload.severity === 'critical' ? 'error' : 
                    payload.severity === 'error' ? 'error' :
                    payload.severity === 'warning' ? 'warning' : 'info';

  const event = {
    title: `[DEMO] ${payload.summary}`,
    text: `Demo scenario: ${scenario.name}\n\n${scenario.description}\n\nCustom Details:\n${JSON.stringify(payload.custom_details, null, 2)}`,
    alert_type: alertType,
    source_type_name: 'pagerduty-demo',
    tags: [
      `env:${payload.custom_details?.env || 'production'}`,
      `service:${payload.custom_details?.service || payload.custom_details?.pd_service || 'demo'}`,
      `scenario:${scenario.id}`,
      'source:demo-dashboard',
      'demo:true'
    ],
    aggregation_key: `demo-${scenario.id}`
  };

  const response = await fetch(DATADOG_EVENTS_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': apiKey
    },
    body: JSON.stringify(event)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.errors?.[0] || `Datadog event API error: ${response.status}`);
  }

  return response.json();
}

async function sendMetricSpike(apiKey, scenario, payload, metricConfig) {
  const now = Math.floor(Date.now() / 1000);

  const series = {
    series: [{
      metric: metricConfig.metric,
      type: 0,
      points: [{
        timestamp: now,
        value: metricConfig.spikeValue
      }],
      tags: [
        `env:${payload.custom_details?.env || 'production'}`,
        `service:${payload.custom_details?.service || 'demo-service'}`,
        `scenario:${scenario.id}`,
        'source:demo-dashboard',
        'demo:true'
      ]
    }]
  };

  const response = await fetch(DATADOG_METRICS_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': apiKey
    },
    body: JSON.stringify(series)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.errors?.[0] || `Datadog metric API error: ${response.status}`);
  }

  return { status: 'accepted' };
}

export async function sendDatadogMetric(scenario, metricName, value) {
  const { apiKey } = getDatadogCredentials();
  
  if (!apiKey) {
    throw new Error('Datadog API key not configured');
  }

  const payload = scenario.payload?.payload || {};
  const now = Math.floor(Date.now() / 1000);

  const series = {
    series: [{
      metric: metricName || 'demo.api.response_time',
      type: 0,
      points: [{
        timestamp: now,
        value: value || 2500
      }],
      tags: [
        `env:${payload.custom_details?.env || 'production'}`,
        `service:${payload.custom_details?.service || 'demo'}`,
        `scenario:${scenario.id}`,
        'demo:true'
      ]
    }]
  };

  const response = await fetch(DATADOG_METRICS_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': apiKey
    },
    body: JSON.stringify(series)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.errors?.[0] || `Datadog API error: ${response.status}`);
  }

  return {
    status: 'success',
    message: 'Metric sent to Datadog',
    integration: 'datadog'
  };
}
