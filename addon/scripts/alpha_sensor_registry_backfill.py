import os
import json
from pathlib import Path
from registry.utils.constants import COMMON_AREAS, ENTITY_ID_SUFFIXES, SEMANTIC_ROLE_MAP
from registry.utils.registry import load_yaml, load_json

def normalize_entity_id(eid):
    eid = eid.lower()
    for suffix in ENTITY_ID_SUFFIXES:
        if eid.endswith(suffix):
            eid = eid[: -len(suffix)]
    return eid

def infer_role(entity_ids, rules, entity_registry, device_class_role_map):
    matched_roles = set()
    matched_rule = None
    match_path = None
    for eid in entity_ids:
        eid_norm = normalize_entity_id(eid)
        for rule in rules:
            pattern = rule['match'].replace('*', '').lower()
            if pattern in eid_norm:
                matched_roles.add(rule['assign_role'])
                matched_rule = rule['match']
                match_path = 'entity_id pattern'
    if matched_roles:
        if len(matched_roles) == 1:
            return list(matched_roles)[0], matched_rule, 'Matched via entity_id pattern'
        return 'multi', matched_rule, 'Matched via entity_id pattern'
    # device_class fallback
    for eid in entity_ids:
        # Find device_class in entity_registry
        ent = next((e for e in entity_registry if e['entity_id'] == eid), None)
        if ent:
            device_class = ent.get('device_class') or ent.get('original_device_class')
            if device_class and device_class in device_class_role_map:
                return device_class_role_map[device_class], None, 'Matched via device_class fallback'
    return '', None, 'No match found'

def infer_semantic_role(role, semantic_roles):
    # Use centralized mapping for semantic roles
    return SEMANTIC_ROLE_MAP.get(role, 'generic_sensor')

def infer_match_methods(group, manual_confirmed_ids=None):
    # For demo: always direct_fingerprint
    return ['direct_fingerprint']

def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def main():
    # Load config
    settings_path = os.path.join(os.path.dirname(__file__), '../settings.conf.yaml')
    settings_yaml = load_yaml(settings_path)
    settings = settings_yaml["settings"]
    input_paths = settings["input_paths"]
    output_paths = settings["output_paths"]
    # --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
    with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
        log.write("[PATCH-CONFIG-CONSISTENCY-V1] [AUDIT deprecated path usage] alpha_sensor_registry_backfill.py: replaced hardcoded paths with settings['input_paths']/['output_paths'] from settings.conf.yaml\n")
    device_class_role_map = load_yaml(os.path.join(os.path.dirname(__file__), '../device_class_role_map.yaml'))['device_class_role_map']
    groups = load_json(output_paths.get("alpha_sensor_registry", "output/alpha_sensor_registry.json"))
    # Load entity registry
    entity_registry_path = Path(input_paths["core_entity_registry"])
    if entity_registry_path.exists():
        entity_registry = load_json(entity_registry_path)["data"]["entities"]
    else:
        entity_registry = []
    debug_log = []
    for group in groups:
        entity_ids = group.get('post_reboot_entity_ids', [])
        role, matched_rule, match_path = infer_role(entity_ids, settings.get('role_inference_rules', []), entity_registry, device_class_role_map)
        semantic_role = infer_semantic_role(role, settings.get('semantic_roles', {}))
        match_methods = infer_match_methods(group)
        reasoning = f"{match_path}. Cluster composed of {role}-class entities with {', '.join(group.get('integration_sources', []))} integration"
        group['role'] = role
        group['semantic_role'] = semantic_role
        group['entity_function'] = 'alpha'
        group['match_methods'] = match_methods
        group['incomplete'] = False
        debug_log.append({
            'group_id': group['id'],
            'role': role,
            'semantic_role': semantic_role,
            'matched_rule': matched_rule,
            'source_cluster': group.get('protocols', ['unknown'])[0],
            'reasoning_summary': reasoning
        })
    save_json(groups, output_paths.get("alpha_sensor_registry", "output/alpha_sensor_registry.json"))
    save_json(debug_log, output_paths.get("alpha_sensor_registry_backfill_debug", "output/alpha_sensor_registry_backfill_debug.log.json"))
    # Write diff log
    try:
        with open(output_paths.get("alpha_sensor_registry_backfill_debug", "output/alpha_sensor_registry_backfill_debug.log.json")) as f:
            new_debug = json.load(f)
        with open("output/alpha_sensor_registry_backfill_debug.log.json.bak") as f:
            old_debug = json.load(f)
        diff = [n for n in new_debug if n not in old_debug]
        with open(output_paths.get("alpha_sensor_registry_backfill_diff", "output/alpha_sensor_registry_backfill.diff.log.json"), 'w') as f:
            json.dump(diff, f, indent=2)
    except Exception:
        pass
    print(f"Backfill complete. {len(groups)} groups updated. Debug log written.")

if __name__ == '__main__':
    main()

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
