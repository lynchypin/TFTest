import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import scenariosData from './data/scenarios.json';
import FilterPanel from './components/FilterPanel';
import LicenseFilterPanel from './components/LicenseFilterPanel';
import FeatureSidebar from './components/FeatureSidebar';
import ScenarioCard from './components/ScenarioCard';
import PayloadModal from './components/PayloadModal';
import TraceModal from './components/TraceModal';
import SettingsModal from './components/SettingsModal';
import { getInstance, saveInstance } from './services/pagerduty';
import { getLicenseConfig, saveLicenseConfig, filterByLicense } from './services/license';
import { triggerNativeIntegration, isIntegrationConfigured, hasPagerDutyCredentials } from './services/integrations';
import { hasOrchestratorConfigured, cleanupDemoIncidents, pauseDemo, resumeDemo, getDemoStatus } from './services/orchestrator';

function App() {
  const [filters, setFilters] = useState({});
  const [licenseConfig, setLicenseConfig] = useState(() => getLicenseConfig());
  const [pdInstance, setPdInstance] = useState(() => getInstance());
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [modalType, setModalType] = useState(null);
  const [notification, setNotification] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [demoPaused, setDemoPaused] = useState(false);
  const [activeDemos, setActiveDemos] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [triggeringId, setTriggeringId] = useState(null);
  const notificationTimer = useRef(null);
  const [notificationExiting, setNotificationExiting] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlFilters = {};
    ['industry', 'team_type', 'org_style', 'features', 'integration', 'tool', 'tool_type', 'severity', 'agent_type'].forEach(key => {
      const value = params.get(key);
      if (value) urlFilters[key] = value.split(',');
    });
    if (Object.keys(urlFilters).length > 0) {
      setFilters(urlFilters);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, values]) => {
      if (values?.length > 0) {
        params.set(key, values.join(','));
      }
    });
    const search = params.toString();
    window.history.replaceState({}, '', search ? `?${search}` : window.location.pathname);
  }, [filters]);

  const filteredScenarios = useMemo(() => {
    const licenseFiltered = filterByLicense(scenariosData.scenarios, licenseConfig);
    const query = searchQuery.toLowerCase().trim();

    return licenseFiltered.filter(scenario => {
      if (query) {
        const matchFields = [
          scenario.name,
          scenario.id,
          scenario.description,
          scenario.target_service
        ].filter(Boolean).map(f => f.toLowerCase());
        if (!matchFields.some(f => f.includes(query))) return false;
      }
      if (filters.industry?.length && !filters.industry.some(i => scenario.tags.industry.includes(i))) return false;
      if (filters.team_type?.length && !filters.team_type.some(t => scenario.tags.team_type.includes(t))) return false;
      if (filters.org_style?.length && !filters.org_style.some(o => scenario.tags.org_style.includes(o))) return false;
      if (filters.features?.length) {
        const scenarioFeatures = scenario.required_features || scenario.features_demonstrated || [];
        if (!filters.features.some(f => scenarioFeatures.includes(f))) return false;
      }
      if (filters.integration?.length && !filters.integration.includes(scenario.tags.integration)) return false;
      if (filters.tool?.length) {
        const scenarioTools = Array.isArray(scenario.tags.tool)
          ? scenario.tags.tool
          : scenario.tags.tool
            ? [scenario.tags.tool]
            : scenario.tags.integration
              ? [scenario.tags.integration]
              : [];
        if (!filters.tool.some(t => scenarioTools.includes(t))) return false;
      }
      if (filters.tool_type?.length) {
        const scenarioToolTypes = Array.isArray(scenario.tags.tool_type)
          ? scenario.tags.tool_type
          : scenario.tags.tool_type
            ? [scenario.tags.tool_type]
            : [];
        if (!filters.tool_type.some(t => scenarioToolTypes.includes(t))) return false;
      }
      if (filters.agent_type?.length) {
        const scenarioTools = Array.isArray(scenario.tags.tool) ? scenario.tags.tool : (scenario.tags.tool ? [scenario.tags.tool] : []);
        const scenarioFeatures = scenario.tags.features || [];
        const hasAgentType = filters.agent_type.some(agentType => {
          const toolMatch = scenarioTools.some(t => t === `pagerduty_agent_${agentType}`);
          const featureMatch = scenarioFeatures.some(f => f === `agent_${agentType}`);
          return toolMatch || featureMatch;
        });
        if (!hasAgentType) return false;
      }
      if (filters.severity?.length && !filters.severity.includes(scenario.severity)) return false;
      return true;
    });
  }, [filters, licenseConfig, searchQuery]);

  const licenseFilteredCount = useMemo(() => {
    return filterByLicense(scenariosData.scenarios, licenseConfig).length;
  }, [licenseConfig]);

  const handleFilterChange = (category, values) => {
    setFilters(prev => ({ ...prev, [category]: values }));
  };

  const handleClearFilters = () => {
    setFilters({});
  };

  const handleCleanup = async () => {
    if (!hasOrchestratorConfigured()) {
      showNotification('Configure Orchestrator URL in Settings first', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const result = await cleanupDemoIncidents();
      showNotification(`Cleaned up ${result.resolved} demo incidents`, 'success');
      refreshDemoStatus();
    } catch (e) {
      showNotification(`Cleanup failed: ${e.message}`, 'error');
    }
    setIsLoading(false);
  };

  const handlePause = async () => {
    if (!hasOrchestratorConfigured()) {
      showNotification('Configure Orchestrator URL in Settings first', 'error');
      return;
    }
    setIsLoading(true);
    try {
      await pauseDemo();
      setDemoPaused(true);
      showNotification('Demo paused (15 min timeout)', 'success');
    } catch (e) {
      showNotification(`Pause failed: ${e.message}`, 'error');
    }
    setIsLoading(false);
  };

  const handleResume = async () => {
    if (!hasOrchestratorConfigured()) {
      showNotification('Configure Orchestrator URL in Settings first', 'error');
      return;
    }
    setIsLoading(true);
    try {
      await resumeDemo();
      setDemoPaused(false);
      showNotification('Demo resumed', 'success');
    } catch (e) {
      showNotification(`Resume failed: ${e.message}`, 'error');
    }
    setIsLoading(false);
  };

  const refreshDemoStatus = async () => {
    if (!hasOrchestratorConfigured()) return;
    try {
      const status = await getDemoStatus();
      setActiveDemos(status.count || 0);
    } catch (e) {
      console.error('Failed to get demo status:', e);
    }
  };

  useEffect(() => {
    refreshDemoStatus();
    const interval = setInterval(refreshDemoStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLicenseChange = (newConfig) => {
    setLicenseConfig(newConfig);
    saveLicenseConfig(newConfig);
  };

  const handleSaveSettings = (instance) => {
    setPdInstance(instance);
    saveInstance(instance);
  };

  const showNotification = useCallback((message, type = 'success') => {
    if (notificationTimer.current) clearTimeout(notificationTimer.current);
    setNotificationExiting(false);
    setNotification({ message, type, startTime: Date.now() });
    notificationTimer.current = setTimeout(() => {
      setNotificationExiting(true);
      setTimeout(() => {
        setNotification(null);
        setNotificationExiting(false);
      }, 300);
    }, 3000);
  }, []);

  const dismissNotification = useCallback(() => {
    if (notificationTimer.current) clearTimeout(notificationTimer.current);
    setNotificationExiting(true);
    setTimeout(() => {
      setNotification(null);
      setNotificationExiting(false);
    }, 300);
  }, []);

  const handleTrigger = async (scenario) => {
    const integration = scenario.tags?.integration;
    const nativeConfigured = isIntegrationConfigured(integration);
    setTriggeringId(scenario.id);

    try {
      const result = await triggerNativeIntegration(scenario);

      if (result.nativeTriggered) {
        showNotification(
          `${scenario.id} sent via ${result.integration}! ${result.message}`,
          'success'
        );
        return;
      }

      if (result.success && result.fallbackUsed) {
        showNotification(
          `${scenario.id} sent via PagerDuty Direct (fallback). Dedup: ${result.dedup_key}`,
          'success'
        );
        return;
      }

      if (result.error) {
        const hasFallback = hasPagerDutyCredentials();
        if (!hasFallback && !nativeConfigured) {
          showNotification(
            `Configure ${integration} credentials in Settings → External Tools, or add a Fallback Routing Key.`,
            'error'
          );
        } else {
          showNotification(`Failed: ${result.error}`, 'error');
        }
      }
    } catch (error) {
      showNotification(`Failed: ${error.message}`, 'error');
    } finally {
      setTriggeringId(null);
    }
  };

  const handleViewPayload = (scenario) => {
    setSelectedScenario(scenario);
    setModalType('payload');
  };

  const handleViewTrace = (scenario) => {
    setSelectedScenario(scenario);
    setModalType('trace');
  };

  const closeModal = () => {
    setSelectedScenario(null);
    setModalType(null);
  };

  const activeFilterLabels = useMemo(() => {
    const labels = [];
    if (filters.industry?.length) labels.push(...filters.industry.map(v => ({ category: 'industry', value: v })));
    if (filters.team_type?.length) labels.push(...filters.team_type.map(v => ({ category: 'team_type', value: v })));
    if (filters.tool?.length) labels.push(...filters.tool.map(v => ({ category: 'tool', value: v })));
    if (filters.tool_type?.length) labels.push(...filters.tool_type.map(v => ({ category: 'tool_type', value: v })));
    if (filters.severity?.length) labels.push(...filters.severity.map(v => ({ category: 'severity', value: v })));
    if (filters.agent_type?.length) labels.push(...filters.agent_type.map(v => ({ category: 'agent_type', value: v })));
    if (filters.features?.length) labels.push(...filters.features.map(v => ({ category: 'features', value: v })));
    return labels;
  }, [filters]);

  return (
    <div className="min-h-screen bg-gray-950 scrollbar-thin">
      <header className="sticky top-0 z-40 bg-gray-900/95 backdrop-blur-xl border-b border-gray-800 shadow-lg shadow-black/20">
        <div className="max-w-[1800px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-100">PagerDuty Demo</h1>
              <p className="text-xs text-gray-500">
                {pdInstance ? (
                  <a
                    href={`https://${pdInstance}.pagerduty.com`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                  >
                    {pdInstance}.pagerduty.com
                  </a>
                ) : (
                  <span className="text-amber-400">Configure in Settings</span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search scenarios..."
                className="w-56 pl-9 pr-8 py-2 bg-gray-800/80 border border-gray-700 rounded-xl text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-600 transition-all duration-200"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            {hasOrchestratorConfigured() && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/80 rounded-lg border border-gray-700">
                {activeDemos > 0 && (
                  <span className="flex items-center gap-1.5 text-xs text-amber-400">
                    <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></span>
                    {activeDemos} active
                  </span>
                )}
                <button
                  onClick={handleCleanup}
                  disabled={isLoading}
                  className="px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition-colors disabled:opacity-50"
                  title="Resolve all demo incidents"
                >
                  Cleanup
                </button>
                {demoPaused ? (
                  <button
                    onClick={handleResume}
                    disabled={isLoading}
                    className="px-2 py-1 text-xs text-emerald-400 hover:text-emerald-300 hover:bg-emerald-900/30 rounded transition-colors disabled:opacity-50"
                    title="Resume demo actions"
                  >
                    Resume
                  </button>
                ) : (
                  <button
                    onClick={handlePause}
                    disabled={isLoading}
                    className="px-2 py-1 text-xs text-amber-400 hover:text-amber-300 hover:bg-amber-900/30 rounded transition-colors disabled:opacity-50"
                    title="Pause demo (15 min timeout)"
                  >
                    Pause
                  </button>
                )}
              </div>
            )}
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/80 rounded-xl border border-gray-700">
              <span className="text-2xl font-bold text-emerald-400 tabular-nums transition-all duration-300">{filteredScenarios.length}</span>
              <span className="text-sm text-gray-400">of {licenseFilteredCount}</span>
              <span className="text-xs text-gray-500">({scenariosData.scenarios.length} total)</span>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-ghost text-sm ${showFilters ? 'bg-gray-800 text-emerald-400' : ''}`}
            >
              <svg className={`w-4 h-4 transition-transform duration-200 ${showFilters ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filters
              {hasActiveFilters && (
                <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
              )}
            </button>
            <button
              onClick={() => setModalType('settings')}
              className="btn-secondary text-sm"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </button>
          </div>
        </div>

        {!showFilters && activeFilterLabels.length > 0 && (
          <div className="border-t border-gray-800/50 bg-gray-900/60">
            <div className="max-w-[1800px] mx-auto px-6 py-2 flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-500 mr-1">Active:</span>
              {activeFilterLabels.slice(0, 8).map(({ category, value }, idx) => (
                <span
                  key={`${category}-${value}-${idx}`}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-900/40 text-indigo-300 border border-indigo-700/30"
                >
                  {value}
                  <button
                    onClick={() => {
                      const updated = filters[category]?.filter(v => v !== value) || [];
                      handleFilterChange(category, updated);
                    }}
                    className="hover:text-white transition-colors ml-0.5"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </span>
              ))}
              {activeFilterLabels.length > 8 && (
                <span className="text-xs text-gray-500">+{activeFilterLabels.length - 8} more</span>
              )}
              <button
                onClick={handleClearFilters}
                className="text-xs text-gray-500 hover:text-gray-300 ml-2 transition-colors"
              >
                Clear all
              </button>
            </div>
          </div>
        )}

        <div
          className="overflow-hidden transition-all duration-300 ease-in-out"
          style={{
            maxHeight: showFilters ? '600px' : '0',
            opacity: showFilters ? 1 : 0,
          }}
        >
          <div className="border-t border-gray-800 bg-gray-900/80">
            <div className="max-w-[1800px] mx-auto px-6 py-4">
              <div className="flex gap-6">
                <div className="w-72 flex-shrink-0">
                  <LicenseFilterPanel
                    config={licenseConfig}
                    onChange={handleLicenseChange}
                  />
                </div>
                <div className="flex-1">
                  <FilterPanel
                    filters={filters}
                    scenarios={scenariosData.scenarios}
                    filteredScenarios={filteredScenarios}
                    onFilterChange={handleFilterChange}
                    onClear={handleClearFilters}
                    licenseConfig={licenseConfig}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="flex gap-6">
          <div className="flex-1">
            {filteredScenarios.length === 0 ? (
              <div className="card-elevated p-12 text-center max-w-md mx-auto animate-fade-in">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-800 flex items-center justify-center">
                  <div className="relative">
                    <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-gray-600 rounded-full animate-pulse"></span>
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-gray-100 mb-2">No scenarios found</h3>
                <p className="text-gray-400 mb-6">
                  {searchQuery ? `No results for "${searchQuery}"` : 'Try adjusting your filters to see more results'}
                </p>
                <div className="flex gap-3 justify-center">
                  {searchQuery && (
                    <button onClick={() => setSearchQuery('')} className="btn-secondary text-sm">
                      Clear search
                    </button>
                  )}
                  <button onClick={handleClearFilters} className="btn-primary text-sm">
                    Clear all filters
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredScenarios.map((scenario, index) => (
                  <div
                    key={scenario.id}
                    className="animate-card-in"
                    style={{ animationDelay: `${Math.min(index * 30, 300)}ms` }}
                  >
                    <ScenarioCard
                      scenario={scenario}
                      licenseConfig={licenseConfig}
                      onTrigger={handleTrigger}
                      onViewPayload={handleViewPayload}
                      onViewTrace={handleViewTrace}
                      isTriggering={triggeringId === scenario.id}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          <aside className="w-72 flex-shrink-0 hidden lg:block">
            <div className="sticky top-32">
              <FeatureSidebar config={licenseConfig} />
            </div>
          </aside>
        </div>
      </main>

      {notification && (
        <div
          onClick={dismissNotification}
          className={`fixed bottom-6 right-6 max-w-sm cursor-pointer rounded-2xl shadow-2xl overflow-hidden z-50 transition-all duration-300 ${
            notificationExiting ? 'animate-slide-out' : 'animate-slide-up'
          } ${
            notification.type === 'error'
              ? 'bg-gradient-to-r from-red-600 to-rose-500'
              : 'bg-gradient-to-r from-emerald-600 to-teal-500'
          }`}
        >
          <div className="px-5 py-4 text-white font-medium pr-10">
            {notification.message}
            <button className="absolute top-3 right-3 text-white/60 hover:text-white transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div className="h-1 bg-white/20">
            <div className={`h-full bg-white/50 ${notificationExiting ? '' : 'animate-progress-shrink'}`}></div>
          </div>
        </div>
      )}

      {modalType === 'payload' && selectedScenario && (
        <PayloadModal
          scenario={selectedScenario}
          onClose={closeModal}
          onSend={handleTrigger}
        />
      )}

      {modalType === 'trace' && selectedScenario && (
        <TraceModal
          scenario={selectedScenario}
          onClose={closeModal}
        />
      )}

      {modalType === 'settings' && (
        <SettingsModal
          instance={pdInstance}
          onSave={handleSaveSettings}
          onClose={closeModal}
        />
      )}
    </div>
  );
}

export default App;
