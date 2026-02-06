#!/usr/bin/env python3
"""
ServiceNow PDI Keep-Alive Script

Prevents your ServiceNow Personal Developer Instance from being reclaimed
due to 10-day inactivity by making periodic API calls.

Setup:
1. Set environment variables:
   - SNOW_INSTANCE: Your instance name (e.g., dev12345)
   - SNOW_USER: Your username
   - SNOW_PASSWORD: Your password

2. Run via cron (every 3 days):
   0 9 */3 * * /path/to/snow_keepalive.py

3. Or use the GitHub Action workflow (snow_keepalive.yml)
"""

import os
import sys
import requests
from datetime import datetime

def keep_alive():
    instance = os.environ.get('SNOW_INSTANCE')
    user = os.environ.get('SNOW_USER')
    password = os.environ.get('SNOW_PASSWORD')
    
    if not all([instance, user, password]):
        print("Error: Set SNOW_INSTANCE, SNOW_USER, SNOW_PASSWORD env vars")
        sys.exit(1)
    
    base_url = f"https://{instance}.service-now.com"
    
    # Method 1: Simple API call to get sys_user (lightweight)
    try:
        response = requests.get(
            f"{base_url}/api/now/table/sys_user",
            auth=(user, password),
            headers={"Accept": "application/json"},
            params={"sysparm_limit": 1}
        )
        
        if response.status_code == 200:
            print(f"[{datetime.now()}] SUCCESS: Instance {instance} is active")
            return True
        elif response.status_code == 401:
            print(f"[{datetime.now()}] ERROR: Authentication failed")
        elif response.status_code == 503:
            print(f"[{datetime.now()}] WARNING: Instance hibernating, waking up...")
            # Try again after wake-up
            import time
            time.sleep(60)
            return keep_alive()
        else:
            print(f"[{datetime.now()}] ERROR: Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ERROR: {e}")
    
    return False

if __name__ == "__main__":
    success = keep_alive()
    sys.exit(0 if success else 1)
