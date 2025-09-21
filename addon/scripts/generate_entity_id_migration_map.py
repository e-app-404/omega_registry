import json
import os
from pathlib import Path
from registry.utils.inference import infer_area_id
from registry.utils.constants import COMMON_AREAS

DIAGNOSTICS_PATH = "output/migration_diagnostics.json"
REGISTRY_PATH = "input/core.entity_registry"
MIGRATION_MAP_PATH = "output/entity_id_migration_map.annotated.v4.full.json"
DELTA_TRACE_PATH = "output/entity_id_migration_map.delta_trace.json"

REQUIRED_FIELDS = [
    "entity_id",
    "post_reboot_entity_id",
    "canonical_entity_key",
    "role",
    "semantic_role",
    "final_area",
    "area_inference_source",
    "cluster_id",
    "tier",
    "confidence_score"
]

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    diagnostics = load_json(DIAGNOSTICS_PATH)
    registry = load_json(REGISTRY_PATH)["data"]["entities"]
    accepted_ids = set(e["entity_id"] for e in diagnostics if e["status"] == "accepted")
    rejected_ids = set(e["entity_id"] for e in diagnostics if e["status"] != "accepted")

    # Build lookup for registry entities
    registry_map = {e["entity_id"]: e for e in registry}
    migration_map = []
    missing_fields = []

    # Load area IDs from core.area_registry if available, else fallback to COMMON_AREAS
    area_registry_path = "input/core.area_registry"
    area_ids = None
    if Path(area_registry_path).exists():
        with open(area_registry_path) as f:
            area_registry = json.load(f)
            area_ids = set(a['id'] for a in area_registry.get('data', {}).get('areas', []))
    else:
        area_ids = set(COMMON_AREAS)

    for eid in accepted_ids:
        reg = registry_map.get(eid)
        if not reg:
            missing_fields.append(eid)
            continue
        inferred_area = infer_area_id(reg, {}, area_ids)
        entry = {
            "entity_id": reg["entity_id"],
            "post_reboot_entity_id": reg.get("entity_id"),
            "canonical_entity_key": reg.get("unique_id"),
            "role": reg.get("entity_category", "unknown"),
            "semantic_role": reg.get("device_class", "unknown"),
            "final_area": inferred_area,
            "area_inference_source": "centralized_infer_area_id",
            "cluster_id": reg.get("device_id"),
            "tier": reg.get("platform", "unknown"),
            "confidence_score": 1.0
        }
        migration_map.append(entry)

    # Write migration map
    with open(MIGRATION_MAP_PATH, "w") as f:
        json.dump(migration_map, f, indent=2)

    # Delta trace: entities in registry but not in migration map
    registry_ids = set(registry_map.keys())
    missing_in_map = list(registry_ids - accepted_ids)
    delta_trace = {
        "total_registry": len(registry_ids),
        "total_accepted": len(accepted_ids),
        "total_rejected": len(rejected_ids),
        "missing_in_map": missing_in_map,
        "missing_fields": missing_fields
    }
    with open(DELTA_TRACE_PATH, "w") as f:
        json.dump(delta_trace, f, indent=2)

    print(f"Migration map generated: {len(migration_map)} entries. Delta trace written.")

if __name__ == "__main__":
    main()
