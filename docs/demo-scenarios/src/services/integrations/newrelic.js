const STORAGE_KEYS = {
  licenseKey: 'newrelic_license_key',
  userApiKey: 'newrelic_user_api_key',
  accountId: 'newrelic_account_id'
};

export function getNewRelicCredentials() {
  return {
    licenseKey: localStorage.getItem(STORAGE_KEYS.licenseKey) || '',
    userApiKey: localStorage.getItem(STORAGE_KEYS.userApiKey) || '',
    accountId: localStorage.getItem(STORAGE_KEYS.accountId) || ''
  };
}

export function saveNewRelicCredentials({ licenseKey, userApiKey, accountId }) {
  if (licenseKey) localStorage.setItem(STORAGE_KEYS.licenseKey, licenseKey);
  if (userApiKey) localStorage.setItem(STORAGE_KEYS.userApiKey, userApiKey);
  if (accountId) localStorage.setItem(STORAGE_KEYS.accountId, accountId);
}

export function clearNewRelicCredentials() {
  Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
}

export function hasNewRelicCredentials() {
  const creds = getNewRelicCredentials();
  return !!(creds.licenseKey && creds.accountId);
}

export async function sendNewRelicEvent(scenario) {
  const { licenseKey, accountId } = getNewRelicCredentials();
  
  if (!licenseKey || !accountId) {
    return { requiresFallback: true, reason: 'New Relic credentials not configured' };
  }

  const eventData = [{
    eventType: 'PagerDutyDemoScenario',
    scenarioId: scenario.id,
    scenarioName: scenario.name,
    description: scenario.description,
    severity: scenario.severity,
    targetService: scenario.target_service,
    expectedPriority: scenario.expected_priority,
    integration: scenario.tags?.integration || 'newrelic',
    industry: scenario.tags?.industry?.join(',') || '',
    teamType: scenario.tags?.team_type?.join(',') || '',
    timestamp: Date.now()
  }];

  try {
    const response = await fetch(
      `https://insights-collector.newrelic.com/v1/accounts/${accountId}/events`,
      {
        method: 'POST',
        headers: {
          'Api-Key': licenseKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(eventData)
      }
    );

    if (!response.ok) {
      const text = await response.text();
      return { requiresFallback: true, reason: `New Relic API error: ${response.status} - ${text}` };
    }

    return { 
      success: true, 
      message: `Event sent to account ${accountId}`
    };
  } catch (error) {
    if (error.message.includes('Failed to fetch') || error.message.includes('CORS') || error.message.includes('NetworkError')) {
      return { requiresFallback: true, reason: 'New Relic API blocked by CORS - using PagerDuty fallback' };
    }
    return { requiresFallback: true, reason: error.message };
  }
}