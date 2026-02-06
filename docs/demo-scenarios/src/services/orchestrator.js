const DEFAULT_ORCHESTRATOR_URL = '';

export function getOrchestratorUrl() {
  return localStorage.getItem('orchestrator_url') || DEFAULT_ORCHESTRATOR_URL;
}

export function saveOrchestratorUrl(url) {
  if (url) localStorage.setItem('orchestrator_url', url);
}

export function clearOrchestratorUrl() {
  localStorage.removeItem('orchestrator_url');
}

export function hasOrchestratorConfigured() {
  return !!getOrchestratorUrl();
}

async function callOrchestrator(path, method = 'GET', body = null) {
  const baseUrl = getOrchestratorUrl();
  if (!baseUrl) {
    throw new Error('Orchestrator URL not configured');
  }

  const url = `${baseUrl.replace(/\/$/, '')}${path}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `Orchestrator error: ${response.status}`);
  }

  return response.json();
}

export async function cleanupDemoIncidents() {
  return callOrchestrator('/cleanup', 'POST');
}

export async function pauseDemo(incidentId = null) {
  const body = incidentId ? { incident_id: incidentId } : {};
  return callOrchestrator('/pause', 'POST', body);
}

export async function resumeDemo(incidentId = null) {
  const body = incidentId ? { incident_id: incidentId } : {};
  return callOrchestrator('/resume', 'POST', body);
}

export async function getDemoStatus(incidentId = null) {
  const path = incidentId ? `/status?incident_id=${incidentId}` : '/status';
  return callOrchestrator(path, 'GET');
}

export async function checkOrchestratorHealth() {
  try {
    const result = await callOrchestrator('/health', 'GET');
    return { healthy: true, ...result };
  } catch (error) {
    return { healthy: false, error: error.message };
  }
}
