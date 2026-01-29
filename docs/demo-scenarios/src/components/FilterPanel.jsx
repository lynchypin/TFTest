import { useState, useMemo } from 'react';
import { FEATURE_HIERARCHY, isFeatureAvailable } from '../services/license';

const FILTER_CONFIG = {
  industry: {
    label: 'Industry',
    options: ['banking', 'fintech', 'healthcare', 'retail', 'ecommerce', 'technology', 'mining', 'manufacturing', 'energy', 'telecom']
  },
  team_type: {
    label: 'Team',
    options: ['soc', 'noc', 'devops', 'platform', 'sre', 'support', 'dba', 'ot_ops']
  },
  integration: {
    label: 'Integration',
    options: ['prometheus', 'grafana', 'datadog', 'newrelic', 'sentry', 'splunk', 'cloudwatch', 'github_actions', 'uptimerobot']
  },
  severity: {
    label: 'Severity',
    options: ['critical', 'error', 'warning', 'info']
  }
};

const SEVERITY_COLORS = {
  critical: { active: 'bg-red-600 text-white border-red-600', inactive: 'border-red-700/50 text-red-400 hover:bg-red-900/30' },
  error: { active: 'bg-orange-600 text-white border-orange-600', inactive: 'border-orange-700/50 text-orange-400 hover:bg-orange-900/30' },
  warning: { active: 'bg-amber-600 text-white border-amber-600', inactive: 'border-amber-700/50 text-amber-400 hover:bg-amber-900/30' },
  info: { active: 'bg-blue-600 text-white border-blue-600', inactive: 'border-blue-700/50 text-blue-400 hover:bg-blue-900/30' }
};

