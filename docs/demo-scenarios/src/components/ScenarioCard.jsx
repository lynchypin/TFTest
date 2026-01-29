import { useState } from 'react';
import { FEATURES, getScenarioLicenseInfo, getPlanDisplay, PLAN_RANK, ADDONS } from '../services/license';
import FeaturesModal from './FeaturesModal';

const PLAN_COLORS = {
  professional: { bg: 'bg-blue-900/50', text: 'text-blue-300', border: 'border-blue-700/50' },
  business: { bg: 'bg-indigo-900/50', text: 'text-indigo-300', border: 'border-indigo-700/50' },
  digital_operations: { bg: 'bg-amber-900/50', text: 'text-amber-300', border: 'border-amber-700/50' },
  enterprise_im: { bg: 'bg-emerald-900/50', text: 'text-emerald-300', border: 'border-emerald-700/50' }
};

const ADDON_COLOR = { bg: 'bg-purple-900/50', text: 'text-purple-300', border: 'border-purple-700/50' };

const FEATURE_TIER_COLORS = {
  tier1: { bg: 'bg-cyan-900/50', text: 'text-cyan-300' },
  tier2: { bg: 'bg-cyan-900/30', text: 'text-cyan-400' },
  tier3: { bg: 'bg-cyan-900/20', text: 'text-cyan-500' }
};

export default function ScenarioCard({ scenario, onTrigger, onViewPayload, onViewTrace }) {
  const [showFeaturesModal, setShowFeaturesModal] = useState(false);
  
  const featuresDemo = scenario.features_demonstrated || scenario.required_features || [];
  const licenseInfo = getScenarioLicenseInfo(scenario);
  const planDisplay = getPlanDisplay(licenseInfo.minimumPlan);
  const planColor = PLAN_COLORS[licenseInfo.minimumPlan] || PLAN_COLORS.professional;

  const requiredAddons = licenseInfo.requiredAddons || [];
  const addonLabels = requiredAddons.map(key => {
    const addon = ADDONS.find(a => a.key === key);
    return addon?.label || key;
  });

  const getFeatureTier = (featureKey, index) => {
    const feature = FEATURES[featureKey];
    if (!feature) return FEATURE_TIER_COLORS.tier1;
    
    if (index < 2) return FEATURE_TIER_COLORS.tier1;
    if (index < 4) return FEATURE_TIER_COLORS.tier2;
    return FEATURE_TIER_COLORS.tier3;
  };

  const displayFeatures = featuresDemo.slice(0, 4);
  const remainingCount = featuresDemo.length - 4;

  const truncateName = (name, maxLen = 28) => {
    if (name.length <= maxLen) return name;
    return name.substring(0, maxLen - 1) + '…';
  };

  return (
    <>
      <div className="group bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden transition-all duration-300 hover:shadow-2xl hover:shadow-black/50 hover:-translate-y-1 hover:border-gray-700">
        <div className="p-5">
          <div className="flex items-start justify-between gap-3 mb-3">
            <h3 className="font-bold text-gray-100 text-lg leading-tight group-hover:text-emerald-400 transition-colors line-clamp-2">
              {scenario.name}
            </h3>
            <span className="text-xs font-mono text-gray-500 shrink-0">{scenario.id}</span>
          </div>

          <div className="flex flex-wrap gap-1.5 mb-3">
            <span className={`px-2.5 py-1 text-xs font-semibold rounded-lg border ${planColor.bg} ${planColor.text} ${planColor.border}`}>
              {truncateName(planDisplay.label, 20)}
            </span>
            {addonLabels.map((label, idx) => (
              <span 
                key={idx}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg border ${ADDON_COLOR.bg} ${ADDON_COLOR.text} ${ADDON_COLOR.border}`}
              >
                {truncateName(label, 18)}
              </span>
            ))}
          </div>

          <p className="text-sm text-gray-400 mb-4 line-clamp-2 leading-relaxed">{scenario.description}</p>

          <div className="flex flex-wrap gap-1.5 mb-4">
            {displayFeatures.map((featureKey, index) => {
              const feature = FEATURES[featureKey];
              const tierColor = getFeatureTier(featureKey, index);
              return (
                <span 
                  key={featureKey} 
                  className={`px-2 py-0.5 text-xs font-medium rounded-md ${tierColor.bg} ${tierColor.text} transition-colors border border-cyan-700/30`}
                  title={feature?.name}
                >
                  {truncateName(feature?.name || featureKey.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '), 22)}
                </span>
              );
            })}
            {remainingCount > 0 && (
              <button
                onClick={() => setShowFeaturesModal(true)}
                className="px-2 py-0.5 text-xs font-medium rounded-md bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-300 transition-all cursor-pointer border border-gray-700"
              >
                +{remainingCount}
              </button>
            )}
          </div>

          <div className="bg-gray-800/50 rounded-xl px-4 py-3 mb-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">Routes to</span>
              <span className="font-semibold text-gray-200 text-sm">{scenario.target_service}</span>
            </div>
            {scenario.expected_priority && (
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700/50">
                <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">Priority</span>
                <span className={`font-bold text-sm px-2 py-0.5 rounded ${
                  scenario.expected_priority === 'P1' 
                    ? 'bg-red-900/50 text-red-300 border border-red-700/50' 
                    : scenario.expected_priority === 'P2'
                    ? 'bg-orange-900/50 text-orange-300 border border-orange-700/50'
                    : 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50'
                }`}>
                  {scenario.expected_priority}
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onTrigger(scenario)}
              className="flex-1 btn-success text-sm py-2.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Trigger
            </button>
            <button
              onClick={() => onViewPayload(scenario)}
              className="flex-1 btn-secondary text-sm py-2.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              Payload
            </button>
            <button
              onClick={() => onViewTrace(scenario)}
              className="btn-ghost px-3"
              title="View Trace"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {showFeaturesModal && (
        <FeaturesModal
          scenario={scenario}
          onClose={() => setShowFeaturesModal(false)}
        />
      )}
    </>
  );
}
