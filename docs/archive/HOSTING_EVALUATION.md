# Hosting Evaluation: Oracle Cloud Free Tier vs AWS

## Executive Summary

**Recommendation**: Oracle Cloud Free Tier is a **viable and cost-effective alternative** for hosting the Demo Orchestrator, especially for low-to-moderate usage. However, AWS provides better integration with EventBridge Scheduler (critical for timed actions) and a more mature serverless ecosystem.

**Hybrid Approach Recommended**: Use Oracle VPS for the always-on orchestrator with a cron-based scheduler, keeping AWS only for specific services if needed.

---

## Comparison Matrix

| Feature | Oracle Cloud Free Tier | AWS (Lambda + Services) |
|---------|----------------------|-------------------------|
| **Compute** | 2 AMD VMs (1 GB RAM each) or 4 ARM VMs (24 GB total) FOREVER FREE | Lambda: 1M requests/month free, then $0.20/M |
| **Always-On** | ✅ Yes, VPS runs 24/7 | ❌ Lambda is event-driven only |
| **Cost (Ongoing)** | $0 (within limits) | ~$5-20/month for moderate usage |
| **Scheduler** | Cron jobs on VPS | EventBridge Scheduler ($1/M schedules) |
| **Database** | 2 Autonomous DBs (20GB each) FREE | DynamoDB: 25GB free, then $1.25/GB/month |
| **API Gateway** | Nginx/Caddy on VPS (free) | API Gateway: $3.50/M requests |
| **Maintenance** | Manual OS updates, security patches | Fully managed |
| **Scaling** | Limited to VM specs | Auto-scales |
| **Complexity** | Higher (manage server) | Lower (serverless) |
| **Vendor Lock-in** | Low (standard Linux) | Higher (AWS-specific services) |

---

## Oracle Cloud Free Tier Details

### What's Included (Always Free)

**Compute**:
- 2 AMD Compute VMs (1/8 OCPU, 1 GB RAM each)
- OR 4 ARM Ampere A1 VMs (4 OCPUs, 24 GB RAM total)
- 200 GB total boot volume storage

**Database**:
- 2 Oracle Autonomous Databases (20 GB each)
- OR use VM disk for SQLite/PostgreSQL

**Networking**:
- 10 TB outbound data transfer/month
- Load Balancer (10 Mbps)
- VCN, Subnets, Security Lists

**Storage**:
- 200 GB block volume storage
- 10 GB object storage
- 10 GB archive storage

### What You'd Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                    ORACLE CLOUD VPS                         │
│                    (ARM A1: 2 OCPU, 12GB RAM)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Nginx/Caddy   │  │   Python App    │                  │
│  │   (Reverse      │  │   (FastAPI/     │                  │
│  │    Proxy)       │  │    Flask)       │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│           └─────────┬──────────┘                            │
│                     │                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SQLite / PostgreSQL                     │   │
│  │              (Demo State Storage)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Cron Jobs (systemd timers)              │   │
│  │              - Process scheduled actions             │   │
│  │              - Cleanup expired demos                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Let's Encrypt (Certbot)                 │   │
│  │              - HTTPS for webhooks                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Comparison

### Option A: Pure Oracle Cloud

```
PagerDuty Webhooks → Oracle VPS (Nginx) → Python App → SQLite
                                              │
                                              ├── Process webhook
                                              ├── Store state
                                              └── Insert into scheduler queue
                                              
Cron (every 10s) → Python App → Check queue → Execute actions → PagerDuty API
```

**Pros**:
- $0 cost
- Simple, all-in-one
- No vendor lock-in

**Cons**:
- 10-second granularity for scheduled actions (cron limitation)
- Manual server management
- Single point of failure (unless you set up HA)

### Option B: Pure AWS (Current Design)

```
PagerDuty Webhooks → API Gateway → Lambda → DynamoDB
                                      │
                                      └── Create EventBridge Schedule
                                      
EventBridge Schedule → Lambda → Execute action → PagerDuty API
```

**Pros**:
- Sub-second scheduling precision
- Fully managed
- Auto-scaling

**Cons**:
- ~$5-20/month ongoing cost
- AWS lock-in
- More complex (multiple services)

### Option C: Hybrid (Recommended)

```
PagerDuty Webhooks → Oracle VPS → Python App → PostgreSQL
                                      │
                                      ├── Process webhook
                                      ├── Store state  
                                      └── Insert scheduled action (timestamp)
                                      
Cron (every 5s) → Python Worker → Query due actions → Execute → PagerDuty API
```

**Pros**:
- $0 cost
- 5-second granularity (acceptable for demos)
- Simple deployment
- Easy to modify

**Cons**:
- Requires server management
- Need to handle worker failures

---

## Implementation on Oracle Cloud

### Step 1: Create VM Instance

```bash
# In Oracle Cloud Console:
# Compute → Instances → Create Instance
# Shape: VM.Standard.A1.Flex (ARM)
# OCPUs: 2, Memory: 12 GB
# Image: Oracle Linux 8 or Ubuntu 22.04
# Add SSH key
```

### Step 2: Install Dependencies

