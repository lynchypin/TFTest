import { useState, useEffect } from 'react';
import { getFullPayload, maskKey } from '../services/pagerduty';
import { getPagerDutyCredentials } from '../services/integrations';
import { FEATURES, getScenarioLicenseInfo, getPlanDisplay, ADDONS } from '../services/license';

const FEATURE_TIER_COLORS = {
  tier1: { bg: 'bg-cyan-900/50', text: 'text-cyan-300' },
  tier2: { bg: 'bg-cyan-900/30', text: 'text-cyan-400' },
  tier3: { bg: 'bg-cyan-900/20', text: 'text-cyan-500' }
};

const FULL_FLOW_INTEGRATIONS = ['datadog', 'grafana', 'cloudwatch', 'newrelic', 'github_actions', 'prometheus'];

function getIntegrationPayload(scenario) {
  const integration = scenario.integration || 'pagerduty';
  const isFullFlow = FULL_FLOW_INTEGRATIONS.includes(integration);
  const payload = scenario.payload?.payload || {};

  if (!isFullFlow) {
    return null;
  }

  switch (integration) {
    case 'datadog':
      return {
        _info: `This payload is sent to Datadog API. Datadog monitors then trigger PagerDuty via native integration.`,
        _endpoint: 'https://api.us5.datadoghq.com/api/v1/events',
        event: {
          title: `[DEMO] ${payload.summary}`,
          text: `Demo scenario: ${scenario.name}\n\n${scenario.description}`,
          alert_type: payload.severity === 'critical' ? 'error' : payload.severity === 'warning' ? 'warning' : 'info',
          source_type_name: 'pagerduty-demo',
          tags: [
            `env:${payload.custom_details?.env || 'production'}`,
            `service:${payload.custom_details?.service || 'demo'}`,
            `scenario:${scenario.id}`
          ]
        },
        metric_spike: {
          metric: 'demo.api.response_time',
          value: 2500,
          threshold: 500
        }
      };
    case 'newrelic':
      return {
        _info: `This payload is sent to New Relic Events API. New Relic alerts then trigger PagerDuty.`,
        _endpoint: 'https://insights-collector.newrelic.com/v1/accounts/{account_id}/events',
        event: {
          eventType: 'DemoIncident',
          summary: payload.summary,
          severity: payload.severity,
          scenario_id: scenario.id,
          ...payload.custom_details
        }
      };
    case 'grafana':
      return {
        _info: `This payload creates a Grafana annotation. Grafana alerts then trigger PagerDuty.`,
        _endpoint: 'https://{instance}.grafana.net/api/annotations',
        annotation: {
          text: `[DEMO] ${payload.summary}`,
          tags: ['demo', 'pagerduty', scenario.id]
        }
      };
    case 'cloudwatch':
      return {
        _info: `This payload is sent to AWS CloudWatch. CloudWatch alarms then trigger PagerDuty via SNS.`,
        _endpoint: 'cloudwatch:PutMetricData',
        metric_data: {
          Namespace: 'PagerDutyDemo',
          MetricName: 'DemoAlert',
          Value: 100,
          Unit: 'Count',
          Dimensions: [{ Name: 'Scenario', Value: scenario.id }]
        }
      };
    default:
      return null;
  }
}

