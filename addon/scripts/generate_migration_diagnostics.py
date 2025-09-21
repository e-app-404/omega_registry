import json
import os
from collections import Counter

# Input and output paths
INPUT_PATH = "input/core.entity_registry"
DIAGNOSTICS_PATH = "output/migration_diagnostics.json"
SUMMARY_PATH = "output/migration_diagnostics_summary.json"

# Unsupported domains
UNSUPPORTED_DOMAINS = {"sun", "hassio", "calendar"}

def get_domain(entity_id):
    return entity_id.split(".")[0] if "." in entity_id else "unknown"

def main():
    with open(INPUT_PATH, "r") as f:
        registry = json.load(f)
    entities = registry["data"]["entities"]
    diagnostics = []
    summary_counter = Counter()
    rejection_reasons = Counter()
    for entity in entities:
        entity_id = entity.get("entity_id")
        device_id = entity.get("device_id")
        domain = get_domain(entity_id)
        if domain in UNSUPPORTED_DOMAINS:
            diagnostics.append({
                "entity_id": entity_id,
                "status": "rejected",
                "reason": f"unsupported domain: {domain}"
            })
            summary_counter["rejected"] += 1
            rejection_reasons[f"unsupported domain: {domain}"] += 1
        elif not device_id:
            diagnostics.append({
                "entity_id": entity_id,
                "status": "rejected",
                "reason": "missing device_id"
            })
            summary_counter["rejected"] += 1
            rejection_reasons["missing device_id"] += 1
        else:
            diagnostics.append({
                "entity_id": entity_id,
                "status": "accepted",
                "reason": "valid"
            })
            summary_counter["accepted"] += 1
    # Write diagnostics file
    with open(DIAGNOSTICS_PATH, "w") as f:
        json.dump(diagnostics, f, indent=2)
    # Write summary file
    summary = {
        "total": len(entities),
        "accepted": summary_counter["accepted"],
        "rejected": summary_counter["rejected"],
        "rejection_reasons": dict(rejection_reasons)
    }
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
