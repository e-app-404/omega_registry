# Delta analysis between annotated.v4.full.json and rosetta.v5.json
# This script compares the two migration maps and emits delta diagnostics as required by the patch directive.

import json
import os
from collections import defaultdict

V4_PATH = "output/entity_id_migration_map.annotated.v4.full.json"
V5_PATH = "input/mappings/entity_id_migration_map.rosetta.v5.json"
DELTA_DIR = "output/migration_diagnostics/migration_delta_v4_to_v5/"

os.makedirs(DELTA_DIR, exist_ok=True)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    v4 = load_json(V4_PATH)
    v5 = load_json(V5_PATH)

    # Index by pre_entity_id/old_entity_id
    v4_by_pre = {e.get("pre_entity_id") or e.get("old_entity_id"): e for e in v4 if (e.get("pre_entity_id") or e.get("old_entity_id"))}
    v5_by_pre = {e.get("old_entity_id") or e.get("pre_entity_id"): e for e in v5 if (e.get("old_entity_id") or e.get("pre_entity_id"))}

    added_in_v5 = []
    missing_from_v5 = []
    matched_diff = []

    # Find entries present in v5 but not in v4
    for pre_id in v5_by_pre:
        if pre_id not in v4_by_pre:
            added_in_v5.append(v5_by_pre[pre_id])

    # Find entries present in v4 but not in v5
    for pre_id in v4_by_pre:
        if pre_id not in v5_by_pre:
            missing_from_v5.append(v4_by_pre[pre_id])
        else:
            # Compare match details
            v4e = v4_by_pre[pre_id]
            v5e = v5_by_pre[pre_id]
            v4_match = v4e.get("post_entity_id") or v4e.get("new_entity_id")
            v5_match = v5e.get("new_entity_id") or v5e.get("post_entity_id")
            if v4_match != v5_match or v4e.get("confidence_score") != v5e.get("confidence_score"):
                matched_diff.append({
                    "pre_entity_id": pre_id,
                    "v4_match": v4_match,
                    "v5_match": v5_match,
                    "v4_confidence": v4e.get("confidence_score"),
                    "v5_confidence": v5e.get("confidence_score"),
                    "v4_method": v4e.get("match_method"),
                    "v5_method": v5e.get("match_method")
                })

    # Write outputs
    with open(os.path.join(DELTA_DIR, "added_in_v5.json"), "w", encoding="utf-8") as f:
        json.dump(added_in_v5, f, indent=2)
    with open(os.path.join(DELTA_DIR, "missing_from_v5.json"), "w", encoding="utf-8") as f:
        json.dump(missing_from_v5, f, indent=2)
    with open(os.path.join(DELTA_DIR, "matched_diff.json"), "w", encoding="utf-8") as f:
        json.dump(matched_diff, f, indent=2)

if __name__ == "__main__":
    main()
