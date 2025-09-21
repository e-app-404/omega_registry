import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
fingerprint_entity_reconciliation.py

Performs fuzzy fingerprint-based reconciliation between pre-reboot and post-reboot Home Assistant registries.

- Reads pre-reboot room registry and canonical omega device registry
- Applies fingerprinting strategies (see context seed)
- Outputs:
    - entity_fingerprint_map.json
    - unmatched_entity_trace.json
    - omega_room_registry.relinked.json

Non-destructive: does not overwrite canonical registry or supporting files.

Configuration is now loaded from 'settings.conf.yaml' (centralized project config).

--- CHANGELOG ---
- Replaced legacy role/area inference functions with centralized logic utilities.
- Deprecated legacy get_role, infer_cluster_role, and device_class_role logic.
- Unified area inference using infer_area_id.
- Enhanced path resolution using get_input_path, get_output_path, get_path_from_settings.
"""
import os
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import copy
import yaml # type: ignore
import csv
import argparse
import collections
from datetime import datetime
# --- Import shared utility modules ---
from registry.utils.synonyms import (
    ATTRIBUTE_SYNONYMS, ROLE_SYNONYMS, AREA_SYNONYMS,
    normalize_attribute, normalize_role, normalize_area, normalize_slug
)
from registry.utils.config import load_settings, get_input_path, get_output_path, get_path_from_settings
from registry.utils.registry import extract_entities
from registry.utils.constants import ENTITY_FEATURES, STANDARD_DEVICE_CLASSES, greek_tiers
from registry.utils.inference import infer_area_id, infer_role, patch_devices
from registry.utils.cluster import make_cluster_id, build_device_map, get_device_area, resolve_cluster_metadata

# --- Utility functions: moved to top for global visibility ---
def fuzzy_group_match(g1, g2):
    if not g1 or not g2:
        return 0.0
    if g1 == g2:
        return 1.0
    from difflib import SequenceMatcher
    return SequenceMatcher(None, g1, g2).ratio()

def fuzzy_slug_match(s1, s2):
    if not s1 or not s2:
        return 0.0
    from difflib import SequenceMatcher
    return SequenceMatcher(None, s1, s2).ratio()

def jaro_winkler(s1, s2):
    try:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1 or "", s2 or "").ratio()
    except ImportError:
        return 0.0

# --- Helper function definitions (all moved up and ordered to resolve Pylance errors) ---

# --- Anti-greedy area prefix matcher ---
def infer_area_from_slug(slug, valid_areas_set, area_alias_map, area_synonyms):
    if not slug:
        return "unknown_area", "no_area_found"
    tokens = slug.lower().split('_')
    for i in range(len(tokens), 0, -1):
        prefix = '_'.join(tokens[:i])
        # Direct match
        if prefix in valid_areas_set or prefix in area_alias_map:
            return prefix, "fallback_prefix_match"
        # Synonym match
        if prefix in area_synonyms:
            synonym_target = area_synonyms[prefix]
            if synonym_target in valid_areas_set or synonym_target in area_alias_map:
                return synonym_target, "synonym_fallback"
    return "unknown_area", "no_area_found"
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def load_core_entity_registry(path):
    with open(path, "r") as f:
        data = json.load(f)
        return data["data"]["entities"]

def get_domain(entity_id):
    if not entity_id or "." not in entity_id:
        return "unknown"
    return entity_id.split(".")[0]

def get_slug(entity_id):
    if not entity_id or "." not in entity_id:
        return ""
    return entity_id.split(".")[1]

def parse_core_slug(slug):
    if not slug:
        return None, None, None
    parts = slug.split('_')
    for i, part in enumerate(parts):
        if part in greek_tiers:
            group = '_'.join(parts[:i]) if i > 0 else None
            tier = part
            attribute = '_'.join(parts[i+1:]) if i+1 < len(parts) else None
            return group, tier, attribute
    return slug, None, None

def normalize_name(name):
    if not name:
        return ""
    return str(name).replace("_", " ").lower().strip()

def infer_device_class(entity):
    device_class = entity.get("device_class")
    if device_class and device_class in STANDARD_DEVICE_CLASSES:
        return device_class
    eid = entity.get("entity_id")
    if eid and "." in eid:
        domain = eid.split(".")[0]
        if domain in STANDARD_DEVICE_CLASSES:
            return domain
    return None

# --- PATCH-MANUAL-MATCH-PRESERVE-001: CLI flag for force overwrite ---
# --- CLI ARGUMENTS ---
parser = argparse.ArgumentParser(description="Fingerprint-based entity reconciliation.")
parser.add_argument("--force-overwrite", action="store_true", help="Force overwrite manual_confirmed_matches.json even if empty.")
args, unknown = parser.parse_known_args()

# --- Aggressive canonical key function for diagnostics handshake ---
def aggressive_canonical_key(entity_id):
    if not entity_id or not isinstance(entity_id, str):
        return None
    # Remove domain prefix
    if "." in entity_id:
        entity_id = entity_id.split(".", 1)[1]
    patterns = [
        r"(_alpha_|_omega_|_beta_|_gamma_|_contact|_sensor|_monitor|_cloud_connection|_motion|_timeout|_battery|_signal_level|_signal_strength|_occupancy|_illumination|_presence|_door|_window|_restart|_sensitivity|_attribute|_matter|_tplink|_tp_link|_wifi|_aeotec|_multipurpose|_sonoff|_tapo|_smartthings|_mtr|_relinked|_enriched|_devtools|_canonical|_patched|_snapshot|_v\\d+|_stage\\d+|_run\\d+|_full|_final|_debug|_log|_trace|_csv|_json|_txt|_tmp|_archive|_output|_input|_data|_role|_area|_zone|_room|_entity|_device|_id|_name|_type|_class|_unique|_core|_main|_base|_test|_sample|_manual|_auto|_fallback|_unknown|_unmatched|_ambiguous|_gray|_true|_false|_none|_null|_other)+$",
        r"(_[a-z]+){1,2}$"
    ]
    key = entity_id.lower()
    for pat in patterns:
        key = re.sub(pat, "", key)
    key = re.sub(r"__+", "_", key)
    key = key.strip("_")
    return key if key else None

# --- CONFIG ---
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "settings.conf.yaml"
config = load_settings(CONFIG_PATH)
# PATCH: Support both legacy and new config structures
if "settings" in config:
    settings = config["settings"]
    input_paths = settings["input_paths"]
    output_paths = settings["output_paths"]
else:
    # Use 'general' or root keys
    settings = config.get("general", config)
    input_paths = settings.get("input_paths", config.get("input_paths", {}))
    output_paths = settings.get("output_paths", config.get("output_paths", {}))
# INPUT_DIR = Path(input_paths.get("input_dir", BASE_DIR / "input"))
PRE_REBOOT_DIR = Path(input_paths["pre_reboot_dir"])
OUTPUT_DIR = Path(output_paths["fingerprinting_run"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- PATCH: Emit OUTPUT_DIR path and file count for audit ---
from glob import glob
with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
    audit_log.write(f"[OUTPUT_DIR] {OUTPUT_DIR.resolve()}\n")
    file_list = list(OUTPUT_DIR.glob("*"))
    audit_log.write(f"[OUTPUT_DIR_FILE_COUNT] {len(file_list)} files: {[str(f.name) for f in file_list]}\n")
print("[TRACE] OUTPUT_DIR:", OUTPUT_DIR.resolve())
print("[TRACE] OUTPUT_DIR file count:", len(file_list))

PRE_REBOOT_ROOM_REGISTRY = PRE_REBOOT_DIR / "omega_room_registry.json"
CORE_ENTITY_REGISTRY = input_paths["core_entity_registry"]
ALPHA_SENSOR_REGISTRY = PRE_REBOOT_DIR / "alpha_sensor_registry.json"
ALPHA_LIGHT_REGISTRY = PRE_REBOOT_DIR / "alpha_light_registry.json"
DEVICE_REGISTRY_PATH = input_paths["core_device_registry"]

# --- LOAD YAML CONFIG FOR WEIGHTS AND THRESHOLDS ---
weights = config.get('weights', {})
thresholds = config.get('thresholds', {})
HIGH_CONFIDENCE = thresholds.get('high_confidence', 0.85)
GRAY_ZONE = thresholds.get('gray_zone', 0.75)

# --- LOAD DATA ---
pre_reboot_rooms = load_json(PRE_REBOOT_ROOM_REGISTRY)
alpha_sensor_registry = load_json(ALPHA_SENSOR_REGISTRY) if ALPHA_SENSOR_REGISTRY.exists() else {}
alpha_light_registry = load_json(ALPHA_LIGHT_REGISTRY) if ALPHA_LIGHT_REGISTRY.exists() else {}
# Use core.entity_registry as the post-reboot entity pool
post_entities = load_core_entity_registry(CORE_ENTITY_REGISTRY)
# --- PATCH: Correct extraction of pre-reboot entities from alpha_sensor_registry.json ---
# Use alpha_sensor_registry['sensors'].values() if present, else fallback to extract_entities
if isinstance(alpha_sensor_registry, dict) and 'sensors' in alpha_sensor_registry:
    pre_reboot_entities = []
    for k, v in alpha_sensor_registry['sensors'].items():
        ent = dict(v)
        if 'entity_id' not in ent:
            ent['entity_id'] = k
        pre_reboot_entities.append(ent)
else:
    pre_reboot_entities = extract_entities(alpha_sensor_registry)

# --- Remove legacy normalization, synonym, and inference logic (now in utils) ---

# --- LOAD AREA/ALIAS/DEVICE MAPS FOR AREA RESOLUTION ---
with open(DEVICE_REGISTRY_PATH, "r") as f:
    device_registry = json.load(f)["data"]["devices"]
_device_map = {dev["id"]: dev for dev in device_registry}
rooms = config.get("rooms", [])
role_inference_rules = config.get("role_inference_rules", [])
area_id_set = set()
area_alias_map = {}
for room in rooms:
    area_id_set.add(room["id"])
    for alias in room.get("aliases", []):
        area_alias_map[alias.lower()] = room["id"]
    area_alias_map[room["id"].lower()] = room["id"]

# PATCH-FP-RECON-FIELD-EMIT-V1: Instrumented logging for area/role inference
inference_debug = {}
area_inference_debug_log = []

# --- Variable initializations for output/debug ---
manual_confirmed = {}
entity_fingerprint_map_normalized = {}
manual_true_count = 0
manual_false_count = 0
pattern_stats = defaultdict(lambda: {"boost": 0, "penalty": 0, "true": 0, "false": 0})
score_deltas = []
area_inference_audit = []
area_inference_summary = {}
match_counts = {"0.85+": 0, "0.7+": 0, "0.5+": 0, "<0.5": 0}

# --- Deduplicated and patched resolve_area_id ---
def resolve_area_id(entity, device_map, area_id_set, area_alias_map):
    eid = entity.get("entity_id", "")
    slug = get_slug(eid)
    debug_entry = {
        "entity_id": eid,
        "slug": slug,
        "fallback_prefix": None,
        "final_area": None,
        "area_inference_method": None
    }
    # First try entity-level assignment
    if entity.get("area_id"):
        area_id = entity["area_id"]
        if area_id in area_id_set:
            debug_entry["final_area"] = area_id
            debug_entry["area_inference_method"] = "entity_area_id"
            area_inference_debug_log.append(debug_entry)
            return area_id, "entity_area_id"
        elif area_id.lower() in area_alias_map:
            debug_entry["final_area"] = area_alias_map[area_id.lower()]
            debug_entry["area_inference_method"] = "entity_area_id_alias"
            area_inference_debug_log.append(debug_entry)
            return area_alias_map[area_id.lower()], "entity_area_id_alias"
        else:
            debug_entry["final_area"] = "unknown_area"
            debug_entry["area_inference_method"] = "entity_area_id_unknown"
            area_inference_debug_log.append(debug_entry)
            return "unknown_area", "entity_area_id_unknown"
    # Fallback to device-level area
    device_id = entity.get("device_id")
    if device_id and device_id in device_map:
        device_area_id = device_map[device_id].get("area_id")
        if device_area_id:
            debug_entry["final_area"] = device_area_id
            debug_entry["area_inference_method"] = "device_area_id"
            area_inference_debug_log.append(debug_entry)
            return device_area_id, "device_area_id"
        else:
            debug_entry["final_area"] = "unknown_area"
            debug_entry["area_inference_method"] = "device_area_fallback_failed"
            area_inference_debug_log.append(debug_entry)
            return "unknown_area", "device_area_fallback_failed"
    # --- PATCH: Anti-greedy fallback area extraction ---
    if slug:
        area, area_reason = infer_area_from_slug(slug, area_id_set, area_alias_map, AREA_SYNONYMS)
        debug_entry["fallback_prefix"] = area if area != "unknown_area" else None
        debug_entry["final_area"] = area
        debug_entry["area_inference_method"] = area_reason + ("|anti_greedy_area_patch" if area != "unknown_area" else "")
        area_inference_debug_log.append(debug_entry)
        if area != "unknown_area":
            return area, area_reason + "|anti_greedy_area_patch"
    # No match found
    debug_entry["final_area"] = "unknown_area"
    debug_entry["area_inference_method"] = "no_area_found"
    area_inference_debug_log.append(debug_entry)
    return "unknown_area", "no_area_found"

# --- MAIN MATCHING LOOP ---
entity_fingerprint_map = copy.deepcopy(manual_confirmed)
unmatched_entity_trace = {}
omega_room_registry_relinked = {}

# Patch: Area inference debug logging for every entity
for pre_entity in pre_reboot_entities:
    # Use centralized area inference for all entities
    area = infer_area_id(pre_entity, _device_map, area_id_set)
    area_inference_debug_log.append({
        "entity_id": pre_entity.get("entity_id"),
        "slug": get_slug(pre_entity.get("entity_id")),
        "matched_area": area,
        "matched_reason": "centralized_infer_area_id"
    })
    # ...existing code for fingerprinting, matching, etc...

# --- Emit area inference debug log at the end ---
try:
    print("Writing debug log to", OUTPUT_DIR / "area_inference_debug.json")
    with open(OUTPUT_DIR / "area_inference_debug.json", "w") as f:
        json.dump(area_inference_debug_log, f, indent=2)
    # Log debug log length
    with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
        audit_log.write(f"[DEBUG_LOG_LEN] {len(area_inference_debug_log)} entries\n")
    print(f"[TRACE] area_inference_debug.json written with {len(area_inference_debug_log)} entries.")
except Exception as e:
    print("⚠️ area_inference_debug.json was not emitted — log is empty or write failed.")
    with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
        audit_log.write(f"[DEBUG_LOG_WRITE_FAIL] {str(e)}\n")

# --- MAIN MATCHING LOOP (PHASE 2b PATCH) ---
# Use all entities from core.entity_registry for area inference and fingerprinting
all_entities = post_entities  # post_entities is loaded from core.entity_registry
area_inference_debug_log = []
prefix_match_count = 0
unknown_area_count = 0
schema_incomplete_count = 0
fallback_area_count = 0
fallback_role_count = 0
high_confidence_count = 0
low_confidence_count = 0
none_confidence_count = 0
entity_fingerprint_map = {}
schema_incomplete_entities = []
entity_fingerprint_area_trace = {}
entity_inference_traces = {}

total_entities = len(all_entities)
for entity in all_entities:
    eid = entity.get("entity_id", "")
    slug = get_slug(eid)
    # Use patched infer_area_id and infer_role to get traces
    area, area_trace = infer_area_id(entity, _device_map, area_id_set)
    role_data = infer_role(entity)
    role = role_data.get("role")
    semantic_role = role_data.get("semantic_role")
    role_reason = role_data.get("role_reason")
    role_trace = role_data.get("trace")
    if not role or role == "unknown":
        role = "unclassified"
        semantic_role = "unclassified"
        role_reason = "strict_unclassified"
    tier = entity.get("tier") or "gamma"
    confidence_score = entity.get("confidence_score")
    if confidence_score is None:
        confidence_score = 0.0
    # Fallback annotation
    fallback_annotation = {}
    if area == "unknown_area" or area in (None, '', 'null', 'unknown', 'null_area', 'null'):
        fallback_annotation["area"] = area_trace.get("method")
    if not role or role == "unknown":
        fallback_annotation["role"] = role_reason
    # Schema completeness check
    required_fields = [eid, slug, role, semantic_role, tier, area, area_trace.get("method")]
    schema_complete = all(required_fields)
    # Build fingerprint entry
    entry = {
        "entity_id": eid,
        "canonical_entity_key": aggressive_canonical_key(eid),
        "role": role or "unknown",
        "semantic_role": semantic_role or "unknown",
        "tier": tier,
        "final_area": area,
        "area_inference_source": area_trace.get("method"),
        "confidence_score": confidence_score,
        "inference_trace": {
            "area": area_trace,
            "role": role_trace
        },
        "schema_complete": schema_complete
    }
    if fallback_annotation:
        entry["fallback_annotation"] = fallback_annotation
    entity_fingerprint_map[eid] = entry
    entity_inference_traces[eid] = entry["inference_trace"]
    # --- PATCH: Always append area inference debug entry for every entity ---
    area_inference_debug_log.append({
        "entity_id": eid,
        "slug": slug,
        "final_area": area,
        "area_inference_method": area_trace.get("method"),
        "area_trace": area_trace
    })

# --- Emit outputs ---
with open(OUTPUT_DIR / "entity_fingerprint_map.json", "w") as f:
    json.dump(entity_fingerprint_map, f, indent=2)
with open(OUTPUT_DIR / "entity_fingerprint_area_trace.json", "w") as f:
    json.dump(entity_fingerprint_area_trace, f, indent=2)
with open(OUTPUT_DIR / "fingerprint_coverage_trace.json", "w") as f:
    json.dump([
        {
            "entity_id": eid,
            "schema_complete": entry.get("schema_complete", False),
            "final_area": entry.get("final_area"),
            "role": entry.get("role"),
            "confidence_score": entry.get("confidence_score", 0.0)
        }
        for eid, entry in entity_fingerprint_map.items()
    ], f, indent=2)
with open(OUTPUT_DIR / "fingerprint_coverage_report.json", "w") as f:
    coverage = {
        "total_entities": total_entities,
        "included_in_fingerprint_map": len(entity_fingerprint_map),
        "coverage_percent": round(100.0 * len(entity_fingerprint_map) / total_entities, 2) if total_entities else 0.0,
        "fallback_area_count": fallback_area_count,
        "fallback_role_count": fallback_role_count,
        "high_confidence_count": high_confidence_count,
        "low_confidence_count": low_confidence_count,
        "none_confidence_count": none_confidence_count,
        "schema_incomplete_count": schema_incomplete_count
    }
    json.dump(coverage, f, indent=2)
with open(OUTPUT_DIR / "unresolved_entity_linkage.log", "w") as f:
    for eid in schema_incomplete_entities:
        f.write(f"{eid}\n")
with open(OUTPUT_DIR / "canonical_key_inference_trace.json", "w") as f:
    json.dump({eid: entry["canonical_entity_key"] for eid, entry in entity_fingerprint_map.items()}, f, indent=2)
# Emit debug log
with open(OUTPUT_DIR / "area_inference_debug.json", "w") as f:
    json.dump(area_inference_debug_log, f, indent=2)
# --- Update audit logs ---
with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
    audit_log.write(f"[FINGERPRINT_PATCH] {total_entities} entities processed, {len(entity_fingerprint_map)} in map, {schema_incomplete_count} schema incomplete, {fallback_area_count} fallback area, {fallback_role_count} fallback role\n")
    audit_log.write(f"[COVERAGE] {round(100.0 * len(entity_fingerprint_map) / total_entities, 2)}%\n")
    audit_log.write(f"[SCHEMA_COMPLETENESS] {round(100.0 * (total_entities - schema_incomplete_count) / total_entities, 2)}%\n")
    audit_log.write(f"[UNKNOWN_AREA] {fallback_area_count} ({round(100.0 * fallback_area_count / total_entities, 2)}%)\n")
with open(BASE_DIR / "copilot_patchlog_overview.log", "a") as patchlog:
    patchlog.write(f"[FINGERPRINT_PATCH] {total_entities} entities processed, {len(entity_fingerprint_map)} in map, {schema_incomplete_count} schema incomplete, {fallback_area_count} fallback area, {fallback_role_count} fallback role\n")
    patchlog.write(f"[COVERAGE] {round(100.0 * len(entity_fingerprint_map) / total_entities, 2)}%\n")
    patchlog.write(f"[SCHEMA_COMPLETENESS] {round(100.0 * (total_entities - schema_incomplete_count) / total_entities, 2)}%\n")
    patchlog.write(f"[UNKNOWN_AREA] {fallback_area_count} ({round(100.0 * fallback_area_count / total_entities, 2)}%)\n")

# --- STRICT PATCH: Disable area fallback, enforce non-null role, strict slug matching, trace logging, log failures ---
fingerprint_inference_trace = {}
fingerprint_inference_failures = []
strict_entity_fingerprint_map = {}
for entity in all_entities:
    eid = entity.get("entity_id", "")
    slug = get_slug(eid)
    # Strict slug logic: camel/underscore separation, prefix priority
    slug_parts = re.split(r'[_]', slug)
    prefix = slug_parts[0] if slug_parts else None
    # Area inference: no fallback, only emit unknown_area if all fail
    area, area_reason = resolve_area_id(entity, _device_map, area_id_set, area_alias_map)
    # --- PATCH: Inherit area from device if area is unknown but device has area_id ---
    if area == "unknown_area" and entity.get("device_id"):
        device_id = entity["device_id"]
        device = _device_map.get(device_id)
        if device and device.get("area_id"):
            area = device["area_id"]
            area_reason = "device_area_id_patch"
    if area == "unknown_area":
        # Only allow unknown_area if all inference fails
        if area_reason != "no_area_found":
            area = prefix if prefix in area_id_set else "unknown_area"
            area_reason = "prefix_inference" if area != "unknown_area" else "no_area_found"
    # Role/semantic_role: enforce non-null, mark as unclassified if not found
    role_data = infer_role(entity)
    role = role_data.get("role")
    semantic_role = role_data.get("semantic_role")
    role_reason = role_data.get("reason")
    if not role or role == "unknown":
        role = "unclassified"
        semantic_role = "unclassified"
        role_reason = "strict_unclassified"
    # Trace logging
    fingerprint_inference_trace[eid] = {
        "entity_id": eid,
        "slug": slug,
        "prefix": prefix,
        "prefix_to_area": area,
        "area_inference_method": area_reason,
        "entity_id_pattern_to_role": role,
        "device_class_to_semantic_role": semantic_role,
        "role_inference_method": role_reason
    }
    # Log failures and exclude from clustering
    if area == "unknown_area" or role == "unclassified":
        fingerprint_inference_failures.append(eid)
        continue
    # Build strict fingerprint entry
    entry = {
        "entity_id": eid,
        "canonical_entity_key": aggressive_canonical_key(eid),
        "role": role,
        "semantic_role": semantic_role,
        "tier": entity.get("tier") or "gamma",
        "final_area": area,
        "area_inference_source": area_reason,
        "confidence_score": entity.get("confidence_score", 0.0),
        "schema_complete": True
    }
    # Inject cluster_id and cluster_role using centralized logic
    cluster_data = resolve_cluster_metadata(entry, _device_map, area_id_set)
    entry["cluster_id"] = cluster_data["cluster_id"]
    entry["cluster_role"] = cluster_data["cluster_role"]
    strict_entity_fingerprint_map[eid] = entry
# Emit strict outputs
with open(OUTPUT_DIR / "entity_fingerprint_map.json", "w") as f:
    json.dump(strict_entity_fingerprint_map, f, indent=2)
with open(OUTPUT_DIR / "fingerprint_mapping_trace.json", "w") as f:
    json.dump(fingerprint_inference_trace, f, indent=2)
with open(OUTPUT_DIR / "fingerprint_inference_failures.log", "w") as f:
    for eid in fingerprint_inference_failures:
        f.write(f"{eid}\n")
# Log patch activity and output file line counts
trace_count = len(fingerprint_inference_trace)
failure_count = len(fingerprint_inference_failures)
with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
    audit_log.write(f"[STRICT_PATCH] fingerprint_inference_trace.json: {trace_count} entities, fingerprint_inference_failures.log: {failure_count} failures\n")
with open(BASE_DIR / "copilot_patchlog_overview.log", "a") as patchlog:
    patchlog.write(f"[STRICT_PATCH] fingerprint_inference_trace.json: {trace_count} entities, fingerprint_inference_failures.log: {failure_count} failures\n")
print(f"[DEBUG] Writing fingerprint_inference_trace.json with {len(fingerprint_inference_trace)} entries")
if fingerprint_inference_trace:
    with open(OUTPUT_DIR / "fingerprint_inference_trace.json", "w") as f:
        json.dump(fingerprint_inference_trace, f, indent=2)
    trace_path = OUTPUT_DIR / "fingerprint_inference_trace.json"
    print(f"[DEBUG] fingerprint_inference_trace.json written to {trace_path}")
    with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
        audit_log.write(f"[STRICT_PATCH] fingerprint_inference_trace.json: {len(fingerprint_inference_trace)} entities, path: {trace_path}\n")
    with open(BASE_DIR / "copilot_patchlog_overview.log", "a") as patchlog:
        patchlog.write(f"[STRICT_PATCH] fingerprint_inference_trace.json: {len(fingerprint_inference_trace)} entities, path: {trace_path}\n")
else:
    print("[DEBUG] fingerprint_inference_trace is empty; file not written.")
    with open(BASE_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit_log:
        audit_log.write("[STRICT_PATCH] fingerprint_inference_trace.json: 0 entities, file not written.\n")
    with open(BASE_DIR / "copilot_patchlog_overview.log", "a") as patchlog:
        patchlog.write("[STRICT_PATCH] fingerprint_inference_trace.json: 0 entities, file not written.\n")

# --- At the end of the script, after emitting strict_entity_fingerprint_map and fingerprint_inference_trace ---
now = datetime.now().strftime("%Y%m%dT%H%M%S")
map_path = OUTPUT_DIR / f"entity_fingerprint_map.{now}.json"
trace_path = OUTPUT_DIR / f"fingerprint_inference_trace.{now}.json"
metrics_path = OUTPUT_DIR / f"fingerprint_consolidation_metrics.{now}.json"

# Write timestamped outputs
with open(map_path, "w") as f:
    json.dump(strict_entity_fingerprint_map, f, indent=2)
with open(trace_path, "w") as f:
    json.dump(fingerprint_inference_trace, f, indent=2)

# Compute and write metrics
input_entities = len(all_entities)
output_entities = len(strict_entity_fingerprint_map)
areas = set(e.get("final_area") for e in strict_entity_fingerprint_map.values() if e.get("final_area"))
roles = set(e.get("role") for e in strict_entity_fingerprint_map.values() if e.get("role"))
conf_scores = [e.get("confidence_score", 0.0) for e in strict_entity_fingerprint_map.values()]
complete_count = sum(1 for e in strict_entity_fingerprint_map.values() if e.get("entity_id") and e.get("final_area") and e.get("role") and e.get("confidence_score") is not None)
from collections import Counter
conf_dist = Counter(int((c or 0)*10)/10 for c in conf_scores)
metrics = {
    "input_entities": input_entities,
    "output_entities": output_entities,
    "unique_areas": len(areas),
    "unique_roles": len(roles),
    "area_inference_success_rate": round(len(areas)/input_entities, 3) if input_entities else 0.0,
    "role_inference_success_rate": round(len(roles)/input_entities, 3) if input_entities else 0.0,
    "confidence_score_distribution": dict(conf_dist),
    "all_fields_populated": complete_count == input_entities,
    "confidence_score_majority_above_0_80": sum(1 for c in conf_scores if c and c > 0.8) > input_entities/2
}
with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"[FINGERPRINT MAP] {map_path}")
print(f"[TRACE] {trace_path}")
print(f"[METRICS] {metrics_path}")

# --- DIAGNOSTIC COUNTERS ---
area_method_counts = {}
role_method_counts = {}
area_non_null_count = 0
role_non_null_count = 0
conf_gt_05 = 0
conf_gt_08 = 0
for entity in all_entities:
    eid = entity.get("entity_id", "")
    slug = get_slug(eid)
    area, area_trace = infer_area_id(entity, _device_map, area_id_set)
    role_data = infer_role(entity)
    role = role_data.get("role")
    confidence_score = role_data.get("confidence", 0.0)
    # Count area/role/score
    if area and area != 'null' and area != 'unknown_area':
        area_non_null_count += 1
    if role and role != 'unclassified' and role != 'unknown':
        role_non_null_count += 1
    if confidence_score > 0.5:
        conf_gt_05 += 1
    if confidence_score > 0.8:
        conf_gt_08 += 1
    # Count inference methods
    am = area_trace.get("method", "null")
    area_method_counts[am] = area_method_counts.get(am, 0) + 1
    rm = role_data.get("match_method", "null")
    role_method_counts[rm] = role_method_counts.get(rm, 0) + 1
# Emit diagnostics
patchlog_path = BASE_DIR / "copilot_patchlog_overview.log"
with open(patchlog_path, "a") as patchlog:
    patchlog.write(f"[DIAGNOSTICS] area_non_null: {area_non_null_count}, role_non_null: {role_non_null_count}, conf>0.5: {conf_gt_05}, conf>0.8: {conf_gt_08}\n")
    patchlog.write(f"[AREA_METHOD_BREAKDOWN] {area_method_counts}\n")
    patchlog.write(f"[ROLE_METHOD_BREAKDOWN] {role_method_counts}\n")
# Optionally emit as JSON for post-run analysis
with open(OUTPUT_DIR / "inference_method_breakdown.json", "w") as f:
    json.dump({"area_method_counts": area_method_counts, "role_method_counts": role_method_counts, "area_non_null": area_non_null_count, "role_non_null": role_non_null_count, "conf_gt_05": conf_gt_05, "conf_gt_08": conf_gt_08}, f, indent=2)
