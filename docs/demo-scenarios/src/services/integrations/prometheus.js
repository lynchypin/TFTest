export function getPrometheusCredentials() {
  return {
    alertmanagerUrl: localStorage.getItem('alertmanager_url') || '',
    username: localStorage.getItem('alertmanager_username') || '',
    password: localStorage.getItem('alertmanager_password') || ''
  };
}

export function savePrometheusCredentials(alertmanagerUrl, username, password) {
  if (alertmanagerUrl) localStorage.setItem('alertmanager_url', alertmanagerUrl);
  if (username) localStorage.setItem('alertmanager_username', username);
  if (password) localStorage.setItem('alertmanager_password', password);
}

export function clearPrometheusCredentials() {
  localStorage.removeItem('alertmanager_url');
  localStorage.removeItem('alertmanager_username');
  localStorage.removeItem('alertmanager_password');
}

export function hasPrometheusCredentials() {
  const { alertmanagerUrl } = getPrometheusCredentials();
  return !!alertmanagerUrl;
}

export async function sendAlertmanagerAlert(scenario) {
  const { alertmanagerUrl, username, password } = getPrometheusCredentials();
  
  if (!alertmanagerUrl) {
    throw new Error('Alertmanager URL not configured');
  }

  const payload = scenario.payload.payload;
  const now = new Date().toISOString();
  
  const alerts = [{
    labels: {
      alertname: scenario.name.replace(/\s+/g, '_'),
      severity: payload.severity,
      service: payload.custom_details?.service || payload.custom_details?.pd_service || 'demo',
      env: payload.custom_details?.env || 'production',
      scenario_id: scenario.id,
      source: 'demo-dashboard'
    },
    annotations: {
      summary: payload.summary,
      description: scenario.description,
      scenario: scenario.name
    },
    startsAt: now,
    generatorURL: `http://demo-dashboard/scenarios/${scenario.id}`
  }];

  const headers = {
    'Content-Type': 'application/json'
  };

  if (username && password) {
    headers['Authorization'] = 'Basic ' + btoa(`${username}:${password}`);
  }

  const url = alertmanagerUrl.replace(/\/$/, '') + '/api/v2/alerts';
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(alerts)
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Alertmanager error: ${response.status} - ${error}`);
  }

  return {
    status: 'success',
    message: 'Alert sent to Alertmanager',
    integration: 'prometheus'
  };
}
