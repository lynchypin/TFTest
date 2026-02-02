export function getSplunkCredentials() {
  return {
    hecUrl: localStorage.getItem('splunk_hec_url') || '',
    hecToken: localStorage.getItem('splunk_hec_token') || ''
  };
}

export function saveSplunkCredentials(hecUrl, hecToken) {
  if (hecUrl) localStorage.setItem('splunk_hec_url', hecUrl);
  if (hecToken) localStorage.setItem('splunk_hec_token', hecToken);
}

export function clearSplunkCredentials() {
  localStorage.removeItem('splunk_hec_url');
  localStorage.removeItem('splunk_hec_token');
}

export function hasSplunkCredentials() {
  const { hecUrl, hecToken } = getSplunkCredentials();
  return !!(hecUrl && hecToken);
}

export async function sendSplunkEvent(scenario) {
  const { hecUrl, hecToken } = getSplunkCredentials();
  
  if (!hecUrl || !hecToken) {
    throw new Error('Splunk HEC credentials not configured');
  }

  const payload = scenario.payload.payload;
  
  const event = {
    event: {
      scenario_id: scenario.id,
      scenario_name: scenario.name,
      summary: payload.summary,
      severity: payload.severity,
      source: payload.source,
      ...payload.custom_details
    },
    sourcetype: 'pagerduty:demo',
    source: 'demo-dashboard',
    index: 'main',
    time: Math.floor(Date.now() / 1000)
  };

  const response = await fetch(hecUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Splunk ${hecToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(event)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.text || `Splunk HEC error: ${response.status}`);
  }

  return {
    status: 'success',
    message: 'Event sent to Splunk',
    integration: 'splunk'
  };
}
