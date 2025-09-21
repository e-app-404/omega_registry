import json
import yaml # type: ignore
import re
from pathlib import Path
from collections import defaultdict, Counter
import os
from registry.utils.cluster import make_cluster_id
from registry.utils.inference import infer_area_id, patch_devices
from registry.utils.cluster import make_cluster_id, build_device_map, get_device_area, resolve_cluster_metadata
from registry.utils.config import get_input_path, get_output_path, get_path_from_settings

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.

# Load config and mappings
settings_path = Path(__file__).parent.parent / "settings.conf.yaml"
with open(settings_path) as f:
    settings_yaml = yaml.safe_load(f)
settings = settings_yaml["settings"]
input_paths = settings["input_paths"]
output_paths = settings["output_paths"]
# --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
    log.write("[PATCH-MASTER-OMEGA-PATH-REFRACTOR-V2] regenerate_alpha_sensor_registry_v3_002.py: all master.omega_registry/ path references removed; using project-root-relative/config-driven paths.\n")
area_registry_path = Path(input_paths["core_area_registry"])
entity_registry_path = Path(input_paths["core_entity_registry"])
manual_confirmed_path = Path(output_paths.get("manual_confirmed_matches", "output/fingerprinting_run/manual_confirmed_matches.json"))
contract_path = Path("contracts/expected_alpha_sensor_registry.yaml")

alpha_sensor_registry_path = Path(output_paths.get("alpha_sensor_registry", "output/alpha_sensor_registry.json"))
debug_log_path = Path(output_paths.get("alpha_sensor_registry_debug", "output/data/alpha_sensor_registry.debug.log.json"))
mapping_trace_path = Path(output_paths.get("alpha_sensor_registry_mapping_trace", "output/data/alpha_sensor_registry.debug.mapping_trace.json"))
validation_report_path = Path(output_paths.get("alpha_sensor_registry_validation_report", "output/alpha_sensor_registry.validation_report.json"))
cluster_coverage_metrics_path = Path(output_paths.get("cluster_coverage_metrics", "output/data/cluster_coverage_metrics.json"))

with open(area_registry_path) as f:
    area_data = json.load(f)["data"]["areas"]
with open(entity_registry_path) as f:
    core_entities = json.load(f)["data"]["entities"]
with open(manual_confirmed_path) as f:
    manual_confirmed = json.load(f)
with open(contract_path) as f:
    contract = yaml.safe_load(f)

# Build area_id → area_name map
area_id_to_name = {a["id"]: a["name"] for a in area_data}
area_alias_map = {}
for room in settings.get("rooms", []):
    for alias in room.get("aliases", []):
        area_alias_map[alias.lower()] = room["name"]
    area_alias_map[room["id"].lower()] = room["name"]

# Compile role inference rules
role_rules = settings.get("role_inference_rules", [])
semantic_roles = settings.get("semantic_roles", {})
negative_score_rules = settings.get("negative_score_rules", [])

def infer_role(entity_id):
    for rule in role_rules:
        if re.match(rule["match"].replace("*", ".*"), entity_id):
            return rule["assign_role"]
    return "generic_sensor"

def infer_semantic_role(role):
    return role if role in semantic_roles else "generic_sensor"

def apply_negative_score(entity_id, role):
    penalty = 0.0
    for rule in negative_score_rules:
        if rule.get("suffixes"):
            for suf in rule["suffixes"]:
                if entity_id.endswith(suf):
                    penalty += rule["penalty"]
        if rule.get("match"):
            for pair in rule["match"]:
                if role in pair:
                    penalty += rule["penalty"]
    return penalty

def is_feature_role(role):
    return role in ["tuning_param", "timeout_config", "battery_monitor"]

