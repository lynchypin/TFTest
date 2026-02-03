import { useState, useEffect } from 'react';
import { maskKey } from '../services/pagerduty';
import { getIntegrationStatus, getPagerDutyCredentials, savePagerDutyCredentials, clearPagerDutyCredentials } from '../services/integrations';

const externalTools = [
  { key: 'datadog', name: 'Datadog', icon: '🐕', fields: [
    { name: 'datadog_api_key', label: 'API Key', placeholder: 'Your Datadog API key' }
  ]},
  { key: 'sentry', name: 'Sentry', icon: '🐛', fields: [
    { name: 'sentry_auth_token', label: 'Auth Token', placeholder: 'sntrys_...' },
    { name: 'sentry_org', label: 'Organization', placeholder: 'alan-xl' },
    { name: 'sentry_project', label: 'Project', placeholder: 'demo-app' }
  ]},
  { key: 'github_actions', name: 'GitHub', icon: '⚙️', fields: [
    { name: 'github_token', label: 'Personal Access Token', placeholder: 'ghp_...' },
    { name: 'github_owner', label: 'Owner/Org', placeholder: 'username or org' },
    { name: 'github_repo', label: 'Repository', placeholder: 'repo-name' }
  ]},
  { key: 'newrelic', name: 'New Relic', icon: '🔮', fields: [
    { name: 'newrelic_license_key', label: 'License Key (Ingest)', placeholder: '...FFFFNRAL' },
    { name: 'newrelic_user_api_key', label: 'User API Key', placeholder: 'NRAK-...' },
    { name: 'newrelic_account_id', label: 'Account ID', placeholder: '1234567' }
  ]},
  { key: 'splunk', name: 'Splunk', icon: '🔍', fields: [
    { name: 'splunk_hec_url', label: 'HEC URL', placeholder: 'https://splunk:8088/services/collector' },
    { name: 'splunk_hec_token', label: 'HEC Token', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx' }
  ]},
  { key: 'prometheus', name: 'Alertmanager', icon: '📊', fields: [
    { name: 'alertmanager_url', label: 'Alertmanager URL', placeholder: 'http://alertmanager:9093' }
  ]},
  { key: 'grafana', name: 'Grafana', icon: '📈', fields: [
    { name: 'grafana_url', label: 'Grafana URL', placeholder: 'https://grafana.example.com' },
    { name: 'grafana_api_key', label: 'API Key', placeholder: 'eyJr...' }
  ]},
  { key: 'uptimerobot', name: 'UptimeRobot', icon: '🤖', fields: [
    { name: 'uptimerobot_api_key', label: 'API Key', placeholder: 'u1234567-...' }
  ]},
  { key: 'cloudwatch', name: 'AWS CloudWatch', icon: '☁️', fields: [
    { name: 'aws_access_key', label: 'Access Key ID', placeholder: 'AKIA...' },
    { name: 'aws_secret_key', label: 'Secret Access Key', placeholder: 'Your AWS secret key' },
    { name: 'aws_region', label: 'Region', placeholder: 'us-east-1' }
  ]}
];

export default function SettingsModal({ instance, onSave, onClose }) {
  const [pdInstance, setPdInstance] = useState(instance || '');
  const [fallbackKey, setFallbackKey] = useState('');
  const [showFallbackKey, setShowFallbackKey] = useState(false);
  const [showKeys, setShowKeys] = useState({});
  const [externalCreds, setExternalCreds] = useState({});
  const [activeTab, setActiveTab] = useState('pagerduty');

  useEffect(() => {
    const savedCreds = {};
    externalTools.forEach(tool => {
      tool.fields.forEach(field => { savedCreds[field.name] = ''; });
    });
    setExternalCreds(savedCreds);
  }, []);

  const handleExternalCredChange = (fieldName, value) => {
    setExternalCreds(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleSave = () => {
    if (fallbackKey && fallbackKey.trim()) {
      savePagerDutyCredentials(fallbackKey.trim());
    }
    Object.entries(externalCreds).forEach(([key, value]) => {
      if (value && value.trim()) localStorage.setItem(key, value.trim());
    });
    onSave(pdInstance);
    onClose();
  };

  const handleClearFallbackKey = () => {
    clearPagerDutyCredentials();
    setFallbackKey('');
  };

  const handleClearExternalCred = (fieldName) => {
    localStorage.removeItem(fieldName);
    setExternalCreds(prev => ({ ...prev, [fieldName]: '' }));
  };

  const toggleShowKey = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const { routingKey: storedFallbackKey } = getPagerDutyCredentials();
  const integrationStatus = getIntegrationStatus();

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl shadow-2xl shadow-black/50 border border-gray-800 max-w-3xl w-full max-h-[90vh] flex flex-col animate-scale-in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-800/50 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-gray-100">Settings</h3>
              <p className="text-xs text-gray-500">Configure integrations</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex border-b border-gray-800">
          <button onClick={() => setActiveTab('pagerduty')} className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'pagerduty' ? 'text-emerald-400 border-b-2 border-emerald-400 bg-emerald-900/20' : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/50'}`}>
            PagerDuty
          </button>
          <button onClick={() => setActiveTab('external')} className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'external' ? 'text-violet-400 border-b-2 border-violet-400 bg-violet-900/20' : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/50'}`}>
            External Tools
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 scrollbar-thin">
          {activeTab === 'pagerduty' && (
            <div>
              <div className="mb-6 p-4 bg-indigo-900/30 rounded-xl border border-indigo-700/50">
                <label className="block text-sm font-semibold text-indigo-300 mb-2">PagerDuty Instance</label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-indigo-400 font-medium">https://</span>
                  <input type="text" value={pdInstance} onChange={(e) => setPdInstance(e.target.value)} placeholder="your-company" className="flex-1 input-field" />
                  <span className="text-sm text-indigo-400 font-medium">.pagerduty.com</span>
                </div>
                <p className="text-xs text-indigo-400 mt-2">Your PagerDuty subdomain (e.g., "acme" for acme.pagerduty.com)</p>
              </div>

              <div className="mb-6 p-4 bg-amber-900/30 rounded-xl border border-amber-700/50">
                <label className="block text-sm font-semibold text-amber-300 mb-2">Fallback Routing Key (Optional)</label>
                <p className="text-xs text-amber-400 mb-3">Used only when external tool integration fails. Most scenarios trigger through their native integration flow.</p>
                {storedFallbackKey && !fallbackKey ? (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 px-3 py-2 bg-gray-800/50 rounded-lg border border-gray-700 text-gray-400 font-mono text-sm">{maskKey(storedFallbackKey)}</div>
                    <button type="button" onClick={handleClearFallbackKey} className="px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors">Clear</button>
                  </div>
                ) : (
                  <div className="relative">
                    <input type={showFallbackKey ? 'text' : 'password'} value={fallbackKey} onChange={(e) => setFallbackKey(e.target.value)} placeholder={storedFallbackKey ? 'Enter new key to replace' : 'R0...'} className="w-full input-field pr-10" />
                    <button type="button" onClick={() => setShowFallbackKey(!showFallbackKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">{showFallbackKey ? '🙈' : '👁️'}</button>
                  </div>
                )}
              </div>

              <div className="p-4 bg-emerald-900/20 rounded-xl border border-emerald-700/30">
                <h4 className="text-sm font-semibold text-emerald-300 mb-2">How Scenarios Work</h4>
                <div className="text-xs text-emerald-400 space-y-2">
                  <p><strong>Full Flow (Datadog, Grafana, CloudWatch, New Relic, GitHub Actions, Prometheus):</strong> Sends metrics/events to the tool → Tool's monitors trigger alerts → Alerts flow to PagerDuty through existing integrations.</p>
                  <p><strong>Fallback Flow (Sentry, Splunk, UptimeRobot):</strong> Uses PagerDuty Events API directly when native integration isn't available.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'external' && (
            <div>
              <div className="mb-4 p-4 bg-violet-900/30 rounded-xl border border-violet-700/50">
                <p className="text-sm text-violet-300"><strong>External Tool Credentials:</strong> Configure API keys to send metrics/events to monitoring tools.</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {Object.entries(integrationStatus).filter(([key]) => key !== 'pagerduty_direct').map(([key, { configured, name, fullFlow }]) => (
                    <span key={key} className={`px-2 py-1 rounded text-xs font-medium ${configured ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/50' : 'bg-gray-800/50 text-gray-500 border border-gray-700/50'}`}>
                      {configured ? '✓' : '○'} {name} {fullFlow && <span className="opacity-60">(full flow)</span>}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                {externalTools.map(tool => (
                  <div key={tool.key} className="p-4 bg-gray-800/50 rounded-xl border border-gray-700/50">
                    <h5 className="flex items-center gap-2 text-sm font-semibold text-gray-200 mb-3">
                      <span>{tool.icon}</span>{tool.name}
                      {integrationStatus[tool.key]?.configured && <span className="ml-auto text-xs text-emerald-500 font-normal">✓ Configured</span>}
                    </h5>
                    <div className="space-y-3">
                      {tool.fields.map(field => {
                        const storedValue = localStorage.getItem(field.name);
                        const hasStored = !!storedValue;
                        return (
                          <div key={field.name}>
                            <label className="block text-xs text-gray-400 mb-1">{field.label}</label>
                            {hasStored && !externalCreds[field.name] ? (
                              <div className="flex items-center gap-2">
                                <div className="flex-1 px-3 py-2 bg-gray-900/50 rounded-lg border border-gray-700 text-gray-400 font-mono text-xs truncate">{maskKey(storedValue)}</div>
                                <button type="button" onClick={() => handleClearExternalCred(field.name)} className="px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition-colors">Clear</button>
                              </div>
                            ) : (
                              <div className="relative">
                                <input type={showKeys[field.name] ? 'text' : 'password'} value={externalCreds[field.name] || ''} onChange={(e) => handleExternalCredChange(field.name, e.target.value)} placeholder={field.placeholder} className="w-full input-field text-sm pr-10" />
                                <button type="button" onClick={() => toggleShowKey(field.name)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 text-sm">{showKeys[field.name] ? '🙈' : '👁️'}</button>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 p-4 bg-gray-800/30 rounded-xl border border-gray-700/50">
            <div className="flex items-start gap-2">
              <span className="text-gray-400">🔒</span>
              <div>
                <p className="text-sm font-medium text-gray-300">Security Note</p>
                <p className="text-xs text-gray-400 mt-1">All credentials are stored in your browser's localStorage and never leave your device.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 p-6 flex gap-3 bg-gray-800/50 rounded-b-2xl">
          <button onClick={onClose} className="flex-1 btn-secondary">Cancel</button>
          <button onClick={handleSave} className="flex-1 btn-primary">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
