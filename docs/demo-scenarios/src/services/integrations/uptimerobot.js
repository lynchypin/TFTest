export function getUptimeRobotCredentials() {
  return {
    apiKey: localStorage.getItem('uptimerobot_api_key') || ''
  };
}

export function saveUptimeRobotCredentials(apiKey) {
  if (apiKey) localStorage.setItem('uptimerobot_api_key', apiKey);
}

export function clearUptimeRobotCredentials() {
  localStorage.removeItem('uptimerobot_api_key');
}

export function hasUptimeRobotCredentials() {
  const { apiKey } = getUptimeRobotCredentials();
  return !!apiKey;
}

export async function triggerUptimeRobotAlert(scenario) {
  const { apiKey } = getUptimeRobotCredentials();
  
  if (!apiKey) {
    throw new Error('UptimeRobot API key not configured');
  }

  return {
    status: 'fallback',
    message: 'UptimeRobot alerts are triggered by actual monitor failures. Using Events API instead.',
    integration: 'uptimerobot',
    requiresFallback: true
  };
}
