import os
import json
import yaml # type: ignore
import re
import datetime
from pathlib import Path

# --- Configurable paths ---
# Load config-driven paths from settings.conf.yaml
SETTINGS_PATH = Path(__file__).parent.parent / "settings.conf.yaml"
with open(SETTINGS_PATH) as f:
    settings_yaml = yaml.safe_load(f)
settings = settings_yaml["settings"]
input_paths = settings["input_paths"]
output_paths = settings["output_paths"]

# Helper to resolve config paths robustly
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
def resolve_config_path(path_str):
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()

ENTITY_REGISTRY_PATH = resolve_config_path(input_paths.get("core_entity_registry", "input/core.entity_registry"))
ALPHA_SENSOR_REGISTRY_PATH = resolve_config_path(output_paths.get("alpha_sensor_registry", "output/alpha_sensor_registry.json"))
CONV_LOG_PATH = resolve_config_path(output_paths.get("conversation_full_history_log", "output/conversation_full_history.log"))

# Output directory for audit
output_data_dir = resolve_config_path(output_paths.get("audit_output_data_dir", "output/data"))
README_PATH = Path(__file__).parent.parent / "README.md"

# --- Load helpers ---
def load_entity_registry(path):
    with open(path) as f:
        data = json.load(f)
    return data["data"]["entities"]

def load_alpha_sensor_registry(path):
    with open(path) as f:
        return json.load(f)

def load_settings(path):
    with open(path) as f:
        return yaml.safe_load(f)

# --- Role inference matching ---
def get_role_inference_rules(settings):
    # Accepts list-of-dicts format for role_inference_rules
    rules = []
    for rule in settings.get("role_inference_rules", []):
        # Support both new and legacy keys for robustness
        role = rule.get("assign_role") or rule.get("name") or rule.get("role")
        pattern = rule.get("match", {}).get("pattern") or rule.get("pattern")
        if role and pattern:
            rules.append({"role": role, "pattern": pattern})
    return rules

def match_role(entity_id, rules):
    for rule in rules:
        pattern = rule["pattern"]
        if re.fullmatch(pattern.replace("*", ".*"), entity_id):
            return rule["role"]
    return None

# --- Main logic ---
def main():
    entities = load_entity_registry(ENTITY_REGISTRY_PATH)
    clusters = load_alpha_sensor_registry(ALPHA_SENSOR_REGISTRY_PATH)
    settings = load_settings(SETTINGS_PATH)
    rules = get_role_inference_rules(settings)

    # Find all clusterable entities
    clusterable = []
    for e in entities:
        role = match_role(e["entity_id"], rules)
        if role:
            clusterable.append({
                "entity_id": e["entity_id"],
                "domain": e["entity_id"].split(".")[0],
                "role": role
            })

    # Find all clustered entity_ids
    clustered = set()
    for c in clusters:
        for eid in c.get("post_reboot_entity_ids", []):
            clustered.add(eid)

    # Find unclustered
    unclustered = [e for e in clusterable if e["entity_id"] not in clustered]

    # Prepare output directory
    os.makedirs(output_data_dir, exist_ok=True)

    # Write unclustered_entity_trace.json to output/data/
    unclustered_entity_trace_path = os.path.join(output_data_dir, "unclustered_entity_trace.json")
    with open(unclustered_entity_trace_path, "w") as f:
        json.dump(unclustered, f, indent=2)

    # Write cluster_coverage_metrics.json to output/data/
    cluster_coverage_metrics = {
        "total_clusterable": len(clusterable),
        "clustered": len(clusterable) - len(unclustered),
        "unclustered": len(unclustered),
        "coverage_percent": round(100 * (len(clusterable) - len(unclustered)) / max(1, len(clusterable)), 2),
        "covered_entities": len(clusterable) - len(unclustered),
        "total_entities": len(clusterable),
        "per_tier_counts": None  # Not computed in this script
    }
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_data_dir, f"cluster_coverage_metrics.{timestamp}.json")
    with open(output_path, 'w') as f:
        json.dump(cluster_coverage_metrics, f, indent=2)
    print(f"Cluster coverage metrics written to {output_path}")

    # Print traceability info
    unique_domains = sorted(set(e["domain"] for e in clusterable))
    print(f"Total clusterable: {len(clusterable)}")
    print(f"Clustered: {cluster_coverage_metrics['clustered']}")
    print(f"Unclustered: {cluster_coverage_metrics['unclustered']}")
    print(f"Coverage: {cluster_coverage_metrics['coverage_percent']}%")
    print(f"Unique domains: {unique_domains}")
    if clusterable:
        print(f"First clusterable: {clusterable[0]['entity_id']}")
        print(f"Last clusterable: {clusterable[-1]['entity_id']}")

    # Write summary line to conversation_full_history.log
    with open("conversation_full_history.log", "a") as log_file:
        log_file.write("[SCRIPT_RUN audit_cluster_coverage] → See output/data/unclustered_entity_trace.json and output/data/cluster_coverage_metrics.json for full results.\n")

if __name__ == "__main__":
    main()

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
