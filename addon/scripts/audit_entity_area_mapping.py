import json
import yaml # type: ignore
from pathlib import Path
from collections import Counter, defaultdict
import os

# Use config-driven path for settings.conf.yaml
SETTINGS_PATH = Path(__file__).parent.parent / "settings.conf.yaml"
with open(SETTINGS_PATH) as f:
    settings_yaml = yaml.safe_load(f)
settings = settings_yaml["settings"]
input_paths = settings["input_paths"]
output_paths = settings["output_paths"]
# --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
    log.write("[PATCH-CONFIG-CONSISTENCY-V2] [AUDIT deprecated path usage] audit_entity_area_mapping.py: replaced hardcoded settings_path with config-driven path from project root.\n")
entity_registry_path = Path(input_paths["core_entity_registry"])
device_registry_path = Path(input_paths["core_device_registry"])
area_report_path = Path(output_paths.get("entity_area_resolution_report", "output/data/entity_area_resolution_report.json"))
area_summary_path = Path(output_paths.get("entity_area_resolution_summary", "output/data/entity_area_resolution_summary.json"))
conv_log_path = Path(output_paths.get("conversation_full_history_log", "output/conversation_full_history.log"))

with open(entity_registry_path) as f:
    core_entities = json.load(f)["data"]["entities"]
with open(device_registry_path) as f:
    device_registry = json.load(f)["data"]["devices"]
# Build device_id -> device mapping
_device_map = {dev["id"]: dev for dev in device_registry}

def resolve_area_id(entity, device_registry):
    if entity.get("area_id"):
        return entity["area_id"], "entity_area_id"
    device_id = entity.get("device_id")
    if not device_id:
        return None, "no_device_id"
    device = device_registry.get(device_id)
    if device and device.get("area_id"):
        return device["area_id"], "device_area_id"
    return None, "unknown_area"

# Build area/alias lookup from settings.conf.yaml
rooms = settings.get("rooms", [])
area_id_set = set()
area_alias_map = {}
for room in rooms:
    area_id_set.add(room["id"])
    for alias in room.get("aliases", []):
        area_alias_map[alias.lower()] = room["id"]
    area_alias_map[room["id"].lower()] = room["id"]

# Audit each entity
results = []
summary = Counter()
unknown_area_ids = Counter()
for ent in core_entities:
    eid = ent["entity_id"]
    name = ent.get("name")
    # PATCH-AREA-MAP-AUDIT-002: Use fallback area resolution
    resolved_area_id, matched_via = resolve_area_id(ent, _device_map)
    area_id = ent.get("area_id")
    conflict = False
    if area_id and area_id.lower() in area_alias_map and area_id not in area_id_set:
        conflict = True
    if resolved_area_id is None:
        unknown_area_ids[area_id] += 1
    results.append({
        "entity_id": eid,
        "name": name,
        "area_id": area_id,
        "device_id": ent.get("device_id"),
        "resolved_area": resolved_area_id,
        "matched_via": matched_via,
        "conflict": conflict
    })
    summary[matched_via or "unknown"] += 1
    if conflict:
        summary["conflict"] += 1
    if resolved_area_id is None:
        summary["unknown"] += 1

# Write detailed report
with open(area_report_path, "w") as f:
    json.dump(results, f, indent=2)
# Write summary
with open(area_summary_path, "w") as f:
    json.dump(dict(summary), f, indent=2)
# Append to conversation log
with open(conv_log_path, "a") as f:
    f.write("[AUDIT entity-area-mapping PATCH-AREA-MAP-AUDIT-002]\n")
    f.write(json.dumps(dict(summary), indent=2) + "\n")

# Use config-driven or project-root-relative path for audit log
with open(conv_log_path, "a") as logf:
    logf.write("[AUDIT entity-area-mapping PATCH-AREA-MAP-AUDIT-002] Entity-to-Area Mapping Audit Summary:\n")
    logf.write(json.dumps(dict(summary), indent=2) + "\n")
    if unknown_area_ids:
        logf.write("Top unmatched area_ids:\n")
        for area, count in unknown_area_ids.most_common(10):
            logf.write(f"  {area}: {count}\n")

# Print summary to stdout
print("Entity-to-Area Mapping Audit Summary:")
print(json.dumps(dict(summary), indent=2))
if unknown_area_ids:
    print("Top unmatched area_ids:")
    for area, count in unknown_area_ids.most_common(10):
        print(f"  {area}: {count}")
# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
