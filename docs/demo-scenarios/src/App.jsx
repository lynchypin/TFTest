import { useState, useEffect, useMemo } from 'react';
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
  const [showFilters, setShowFilters] = useState(true);
  const [demoPaused, setDemoPaused] = useState(false);
  const [activeDemos, setActiveDemos] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

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

    return licenseFiltered.filter(scenario => {
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
  }, [filters, licenseConfig]);

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

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleTrigger = async (scenario) => {
    const integration = scenario.tags?.integration;
    const nativeConfigured = isIntegrationConfigured(integration);

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

  const hasActiveFilters = Object.values(filters).some(v => v?.length > 0) || 
    licenseConfig.plan !== null || 
    Object.values(licenseConfig.addons).some(v => v);

  return (
    <div className="min-h-screen bg-gray-950">
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
              <span className="text-2xl font-bold text-emerald-400">{filteredScenarios.length}</span>
              <span className="text-sm text-gray-400">of {licenseFilteredCount}</span>
              <span className="text-xs text-gray-500">({scenariosData.scenarios.length} total)</span>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-ghost text-sm ${showFilters ? 'bg-gray-800 text-emerald-400' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

        {showFilters && (
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
        )}
      </header>

      <main className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="flex gap-6">
          <div className="flex-1">
            {filteredScenarios.length === 0 ? (
              <div className="card-elevated p-12 text-center max-w-md mx-auto">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-800 flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-100 mb-2">No scenarios found</h3>
                <p className="text-gray-400 mb-6">Try adjusting your filters to see more results</p>
                <button
                  onClick={handleClearFilters}
                  className="btn-primary"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredScenarios.map(scenario => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    licenseConfig={licenseConfig}
                    onTrigger={handleTrigger}
                    onViewPayload={handleViewPayload}
                    onViewTrace={handleViewTrace}
                  />
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
        <div className={`fixed bottom-6 right-6 px-5 py-4 rounded-2xl shadow-2xl animate-slide-down ${
          notification.type === 'error'
            ? 'bg-gradient-to-r from-red-600 to-rose-500'
            : 'bg-gradient-to-r from-emerald-600 to-teal-500'
        } text-white font-medium z-50`}>
          {notification.message}
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
