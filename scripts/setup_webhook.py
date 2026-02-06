#!/usr/bin/env python3
import os
import sys
import requests
import json

PAGERDUTY_API_URL = 'https://api.pagerduty.com'

WEBHOOK_EVENTS = [
    'incident.triggered',
    'incident.acknowledged',
    'incident.annotated',
    'incident.resolved',
    'incident.responder.added',
    'incident.responder.replied',
    'incident.priority_updated',
    'incident.reassigned',
    'incident.escalated',
    'incident.delegated',
    'incident.reopened',
]

def get_headers(token):
    return {
        'Authorization': f'Token token={token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def list_webhook_subscriptions(token):
    resp = requests.get(
        f'{PAGERDUTY_API_URL}/webhook_subscriptions',
        headers=get_headers(token),
        timeout=30
    )
    if resp.ok:
        return resp.json().get('webhook_subscriptions', [])
    print(f"Error listing webhooks: {resp.status_code} - {resp.text}")
    return []

def create_webhook_subscription(token, url, description="Demo Orchestrator Webhook"):
    payload = {
        'webhook_subscription': {
            'delivery_method': {
                'type': 'http_delivery_method',
                'url': url
            },
            'description': description,
            'events': WEBHOOK_EVENTS,
            'filter': {
                'type': 'account_reference'
            },
            'type': 'webhook_subscription'
        }
    }
    
    resp = requests.post(
        f'{PAGERDUTY_API_URL}/webhook_subscriptions',
        headers=get_headers(token),
        json=payload,
        timeout=30
    )
    
    if resp.ok:
        data = resp.json()
        webhook = data.get('webhook_subscription', {})
        print(f"Created webhook subscription: {webhook.get('id')}")
        print(f"  URL: {url}")
        print(f"  Events: {len(WEBHOOK_EVENTS)} subscribed")
        if webhook.get('secret'):
            print(f"  Secret (save this!): {webhook.get('secret')}")
        return webhook
    else:
        print(f"Error creating webhook: {resp.status_code} - {resp.text}")
        return None

def delete_webhook_subscription(token, webhook_id):
    resp = requests.delete(
        f'{PAGERDUTY_API_URL}/webhook_subscriptions/{webhook_id}',
        headers=get_headers(token),
        timeout=30
    )
    if resp.ok:
        print(f"Deleted webhook subscription: {webhook_id}")
        return True
    print(f"Error deleting webhook: {resp.status_code} - {resp.text}")
    return False

def main():
    token = os.environ.get('PAGERDUTY_TOKEN') or os.environ.get('PAGERDUTY_ADMIN_TOKEN')
    
    if not token:
        print("Error: PAGERDUTY_TOKEN or PAGERDUTY_ADMIN_TOKEN environment variable required")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_webhook.py list")
        print("  python setup_webhook.py create <lambda_url>")
        print("  python setup_webhook.py delete <webhook_id>")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == 'list':
        webhooks = list_webhook_subscriptions(token)
        print(f"\nFound {len(webhooks)} webhook subscriptions:\n")
        for wh in webhooks:
            print(f"  ID: {wh.get('id')}")
            print(f"  Description: {wh.get('description')}")
            print(f"  URL: {wh.get('delivery_method', {}).get('url')}")
            print(f"  Events: {len(wh.get('events', []))}")
            print(f"  Active: {wh.get('active')}")
            print()
    
    elif action == 'create':
        if len(sys.argv) < 3:
            print("Error: Lambda URL required")
            print("Usage: python setup_webhook.py create <lambda_url>")
            sys.exit(1)
        
        lambda_url = sys.argv[2]
        if not lambda_url.startswith('http'):
            print("Error: URL must start with http:// or https://")
            sys.exit(1)
        
        webhook_url = lambda_url.rstrip('/') + '/webhook'
        
        existing = list_webhook_subscriptions(token)
        for wh in existing:
            if webhook_url in wh.get('delivery_method', {}).get('url', ''):
                print(f"Webhook already exists for this URL: {wh.get('id')}")
                print("Use 'delete' to remove it first if you want to recreate.")
                return
        
        create_webhook_subscription(token, webhook_url)
    
    elif action == 'delete':
        if len(sys.argv) < 3:
            print("Error: Webhook ID required")
            print("Usage: python setup_webhook.py delete <webhook_id>")
            sys.exit(1)
        
        webhook_id = sys.argv[2]
        delete_webhook_subscription(token, webhook_id)
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == '__main__':
    main()
