const PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue';

export function getPagerDutyCredentials() {
  return {
    routingKey: localStorage.getItem('pagerduty_routing_key') || ''
  };
}

export function savePagerDutyCredentials(routingKey) {
  if (routingKey) localStorage.setItem('pagerduty_routing_key', routingKey);
}

export function clearPagerDutyCredentials() {
  localStorage.removeItem('pagerduty_routing_key');
}

export function hasPagerDutyCredentials() {
  const { routingKey } = getPagerDutyCredentials();
  return !!routingKey;
}

export async function triggerPagerDutyDirect(scenario) {
  const { routingKey } = getPagerDutyCredentials();
  
  if (!routingKey) {
    throw new Error('PagerDuty routing key not configured');
  }

  const payload = scenario.payload?.payload || {};
  const dedupKey = `demo-${scenario.id}-${Date.now()}`;

  const event = {
    routing_key: routingKey,
    event_action: 'trigger',
    dedup_key: dedupKey,
    payload: {
      summary: `[DEMO] ${payload.summary || scenario.name}`,
      severity: payload.severity || 'warning',
      source: payload.source || scenario.tags?.integration || 'demo-scenarios',
      custom_details: {
        scenario_id: scenario.id,
        scenario_name: scenario.name,
        description: scenario.description,
        triggered_by: 'scenarios-dashboard',
        original_integration: scenario.tags?.integration,
        pd_service: payload.custom_details?.pd_service,
        env: payload.custom_details?.env || 'production',
        ...(payload.custom_details || {})
      }
    }
  };

  const response = await fetch(PAGERDUTY_EVENTS_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(event)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `PagerDuty API error: ${response.status}`);
  }

  const data = await response.json();
  return {
    status: 'success',
    message: 'Incident triggered directly in PagerDuty',
    dedup_key: data.dedup_key,
    integration: 'pagerduty_direct'
  };
}
