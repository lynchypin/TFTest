import { FEATURES, PLANS, ADDONS, PLAN_RANK } from '../services/license';

const XIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const PLAN_COLORS = {
  professional: 'bg-blue-900/50 text-blue-300 border-blue-700/50',
  business: 'bg-indigo-900/50 text-indigo-300 border-indigo-700/50',
  digital_operations: 'bg-orange-900/50 text-orange-300 border-orange-700/50',
  enterprise_im: 'bg-emerald-900/50 text-emerald-300 border-emerald-700/50'
};

export default function FeaturesModal({ features, onClose, title = 'Features Demonstrated' }) {
  if (!features || features.length === 0) return null;

  const getPlanLabel = (planKey) => {
    const plan = PLANS.find(p => p.key === planKey);
    return plan?.label || planKey;
  };

  const getMinPlanColor = (feature) => {
    const { plans } = feature;
    if (plans.length === 0) return PLAN_COLORS.professional;
    const minPlanRank = Math.min(...plans.map(p => PLAN_RANK[p] ?? 99));
    const minPlan = Object.entries(PLAN_RANK).find(([, rank]) => rank === minPlanRank)?.[0];
    return PLAN_COLORS[minPlan] || PLAN_COLORS.professional;
  };

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in" 
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-2xl shadow-2xl shadow-black/50 border border-gray-800 max-w-lg w-full max-h-[85vh] overflow-hidden animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-gray-100">{title}</h3>
              <p className="text-xs text-gray-500">{features.length} features</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-xl transition-colors"
          >
            <XIcon />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[60vh] scrollbar-thin">
          <div className="space-y-3">
            {features.map(featureKey => {
              const feature = FEATURES[featureKey];
              if (!feature) {
                return (
                  <div key={featureKey} className="p-3 bg-gray-800/50 rounded-xl border border-gray-700/50">
                    <span className="text-sm text-gray-400 font-mono">{featureKey}</span>
                  </div>
                );
              }
              const { plans, addons } = feature;
              
              return (
                <div key={featureKey} className="p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-100">{feature.name}</h4>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {plans.length > 0 && (
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-lg border ${getMinPlanColor(feature)}`}>
                        {getPlanLabel(plans[0])}+
                      </span>
                    )}
                    {addons.length > 0 && addons.map(addonKey => {
                      const addon = ADDONS.find(a => a.key === addonKey);
                      return (
                        <span key={addonKey} className="text-xs font-medium px-2.5 py-1 rounded-lg bg-purple-900/50 text-purple-300 border border-purple-700/50">
                          {addon?.label || addonKey}
                        </span>
                      );
                    })}
                    {plans.length === 0 && addons.length === 0 && (
                      <span className="text-xs font-medium px-2.5 py-1 rounded-lg bg-emerald-900/50 text-emerald-300 border border-emerald-700/50">
                        All plans
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-gray-800 bg-gray-800/50">
          <button
            onClick={onClose}
            className="w-full btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