```bash
# Connect to VM
ssh -i <key> opc@<public-ip>

# Update system
sudo dnf update -y  # Oracle Linux
# or
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python
sudo dnf install python3.11 python3.11-pip -y
# or
sudo apt install python3.11 python3.11-venv -y

# Install PostgreSQL (optional, SQLite works too)
sudo dnf install postgresql-server postgresql -y
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

# Install Nginx
sudo dnf install nginx -y
sudo systemctl enable --now nginx

# Install Certbot for HTTPS
sudo dnf install certbot python3-certbot-nginx -y
```

### Step 3: Deploy Application

```bash
# Clone repository
git clone <repo-url> /opt/demo-orchestrator
cd /opt/demo-orchestrator

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn requests psycopg2-binary

# Create systemd service
sudo tee /etc/systemd/system/demo-orchestrator.service << EOF
[Unit]
Description=PagerDuty Demo Orchestrator
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/opt/demo-orchestrator
Environment="PAGERDUTY_TOKEN=xxx"
Environment="SLACK_BOT_TOKEN=xxx"
ExecStart=/opt/demo-orchestrator/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now demo-orchestrator
```

### Step 4: Configure Nginx

```nginx
# /etc/nginx/conf.d/demo-orchestrator.conf
server {
    listen 80;
    server_name demo.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Step 5: Enable HTTPS

```bash
sudo certbot --nginx -d demo.yourdomain.com
```

### Step 6: Create Scheduler Worker

```python
# /opt/demo-orchestrator/worker.py
import time
import sqlite3
from datetime import datetime, timezone
from app import execute_scheduled_action

DB_PATH = '/opt/demo-orchestrator/demo_state.db'

def process_due_actions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute('''
        SELECT id, incident_id, action, user_id 
        FROM scheduled_actions 
        WHERE execute_at <= ? AND executed = 0
    ''', (now,))
    
    for row in cursor.fetchall():
        action_id, incident_id, action, user_id = row
        try:
            execute_scheduled_action(incident_id, action, user_id)
            cursor.execute('UPDATE scheduled_actions SET executed = 1 WHERE id = ?', (action_id,))
        except Exception as e:
            print(f"Error executing action {action_id}: {e}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    while True:
        process_due_actions()
        time.sleep(5)  # Check every 5 seconds
```

### Step 7: Create Worker Service

```bash
sudo tee /etc/systemd/system/demo-worker.service << EOF
[Unit]
Description=Demo Orchestrator Scheduler Worker
After=demo-orchestrator.service

[Service]
Type=simple
User=opc
WorkingDirectory=/opt/demo-orchestrator
Environment="PAGERDUTY_TOKEN=xxx"
Environment="SLACK_BOT_TOKEN=xxx"
ExecStart=/opt/demo-orchestrator/venv/bin/python worker.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now demo-worker
```

---

## Cost Analysis (Monthly)

### Oracle Cloud Free Tier

| Component | Cost |
|-----------|------|
| ARM VM (2 OCPU, 12GB) | $0 |
| Boot Volume (50GB) | $0 |
| PostgreSQL (on VM) | $0 |
| Outbound Data (<10TB) | $0 |
| **Total** | **$0** |

### AWS (Current Design)

| Component | Estimated Usage | Cost |
|-----------|-----------------|------|
| Lambda | 50K invocations | $0 (free tier) |
| API Gateway | 50K requests | $0.18 |
| DynamoDB | 1GB storage, 100K reads/writes | $0.25 |
| EventBridge Scheduler | 10K schedules | $0.01 |
| CloudWatch Logs | 5GB | $2.50 |
| **Total** | | **~$3-5/month** |

### AWS (Post-Free-Tier)

| Component | Estimated Usage | Cost |
|-----------|-----------------|------|
| Lambda | 100K invocations | $0.20 |
| API Gateway | 100K requests | $3.50 |
| DynamoDB | 5GB storage, 500K reads/writes | $5.00 |
| EventBridge Scheduler | 50K schedules | $0.05 |
| CloudWatch Logs | 10GB | $5.00 |
| **Total** | | **~$15-20/month** |

---

## Recommendation

### For Personal/Demo Use: **Oracle Cloud Free Tier**

- $0 ongoing cost
- Sufficient for demo purposes
- 5-second action granularity is acceptable
- Good learning experience managing a server

### For Production/Enterprise: **AWS**

- Better reliability guarantees
- Sub-second scheduling
- No server management
- Easier to scale

### Migration Path

Start with Oracle Cloud Free Tier. If you need:
- Sub-second scheduling → Migrate to AWS
- Higher reliability → Migrate to AWS
- Multi-region → Migrate to AWS

The application code (Python) remains largely the same; only the infrastructure layer changes.

---

## Quick Decision Guide

| If You... | Choose |
|-----------|--------|
| Want $0 cost | Oracle Cloud |
| Need sub-second timing | AWS |
| Prefer serverless | AWS |
| Want to learn server management | Oracle Cloud |
| Need high availability | AWS (or Oracle with HA setup) |
| Have existing AWS infrastructure | AWS |
| Want vendor flexibility | Oracle Cloud |

---

## Next Steps to Implement Oracle Cloud

1. Sign up for Oracle Cloud Free Tier (credit card required but won't be charged)
2. Create ARM VM instance
3. Refactor Lambda handler to FastAPI app
4. Deploy using steps above
5. Configure PagerDuty webhook to point to Oracle VM
6. Test end-to-end

Estimated setup time: 2-3 hours
