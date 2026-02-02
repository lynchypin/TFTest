const STORAGE_KEYS = {
  authToken: 'sentry_auth_token',
  org: 'sentry_org',
  project: 'sentry_project'
};

export function getSentryCredentials() {
  return {
    authToken: localStorage.getItem(STORAGE_KEYS.authToken) || '',
    org: localStorage.getItem(STORAGE_KEYS.org) || '',
    project: localStorage.getItem(STORAGE_KEYS.project) || ''
  };
}

export function saveSentryCredentials({ authToken, org, project }) {
  if (authToken) localStorage.setItem(STORAGE_KEYS.authToken, authToken);
  if (org) localStorage.setItem(STORAGE_KEYS.org, org);
  if (project) localStorage.setItem(STORAGE_KEYS.project, project);
}

export function clearSentryCredentials() {
  Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
}

export function hasSentryCredentials() {
  const creds = getSentryCredentials();
  return !!(creds.authToken && creds.org && creds.project);
}

export async function sendSentryIssue(scenario) {
  const { authToken, org, project } = getSentryCredentials();
  
  if (!authToken || !org || !project) {
    return { requiresFallback: true, reason: 'Sentry credentials not configured' };
  }

  const issueData = {
    title: `[${scenario.severity}] ${scenario.name}`,
    culprit: scenario.target_service,
    message: scenario.description,
    level: scenario.severity === 'critical' ? 'fatal' : scenario.severity === 'error' ? 'error' : 'warning',
    tags: {
      scenario_id: scenario.id,
      service: scenario.target_service,
      integration: scenario.tags?.integration || 'sentry',
      industry: scenario.tags?.industry?.join(',') || '',
      team_type: scenario.tags?.team_type?.join(',') || ''
    },
    extra: {
      payload: scenario.payload,
      expected_priority: scenario.expected_priority,
      features_demonstrated: scenario.features_demonstrated || scenario.required_features
    }
  };

  try {
    const response = await fetch(
      `https://us.sentry.io/api/0/projects/${org}/${project}/issues/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(issueData)
      }
    );

    if (response.status === 403 || response.status === 401) {
      const storeResponse = await sendSentryStoreEvent(scenario, authToken, org, project);
      return storeResponse;
    }

    if (!response.ok) {
      const storeResponse = await sendSentryStoreEvent(scenario, authToken, org, project);
      return storeResponse;
    }

    const result = await response.json();
    return { 
      success: true, 
      message: `Issue created: ${result.id || 'pending'}`,
      issueId: result.id 
    };
  } catch (error) {
    const storeResponse = await sendSentryStoreEvent(scenario, authToken, org, project);
    return storeResponse;
  }
}

async function sendSentryStoreEvent(scenario, authToken, org, project) {
  const eventPayload = {
    event_id: crypto.randomUUID().replace(/-/g, ''),
    timestamp: new Date().toISOString(),
    platform: 'javascript',
    level: scenario.severity === 'critical' ? 'fatal' : scenario.severity === 'error' ? 'error' : 'warning',
    logger: 'pagerduty-demo',
    transaction: scenario.target_service,
    server_name: 'demo-dashboard',
    release: '1.0.0',
    environment: 'demo',
    message: {
      formatted: `[${scenario.id}] ${scenario.name}: ${scenario.description}`
    },
    tags: {
      scenario_id: scenario.id,
      service: scenario.target_service,
      severity: scenario.severity
    },
    extra: {
      scenario: scenario
    }
  };

  try {
    const response = await fetch(
      `https://us.sentry.io/api/0/projects/${org}/${project}/store/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-Sentry-Auth': `Sentry sentry_version=7, sentry_client=demo/1.0, sentry_key=${authToken}`
        },
        body: JSON.stringify(eventPayload)
      }
    );

    if (!response.ok) {
      return { requiresFallback: true, reason: `Sentry API error: ${response.status}` };
    }

    return { 
      success: true, 
      message: `Event sent: ${eventPayload.event_id.substring(0, 8)}...`
    };
  } catch (error) {
    return { requiresFallback: true, reason: error.message };
  }
}

export { sendSentryIssue as sendSentryError };
