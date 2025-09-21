import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import re
from collections import defaultdict
import yaml # type: ignore
from pathlib import Path
from registry.utils.pathing import resolve_path, project_root
from registry.utils.registry import load_json, load_yaml
from registry.utils.inference import patch_devices, infer_area_id
from registry.utils.constants import COMMON_AREAS, STANDARD_DEVICE_CLASSES, ENTITY_FEATURES
from registry.utils.cluster import resolve_cluster_metadata


def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

# --- AUTOEXPAND CLUSTERABLE_PATTERNS ---
def build_clusterable_patterns():
    classes = set(STANDARD_DEVICE_CLASSES) | set(ENTITY_FEATURES)
    patterns = []
    for cls in classes:
        patterns.append(re.compile(rf"^sensor\\.{cls}(_|\\.).*"))
        patterns.append(re.compile(rf"^binary_sensor\\.{cls}(_|\\.).*"))
        patterns.append(re.compile(rf"^select\\.{cls}(_|\\.).*"))
        patterns.append(re.compile(rf"^number\\.{cls}(_|\\.).*"))
        # Domain-level direct match (e.g. fan, lock, etc.)
        patterns.append(re.compile(rf"^{cls}\\..*"))
    return patterns

CLUSTERABLE_PATTERNS = build_clusterable_patterns()

def is_clusterable(entity_id):
    return any(p.match(entity_id) for p in CLUSTERABLE_PATTERNS)

def infer_cluster_role(entity):
    # Try device_class, original_device_class, original_name, entity_id patterns
    for key in ['device_class', 'original_device_class']:
        if entity.get(key):
            return entity[key]
    if entity.get('original_name'):
        return entity['original_name']
    # Fallback: try to extract from entity_id
    eid = entity.get('entity_id', '')
    for role in ['motion', 'occupancy', 'temperature', 'humidity', 'button', 'switch', 'light', 'media_player']:
        if role in eid:
            return role
    return None

def main():
    # Load config
    settings_path = Path(__file__).parent.parent / "settings.conf.yaml"
    with open(settings_path) as f:
        settings_yaml = yaml.safe_load(f)
    # DEBUG: Dump all top-level keys
    top_keys = list(settings_yaml.keys())
    debug_msg = f"[DEBUG] Top-level keys in settings.conf.yaml: {top_keys}\n"
    print(debug_msg)
    with open(os.path.join(os.path.dirname(__file__), '../diagnostic.log'), "a") as log:
        log.write(debug_msg)
    # Accept both top-level and nested 'settings' key
    if "settings" in settings_yaml:
        settings = settings_yaml["settings"]
    else:
        settings = settings_yaml
    # Patch: input_paths/output_paths may be under 'general'
    if "general" in settings:
        input_paths = settings["general"]["input_paths"]
        output_paths = settings["general"]["output_paths"]
    else:
        raise KeyError("Could not find 'general' key in settings.conf.yaml; please check your config structure.")
    # --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
    with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
        log.write("[PATCH-CONFIG-CONSISTENCY-V1] [AUDIT deprecated path usage] autocluster_audit.py: replaced hardcoded paths with settings['input_paths']/['output_paths'] from settings.conf.yaml\n")
    entity_registry = load_json(input_paths["core_entity_registry"])
    try:
        clusters = load_json(output_paths.get("alpha_sensor_registry_provisional_autoclustered", "output/alpha_sensor_registry.provisional_autoclustered.json"))
    except Exception:
        clusters = []
    # Load device registry for area inference
    try:
        device_registry = load_json(input_paths["core_device_registry"])
        device_map = {d['id']: d for d in device_registry.get('data', {}).get('devices', [])}
    except Exception:
        device_map = {}
    clusterable = []
    skipped = []
    skipped_breakdown = defaultdict(int)
    for e in entity_registry.get('data', {}).get('entities', entity_registry.get('entities', [])):
        entity_id = e.get('entity_id')
        reason = None
        if not is_clusterable(entity_id):
            reason = "Does not match clusterable criteria"
        elif e.get('disabled_by'):
            reason = f"Disabled by {e.get('disabled_by')}"
        else:
            meta = resolve_cluster_metadata(e, device_map, set(COMMON_AREAS))
            area_id = meta['area_id']
            cluster_role = meta['cluster_role']
            if not area_id:
                reason = "Missing area_id (after inference)"
            elif not cluster_role:
                reason = "Missing cluster_role (after inference)"
        if reason:
            skipped.append({"entity_id": entity_id, "excluded_reason": reason})
            skipped_breakdown[reason] += 1
        else:
            meta = resolve_cluster_metadata(e, device_map, set(COMMON_AREAS))
            clusterable.append({
                "entity_id": meta['entity_id'],
                "platform": meta['platform'],
                "area_id": meta['area_id'],
                "cluster_role": meta['cluster_role'],
                "cluster_id": meta['cluster_id'],
                "match_type": "entity_registry_autocluster",
                "disabled_by": e.get('disabled_by')
            })
    audit = {
        "summary": {
            "total_entities": len(entity_registry.get('data', {}).get('entities', entity_registry.get('entities', []))),
            "clusterable_entities": len(clusterable),
            "actually_clustered": len(clusters),
            "skipped_entities": len(skipped),
            "skipped_breakdown": dict(skipped_breakdown),
            "clusterable_pattern_count": len(CLUSTERABLE_PATTERNS)
        },
        "matches": clusterable,
        "skipped": skipped
    }
    save_json(audit, output_paths.get("entity_registry_autocluster_audit", "output/entity_registry_autocluster_audit.json"))
    # --- PATCHLOG ---
    patch_summary = (
        f"[PATCH-CLUSTERABLE-PATTERN-AUTOEXPAND] Patterns: {len(CLUSTERABLE_PATTERNS)}, "
        f"Clusterable: {len(clusterable)}, Skipped: {len(skipped)}\n"
    )
    with open(os.path.join(os.path.dirname(__file__), '../copilot_patchlog_overview.log'), "a") as log:
        log.write(patch_summary)
    patchlog_path = os.path.join(os.path.dirname(__file__), '../copilot_patches/PATCH-CLUSTERABLE-PATTERN-AUTOEXPAND.log')
    os.makedirs(os.path.dirname(patchlog_path), exist_ok=True)
    with open(patchlog_path, "a") as log:
        log.write(patch_summary)
    print(f"Audit complete. Clusterable: {len(clusterable)}, Actually clustered: {len(clusters)}, Skipped: {len(skipped)}. Patterns: {len(CLUSTERABLE_PATTERNS)}")

if __name__ == "__main__":
    main()

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
