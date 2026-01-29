const PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue';

export function getInstance() {
  return localStorage.getItem('pd_instance') || '';
}

export function saveInstance(instance) {
  localStorage.setItem('pd_instance', instance);
}

export function getRoutingKeys() {
  const stored = localStorage.getItem('pd_routing_keys');
  return stored ? JSON.parse(stored) : {};
}

export function saveRoutingKeys(keys) {
  localStorage.setItem('pd_routing_keys', JSON.stringify(keys));
}

export function getRoutingKey(integration) {
  const keys = getRoutingKeys();
  return keys[integration] || '';
}

export function maskKey(key) {
  if (!key || key.length < 4) return key ? '****' : '';
  return key.substring(0, 4) + '•'.repeat(Math.min(key.length - 4, 20));
}

export async function sendEvent(scenario, routingKey) {
  const payload = getFullPayload(scenario, routingKey);

  const response = await fetch(PAGERDUTY_EVENTS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }

  return {
    status: 'success',
    message: data.message || 'Event accepted',
    dedup_key: data.dedup_key
  };
}

export function getFullPayload(scenario, routingKey) {
  return {
    routing_key: routingKey,
    event_action: 'trigger',
    dedup_key: `demo-${scenario.id}-${Date.now()}`,
    payload: {
      summary: scenario.payload.payload.summary,
      source: scenario.payload.payload.source,
      severity: scenario.payload.payload.severity,
      custom_details: scenario.payload.payload.custom_details
    },
    links: scenario.payload.links || [],
    images: scenario.payload.images || []
  };
}
