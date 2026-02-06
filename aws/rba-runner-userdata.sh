#!/bin/bash
set -ex

exec > /var/log/rba-runner-setup.log 2>&1

echo "Starting RBA Runner setup..."

yum update -y

# ==============================================================================
# IMPORTANT: DO NOT USE DOCKER WITH ENVIRONMENT VARIABLES FOR MANUAL REPLICAS
# ==============================================================================
# The Docker container approach with RUNNER_RUNDECK_* environment variables
# does NOT work for manual replica types. See docs/setup/RBA_RUNNER_SETUP.md
# for full details.
#
# WHAT DOESN'T WORK:
# docker run -d \
#   --name runner \
#   -e RUNNER_RUNDECK_SERVER_TOKEN="<token>" \
#   -e RUNNER_RUNDECK_SERVER_URL="https://api.runbook.pagerduty.cloud" \
#   -e RUNNER_RUNDECK_CLIENT_ID="<runner-id-or-replica-id>" \
#   rundeckpro/runner:5.19.0
#
# WHAT WORKS:
# Download the custom JAR using the downloadTk from replica creation and run directly
# ==============================================================================

# Install Java 17 (required for runner JAR)
yum install -y java-17-amazon-corretto-headless

# Install AWS CLI (usually pre-installed on Amazon Linux 2)
yum install -y awscli

# Create runner directory
mkdir -p /opt/rba-runner
mkdir -p /usr/bin/runner/logs

# Download the custom runner JAR from S3
# NOTE: The runner JAR must be downloaded using the downloadTk token from replica creation
# and uploaded to S3 beforehand. See docs/setup/RBA_RUNNER_SETUP.md
S3_BUCKET="pagerduty-demo-runner-bucket"
aws s3 cp s3://${S3_BUCKET}/runner.jar /opt/runner.jar

# Verify JAR was downloaded
if [ ! -f /opt/runner.jar ]; then
    echo "ERROR: Failed to download runner.jar from S3"
    exit 1
fi

# Create systemd service for the runner
cat > /etc/systemd/system/pagerduty-runner.service << 'EOF'
[Unit]
Description=PagerDuty RBA Runner
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/java -jar /opt/runner.jar
Restart=always
RestartSec=10
StandardOutput=append:/var/log/runner-stdout.log
StandardError=append:/var/log/runner-stderr.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
systemctl daemon-reload
systemctl enable pagerduty-runner
systemctl start pagerduty-runner

# Wait for startup and verify
sleep 15

# Check if runner is running
if systemctl is-active --quiet pagerduty-runner; then
    echo "RBA Runner started successfully!"
    systemctl status pagerduty-runner
else
    echo "ERROR: RBA Runner failed to start"
    journalctl -u pagerduty-runner --no-pager -n 50
    exit 1
fi

# Show connection status
echo "Checking network connections..."
netstat -an | grep ESTABLISHED | grep 443 || echo "No HTTPS connections yet"

echo "RBA Runner setup complete!"
echo "Logs available at:"
echo "  - /var/log/runner-stdout.log"
echo "  - /var/log/runner-stderr.log"
echo "  - /usr/bin/runner/logs/runner.log"
echo "  - /usr/bin/runner/logs/operations.log"
