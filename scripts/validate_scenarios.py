#!/usr/bin/env python3
import json
import sys

REQUIRED_FIELDS = ['id', 'name', 'description', 'severity', 'payload', 'target_service', 'features_demonstrated', 'tier']
VALID_SEVERITIES = ['info', 'warning', 'error', 'critical']
VALID_TIERS = ['FREE', 'PROFESSIONAL', 'BUSINESS', 'DIGITAL_OPERATIONS', 'AIOPS', 'AUTOMATION', 'INDUSTRY', 'AI_AGENTS', 'COMBINED']

TF_SERVICES = [
    "Platform - DBRE", "Data - Streaming", "Data - Analytics", "SecOps",
    "Corp IT", "Support", "Payments Ops", "App - Checkout Team",
    "App - Orders API Team", "App - Identity Team", "Platform - Networking",
    "Platform - Kubernetes/Platform",
    "App - Backend API", "Platform - Frontend", "Platform - Network",
    "Database - DBRE Team", "DevOps - CI/CD Platform",
    "Payment Processing - Gateway", "OT Operations - Factory Floor",
    "Clinical Systems - EMR", "Grid Operations Center",
    "Network Operations - Core", "Mining Operations - Equipment",
    "Quality Control - Manufacturing", "Retail Systems - POS",
    "Safety Operations",
]

VALIDATED_SCENARIOS = {'FREE-001', 'FREE-002', 'PRO-002', 'BUS-003', 'DIGOPS-001', 'AIOPS-001'}

def validate_scenario(s):
    issues = []
    sid = s.get('id', 'UNKNOWN')

    for field in REQUIRED_FIELDS:
        if field not in s or s[field] is None:
            if field == 'tier':
                issues.append(f"Missing tier")
            else:
                issues.append(f"Missing required field: {field}")

    sev = s.get('severity', '')
    if sev and sev not in VALID_SEVERITIES:
        issues.append(f"Invalid severity: {sev}")

    tier = s.get('tier', '')
    if tier and tier not in VALID_TIERS:
        issues.append(f"Invalid tier: {tier}")

    payload = s.get('payload', {})
    inner = payload.get('payload', payload)
    cd = inner.get('custom_details', {})
    pd_service = cd.get('pd_service', '')

    if not pd_service:
        issues.append("No pd_service in payload.custom_details")
    elif pd_service not in TF_SERVICES:
        issues.append(f"pd_service '{pd_service}' not in Terraform services")

    if not inner.get('summary'):
        issues.append("No summary in payload")

    if not inner.get('source'):
        issues.append("No source in payload")

    features = s.get('features_demonstrated', [])
    if not features:
        issues.append("No features_demonstrated")

    return issues

def main():
    with open('aws/lambda-demo-controller/scenarios.json') as f:
        data = json.load(f)

    scenarios = data.get('scenarios', [])
    print(f"Validating {len(scenarios)} scenarios...\n")

    by_tier = {}
    errors = 0
    warnings = 0
    ready = 0
    validated = 0

    for s in scenarios:
        sid = s.get('id', 'UNKNOWN')
        tier = s.get('tier', 'UNKNOWN')
        issues = validate_scenario(s)

        if tier not in by_tier:
            by_tier[tier] = {'ready': [], 'issues': [], 'validated': []}

        if sid in VALIDATED_SCENARIOS:
            by_tier[tier]['validated'].append(sid)
            validated += 1
        elif not issues:
            by_tier[tier]['ready'].append(sid)
            ready += 1
        else:
            by_tier[tier]['issues'].append((sid, issues))
            errors += len(issues)

    print("=== VALIDATION SUMMARY ===\n")
    print(f"Total: {len(scenarios)} | Validated: {validated} | Ready: {ready} | With Issues: {sum(len(v['issues']) for v in by_tier.values())}\n")

    for tier in VALID_TIERS:
        if tier not in by_tier:
            continue
        t = by_tier[tier]
        total = len(t['validated']) + len(t['ready']) + len(t['issues'])
        print(f"--- {tier} ({total} scenarios) ---")

        if t['validated']:
            print(f"  VALIDATED: {', '.join(t['validated'])}")
        if t['ready']:
            print(f"  READY TO TEST: {', '.join(t['ready'])}")
        if t['issues']:
            for sid, issues in t['issues']:
                print(f"  ISSUES [{sid}]:")
                for i in issues:
                    print(f"    - {i}")
        print()

    if errors > 0:
        print(f"\n{errors} total issues found across {sum(len(v['issues']) for v in by_tier.values())} scenarios")
    else:
        print("\nAll scenarios pass validation!")

    return 0 if errors == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