const ChevronIcon = ({ expanded }) => (
  <svg 
    className={`w-3.5 h-3.5 text-gray-500 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} 
    fill="none" 
    viewBox="0 0 24 24" 
    stroke="currentColor"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

const XIcon = () => (
  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

function getAvailableOptionsFromScenarios(scenarios, filteredScenarios, filters) {
  const available = {
    industry: new Set(),
    team_type: new Set(),
    integration: new Set(),
    severity: new Set(),
    features: new Set()
  };

  const scenariosToCheck = Object.keys(filters).some(k => filters[k]?.length > 0) 
    ? filteredScenarios 
    : scenarios;

  scenariosToCheck.forEach(scenario => {
    if (scenario.tags?.industry) {
      scenario.tags.industry.forEach(i => available.industry.add(i));
    }
    if (scenario.tags?.team_type) {
      scenario.tags.team_type.forEach(t => available.team_type.add(t));
    }
    if (scenario.tags?.integration) {
      available.integration.add(scenario.tags.integration);
    }
    if (scenario.severity) {
      available.severity.add(scenario.severity);
    }
    if (scenario.required_features) {
      scenario.required_features.forEach(f => available.features.add(f));
    }
    if (scenario.features_demonstrated) {
      scenario.features_demonstrated.forEach(f => available.features.add(f));
    }
  });

  return available;
}

function FeatureTreeNode({ name, node, selectedFeatures, onFeatureToggle, licenseConfig, availableFeatures, expandedPath, setExpandedPath }) {
  const isExpanded = expandedPath.startsWith(name);
  const pathPrefix = name + '/';

  if (node.features) {
    return (
      <div className="ml-2 py-1 animate-slide-down">
        <div className="flex flex-wrap gap-1">
          {node.features.map(feature => {
            const licenseAvailable = isFeatureAvailable(feature.key, licenseConfig);
            const hasScenarios = availableFeatures.has(feature.key);
            const available = licenseAvailable && hasScenarios;
            const isSelected = selectedFeatures.includes(feature.key);
            return (
              <button
                key={feature.key}
                onClick={() => available && onFeatureToggle(feature.key)}
                disabled={!available}
                className={`px-2 py-0.5 text-xs rounded-md transition-all border ${
                  !available
                    ? 'bg-gray-900 text-gray-600 border-gray-800 cursor-not-allowed opacity-50'
                    : isSelected
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-gray-800 text-gray-400 border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                }`}
                title={!licenseAvailable ? 'Not available in current license' : !hasScenarios ? 'No scenarios available' : ''}
              >
                {feature.name}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  const childKeys = Object.keys(node);
  
  return (
    <div className="ml-1">
      <button
        onClick={() => setExpandedPath(isExpanded ? '' : name)}
        className="flex items-center gap-1 py-0.5 hover:bg-gray-800/50 rounded text-left"
      >
        <ChevronIcon expanded={isExpanded} />
        <span className="text-xs font-medium text-gray-300">{name}</span>
      </button>
      
      {isExpanded && (
        <div className="border-l border-gray-700 ml-1.5 pl-1">
          {childKeys.map(childKey => (
            <FeatureTreeNode
              key={childKey}
              name={childKey}
              node={node[childKey]}
              selectedFeatures={selectedFeatures}
              onFeatureToggle={onFeatureToggle}
              licenseConfig={licenseConfig}
              availableFeatures={availableFeatures}
              expandedPath={expandedPath.replace(pathPrefix, '')}
              setExpandedPath={(p) => setExpandedPath(p ? name + '/' + p : '')}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FilterPanel({ filters, scenarios, filteredScenarios, onFilterChange, onClear, licenseConfig }) {
  const [expanded, setExpanded] = useState({});
  const [featureExpandedPath, setFeatureExpandedPath] = useState('');

  const availableOptions = useMemo(() => {
    return getAvailableOptionsFromScenarios(scenarios || [], filteredScenarios || [], filters);
  }, [scenarios, filteredScenarios, filters]);

  const toggleExpand = (key) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleToggle = (category, value) => {
    const current = filters[category] || [];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    onFilterChange(category, updated);
  };

  const handleFeatureToggle = (featureKey) => {
    const current = filters.features || [];
    const updated = current.includes(featureKey)
      ? current.filter(v => v !== featureKey)
      : [...current, featureKey];
    onFilterChange('features', updated);
  };

  const formatLabel = (str) => str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

  const hasActiveFilters = Object.values(filters).some(v => v?.length > 0);
  const totalActiveFilters = Object.values(filters).reduce((sum, arr) => sum + (arr?.length || 0), 0);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-100 text-sm">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={onClear}
            className="text-xs text-red-400 hover:text-red-300 font-medium"
          >
            Clear ({totalActiveFilters})
          </button>
        )}
      </div>

      {hasActiveFilters && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {Object.entries(filters).map(([category, values]) =>
            (values || []).map(value => (
              <span key={`${category}-${value}`} className="pill pill-removable text-xs">
                {formatLabel(value)}
                <button 
                  onClick={() => handleToggle(category, value)}
                  className="ml-1 p-0.5 hover:bg-indigo-700 rounded-full transition-colors"
                >
                  <XIcon />
                </button>
              </span>
            ))
          )}
        </div>
      )}

      <div className="space-y-2">
        <div className="border-b border-gray-800 pb-2">
          <button
            onClick={() => toggleExpand('features')}
            className="flex items-center justify-between w-full py-1 text-left"
          >
            <span className="text-xs font-medium text-gray-300">Features</span>
            <div className="flex items-center gap-1">
              {(filters.features?.length > 0) && (
                <span className="badge badge-primary text-[10px]">{filters.features.length}</span>
              )}
              <ChevronIcon expanded={expanded.features} />
            </div>
          </button>
          
          {expanded.features && (
            <div className="mt-1 max-h-40 overflow-y-auto scrollbar-thin animate-slide-down">
              {Object.entries(FEATURE_HIERARCHY).map(([category, children]) => (
                <FeatureTreeNode
                  key={category}
                  name={category}
                  node={children}
                  selectedFeatures={filters.features || []}
                  onFeatureToggle={handleFeatureToggle}
                  licenseConfig={licenseConfig}
                  availableFeatures={availableOptions.features}
                  expandedPath={featureExpandedPath}
                  setExpandedPath={setFeatureExpandedPath}
                />
              ))}
            </div>
          )}
        </div>

        {Object.entries(FILTER_CONFIG).map(([key, config]) => (
          <div key={key} className="border-b border-gray-800 pb-2 last:border-0 last:pb-0">
            <button
              onClick={() => toggleExpand(key)}
              className="flex items-center justify-between w-full py-1 text-left"
            >
              <span className="text-xs font-medium text-gray-300">{config.label}</span>
              <div className="flex items-center gap-1">
                {(filters[key]?.length > 0) && (
                  <span className="badge badge-primary text-[10px]">{filters[key].length}</span>
                )}
                <ChevronIcon expanded={expanded[key]} />
              </div>
            </button>
            
            {expanded[key] && (
              <div className="mt-1 flex flex-wrap gap-1 animate-slide-down">
                {config.options.map(option => {
                  const isSelected = (filters[key] || []).includes(option);
                  const isAvailable = availableOptions[key]?.has(option);
                  const severityColor = key === 'severity' ? SEVERITY_COLORS[option] : null;
                  
                  return (
                    <button
                      key={option}
                      onClick={() => isAvailable && handleToggle(key, option)}
                      disabled={!isAvailable}
                      className={`px-2 py-0.5 text-xs rounded-md transition-all border ${
                        !isAvailable
                          ? 'bg-gray-900 text-gray-600 border-gray-800 cursor-not-allowed opacity-50'
                          : isSelected
                          ? severityColor?.active || 'bg-indigo-600 text-white border-indigo-600'
                          : severityColor?.inactive || 'bg-gray-800 text-gray-400 border-gray-700 hover:bg-gray-700 hover:text-gray-300'
                      }`}
                      title={!isAvailable ? 'No scenarios available with current filters' : ''}
                    >
                      {formatLabel(option)}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
