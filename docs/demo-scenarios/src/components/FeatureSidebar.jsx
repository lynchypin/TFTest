import { useState } from 'react';
import { FEATURE_HIERARCHY, FEATURES, isFeatureAvailable } from '../services/license';

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

function getAvailabilityStatus(node, config) {
  if (node.features) {
    const total = node.features.length;
    const available = node.features.filter(f => isFeatureAvailable(f.key, config)).length;
    if (available === 0) return 'none';
    if (available === total) return 'all';
    return 'partial';
  }
  
  let totalFeatures = 0;
  let availableFeatures = 0;
  
  function countFeatures(obj) {
    if (obj.features) {
      totalFeatures += obj.features.length;
      availableFeatures += obj.features.filter(f => isFeatureAvailable(f.key, config)).length;
    } else {
      Object.values(obj).forEach(child => {
        if (typeof child === 'object') countFeatures(child);
      });
    }
  }
  
  countFeatures(node);
  
  if (availableFeatures === 0) return 'none';
  if (availableFeatures === totalFeatures) return 'all';
  return 'partial';
}

function getStatusColor(status) {
  switch (status) {
    case 'all': return 'bg-emerald-500';
    case 'partial': return 'bg-amber-500';
    case 'none': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
}

function FeatureNode({ name, node, config, depth = 0, expandedPaths, togglePath, path }) {
  const currentPath = path ? `${path}/${name}` : name;
  const isExpanded = expandedPaths[currentPath];
  const status = getAvailabilityStatus(node, config);
  const statusColor = getStatusColor(status);

  if (node.features) {
    const availableCount = node.features.filter(f => isFeatureAvailable(f.key, config)).length;
    return (
      <div style={{ marginLeft: depth * 8 }}>
        <button
          onClick={() => togglePath(currentPath)}
          className="flex items-center justify-between w-full py-1 px-1 rounded hover:bg-gray-800/50 text-left group"
        >
          <div className="flex items-center gap-1.5">
            <ChevronIcon expanded={isExpanded} />
            <span className={`w-2 h-2 rounded-full ${statusColor}`} />
            <span className="text-xs font-medium text-gray-300">{name}</span>
          </div>
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
            status === 'all' ? 'bg-emerald-900/50 text-emerald-300' :
            status === 'partial' ? 'bg-amber-900/50 text-amber-300' :
            'bg-red-900/50 text-red-300'
          }`}>
            {availableCount}/{node.features.length}
          </span>
        </button>
        
        {isExpanded && (
          <div className="ml-4 mt-0.5 space-y-0.5 animate-slide-down">
            {node.features.map(feature => {
              const available = isFeatureAvailable(feature.key, config);
              return (
                <div
                  key={feature.key}
                  className={`flex items-center gap-1.5 text-xs py-0.5 px-2 rounded ${
                    available ? 'text-gray-300' : 'text-gray-600'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${available ? 'bg-emerald-500' : 'bg-red-500/50'}`} />
                  <span className={!available ? 'line-through' : ''}>{feature.name}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  const childKeys = Object.keys(node);
  let totalFeatures = 0;
  let availableFeatures = 0;
  
  function countAll(obj) {
    if (obj.features) {
      totalFeatures += obj.features.length;
      availableFeatures += obj.features.filter(f => isFeatureAvailable(f.key, config)).length;
    } else {
      Object.values(obj).forEach(child => {
        if (typeof child === 'object') countAll(child);
      });
    }
  }
  countAll(node);

  return (
    <div style={{ marginLeft: depth * 8 }}>
      <button
        onClick={() => togglePath(currentPath)}
        className="flex items-center justify-between w-full py-1 px-1 rounded hover:bg-gray-800/50 text-left"
      >
        <div className="flex items-center gap-1.5">
          <ChevronIcon expanded={isExpanded} />
          <span className={`w-2 h-2 rounded-full ${statusColor}`} />
          <span className={`text-xs font-medium ${depth === 0 ? 'text-gray-200' : 'text-gray-300'}`}>{name}</span>
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
          status === 'all' ? 'bg-emerald-900/50 text-emerald-300' :
          status === 'partial' ? 'bg-amber-900/50 text-amber-300' :
          'bg-red-900/50 text-red-300'
        }`}>
          {availableFeatures}/{totalFeatures}
        </span>
      </button>
      
      {isExpanded && (
        <div className="border-l border-gray-700 ml-2.5 animate-slide-down">
          {childKeys.map(childKey => (
            <FeatureNode
              key={childKey}
              name={childKey}
              node={node[childKey]}
              config={config}
              depth={depth + 1}
              expandedPaths={expandedPaths}
              togglePath={togglePath}
              path={currentPath}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FeatureSidebar({ config }) {
  const [expandedPaths, setExpandedPaths] = useState({});
  
  const togglePath = (path) => {
    setExpandedPaths(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const totalCount = Object.keys(FEATURES).length;
  const availableCount = Object.keys(FEATURES).filter(k => isFeatureAvailable(k, config)).length;
  const percentage = Math.round((availableCount / totalCount) * 100);
  
  const overallStatus = availableCount === totalCount ? 'all' : availableCount === 0 ? 'none' : 'partial';

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800/50 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-100 text-sm">Features</h3>
          <div className="flex items-center gap-2">
            <div className="relative w-8 h-8">
              <svg className="w-8 h-8 transform -rotate-90">
                <circle cx="16" cy="16" r="12" fill="none" stroke="#374151" strokeWidth="3" />
                <circle
                  cx="16" cy="16" r="12"
                  fill="none"
                  stroke={overallStatus === 'all' ? '#10b981' : overallStatus === 'partial' ? '#f59e0b' : '#ef4444'}
                  strokeWidth="3"
                  strokeDasharray={`${percentage * 0.754} 75.4`}
                  strokeLinecap="round"
                  className="transition-all duration-500"
                />
              </svg>
            </div>
            <div className="text-xs">
              <span className="font-semibold text-gray-100">{availableCount}</span>
              <span className="text-gray-500">/{totalCount}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 mt-2 text-[10px]">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-gray-500">Available</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-gray-500">Partial</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-gray-500">Unavailable</span>
          </div>
        </div>
      </div>
      
      <div className="p-3 max-h-[calc(100vh-280px)] overflow-y-auto scrollbar-thin">
        {Object.entries(FEATURE_HIERARCHY).map(([category, children]) => (
          <FeatureNode
            key={category}
            name={category}
            node={children}
            config={config}
            depth={0}
            expandedPaths={expandedPaths}
            togglePath={togglePath}
            path=""
          />
        ))}
      </div>
    </div>
  );
}
