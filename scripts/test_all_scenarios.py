#!/usr/bin/env python3
import subprocess
import json
import time
import sys
import os

FUNCTION_NAME = "demo-simulator-controller"
REGION = "us-east-1"
ACTION_DELAY = 15
RESULTS_FILE = "/Users/conalllynch/TFTest/scripts/test_results.json"

SCENARIOS = [
    "AUTO-003", "BUS-001", "BUS-003", "CSO-001",
    "DIGOPS-003", "DIGOPS-005", "DIGOPS-007",
    "EIM-001", "EIM-002", "EIM-005",
    "IND-004", "IND-008",
    "PRO-002", "SRE-004", "SRE-006",
    "WF-002", "WF-003",
    "AIOPS-001", "AIOPS-002", "AIOPS-004",
    "AUTO-001", "AUTO-002",
    "BUS-002", "BUS-004",
    "DIGOPS-001", "DIGOPS-002", "DIGOPS-004", "DIGOPS-006",
    "EIM-003", "EIM-004",
    "FREE-002",
    "IND-001", "IND-002", "IND-003", "IND-005", "IND-006", "IND-007",
    "IND-009", "IND-010", "IND-011", "IND-012", "IND-013",
    "PRO-003",
    "WF-001",
]

results = {}
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE) as f:
        results = json.load(f)

total = len(SCENARIOS)
for i, sid in enumerate(SCENARIOS, 1):
    if sid in results and results[sid].get("success"):
        print(f"[{i}/{total}] SKIP {sid} (already passed)")
        continue

    print(f"\n[{i}/{total}] Testing {sid}...", flush=True)
    payload = json.dumps({"action": "run", "scenario_id": sid, "action_delay": ACTION_DELAY})
    outfile = f"/tmp/test_{sid}.json"

    if os.path.exists(outfile):
        os.remove(outfile)

    start = time.time()
    try:
        proc = subprocess.run(
            [
                "aws", "lambda", "invoke",
                "--function-name", FUNCTION_NAME,
                "--payload", payload,
                "--cli-binary-format", "raw-in-base64-out",
                "--cli-read-timeout", "900",
                "--region", REGION,
                outfile,
            ],
            capture_output=True, text=True, timeout=920,
        )
        elapsed = int(time.time() - start)

        if proc.returncode != 0:
            results[sid] = {"success": False, "elapsed": elapsed, "error": f"aws cli exit {proc.returncode}: {proc.stderr[:200]}"}
            print(f"  [FAIL] {sid}: aws cli error: {proc.stderr[:200]}", flush=True)
        elif not os.path.exists(outfile):
            results[sid] = {"success": False, "elapsed": elapsed, "error": f"No output file. stdout={proc.stdout[:200]} stderr={proc.stderr[:200]}"}
            print(f"  [FAIL] {sid}: No output file created", flush=True)
        else:
            with open(outfile) as f:
                resp = json.load(f)

            status_code = resp.get("statusCode", 0)
            body = json.loads(resp.get("body", "{}"))
            success = status_code == 200 and body.get("success", False)
            triggered_via = body.get("trigger_result", {}).get("triggered_via", "unknown")
            incident_id = body.get("incident_id", "none")
            actions_taken = body.get("responder_result", {}).get("actions_taken", 0)

            results[sid] = {
                "success": success,
                "status_code": status_code,
                "elapsed": elapsed,
                "triggered_via": triggered_via,
                "incident_id": incident_id,
                "actions_taken": actions_taken,
                "error": body.get("error", "") if not success else "",
            }

            status = "PASS" if success else "FAIL"
            print(f"  [{status}] {sid}: {elapsed}s, via={triggered_via}, incident={incident_id}, actions={actions_taken}", flush=True)
            if not success:
                err_detail = body.get("error", "")
                steps = body.get("steps", [])
                last_step = steps[-1] if steps else {}
                print(f"  ERROR: {err_detail or json.dumps(last_step)[:200]}", flush=True)

    except subprocess.TimeoutExpired:
        elapsed = int(time.time() - start)
        results[sid] = {"success": False, "elapsed": elapsed, "error": "TIMEOUT"}
        print(f"  [FAIL] {sid}: TIMEOUT after {elapsed}s", flush=True)
    except Exception as e:
        elapsed = int(time.time() - start)
        results[sid] = {"success": False, "elapsed": elapsed, "error": str(e)}
        print(f"  [FAIL] {sid}: {e}", flush=True)

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    passed = sum(1 for r in results.values() if r.get("success"))
    failed = sum(1 for r in results.values() if not r.get("success"))
    print(f"  Progress: {passed} passed, {failed} failed, {total - len(results)} remaining", flush=True)

print(f"\n{'='*60}")
print(f"FINAL: {sum(1 for r in results.values() if r.get('success'))}/{len(results)} passed")
for sid, r in sorted(results.items()):
    status = "PASS" if r.get("success") else "FAIL"
    print(f"  {status} {sid:12} {r.get('elapsed',0):>4}s {r.get('triggered_via',''):22} {r.get('error','')}")
