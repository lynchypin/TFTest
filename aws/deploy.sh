#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Demo Simulator Lambda Deployment ==="
echo ""

if ! command -v terraform &> /dev/null; then
    echo "Error: terraform is not installed"
    exit 1
fi

echo "Copying shared module to Lambda directories..."
LAMBDA_DIRS=("lambda-orchestrator" "lambda-lifecycle" "lambda-metrics" "lambda-notifier" "lambda-reset" "lambda-user-activity" "lambda-health-check" "lambda-demo-controller")
for dir in "${LAMBDA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir/shared"
        cp -r shared "$dir/shared"
        echo "  Copied shared/ to $dir/"
    fi
done

echo "Copying scenarios.json to demo-controller..."
if [ -f "../docs/demo-scenarios/src/data/scenarios.json" ]; then
    cp "../docs/demo-scenarios/src/data/scenarios.json" "lambda-demo-controller/scenarios.json"
    echo "  Copied scenarios.json to lambda-demo-controller/"
fi

echo "Installing Python dependencies for Lambda functions..."
LAMBDAS_WITH_DEPS=("lambda-orchestrator" "lambda-lifecycle" "lambda-metrics" "lambda-demo-controller")
for dir in "${LAMBDAS_WITH_DEPS[@]}"; do
    if [ -d "$dir" ]; then
        if [ -f "$dir/requirements.txt" ]; then
            echo "  Installing deps for $dir..."
            pip install -r "$dir/requirements.txt" -t "$dir" --quiet --upgrade
        elif [ -f "lambda-orchestrator/requirements.txt" ]; then
            echo "  Installing shared deps for $dir..."
            pip install -r lambda-orchestrator/requirements.txt -t "$dir" --quiet --upgrade
        fi
    fi
done

echo "Initializing Terraform..."
terraform init -upgrade

echo ""
echo "Planning deployment..."
terraform plan -out=tfplan

echo ""
read -p "Apply this plan? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying..."
    terraform apply tfplan
    
    echo ""
    echo "=== Deployment Complete ==="
    echo ""
    terraform output
else
    echo "Deployment cancelled"
fi
