import json
import os
from pathlib import Path
from registry.utils.inference import infer_area_id
from registry.utils.constants import COMMON_AREAS

INPUT_PATH = "output/entity_id_migration_map.annotated.v4.full.json"
OUTPUT_PATH = "output/entity_fingerprint_map.json"
TRACE_PATH = "output/fingerprint_mapping_trace.json"
COVERAGE_PATH = "output/fingerprint_coverage_report.json"
UNRESOLVED_PATH = "output/unresolved_entity_linkage.log"

REQUIRED_FIELDS = [
    "entity_id",
    "canonical_entity_key",
    "final_area",
    "role",
    "semantic_role",
    "tier",
    "confidence_score"
]

# Load area IDs from core.area_registry if available, else fallback to COMMON_AREAS
area_registry_path = "input/core.area_registry"
area_ids = None
if Path(area_registry_path).exists():
    with open(area_registry_path) as f:
        area_registry = json.load(f)
        area_ids = set(a['id'] for a in area_registry.get('data', {}).get('areas', []))
else:
    area_ids = set(COMMON_AREAS)

# Load migration map
with open(INPUT_PATH, "r") as f:
    migration_map = json.load(f)

fingerprint_map = {}
trace_log = []
entities_with_fallbacks = 0
fully_populated_entities = 0
unresolved_entities = []

for entry in migration_map:
    entity_id = entry.get("entity_id", "unknown")
    canonical_entity_key = entry.get("canonical_entity_key", "unknown")
    fingerprint = canonical_entity_key
    inferred_area = infer_area_id(entry, {}, area_ids)
    metadata = {
        "entity_id": entity_id,
        "canonical_entity_key": canonical_entity_key,
        "fingerprint": fingerprint,
        "final_area": inferred_area,
        "role": entry.get("role", "unknown"),
        "semantic_role": entry.get("semantic_role", "unknown"),
        "tier": entry.get("tier", "unknown"),
        "confidence_score": entry.get("confidence_score", "unknown"),
        "fingerprint_confidence_source": "canonical_entity_key|direct"
    }
    missing_fields = [field for field in REQUIRED_FIELDS if metadata[field] == "unknown"]
    if missing_fields:
        entities_with_fallbacks += 1
        trace_log.append({
            "entity_id": entity_id,
            "status": "fallback",
            "missing_fields": missing_fields,
            "notes": f"fallbacks applied: {', '.join(missing_fields)}"
        })
        unresolved_entities.append(entity_id)
    else:
        fully_populated_entities += 1
        trace_log.append({
            "entity_id": entity_id,
            "status": "success",
            "missing_fields": [],
            "notes": "ok"
        })
    fingerprint_map[entity_id] = metadata

# Write fingerprint map
with open(OUTPUT_PATH, "w") as f:
    json.dump(fingerprint_map, f, indent=2)

# Write trace log
with open(TRACE_PATH, "w") as f:
    json.dump(trace_log, f, indent=2)

# Write coverage report
total_entities = len(migration_map)
schema_complete_percent = round(fully_populated_entities / total_entities * 100, 2) if total_entities else 0.0
coverage_report = {
    "total_entities": total_entities,
    "entities_with_fallbacks": entities_with_fallbacks,
    "fully_populated_entities": fully_populated_entities,
    "schema_complete_percent": schema_complete_percent
}
with open(COVERAGE_PATH, "w") as f:
    json.dump(coverage_report, f, indent=2)

# Write unresolved linkage log
with open(UNRESOLVED_PATH, "w") as f:
    for eid in unresolved_entities:
        f.write(f"{eid}\n")
