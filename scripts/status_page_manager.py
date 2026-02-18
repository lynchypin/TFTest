#!/usr/bin/env python3
"""
status_page_manager.py - PagerDuty Status Page Management via REST API

This script manages Status Pages for the Los Andes demo environment.
Status Pages are not yet supported by the Terraform provider, so we use the REST API.

Usage:
    export PAGERDUTY_API_KEY="your-api-key"
    python3 status_page_manager.py create     # Create status page structure
    python3 status_page_manager.py update     # Update component statuses
    python3 status_page_manager.py incident   # Post an incident to the status page
    python3 status_page_manager.py list       # List existing status pages

Requirements:
    pip install requests
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime, timezone

# Configuration
API_KEY = os.environ.get("PAGERDUTY_API_KEY")
BASE_URL = "https://api.pagerduty.com"

# Status Page Configuration
STATUS_PAGE_CONFIG = {
    "name": "Los Andes Platform Status",
    "subdomain": "losandes-status",  # Will be https://losandes-status.pagerduty.io
    "description": "Real-time status for Los Andes e-commerce platform services",
    "contact_email": "status@losandes-demo.com",
    "public_page": True,
    "component_groups": [
        {
            "name": "Core Platform",
            "description": "Infrastructure and platform services",
            "components": [
                {"name": "Kubernetes Cluster", "description": "Container orchestration platform"},
                {"name": "Networking", "description": "Load balancers, CDN, and DNS"},
                {"name": "Database Infrastructure", "description": "PostgreSQL and Redis clusters"},
            ]
        },
        {
            "name": "Application Services",
            "description": "Customer-facing application services",
            "components": [
                {"name": "Orders API", "description": "Order processing and management"},
                {"name": "Checkout", "description": "Shopping cart and checkout flow"},
                {"name": "Identity & Authentication", "description": "User login and authentication"},
                {"name": "Inventory", "description": "Product availability and stock"},
            ]
        },
        {
            "name": "Data Services",
            "description": "Data processing and analytics",
            "components": [
                {"name": "Streaming Platform", "description": "Kafka event streaming"},
                {"name": "Analytics Pipeline", "description": "Data warehouse and ETL"},
            ]
        },
        {
            "name": "Payment Services",
            "description": "Payment processing",
            "components": [
                {"name": "Payment Gateway", "description": "Credit card and payment processing"},
                {"name": "Payment Ops", "description": "Payment operations and reconciliation"},
            ]
        }
    ]
}


def get_headers() -> Dict:
    """Get API headers with authentication."""
    if not API_KEY:
        print("Error: PAGERDUTY_API_KEY environment variable not set")
        sys.exit(1)
    return {
        "Authorization": f"Token token={API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pagerduty+json;version=2"
    }


def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make an API request to PagerDuty."""
    url = f"{BASE_URL}{endpoint}"
    headers = get_headers()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.text else {}
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        raise


def list_status_pages() -> List[Dict]:
    """List all status pages in the account."""
    print("\n=== Listing Status Pages ===\n")
    result = api_request("GET", "/status_pages")
    pages = result.get("status_pages", [])
    
    if not pages:
        print("No status pages found.")
        return []
    
    for page in pages:
        print(f"  ID: {page['id']}")
        print(f"  Name: {page['name']}")
        print(f"  URL: {page.get('url', 'N/A')}")
        print(f"  Status: {page.get('status', 'N/A')}")
        print("")
    
    return pages


def get_status_page(page_id: str) -> Dict:
    """Get details of a specific status page."""
    result = api_request("GET", f"/status_pages/{page_id}")
    return result.get("status_page", {})


def create_status_page() -> str:
    """Create the status page structure."""
    print("\n=== Creating Status Page ===\n")
    
    # Create the status page
    page_data = {
        "status_page": {
            "name": STATUS_PAGE_CONFIG["name"],
            "subdomain": STATUS_PAGE_CONFIG["subdomain"],
            "description": STATUS_PAGE_CONFIG["description"],
            "contact_email": STATUS_PAGE_CONFIG["contact_email"],
            "public_page": STATUS_PAGE_CONFIG["public_page"]
        }
    }
    
    print(f"Creating status page: {STATUS_PAGE_CONFIG['name']}")
    result = api_request("POST", "/status_pages", page_data)
    page_id = result["status_page"]["id"]
    print(f"  Created with ID: {page_id}")
    
    # Create component groups and components
    for group_config in STATUS_PAGE_CONFIG["component_groups"]:
        print(f"\nCreating component group: {group_config['name']}")
        
        group_data = {
            "component_group": {
                "name": group_config["name"],
                "description": group_config.get("description", "")
            }
        }
        group_result = api_request("POST", f"/status_pages/{page_id}/component_groups", group_data)
        group_id = group_result["component_group"]["id"]
        print(f"  Created group with ID: {group_id}")
        
        # Create components in this group
        for comp_config in group_config["components"]:
            print(f"  Creating component: {comp_config['name']}")
            
            comp_data = {
                "component": {
                    "name": comp_config["name"],
                    "description": comp_config.get("description", ""),
                    "component_group_id": group_id,
                    "status": "operational"
                }
            }
            comp_result = api_request("POST", f"/status_pages/{page_id}/components", comp_data)
            print(f"    Created with ID: {comp_result['component']['id']}")
    
    print(f"\n✓ Status page created successfully!")
    print(f"  Public URL: https://{STATUS_PAGE_CONFIG['subdomain']}.pagerduty.io")
    
    return page_id


