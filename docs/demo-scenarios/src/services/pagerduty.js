export function getInstance() {
  return localStorage.getItem('pd_instance') || '';
}

export function saveInstance(instance) {
  localStorage.setItem('pd_instance', instance);
}

export function maskKey(key) {
  if (!key || key.length < 4) return key ? '****' : '';
  return key.substring(0, 4) + '•'.repeat(Math.min(key.length - 4, 20));
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
