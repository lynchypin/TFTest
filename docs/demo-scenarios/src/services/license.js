export const PLANS = [
  { key: null, label: 'All Plans (No Filter)', color: 'gray' },
  { key: 'professional', label: 'Professional', color: 'blue' },
  { key: 'business', label: 'Business', color: 'purple' },
  { key: 'digital_operations', label: 'Dig Ops', color: 'orange' },
  { key: 'enterprise_im', label: 'EIM', color: 'green' }
];

export const PLAN_RANK = {
  professional: 0,
  business: 1,
  digital_operations: 2,
  enterprise_im: 3
};

export const ADDONS = [
  { key: 'aiops', label: 'AIOps', shortLabel: 'AIOps', description: 'Event Intelligence, Noise Reduction & Automation' },
  { key: 'automation_actions', label: 'Automation Actions', shortLabel: 'AA', description: 'Automated Diagnostics & Remediation' },
  { key: 'status_pages', label: 'Status Pages', shortLabel: 'Status Pages', description: 'Internal & External Status Communication' },
  { key: 'runbook_automation', label: 'Runbook Automation', shortLabel: 'RBA', description: 'Process Automation Integration' }
];

export const FEATURE_HIERARCHY = {
  'Event Management': {
    'Event Routing': {
      features: [
        { key: 'basic_routing', name: 'Basic Routing', plans: ['professional'], addons: [] },
        { key: 'service_event_rules', name: 'Service Event Rules', plans: ['professional'], addons: [] },
        { key: 'event_transforms', name: 'Event Transforms', plans: ['professional'], addons: [] }
      ]
    },
    'Event Orchestration': {
      'Service Orchestration': {
        features: [
          { key: 'service_orchestration_rules', name: 'Service Orchestration Rules', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'nested_rules', name: 'Nested Rules', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'rule_variables', name: 'Rule Variables', plans: ['digital_operations'], addons: ['aiops'] }
        ]
      },
      'Global Orchestration': {
        features: [
          { key: 'global_event_orchestration', name: 'Global Event Orchestration', plans: [], addons: ['aiops'] },
          { key: 'global_routing_rules', name: 'Global Routing Rules', plans: [], addons: ['aiops'] },
          { key: 'integration_routing', name: 'Integration-Level Routing', plans: [], addons: ['aiops'] }
        ]
      },
      'Orchestration Conditions': {
        features: [
          { key: 'basic_conditions', name: 'Basic Conditions (If/Else)', plans: ['professional'], addons: [] },
          { key: 'threshold_conditions', name: 'Threshold Conditions', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'recurring_conditions', name: 'Recurring/Frequency Conditions', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'schedule_conditions', name: 'Schedule-Based Conditions', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'time_window_conditions', name: 'Time Window Conditions', plans: ['digital_operations'], addons: ['aiops'] }
        ]
      },
      'Event Enrichment': {
        features: [
          { key: 'basic_enrichment', name: 'Basic Enrichment (Static)', plans: ['professional'], addons: [] },
          { key: 'dynamic_enrichment', name: 'Dynamic Field Enrichment', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'severity_mapping', name: 'Severity Mapping', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'priority_mapping', name: 'Priority Mapping', plans: ['professional'], addons: [] }
        ]
      }
    }
  },
  'Noise Reduction': {
    'Alert Suppression': {
      features: [
        { key: 'alert_suppression', name: 'Alert Suppression', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'transient_alert_suppression', name: 'Transient Alert Suppression', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'maintenance_windows', name: 'Maintenance Windows', plans: ['professional'], addons: [] }
      ]
    },
    'Alert Grouping': {
      'Time-Based Grouping': {
        features: [
          { key: 'time_based_grouping', name: 'Time-Based Alert Grouping', plans: ['digital_operations'], addons: ['aiops'] }
        ]
      },
      'Content-Based Grouping': {
        features: [
          { key: 'content_based_grouping', name: 'Content-Based Alert Grouping', plans: ['digital_operations'], addons: ['aiops'] }
        ]
      },
      'Intelligent Grouping': {
        features: [
          { key: 'intelligent_alert_grouping', name: 'Intelligent Alert Grouping (ML)', plans: ['digital_operations'], addons: ['aiops'] },
          { key: 'global_alert_grouping', name: 'Global Alert Grouping', plans: [], addons: ['aiops'] },
          { key: 'unified_grouping', name: 'Unified Alerting Group', plans: [], addons: ['aiops'] }
        ]
      }
    },
    'Incident Pausing': {
      features: [
        { key: 'auto_pause_incidents', name: 'Auto-Pause Incidents', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'paused_notifications', name: 'Paused Incident Notifications', plans: ['digital_operations'], addons: ['aiops'] }
      ]
    }
  },
  'AIOps & Intelligence': {
    'Machine Learning': {
      features: [
        { key: 'intelligent_alert_grouping', name: 'Intelligent Alert Grouping', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'probable_origin', name: 'Probable Origin', plans: [], addons: ['aiops'] },
        { key: 'outlier_detection', name: 'Outlier Incident Detection', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'triage_suggestions', name: 'Triage Suggestions', plans: [], addons: ['aiops'] }
      ]
    },
    'Incident Context': {
      features: [
        { key: 'past_incidents', name: 'Past Incidents', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'related_incidents', name: 'Related Incidents', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'similar_incidents', name: 'Similar Incidents', plans: ['digital_operations'], addons: ['aiops'] }
      ]
    },
    'Change Intelligence': {
      features: [
        { key: 'change_events', name: 'Change Events', plans: ['professional'], addons: [] },
        { key: 'change_correlation', name: 'Change Correlation', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'recent_changes', name: 'Recent Changes View', plans: ['digital_operations'], addons: ['aiops'] }
      ]
    }
  },
  'Incident Response': {
    'On-Call Management': {
      features: [
        { key: 'escalation_policies', name: 'Escalation Policies', plans: ['professional'], addons: [] },
        { key: 'on_call_schedules', name: 'On-Call Schedules', plans: ['professional'], addons: [] },
        { key: 'schedule_overrides', name: 'Schedule Overrides', plans: ['professional'], addons: [] },
        { key: 'on_call_handoffs', name: 'On-Call Handoffs', plans: ['professional'], addons: [] }
      ]
    },
    'Incident Priority': {
      features: [
        { key: 'priority_levels', name: 'Priority Levels', plans: ['professional'], addons: [] },
        { key: 'priority_assignment', name: 'Priority Assignment', plans: ['professional'], addons: [] },
        { key: 'dynamic_priority', name: 'Dynamic Priority Updates', plans: ['business'], addons: [] }
      ]
    },
    'Response Coordination': {
      features: [
        { key: 'response_mobilizer', name: 'Response Mobilizer', plans: ['business'], addons: [] },
        { key: 'add_responders', name: 'Add Responders', plans: ['business'], addons: [] },
        { key: 'conference_bridge', name: 'Conference Bridge', plans: ['business'], addons: [] },
        { key: 'response_plays', name: 'Response Plays', plans: ['business'], addons: [] }
      ]
    },
    'Enterprise Incident Management': {
      features: [
        { key: 'incident_tasks', name: 'Incident Tasks', plans: ['enterprise_im'], addons: [] },
        { key: 'incident_roles', name: 'Incident Roles', plans: ['professional'], addons: [] },
        { key: 'incident_types', name: 'Custom Incident Types', plans: ['business'], addons: [] },
        { key: 'status_updates', name: 'Status Updates', plans: ['professional'], addons: [] },
        { key: 'incident_timeline', name: 'Incident Timeline', plans: ['professional'], addons: [] }
      ]
    }
  },
  'Automation': {
    'Incident Workflows': {
      features: [
        { key: 'workflows_basic', name: 'Incident Workflows (Limited)', plans: ['professional'], addons: [] },
        { key: 'workflows_full', name: 'Incident Workflows', plans: ['business'], addons: ['incident_workflows'] },
        { key: 'workflows_advanced', name: 'Advanced Workflows', plans: ['enterprise_im'], addons: ['incident_workflows'] },
        { key: 'workflow_triggers', name: 'Workflow Triggers', plans: ['business'], addons: ['incident_workflows'] }
      ]
    },
    'Automation Actions': {
      features: [
        { key: 'automation_diagnostics', name: 'Automated Diagnostics', plans: [], addons: ['automation_actions'] },
        { key: 'automation_remediation', name: 'Automated Remediation', plans: [], addons: ['automation_actions'] },
        { key: 'runbook_automation', name: 'Runbook Automation', plans: [], addons: ['runbook_automation'] },
        { key: 'process_automation', name: 'Process Automation', plans: [], addons: ['runbook_automation'] }
      ]
    },
    'Event-Triggered Actions': {
      features: [
        { key: 'webhooks', name: 'Webhooks', plans: ['professional'], addons: [] },
        { key: 'event_webhooks', name: 'Event-Triggered Webhooks', plans: ['digital_operations'], addons: ['aiops'] },
        { key: 'custom_actions', name: 'Custom Actions', plans: ['business'], addons: [] }
      ]
    }
  },
  'Stakeholder Communication': {
    'Status Pages': {
      features: [
        { key: 'internal_status_page', name: 'Internal Status Page', plans: [], addons: ['status_pages'] },
        { key: 'external_status_page', name: 'External Status Page', plans: [], addons: ['status_pages'] },
        { key: 'status_page_subscribers', name: 'Status Page Subscribers', plans: [], addons: ['status_pages'] }
      ]
    },
    'Stakeholder Notifications': {
      features: [
        { key: 'stakeholder_notifications', name: 'Stakeholder Notifications', plans: ['business'], addons: ['status_pages'] },
        { key: 'status_update_templates', name: 'Status Update Templates', plans: ['business'], addons: ['status_pages'] },
        { key: 'business_subscribers', name: 'Business Subscribers', plans: ['business'], addons: ['status_pages'] }
      ]
    }
  },
  'Integrations': {
    'Collaboration': {
      'Slack': {
        features: [
          { key: 'slack_notifications', name: 'Slack Notifications', plans: ['professional'], addons: [] },
          { key: 'slack_actions', name: 'Slack Actions', plans: ['professional'], addons: [] },
          { key: 'slack_incident_channel', name: 'Slack Incident Channels', plans: ['business'], addons: [] },
          { key: 'slack_advanced', name: 'Advanced Slack Features', plans: ['enterprise_im'], addons: [] }
        ]
      },
      'Microsoft Teams': {
        features: [
          { key: 'teams_notifications', name: 'Teams Notifications', plans: ['professional'], addons: [] },
          { key: 'teams_actions', name: 'Teams Actions', plans: ['professional'], addons: [] }
        ]
      }
    },
    'ITSM': {
      'ServiceNow': {
        features: [
          { key: 'servicenow_sync', name: 'ServiceNow Sync', plans: ['business'], addons: [] },
          { key: 'servicenow_bidirectional', name: 'Bi-directional ServiceNow (ITSM)', plans: ['enterprise_im'], addons: [] }
        ]
      },
      'Jira': {
        features: [
          { key: 'jira_integration', name: 'Jira Integration', plans: ['professional'], addons: [] },
          { key: 'jira_sync', name: 'Jira Sync', plans: ['professional'], addons: [] }
        ]
      }
    },
    'Monitoring': {
      features: [
        { key: 'monitoring_integrations', name: 'Monitoring Integrations', plans: ['professional'], addons: [] },
        { key: 'custom_event_transforms', name: 'Custom Event Transforms', plans: ['professional'], addons: [] }
      ]
    }
  },
  'Analytics & Visibility': {
    'Incident Analytics': {
      features: [
        { key: 'basic_analytics', name: 'Basic Analytics', plans: ['professional'], addons: [] },
        { key: 'advanced_analytics', name: 'Advanced Analytics', plans: ['business'], addons: [] },
        { key: 'operational_reviews', name: 'Operational Reviews', plans: ['business'], addons: [] }
      ]
    },
    'Post-Incident': {
      features: [
        { key: 'post_incident_reviews', name: 'Post-Incident Reviews', plans: ['professional'], addons: [] },
        { key: 'postmortems', name: 'Postmortems', plans: ['professional'], addons: [] }
      ]
    },
    'Service Visibility': {
      features: [
        { key: 'service_graph', name: 'Service Graph', plans: ['business'], addons: [] },
        { key: 'service_dependencies', name: 'Service Dependencies', plans: ['business'], addons: [] },
        { key: 'business_services', name: 'Business Services', plans: ['business'], addons: [] },
        { key: 'service_standards', name: 'Service Standards', plans: ['business'], addons: [] },
        { key: 'impact_metrics', name: 'Impact Metrics', plans: ['business'], addons: [] }
      ]
    },
    'Custom Fields': {
      features: [
        { key: 'custom_fields_basic', name: 'Custom Fields (10 max)', plans: ['professional'], addons: [] },
        { key: 'custom_fields_advanced', name: 'Custom Fields (30 max)', plans: ['enterprise_im'], addons: [] }
      ]
    }
  }
};

