import { useState } from 'react';
import { PLANS, ADDONS, getAvailableFeatures, FEATURES } from '../services/license';

const XIcon = () => (
  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export default function LicenseFilterPanel({ config, onChange }) {
  const availableFeatures = getAvailableFeatures(config);
  const totalFeatures = Object.keys(FEATURES).length;
  const isFiltering = config.plan !== null || Object.values(config.addons).some(v => v);

  const handlePlanChange = (planKey) => {
    onChange({ ...config, plan: planKey === config.plan ? null : planKey });
  };

  const handleAddonToggle = (addonKey) => {
    onChange({ 
      ...config, 
      addons: { 
        ...config.addons, 
        [addonKey]: !config.addons[addonKey] 
      } 
    });
  };

  const handleClearAll = () => {
    onChange({
      plan: null,
      addons: {
        aiops: false,
        automation_actions: false,
        status_pages: false,
        incident_workflows: false,
        runbook_automation: false
      }
    });
  };

  const activeAddons = Object.entries(config.addons).filter(([, v]) => v);
  const selectedPlan = PLANS.find(p => p.key === config.plan);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-100 text-sm">License</h3>
        {isFiltering && (
          <button
            onClick={handleClearAll}
            className="text-xs text-red-400 hover:text-red-300 font-medium"
          >
            Clear
          </button>
        )}
      </div>

      {isFiltering && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {selectedPlan && (
            <span className="pill pill-removable text-xs">
              {selectedPlan.label}
              <button 
                onClick={() => handlePlanChange(null)}
                className="ml-1 p-0.5 hover:bg-indigo-700 rounded-full transition-colors"
              >
                <XIcon />
              </button>
            </span>
          )}
          {activeAddons.map(([key]) => {
            const addon = ADDONS.find(a => a.key === key);
            return (
              <span key={key} className="pill bg-purple-900/50 text-purple-300 border border-purple-700/50 text-xs pr-1.5">
                {addon?.label?.split(' ')[0]}
                <button 
                  onClick={() => handleAddonToggle(key)}
                  className="ml-1 p-0.5 hover:bg-purple-700 rounded-full transition-colors"
                >
                  <XIcon />
                </button>
              </span>
            );
          })}
        </div>
      )}

      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">Plan</label>
        <div className="flex flex-wrap gap-1.5">
          {PLANS.filter(p => p.key).map(plan => (
            <button
              key={plan.key}
              onClick={() => handlePlanChange(plan.key)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all ${
                config.plan === plan.key
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-indigo-500 hover:text-gray-300'
              }`}
            >
              {plan.label.split(' ')[0]}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">Add-ons</label>
        <div className="flex flex-wrap gap-1.5">
          {ADDONS.map(addon => (
            <button
              key={addon.key}
              onClick={() => handleAddonToggle(addon.key)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all ${
                config.addons[addon.key]
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-purple-500 hover:text-gray-300'
              }`}
            >
              {addon.shortLabel || addon.label.split(' ')[0]}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-gray-500">
        <span className="font-semibold text-emerald-400">{availableFeatures.size}</span>/{totalFeatures} features available
      </div>
    </div>
  );
}
