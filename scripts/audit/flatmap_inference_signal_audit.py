# Run with: python -m scripts.audit.flatmap_inference_signal_audit
import json
import random

from scripts.utils.input_list_extract import extract_data
from scripts.utils.logging import attach_meta

flatmap_path = "canonical/derived_views/flatmaps/entity_flatmap.json"
registry_path = "canonical/omega_registry_master.json"
audit_path = "canonical/logs/audit/audit_flatmap/flatmap_inference_signal_audit.json"

fields = ["tier", "area_id", "floor_id", "platform", "domain"]

with open(flatmap_path) as f:
    flatmap_content = json.load(f)
flatmap = extract_data(flatmap_path, flatmap_content)
with open(registry_path) as f:
    registry_content = json.load(f)
registry = extract_data(registry_path, registry_content)

total = len(flatmap)
matrix = {f: sum(1 for e in flatmap if e.get(f)) for f in fields}
completeness = {f: round(100 * matrix[f] / total, 2) for f in fields}

flatmap_ids = set(e["entity_id"] for e in flatmap)
registry_ids = set(e["entity_id"] for e in registry)
delta = {
    "flatmap_only": list(flatmap_ids - registry_ids),
    "registry_only": list(registry_ids - flatmap_ids),
    "intersect_count": len(flatmap_ids & registry_ids),
}

signal_strength = {f: len(set(e.get(f) for e in flatmap if e.get(f))) for f in fields}

# PATCH-FLATMAP-INFER-V1: Use a larger sample for root cause analysis
sample_size = min(100, len(flatmap_ids & registry_ids))
sample_ids = random.sample(list(flatmap_ids & registry_ids), sample_size)
trace_notes = []
for sid in sample_ids:
    f_ent = next(e for e in flatmap if e["entity_id"] == sid)
    r_ent = next(e for e in registry if e["entity_id"] == sid)
    trace_notes.append(
        {
            "entity_id": sid,
            "flatmap": {k: f_ent.get(k) for k in fields},
            "registry": {k: r_ent.get(k) for k in fields},
        }
    )

audit = {
    "field_completeness_matrix": completeness,
    "entity_id_alignment_delta": delta,
    "signal_strength_summary": signal_strength,
    "trace_notes": trace_notes,
}
# PATCH-FLATMAP-INFER-V1: Attach meta as top-level _meta using logging.attach_meta
meta = attach_meta(
    __file__, "PATCH-FLATMAP-INFER-V1", pipeline_stage="flatmap_inference_audit"
)
audit["_meta"] = meta["_meta"]

with open(audit_path, "w") as f:
    json.dump(audit, f, indent=2)