function collectFeaturesFromHierarchy(obj, features = {}) {
  if (obj.features && Array.isArray(obj.features)) {
    for (const f of obj.features) {
      features[f.key] = {
        name: f.name,
        plans: f.plans,
        addons: f.addons
      };
    }
  } else {
    for (const key of Object.keys(obj)) {
      if (typeof obj[key] === 'object') {
        collectFeaturesFromHierarchy(obj[key], features);
      }
    }
  }
  return features;
}

export const FEATURES = collectFeaturesFromHierarchy(FEATURE_HIERARCHY);

function flattenHierarchy(obj, path = [], result = []) {
  for (const [key, value] of Object.entries(obj)) {
    const currentPath = [...path, key];
    if (value.features) {
      result.push({
        path: currentPath,
        label: key,
        depth: currentPath.length,
        features: value.features
      });
    } else {
      flattenHierarchy(value, currentPath, result);
    }
  }
  return result;
}

export const FLAT_FEATURE_CATEGORIES = flattenHierarchy(FEATURE_HIERARCHY);

export const DEFAULT_CONFIG = {
  plan: null,
  addons: {
    aiops: false,
    automation_actions: false,
    customer_service_ops: false,
    workflow_automation: false,
    runbook_automation: false
  }
};

export function getLicenseConfig() {
  try {
    const saved = localStorage.getItem('pagerduty_license_config');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.plan !== undefined) {
        return parsed;
      }
    }
  } catch (e) {
    console.warn('Failed to load license config:', e);
  }
  return DEFAULT_CONFIG;
}

