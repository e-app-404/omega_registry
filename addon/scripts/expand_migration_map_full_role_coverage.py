import json
import yaml # type: ignore
from pathlib import Path
from datetime import datetime
from collections import Counter

# --- CONFIG ---
fingerprint_path = Path("output/fingerprinting_run/entity_fingerprint_map.20250719T080258.json")
output_map_path = Path("output/entity_id_migration_map.annotated.v4.full.json")
diagnostics_path = Path(f"output/migration_expansion_diagnostics.{datetime.now().strftime('%Y%m%dT%H%M%S')}.json")

# --- LOAD FINGERPRINT MAP ---
with open(fingerprint_path) as f:
    fingerprint_map = json.load(f)

migration_map = []
match_method_counter = Counter()
flagged_count = 0

for eid, info in fingerprint_map.items():
    semantic_role = info.get("semantic_role") or info.get("role") or "unknown"
    confidence = info.get("confidence_score", 0.0)
    flag_manual_review = confidence < 0.92 or semantic_role == "unknown"
    match_method = "inferred" if semantic_role != "unknown" else "null_role"
    entry = {
        "post_entity_id": eid,
        "pre_entity_id": None,  # No pre-entity mapping available
        "semantic_role": semantic_role,
        "match_method": match_method,
        "confidence_score": round(confidence, 3),
        "flag_manual_review": flag_manual_review
    }
    migration_map.append(entry)
    match_method_counter[match_method] += 1
    if flag_manual_review:
        flagged_count += 1

with open(output_map_path, "w") as f:
    json.dump(migration_map, f, indent=2)

diagnostics = {
    "total_fingerprinted_entities": len(fingerprint_map),
    "total_migration_mappings": len(migration_map),
    "count_by_match_method": dict(match_method_counter),
    "flagged_entries": flagged_count
}
with open(diagnostics_path, "w") as f:
    json.dump(diagnostics, f, indent=2)

print(f"Wrote migration map: {output_map_path}")
print(f"Wrote diagnostics: {diagnostics_path}")

# PATCH: Full coverage migration map expansion for all fingerprinted entities. No filtering by role or cluster. Diagnostics emitted.
