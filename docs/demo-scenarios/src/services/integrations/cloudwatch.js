export function getCloudWatchCredentials() {
  return {
    accessKeyId: localStorage.getItem('aws_access_key_id') || '',
    secretAccessKey: localStorage.getItem('aws_secret_access_key') || '',
    region: localStorage.getItem('aws_region') || 'us-east-1'
  };
}

export function saveCloudWatchCredentials(accessKeyId, secretAccessKey, region) {
  if (accessKeyId) localStorage.setItem('aws_access_key_id', accessKeyId);
  if (secretAccessKey) localStorage.setItem('aws_secret_access_key', secretAccessKey);
  if (region) localStorage.setItem('aws_region', region);
}

export function clearCloudWatchCredentials() {
  localStorage.removeItem('aws_access_key_id');
  localStorage.removeItem('aws_secret_access_key');
  localStorage.removeItem('aws_region');
}

export function hasCloudWatchCredentials() {
  const { accessKeyId, secretAccessKey } = getCloudWatchCredentials();
  return !!(accessKeyId && secretAccessKey);
}

export async function sendCloudWatchMetric(scenario) {
  const { accessKeyId, secretAccessKey, region } = getCloudWatchCredentials();
  
  if (!accessKeyId || !secretAccessKey) {
    throw new Error('AWS credentials not configured. CloudWatch requires AWS SDK - use Events API fallback.');
  }

  return {
    status: 'fallback',
    message: 'CloudWatch requires AWS SDK. Using Events API instead.',
    integration: 'cloudwatch',
    requiresFallback: true
  };
}