export function saveLicenseConfig(config) {
  try {
    localStorage.setItem('pagerduty_license_config', JSON.stringify(config));
  } catch (e) {
    console.warn('Failed to save license config:', e);
  }
}

export function hasFeature(featureKey, config) {
  if (config.plan === null && !Object.values(config.addons).some(v => v)) {
    return true;
  }
  
  const feature = FEATURES[featureKey];
  if (!feature) {
    return true;
  }
  
  const { plans, addons } = feature;
  
  if (config.plan !== null) {
    const customerPlanRank = PLAN_RANK[config.plan] ?? -1;
    const planGrantsFeature = plans.some(plan => PLAN_RANK[plan] <= customerPlanRank);
    if (planGrantsFeature) {
      return true;
    }
  }
  
  const addonGrantsFeature = addons.some(addon => config.addons[addon]);
  if (addonGrantsFeature) {
    return true;
  }
  
  if (config.plan === null) {
    return true;
  }
  
  return false;
}

export function isFeatureAvailable(featureKey, config) {
  if (config.plan === null && !Object.values(config.addons).some(v => v)) {
    return true;
  }
  
  const feature = FEATURES[featureKey];
  if (!feature) return true;
  
  const { plans, addons } = feature;
  
  if (config.plan !== null && plans.length > 0) {
    const customerPlanRank = PLAN_RANK[config.plan] ?? -1;
    if (plans.some(plan => PLAN_RANK[plan] <= customerPlanRank)) {
      return true;
    }
  }
  
  if (addons.some(addon => config.addons[addon])) {
    return true;
  }
  
  return false;
}