export default function PayloadModal({ scenario, onClose, onSend }) {
  const [copied, setCopied] = useState(false);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedPayload, setEditedPayload] = useState('');
  const [parseError, setParseError] = useState(null);
  const [payloadType, setPayloadType] = useState('integration');

  const { routingKey } = getPagerDutyCredentials();
  const integration = scenario.integration || 'pagerduty';
  const isFullFlow = FULL_FLOW_INTEGRATIONS.includes(integration);
  const integrationPayload = getIntegrationPayload(scenario);
  const pagerdutyPayload = getFullPayload(scenario, routingKey || 'YOUR_ROUTING_KEY');

  const originalPayload = (payloadType === 'integration' && integrationPayload) ? integrationPayload : pagerdutyPayload;
  const originalJsonString = JSON.stringify(originalPayload, null, 2);

  const licenseInfo = getScenarioLicenseInfo(scenario);
  const planDisplay = getPlanDisplay(licenseInfo.minimumPlan);
  const requiredAddons = licenseInfo.requiredAddons || [];
  const featuresDemo = scenario.features_demonstrated || scenario.required_features || [];

  useEffect(() => {
    setEditedPayload(originalJsonString);
  }, [originalJsonString, payloadType]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(isEditing ? editedPayload : originalJsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePayloadChange = (value) => {
    setEditedPayload(value);
    setParseError(null);
    try {
      JSON.parse(value);
    } catch (e) {
      setParseError(e.message);
    }
  };

  const handleReset = () => {
    setEditedPayload(originalJsonString);
    setParseError(null);
    setIsEditing(false);
  };

  const handleSend = async () => {
    if (!routingKey) {
      setResult({ success: false, message: 'No fallback routing key configured. Add one in Settings → PagerDuty tab.' });
      return;
    }

    let payloadToSend;
    if (isEditing && editedPayload !== originalJsonString) {
      try {
        payloadToSend = JSON.parse(editedPayload);
      } catch (e) {
        setResult({ success: false, message: 'Invalid JSON: ' + e.message });
        return;
      }
    } else {
      payloadToSend = originalPayload;
    }

    setSending(true);
    setResult(null);
    try {
      const response = await fetch('https://events.pagerduty.com/v2/enqueue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadToSend)
      });
      const data = await response.json();
      if (response.ok) {
        setResult({ success: true, message: 'Event sent to PagerDuty!', dedup_key: data.dedup_key });
        handleReset();
      } else {
        setResult({ success: false, message: data.message || 'Failed to send event' });
      }
    } catch (error) {
      setResult({ success: false, message: error.message });
    } finally {
      setSending(false);
    }
  };

  const getFeatureTier = (index) => {
    if (index < 2) return FEATURE_TIER_COLORS.tier1;
    if (index < 4) return FEATURE_TIER_COLORS.tier2;
    return FEATURE_TIER_COLORS.tier3;
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl shadow-2xl shadow-black/50 border border-gray-800 max-w-3xl w-full max-h-[90vh] flex flex-col animate-scale-in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-800/50 rounded-t-2xl">
          <div>
            <h3 className="font-bold text-gray-100 text-lg">{scenario.name}</h3>
            <p className="text-sm text-gray-500">{scenario.id}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="btn-ghost text-sm"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {isFullFlow && integrationPayload && (
            <div className="mb-4 flex items-center gap-2">
              <span className="text-xs text-gray-500">View:</span>
              <button
                onClick={() => setPayloadType('integration')}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${payloadType === 'integration' ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700'}`}
              >
                {integration.charAt(0).toUpperCase() + integration.slice(1)} Payload
              </button>
              <button
                onClick={() => setPayloadType('pagerduty')}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${payloadType === 'pagerduty' ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700'}`}
              >
                PagerDuty Fallback
              </button>
            </div>
          )}

          {payloadType === 'integration' && integrationPayload?._info && (
            <div className="mb-3 p-3 bg-blue-900/30 border border-blue-700/50 rounded-lg text-xs text-blue-300">
              ℹ️ {integrationPayload._info}
            </div>
          )}

          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-gray-300">
              {isEditing ? 'Edit Payload' : 'Payload Preview'}
            </span>
            <div className="flex gap-2">
              {isEditing && editedPayload !== originalJsonString && (
                <button onClick={handleReset} className="text-xs text-red-400 hover:text-red-300 font-medium">
                  Reset to Default
                </button>
              )}
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`text-xs font-medium px-2 py-1 rounded ${isEditing ? 'bg-amber-900/50 text-amber-300 border border-amber-700/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700'}`}
              >
                {isEditing ? 'Editing' : 'Enable Edit'}
              </button>
            </div>
          </div>

          {parseError && (
            <div className="mb-2 p-2 bg-red-900/50 border border-red-700/50 rounded-lg text-xs text-red-300">
              JSON Error: {parseError}
            </div>
          )}

          {isEditing ? (
            <textarea
              value={editedPayload}
              onChange={(e) => handlePayloadChange(e.target.value)}
              className="w-full h-64 bg-gray-950 text-emerald-400 p-4 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none border border-gray-700"
              spellCheck={false}
            />
          ) : (
            <pre className="bg-gray-950 text-emerald-400 p-4 rounded-xl text-sm overflow-x-auto max-h-64 scrollbar-thin border border-gray-700">
              {originalJsonString}
            </pre>
          )}

          <p className="text-xs text-gray-500 mt-2">
            {isEditing ? 'Changes are temporary and will reset after sending or closing.' : 'Click "Enable Edit" to modify the payload for this trigger.'}
          </p>
        </div>

        <div className="border-t border-gray-800 p-6 bg-gray-800/50 rounded-b-2xl">
          <div className="bg-gray-800/50 rounded-xl p-4 mb-4 border border-gray-700/50">
            <h4 className="font-semibold text-gray-100 mb-3">Expected Behavior</h4>
            
            <div className="grid grid-cols-2 gap-3 text-sm mb-3">
              <div>
                <span className="text-gray-500">Routes to:</span>
                <span className="ml-2 font-medium text-gray-200">{scenario.target_service}</span>
              </div>
              {scenario.expected_priority && (
                <div>
                  <span className="text-gray-500">Priority:</span>
                  <span className={`ml-2 font-bold px-2 py-0.5 rounded ${
                    scenario.expected_priority === 'P1' ? 'bg-red-900/50 text-red-300 border border-red-700/50' :
                    scenario.expected_priority === 'P2' ? 'bg-orange-900/50 text-orange-300 border border-orange-700/50' :
                    'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50'
                  }`}>{scenario.expected_priority}</span>
                </div>
              )}
            </div>

            <div className="mb-3">
              <span className="text-sm text-gray-500">Plan Required:</span>
              <span className="ml-2 px-2.5 py-1 text-xs font-semibold rounded-lg bg-indigo-900/50 text-indigo-300 border border-indigo-700/50">
                {planDisplay.label}
              </span>
              {requiredAddons.length > 0 && requiredAddons.map(key => {
                const addon = ADDONS.find(a => a.key === key);
                return (
                  <span key={key} className="ml-2 px-2.5 py-1 text-xs font-semibold rounded-lg bg-purple-900/50 text-purple-300 border border-purple-700/50">
                    {addon?.label || key}
                  </span>
                );
              })}
            </div>

            {featuresDemo.length > 0 && (
              <div>
                <span className="text-sm text-gray-500 block mb-2">Features Demonstrated:</span>
                <div className="flex flex-wrap gap-1.5">
                  {featuresDemo.map((featureKey, index) => {
                    const feature = FEATURES[featureKey];
                    const tierColor = getFeatureTier(index);
                    return (
                      <span 
                        key={featureKey}
                        className={`px-2 py-0.5 text-xs font-medium rounded-md border border-cyan-700/30 ${tierColor.bg} ${tierColor.text}`}
                      >
                        {feature?.name || featureKey}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {scenario.rules_triggered?.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700/50">
                <span className="text-sm text-gray-500">Rules Triggered:</span>
                <div className="mt-1 space-y-1">
                  {scenario.rules_triggered.map((rule, i) => (
                    <div key={i} className="text-sm text-gray-300">• {rule}</div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {result && (
            <div className={`mb-4 p-4 rounded-xl ${result.success ? 'bg-emerald-900/50 border border-emerald-700/50 text-emerald-300' : 'bg-red-900/50 border border-red-700/50 text-red-300'}`}>
              <p className="font-medium">{result.success ? '✅' : '❌'} {result.message}</p>
              {result.dedup_key && (
                <p className="text-xs mt-1 opacity-75">Dedup Key: {result.dedup_key}</p>
              )}
            </div>
          )}

          <button
            onClick={handleSend}
            disabled={sending || parseError}
            className={`w-full py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
              sending || parseError
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'btn-success'
            }`}
          >
            {sending ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sending...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Send to PagerDuty
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
