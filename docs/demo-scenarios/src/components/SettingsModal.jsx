import { useState, useEffect } from 'react';
import { maskKey } from '../services/pagerduty';

const integrations = [
  { key: 'prometheus', name: 'Prometheus', icon: '📊' },
  { key: 'grafana', name: 'Grafana', icon: '📈' },
  { key: 'datadog', name: 'Datadog', icon: '🐕' },
  { key: 'newrelic', name: 'New Relic', icon: '🔮' },
  { key: 'sentry', name: 'Sentry', icon: '🐛' },
  { key: 'splunk', name: 'Splunk', icon: '🔍' },
  { key: 'cloudwatch', name: 'CloudWatch', icon: '☁️' },
  { key: 'uptimerobot', name: 'UptimeRobot', icon: '🤖' },
  { key: 'github_actions', name: 'GitHub Actions', icon: '⚙️' }
];

export default function SettingsModal({ routingKeys, instance, onSave, onClose }) {
  const [keys, setKeys] = useState({});
  const [pdInstance, setPdInstance] = useState(instance || '');
  const [pdApiKey, setPdApiKey] = useState('');
  const [showKeys, setShowKeys] = useState({});
  const [editingKey, setEditingKey] = useState(null);

  useEffect(() => {
    const emptyKeys = {};
    integrations.forEach(({ key }) => {
      emptyKeys[key] = '';
    });
    setKeys(emptyKeys);
    setPdApiKey('');
  }, []);

  const handleChange = (integration, value) => {
    setKeys(prev => ({ ...prev, [integration]: value }));
  };

  const handleSave = () => {
    const updatedKeys = { ...routingKeys };
    Object.entries(keys).forEach(([key, value]) => {
      if (value && value.trim()) {
        updatedKeys[key] = value.trim();
      }
    });

    if (pdApiKey && pdApiKey.trim()) {
      localStorage.setItem('pd_api_key', pdApiKey.trim());
    }

    onSave(updatedKeys, pdInstance);
    onClose();
  };

  const handleClearKey = (key) => {
    const updatedKeys = { ...routingKeys };
    delete updatedKeys[key];
    onSave(updatedKeys, pdInstance);
    setKeys(prev => ({ ...prev, [key]: '' }));
  };

  const handleClearApiKey = () => {
    localStorage.removeItem('pd_api_key');
    setPdApiKey('');
  };

  const toggleShowKey = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const hasStoredApiKey = !!localStorage.getItem('pd_api_key');

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl shadow-2xl shadow-black/50 border border-gray-800 max-w-2xl w-full max-h-[90vh] flex flex-col animate-scale-in" onClick={e => e.stopPropagation()}>
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
              <p className="text-xs text-gray-500">Configure integrations & API keys</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 scrollbar-thin">
          <div className="mb-6 p-4 bg-indigo-900/30 rounded-xl border border-indigo-700/50">
            <label className="block text-sm font-semibold text-indigo-300 mb-2">
              PagerDuty Instance
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-indigo-400 font-medium">https://</span>
              <input
                type="text"
                value={pdInstance}
                onChange={(e) => setPdInstance(e.target.value)}
                placeholder="your-company"
                className="flex-1 input-field"
              />
              <span className="text-sm text-indigo-400 font-medium">.pagerduty.com</span>
            </div>
            <p className="text-xs text-indigo-400 mt-2">
              Your PagerDuty subdomain (e.g., "acme" for acme.pagerduty.com)
            </p>
          </div>

          <div className="mb-6 p-4 bg-emerald-900/30 rounded-xl border border-emerald-700/50">
            <label className="block text-sm font-semibold text-emerald-300 mb-2">
              PagerDuty API Key
            </label>
            {hasStoredApiKey && !pdApiKey ? (
              <div className="flex items-center gap-2">
                <div className="flex-1 px-3 py-2 bg-gray-800/50 rounded-lg border border-gray-700 text-gray-400 font-mono text-sm">
                  {maskKey(localStorage.getItem('pd_api_key'))}
                </div>
                <button
                  type="button"
                  onClick={handleClearApiKey}
                  className="px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors"
                  title="Remove saved key"
                >
                  Clear
                </button>
              </div>
            ) : (
              <div className="relative">
                <input
                  type={showKeys.apiKey ? 'text' : 'password'}
                  value={pdApiKey}
                  onChange={(e) => setPdApiKey(e.target.value)}
                  placeholder={hasStoredApiKey ? 'Enter new key to replace' : 'Enter your PagerDuty API key'}
                  className="w-full input-field pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleShowKey('apiKey')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showKeys.apiKey ? '🙈' : '👁️'}
                </button>
              </div>
            )}
            <p className="text-xs text-emerald-400 mt-2">
              🔒 Stored securely in localStorage (never sent to external servers)
            </p>
          </div>

          <div className="mb-4">
            <h4 className="font-semibold text-gray-100 mb-2">Integration Routing Keys</h4>
            <p className="text-sm text-gray-400 mb-4">
              Configure routing keys from your PagerDuty Event Orchestration integrations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {integrations.map(({ key, name, icon }) => {
              const hasStoredKey = !!routingKeys[key];
              const isEditing = editingKey === key || !hasStoredKey;
              
              return (
                <div key={key} className="p-3 bg-gray-800/50 rounded-xl border border-gray-700/50">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                    <span>{icon}</span>
                    {name}
                    {hasStoredKey && (
                      <span className="ml-auto text-xs text-emerald-500">✓ Saved</span>
                    )}
                  </label>
                  {hasStoredKey && !isEditing ? (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 px-3 py-2 bg-gray-900/50 rounded-lg border border-gray-700 text-gray-400 font-mono text-xs truncate">
                        {maskKey(routingKeys[key])}
                      </div>
                      <button
                        type="button"
                        onClick={() => setEditingKey(key)}
                        className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Edit key"
                      >
                        ✏️
                      </button>
                      <button
                        type="button"
                        onClick={() => handleClearKey(key)}
                        className="p-2 text-red-500 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors"
                        title="Remove key"
                      >
                        🗑️
                      </button>
                    </div>
                  ) : (
                    <div className="relative">
                      <input
                        type={showKeys[key] ? 'text' : 'password'}
                        value={keys[key] || ''}
                        onChange={(e) => handleChange(key, e.target.value)}
                        placeholder={hasStoredKey ? 'Enter new key to replace' : 'R0...'}
                        className="w-full input-field text-sm pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => toggleShowKey(key)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 text-sm"
                      >
                        {showKeys[key] ? '🙈' : '👁️'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-amber-900/30 rounded-xl border border-amber-700/50">
            <div className="flex items-start gap-2">
              <span className="text-amber-400">🔒</span>
              <div>
                <p className="text-sm font-medium text-amber-300">Security Note</p>
                <p className="text-xs text-amber-400 mt-1">
                  All keys are stored in your browser's localStorage and never leave your device.
                  Keys are masked by default - only the first 4 characters are shown.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 p-6 flex gap-3 bg-gray-800/50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="flex-1 btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 btn-primary"
          >
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
