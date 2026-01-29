export default function TraceModal({ scenario, onClose }) {
  const getStageIcon = (stage) => {
    if (stage.includes('Global')) return '🔄';
    if (stage.includes('Router')) return '🎯';
    if (stage.includes('Service')) return '📦';
    if (stage.includes('Assignment') || stage.includes('Result')) return '✅';
    return '•';
  };

  const getStageColor = (stage) => {
    if (stage.includes('Global')) return 'border-blue-500';
    if (stage.includes('Router')) return 'border-purple-500';
    if (stage.includes('Service')) return 'border-orange-500';
    if (stage.includes('Assignment') || stage.includes('Result')) return 'border-emerald-500';
    return 'border-gray-600';
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl shadow-2xl shadow-black/50 border border-gray-800 max-w-xl w-full max-h-[90vh] flex flex-col animate-scale-in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-800/50 rounded-t-2xl">
          <div>
            <h3 className="font-bold text-gray-100">Orchestration Trace</h3>
            <p className="text-sm text-gray-500">{scenario.id}: {scenario.name}</p>
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
          <div className="space-y-4">
            {scenario.orchestration_trace?.map((step, index) => (
              <div key={index} className={`border-l-4 ${getStageColor(step.stage)} pl-4 py-2`}>
                <div className="flex items-center gap-2 mb-1">
                  <span>{getStageIcon(step.stage)}</span>
                  <span className="font-medium text-gray-100">{step.stage}</span>
                  {step.rule && (
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded border border-gray-700">{step.rule}</span>
                  )}
                </div>
                {step.match && (
                  <p className="text-sm text-gray-500 mb-1">
                    Match: <code className="bg-gray-800 text-gray-300 px-1 rounded border border-gray-700">{step.match}</code>
                  </p>
                )}
                <p className="text-sm text-gray-400">
                  {step.action || step.result}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-800 p-6 bg-gray-800/50 rounded-b-2xl">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Final Destination:</span>
            <span className="font-semibold text-emerald-400">{scenario.target_service}</span>
          </div>
          {scenario.expected_priority && (
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-gray-500">Final Priority:</span>
              <span className={`font-bold px-2 py-0.5 rounded ${
                scenario.expected_priority === 'P1' 
                  ? 'bg-red-900/50 text-red-300 border border-red-700/50' 
                  : 'bg-amber-900/50 text-amber-300 border border-amber-700/50'
              }`}>
                {scenario.expected_priority}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