# Step 1: Build entity mapping and trace
entity_map = {}
mapping_trace = []
for ent in core_entities:
    eid = ent["entity_id"]
    area_id = ent.get("area_id")
    area_name = area_id_to_name.get(area_id, None)
    if not area_name and area_id:
        area_name = area_alias_map.get(area_id.lower())
    role = infer_role(eid)
    semantic_role = infer_semantic_role(role)
    penalty = apply_negative_score(eid, role)
    is_feature = is_feature_role(role)
    score = 1.0 + penalty
    excluded_reason = None
    if not area_name:
        excluded_reason = "no_area"
    mapping_trace.append({
        "entity_id": eid,
        "area_id": area_id,
        "area_name": area_name,
        "role": role,
        "semantic_role": semantic_role,
        "inferred_cluster_id": make_cluster_id(area_name, role) if area_name else None,
        "score": score,
        "excluded_reason": excluded_reason
    })
    entity_map[eid] = {
        "area": area_name,
        "role": role,
        "semantic_role": semantic_role,
        "tier": "alpha",
        "score": score,
        "is_feature": is_feature,
        "excluded_reason": excluded_reason
    }

# Step 2: Group into clusters
clusters = defaultdict(lambda: {"post_reboot_entity_ids": [], "features": [], "source_clusters": [], "match_methods": []})
for eid, meta in entity_map.items():
    if meta["excluded_reason"]:
        continue
    cluster_key = make_cluster_id(meta['area'], meta['role'])
    if meta["is_feature"]:
        clusters[cluster_key]["features"].append(eid)
    else:
        clusters[cluster_key]["post_reboot_entity_ids"].append(eid)
    clusters[cluster_key]["area"] = meta["area"]
    clusters[cluster_key]["role"] = meta["role"]
    clusters[cluster_key]["semantic_role"] = meta["semantic_role"]
    clusters[cluster_key]["tier"] = meta["tier"]
    clusters[cluster_key]["confidence_score_mean"] = meta["score"]
    clusters[cluster_key]["source_clusters"].append(eid)
    clusters[cluster_key]["match_methods"].append("inferred")

# Step 3: Build output clusters, filter by contract
output_clusters = []
entity_ids_covered = set()
for cid, c in clusters.items():
    if not c["post_reboot_entity_ids"]:
        continue
    cluster = {
        "id": cid,
        "area": c["area"],
        "role": c["role"],
        "semantic_role": c["semantic_role"],
        "tier": c["tier"],
        "confidence_score_mean": c["confidence_score_mean"],
        "post_reboot_entity_ids": c["post_reboot_entity_ids"],
        "source_clusters": c["source_clusters"],
        "match_methods": c["match_methods"]
    }
    if c["features"]:
        cluster["features"] = c["features"]
    output_clusters.append(cluster)
    entity_ids_covered.update(c["post_reboot_entity_ids"])

# Step 4: Validate and emit
with open(mapping_trace_path, "w") as f:
    json.dump(mapping_trace, f, indent=2)

required_fields = set(contract["thresholds"]["required_fields"])
min_coverage = contract["thresholds"].get("min_coverage_percent", 85.0)
total_entities = len([e for e in core_entities if not entity_map[e["entity_id"]]["excluded_reason"]])
covered_entities = len(entity_ids_covered)
coverage_percent = 100.0 * covered_entities / total_entities if total_entities else 0

validation_report = {
    "total_entities": total_entities,
    "covered_entities": covered_entities,
    "coverage_percent": coverage_percent,
    "min_coverage_required": min_coverage,
    "status": "PASS" if coverage_percent >= min_coverage else "REJECTED: Coverage below minimum"
}

if coverage_percent < min_coverage:
    with open(validation_report_path, "w") as f:
        json.dump(validation_report, f, indent=2)
    print(f"[PATCH-ALPHA-REGEN-V3-002] ABORT: Coverage {coverage_percent:.2f}% < {min_coverage}%")
    exit(1)

with open(alpha_sensor_registry_path, "w") as f:
    json.dump(output_clusters, f, indent=2)
with open(debug_log_path, "w") as f:
    json.dump({"clusters": output_clusters}, f, indent=2)
with open(validation_report_path, "w") as f:
    json.dump(validation_report, f, indent=2)
with open(cluster_coverage_metrics_path, "w") as f:
    json.dump({"coverage_percent": coverage_percent, "covered_entities": covered_entities, "total_entities": total_entities}, f, indent=2)
print(f"[PATCH-ALPHA-REGEN-V3-002] Alpha sensor registry regenerated and validated. Coverage: {coverage_percent:.2f}%")
