export function getGrafanaCredentials() {
  return {
    url: localStorage.getItem('grafana_url') || '',
    apiKey: localStorage.getItem('grafana_api_key') || ''
  };
}

export function saveGrafanaCredentials(url, apiKey) {
  if (url) localStorage.setItem('grafana_url', url);
  if (apiKey) localStorage.setItem('grafana_api_key', apiKey);
}

export function clearGrafanaCredentials() {
  localStorage.removeItem('grafana_url');
  localStorage.removeItem('grafana_api_key');
}

export function hasGrafanaCredentials() {
  const { url, apiKey } = getGrafanaCredentials();
  return !!(url && apiKey);
}

export async function sendGrafanaAnnotation(scenario) {
  const { url, apiKey } = getGrafanaCredentials();
  
  if (!url || !apiKey) {
    throw new Error('Grafana credentials not configured');
  }

  const payload = scenario.payload.payload;
  const now = Date.now();
  
  const annotation = {
    time: now,
    timeEnd: now,
    tags: [
      'demo-alert',
      payload.severity,
      scenario.id,
      payload.custom_details?.service || 'demo'
    ],
    text: `<b>${scenario.name}</b><br/>${payload.summary}<br/><br/>${scenario.description}`
  };

  const apiUrl = url.replace(/\/$/, '') + '/api/annotations';
  
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify(annotation)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Grafana API error: ${response.status}`);
  }

  const data = await response.json();
  return {
    status: 'success',
    message: 'Annotation created in Grafana',
    annotation_id: data.id,
    integration: 'grafana'
  };
}
