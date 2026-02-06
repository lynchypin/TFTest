#!/usr/bin/env python3
import os
import json
import requests

NEW_RELIC_API_KEY = os.environ.get('NEW_RELIC_API_KEY')
NEW_RELIC_ACCOUNT_ID = os.environ.get('NEW_RELIC_ACCOUNT_ID', '7637293')
PAGERDUTY_ROUTING_KEY = os.environ.get('PAGERDUTY_ROUTING_KEY')
GRAPHQL_ENDPOINT = 'https://api.newrelic.com/graphql'

if not NEW_RELIC_API_KEY:
    raise ValueError("NEW_RELIC_API_KEY environment variable required")
if not PAGERDUTY_ROUTING_KEY:
    raise ValueError("PAGERDUTY_ROUTING_KEY environment variable required")

headers = {
    'Content-Type': 'application/json',
    'API-Key': NEW_RELIC_API_KEY
}

def graphql_query(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json=payload)
    return response.json()

def create_alert_policy():
    query = '''
    mutation($accountId: Int!, $name: String!) {
        alertsPolicyCreate(accountId: $accountId, policy: {
            name: $name,
            incidentPreference: PER_CONDITION
        }) {
            id
            name
        }
    }
    '''
    result = graphql_query(query, {
        'accountId': NEW_RELIC_ACCOUNT_ID,
        'name': 'Demo Simulator Alerts'
    })
    print(f"Create policy result: {json.dumps(result, indent=2)}")
    if 'data' in result and result['data'].get('alertsPolicyCreate'):
        return result['data']['alertsPolicyCreate']['id']
    return None

def get_existing_destination():
    query = '''
    query($accountId: Int!) {
        actor {
            account(id: $accountId) {
                aiNotifications {
                    destinations {
                        entities {
                            id
                            name
                            type
                        }
                    }
                }
            }
        }
    }
    '''
    result = graphql_query(query, {'accountId': NEW_RELIC_ACCOUNT_ID})
    entities = result.get('data', {}).get('actor', {}).get('account', {}).get('aiNotifications', {}).get('destinations', {}).get('entities', [])
    for entity in entities:
        if entity.get('type') == 'PAGERDUTY_SERVICE_INTEGRATION':
            return entity['id'], entity['name']
    return None, None

def get_existing_channels():
    query = '''
    query($accountId: Int!) {
        actor {
            account(id: $accountId) {
                aiNotifications {
                    channels {
                        entities {
                            id
                            name
                            type
                            destinationId
                        }
                    }
                }
            }
        }
    }
    '''
    result = graphql_query(query, {'accountId': NEW_RELIC_ACCOUNT_ID})
    print(f"Channels: {json.dumps(result, indent=2)}")
    entities = result.get('data', {}).get('actor', {}).get('account', {}).get('aiNotifications', {}).get('channels', {}).get('entities', [])
    return entities

def create_notification_channel(destination_id, name):
    query = '''
    mutation($accountId: Int!, $destinationId: ID!, $name: String!) {
        aiNotificationsCreateChannel(accountId: $accountId, channel: {
            type: PAGERDUTY_SERVICE_INTEGRATION,
            name: $name,
            destinationId: $destinationId,
            product: IINT
        }) {
            channel {
                id
                name
            }
        }
    }
    '''
    result = graphql_query(query, {
        'accountId': NEW_RELIC_ACCOUNT_ID,
        'destinationId': destination_id,
        'name': name
    })
    print(f"Create channel result: {json.dumps(result, indent=2)}")
    if 'data' in result and result['data'].get('aiNotificationsCreateChannel'):
        channel = result['data']['aiNotificationsCreateChannel']
        if channel.get('channel'):
            return channel['channel']['id']
    return None

def get_existing_workflows():
    query = '''
    query($accountId: Int!) {
        actor {
            account(id: $accountId) {
                aiWorkflows {
                    workflows {
                        entities {
                            id
                            name
                            workflowEnabled
                        }
                    }
                }
            }
        }
    }
    '''
    result = graphql_query(query, {'accountId': NEW_RELIC_ACCOUNT_ID})
    print(f"Workflows: {json.dumps(result, indent=2)}")
    return result