export function getAvailableFeatures(config) {
  const available = new Set();
  for (const featureKey of Object.keys(FEATURES)) {
    if (hasFeature(featureKey, config)) {
      available.add(featureKey);
    }
  }
  return available;
}

export function getFeatureRequirements(featureKey) {
  const feature = FEATURES[featureKey];
  if (!feature) return null;
  
  const { plans, addons } = feature;
  const requirements = [];
  
  if (plans.length > 0) {
    const minPlan = plans.reduce((min, plan) => 
      PLAN_RANK[plan] < PLAN_RANK[min] ? plan : min, plans[0]);
    const planObj = PLANS.find(p => p.key === minPlan);
    requirements.push(`${planObj?.label || minPlan}+ plan`);
  }
  
  if (addons.length > 0) {
    const addonNames = addons.map(a => 
      ADDONS.find(addon => addon.key === a)?.label || a);
    requirements.push(addonNames.join(' or ') + ' add-on');
  }
  
  return requirements.length > 0 ? requirements.join(' OR ') : 'All plans';
}

export function filterByLicense(scenarios, config) {
  if (config.plan === null && !Object.values(config.addons).some(v => v)) {
    return scenarios;
  }
  
  return scenarios.filter(scenario => {
    const requiredFeatures = scenario.required_features || [];
    return requiredFeatures.every(featureKey => hasFeature(featureKey, config));
  });
}

export function getScenarioLicenseInfo(scenario) {
  const requiredFeatures = scenario.required_features || [];
  
  let minimumPlan = null;
  let requiredAddons = new Set();
  
  for (const featureKey of requiredFeatures) {
    const feature = FEATURES[featureKey];
    if (!feature) continue;
    
    const { plans, addons } = feature;
    
    if (plans.length > 0) {
      const minPlanForFeature = plans.reduce((min, plan) => 
        PLAN_RANK[plan] < PLAN_RANK[min] ? plan : min, plans[0]);
      if (minimumPlan === null || PLAN_RANK[minPlanForFeature] > PLAN_RANK[minimumPlan]) {
        minimumPlan = minPlanForFeature;
      }
    }
    
    if (plans.length === 0 && addons.length > 0) {
      addons.forEach(a => requiredAddons.add(a));
    }
  }
  
  return {
    minimumPlan: minimumPlan || 'professional',
    requiredAddons: Array.from(requiredAddons),
    requiredFeatures
  };
}

export function getPlanDisplay(planKey) {
  const plan = PLANS.find(p => p.key === planKey);
  return plan || { key: null, label: 'Unknown', color: 'gray' };
}