def update_component_status(page_id: str, component_name: str, status: str, message: Optional[str] = None):
    """Update a component's status.
    
    Status values: operational, degraded_performance, partial_outage, major_outage, under_maintenance
    """
    print(f"\n=== Updating Component Status ===\n")
    
    # Get components
    result = api_request("GET", f"/status_pages/{page_id}/components")
    components = result.get("components", [])
    
    # Find the component by name
    component = next((c for c in components if c["name"] == component_name), None)
    if not component:
        print(f"Component '{component_name}' not found")
        return
    
    # Update the component
    update_data = {
        "component": {
            "status": status
        }
    }
    
    api_request("PUT", f"/status_pages/{page_id}/components/{component['id']}", update_data)
    print(f"✓ Updated '{component_name}' to '{status}'")
    
    if message:
        # Post a status update
        post_status_update(page_id, f"{component_name}: {message}")


def post_status_update(page_id: str, message: str):
    """Post a status update to the status page."""
    update_data = {
        "status_update": {
            "message": message,
            "status": "investigating"
        }
    }

    api_request("POST", f"/status_pages/{page_id}/status_updates", update_data)
    print(f"✓ Posted status update: {message}")


def get_status_page_statuses(page_id: str) -> List[Dict]:
    """Fetch available statuses from the status page API."""
    result = api_request("GET", f"/status_pages/{page_id}/statuses")
    return result.get("statuses", [])


def get_status_page_severities(page_id: str) -> List[Dict]:
    """Fetch available severities from the status page API."""
    result = api_request("GET", f"/status_pages/{page_id}/severities")
    return result.get("severities", [])


def get_status_page_impacts(page_id: str) -> List[Dict]:
    """Fetch available impacts from the status page API."""
    result = api_request("GET", f"/status_pages/{page_id}/impacts")
    return result.get("impacts", [])


def get_status_page_services(page_id: str) -> List[Dict]:
    """Fetch available services from the status page API."""
    result = api_request("GET", f"/status_pages/{page_id}/services")
    return result.get("services", [])


def find_by_name(items: List[Dict], name: str) -> Optional[Dict]:
    """Find an item in a list by name (case-insensitive)."""
    return next((i for i in items if i.get("name", "").lower() == name.lower()), None)


def create_incident(page_id: str, title: str, message: str, components: List[str], impact: str = "minor"):
    """Create an incident on the status page.

    Impact values: none, minor, major, critical
    Status values: investigating, identified, monitoring, resolved
    Severity values: minor, major, critical
    """
    print(f"\n=== Creating Status Page Incident ===\n")

    statuses = get_status_page_statuses(page_id)
    severities = get_status_page_severities(page_id)
    impacts = get_status_page_impacts(page_id)
    services = get_status_page_services(page_id)

    print(f"  Available statuses: {[s.get('name') for s in statuses]}")
    print(f"  Available severities: {[s.get('name') for s in severities]}")
    print(f"  Available impacts: {[s.get('name') for s in impacts]}")
    print(f"  Available services: {[s.get('name') for s in services]}")

    if not statuses or not severities or not impacts:
        raise ValueError(
            "Status page is missing configured statuses, severities, or impacts. "
            "Ensure the status page is fully set up in the PagerDuty UI or via "
            "'python3 scripts/status_page_manager.py create' before creating incidents."
        )

    status_obj = find_by_name(statuses, "Investigating")
    if not status_obj:
        status_obj = statuses[0] if statuses else None
    if not status_obj:
        raise ValueError("No statuses available on this status page")

    severity_obj = find_by_name(severities, impact)
    if not severity_obj:
        severity_obj = severities[0] if severities else None
    if not severity_obj:
        raise ValueError("No severities available on this status page")

    impact_obj = find_by_name(impacts, impact)
    if not impact_obj:
        impact_obj = impacts[0] if impacts else None
    if not impact_obj:
        raise ValueError("No impacts available on this status page")

    impacted_services = []
    for comp_name in components:
        svc = find_by_name(services, comp_name)
        if svc:
            impacted_services.append({
                "id": svc["id"],
                "type": "status_page_service"
            })
        else:
            print(f"Warning: Service '{comp_name}' not found on status page")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    post_data = {
        "post": {
            "type": "status_page_post",
            "post_type": "incident",
            "title": title,
            "status": {
                "id": status_obj["id"],
                "type": "status_page_status"
            },
            "severity": {
                "id": severity_obj["id"],
                "type": "status_page_severity"
            },
            "impact": {
                "id": impact_obj["id"],
                "type": "status_page_impact"
            },
            "impacted_services": impacted_services,
            "updates": [
                {
                    "type": "status_page_post_update",
                    "body": message,
                    "status": {
                        "id": status_obj["id"],
                        "type": "status_page_status"
                    },
                    "severity": {
                        "id": severity_obj["id"],
                        "type": "status_page_severity"
                    },
                    "impacted_services": impacted_services,
                    "update_frequency_ms": 1800000,
                    "notify_subscribers": True,
                    "reported_at": now
                }
            ]
        }
    }

    print(f"  Payload: {json.dumps(post_data, indent=2)}")

    result = api_request("POST", f"/status_pages/{page_id}/posts", post_data)
    post_id = result["post"]["id"]

    print(f"✓ Created incident: {title}")
    print(f"  ID: {post_id}")
    print(f"  Impact: {impact}")
    print(f"  Affected services: {', '.join(components)}")

    return post_id


