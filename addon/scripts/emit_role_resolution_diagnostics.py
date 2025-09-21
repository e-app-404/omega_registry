import json
import os
import datetime

# Input/output paths
INPUT_PATH = "output/alpha_sensor/alpha_sensor_registry.json"
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_PATH = f"data/role_resolution_diagnostics.{TS}.json"

# Helper: extract name tokens

def extract_tokens(name):
    if not name:
        return []
    return [t.strip().lower() for t in name.replace('_', ' ').replace('-', ' ').split() if t.strip()]

def main():
    with open(INPUT_PATH, "r") as f:
        clusters = json.load(f)
    diagnostics = []
    for cluster in clusters:
        role = cluster.get("role", "")
        if role not in ("unclassified", "diagnostic"):
            continue
        cluster_id = cluster.get("id") or cluster.get("cluster_id")
        domain = cluster.get("domain", "")
        device_class = cluster.get("device_class", "")
        name = cluster.get("name", "")
        tokens = extract_tokens(name)
        attempts = []
        if domain:
            attempts.append(f"domain = {domain}")
        if device_class:
            attempts.append(f"device_class = {device_class}")
        if tokens:
            attempts.append(f"name tokens = {tokens}")
        reason = "No match in device_class or role mapping"
        diagnostics.append({
            "cluster_id": cluster_id,
            "final_role": role,
            "inference_attempts": attempts,
            "reason": reason
        })
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(diagnostics, f, indent=2)
    # Log to copilot_patchlog_overview.log
    with open("copilot_patchlog_overview.log", "a") as log:
        log.write(f"[emit_role_resolution_diagnostics.py] Emitted {len(diagnostics)} diagnostics to {OUTPUT_PATH}\n")
    print(f"Diagnostics written to {OUTPUT_PATH} ({len(diagnostics)} entries)")

if __name__ == "__main__":
    main()