def create_workflow(channel_id, policy_id):
    query = '''
    mutation($accountId: Int!, $channelId: ID!, $policyId: String!) {
        aiWorkflowsCreateWorkflow(accountId: $accountId, createWorkflowData: {
            name: "Demo Alert -> PagerDuty",
            workflowEnabled: true,
            destinationsEnabled: true,
            mutingRulesHandling: DONT_NOTIFY_FULLY_MUTED_ISSUES,
            issuesFilter: {
                name: "Demo Issues",
                predicates: [{
                    attribute: "labels.policyIds",
                    operator: EXACTLY_MATCHES,
                    values: [$policyId]
                }],
                type: FILTER
            },
            destinationConfigurations: [{
                channelId: $channelId
            }]
        }) {
            workflow {
                id
                name
            }
            errors {
                type
                description
            }
        }
    }
    '''
    result = graphql_query(query, {
        'accountId': NEW_RELIC_ACCOUNT_ID,
        'channelId': channel_id,
        'policyId': str(policy_id)
    })
    print(f"Create workflow result: {json.dumps(result, indent=2)}")
    return result

def create_nrql_condition(policy_id, name, nrql, threshold):
    query = '''
    mutation($accountId: Int!, $policyId: ID!, $name: String!, $nrql: String!, $threshold: Float!) {
        alertsNrqlConditionStaticCreate(
            accountId: $accountId, 
            policyId: $policyId, 
            condition: {
                name: $name,
                enabled: true,
                nrql: { query: $nrql },
                signal: {
                    aggregationWindow: 60,
                    aggregationMethod: EVENT_FLOW,
                    aggregationDelay: 120
                },
                terms: [{
                    threshold: $threshold,
                    thresholdOccurrences: AT_LEAST_ONCE,
                    thresholdDuration: 60,
                    operator: ABOVE,
                    priority: CRITICAL
                }],
                violationTimeLimitSeconds: 86400
            }
        ) {
            id
            name
        }
    }
    '''
    result = graphql_query(query, {
        'accountId': NEW_RELIC_ACCOUNT_ID,
        'policyId': str(policy_id),
        'name': name,
        'nrql': nrql,
        'threshold': float(threshold)
    })
    print(f"Create condition '{name}' result: {json.dumps(result, indent=2)}")
    return result

def get_existing_policies():
    query = '''
    query($accountId: Int!) {
        actor {
            account(id: $accountId) {
                alerts {
                    policiesSearch {
                        policies { 
                            id 
                            name 
                        }
                    }
                }
            }
        }
    }
    '''
    result = graphql_query(query, {'accountId': NEW_RELIC_ACCOUNT_ID})
    policies = result.get('data', {}).get('actor', {}).get('account', {}).get('alerts', {}).get('policiesSearch', {}).get('policies', [])
    return policies

def main():
    print("=" * 60)
    print("Setting up New Relic Alerts -> PagerDuty Integration")
    print("=" * 60)
    print(f"\nAccount ID: {NEW_RELIC_ACCOUNT_ID}")
    print(f"PagerDuty Routing Key: {PAGERDUTY_ROUTING_KEY[:8]}...")
    
    print("\n--- Step 1: Check existing PagerDuty destination ---")
    dest_id, dest_name = get_existing_destination()
    if dest_id:
        print(f"Found existing destination: {dest_name} ({dest_id})")
    else:
        print("No PagerDuty destination found - you need to configure this in the New Relic UI")
        print("Go to: Alerts & AI -> Destinations -> Add destination -> PagerDuty")
        return
    
    print("\n--- Step 2: Check existing channels ---")
    channels = get_existing_channels()
    channel_id = None
    for ch in channels:
        if ch.get('destinationId') == dest_id:
            channel_id = ch['id']
            print(f"Found existing channel: {ch['name']} ({ch['id']})")
            break
    
    if not channel_id:
        print("Creating notification channel...")
        channel_id = create_notification_channel(dest_id, 'Demo Simulator Channel')
    
    print("\n--- Step 3: Check/Create Alert Policy ---")
    policies = get_existing_policies()
    policy_id = None
    for p in policies:
        if 'Demo' in p['name']:
            policy_id = p['id']
            print(f"Found existing policy: {p['name']} ({p['id']})")
            break
    
    if not policy_id:
        print("Creating alert policy...")
        policy_id = create_alert_policy()
    
    print("\n--- Step 4: Check existing workflows ---")
    get_existing_workflows()
    
    if channel_id and policy_id:
        print("\n--- Step 5: Create Workflow (if needed) ---")
        create_workflow(channel_id, policy_id)
    
    if policy_id:
        print("\n--- Step 6: Create NRQL Alert Conditions ---")
        conditions = [
            ("[DEMO] High Custom Metric", "SELECT max(demo.api.response_time) FROM Metric WHERE demo IS TRUE", 500),
            ("[DEMO] Demo Error Rate", "SELECT count(*) FROM Log WHERE message LIKE '%error%' AND demo IS TRUE", 1),
        ]
        for name, nrql, threshold in conditions:
            create_nrql_condition(policy_id, name, nrql, threshold)
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