def update_incident(page_id: str, post_id: str, status: str, message: str):
    """Update an existing incident post.

    Status values: investigating, identified, monitoring, resolved
    """
    print(f"\n=== Updating Incident ===\n")

    statuses = get_status_page_statuses(page_id)
    severities = get_status_page_severities(page_id)

    status_obj = find_by_name(statuses, status)
    if not status_obj:
        status_obj = statuses[0] if statuses else None
    if not status_obj:
        raise ValueError(f"Status '{status}' not found on this status page")

    severity_obj = severities[0] if severities else None

    now = datetime.now(timezone.utc).isoformat()

    update_data = {
        "post_update": {
            "body": message,
            "status": {
                "id": status_obj["id"],
                "type": "status_page_status"
            },
            "severity": {
                "id": severity_obj["id"],
                "type": "status_page_severity"
            },
            "impacted_services": [],
            "update_frequency_ms": 1800000,
            "notify_subscribers": True,
            "reported_at": now,
            "type": "status_page_post_update"
        }
    }

    api_request("POST", f"/status_pages/{page_id}/posts/{post_id}/post_updates", update_data)
    print(f"✓ Updated incident {post_id} to '{status}'")


def demo_incident_flow(page_id: str):
    """Demonstrate a full incident lifecycle on the status page."""
    print("\n" + "="*60)
    print("DEMO: Status Page Incident Flow")
    print("="*60)
    
    # 1. Create an incident
    incident_id = create_incident(
        page_id,
        title="Elevated Error Rates - Checkout Service",
        message="We are investigating elevated error rates affecting the checkout flow. Some users may experience failures when completing purchases.",
        components=["Checkout", "Payment Gateway"],
        impact="major"
    )
    
    input("\nPress Enter to update incident to 'identified'...")
    
    # 2. Identify the issue
    update_incident(
        page_id,
        incident_id,
        status="identified",
        message="We have identified the root cause as a connection pool exhaustion in the payment gateway. Our team is implementing a fix."
    )
    
    # Update component statuses
    update_component_status(page_id, "Checkout", "degraded_performance")
    update_component_status(page_id, "Payment Gateway", "partial_outage")
    
    input("\nPress Enter to update incident to 'monitoring'...")
    
    # 3. Fix deployed, monitoring
    update_incident(
        page_id,
        incident_id,
        status="monitoring",
        message="A fix has been deployed and we are monitoring the results. Error rates are returning to normal levels."
    )
    
    update_component_status(page_id, "Payment Gateway", "degraded_performance")
    
    input("\nPress Enter to resolve incident...")
    
    # 4. Resolve
    update_incident(
        page_id,
        incident_id,
        status="resolved",
        message="The incident has been resolved. All services are operating normally. A post-incident review will be conducted."
    )
    
    update_component_status(page_id, "Checkout", "operational")
    update_component_status(page_id, "Payment Gateway", "operational")
    
    print("\n✓ Demo incident flow completed!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_status_pages()
    
    elif command == "create":
        create_status_page()
    
    elif command == "update":
        if len(sys.argv) < 5:
            print("Usage: status_page_manager.py update <page_id> <component_name> <status>")
            print("Status: operational, degraded_performance, partial_outage, major_outage, under_maintenance")
            sys.exit(1)
        page_id = sys.argv[2]
        component = sys.argv[3]
        status = sys.argv[4]
        update_component_status(page_id, component, status)
    
    elif command == "incident":
        if len(sys.argv) < 3:
            print("Usage: status_page_manager.py incident <page_id>")
            print("This will run a demo incident flow.")
            sys.exit(1)
        page_id = sys.argv[2]
        demo_incident_flow(page_id)
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
