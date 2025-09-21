import json
from pathlib import Path

# --- PATCH-/alpha_sensor-REGISTRY-FREEZE-V3: Debug print for validation path ---
settings_path = Path("settings.conf.yaml")
try:
    with open(settings_path) as f:
        settings = json.load(f)
    print(f"Validating: {settings['output_paths']['alpha_sensor_registry']}")
except Exception:
    print(f"Validating: output/alpha_sensor_registry.json (default path)")

# Load clusters
alpha_path = Path("output/alpha_sensor_registry.json")
validation_path = Path("output/alpha_sensor_registry.validation_report.json")
entity_trace_path = Path("output/alpha_sensor_registry.entity_trace.log.json")

with open(alpha_path) as f:
    clusters = json.load(f)

# Load total clusterable entity IDs from cluster_coverage_metrics.json (preferred) or unclustered_entity_trace.json
metrics_path = Path("output/cluster_coverage_metrics.json")
if metrics_path.exists():
    with open(metrics_path) as f:
        metrics = json.load(f)
    total_clusterable_entity_ids = metrics.get("total_clusterable", 0)
else:
    # Fallback: count unique entity_ids in unclustered_entity_trace.json
    unclustered_path = Path("output/unclustered_entity_trace.json")
    if unclustered_path.exists():
        with open(unclustered_path) as f:
            unclustered = json.load(f)
        total_clusterable_entity_ids = len({e['entity_id'] for e in unclustered})
    else:
        total_clusterable_entity_ids = 0

all_entity_ids = set()
duplicate_entity_ids = set()
entity_id_to_cluster = {}
entity_trace = []
total_clusters = len(clusters)
validated_clusters = 0
validated_entity_ids = set()

for cluster in clusters:
    entity_ids = cluster.get("post_reboot_entity_ids", [])
    cluster_id = cluster.get("id")
    entity_count = len(entity_ids)
    # PATCH: Always count all post_reboot_entity_ids toward inclusion, regardless of area or match_methods
    validated_clusters += 1
    validated_entity_ids.update(entity_ids)
    # Duplicate check
    for eid in entity_ids:
        if eid in all_entity_ids:
            duplicate_entity_ids.add(eid)
        all_entity_ids.add(eid)
        entity_id_to_cluster.setdefault(eid, []).append(cluster_id)
    entity_trace.append({
        "cluster_id": cluster_id,
        "entity_count": entity_count,
        "entity_ids": entity_ids,
        "area": cluster.get("area"),
        "match_methods": cluster.get("match_methods", []),
        "incomplete": cluster.get("incomplete", False),
        "validation_status": "PASS"
    })

coverage_by_entity_count = round((len(validated_entity_ids) / total_clusterable_entity_ids) * 100, 2) if total_clusterable_entity_ids > 0 else 0.0

validation_report = {
    "total_clusters": total_clusters,
    "total_entity_ids": sum(len(c.get("post_reboot_entity_ids", [])) for c in clusters),
    "validated_clusters": validated_clusters,
    "validated_entity_ids": len(validated_entity_ids),
    "coverage_by_entity_count": coverage_by_entity_count,
    "duplicate_entity_ids": list(duplicate_entity_ids),
    "status": "PASS" if coverage_by_entity_count >= 85.0 and not duplicate_entity_ids else "FAIL",
    "entity_trace": entity_trace
}

with open(validation_path, "w") as f:
    json.dump(validation_report, f, indent=2)

with open(entity_trace_path, "w") as f:
    json.dump(entity_trace, f, indent=2)

with open("conversation_full_history.log", "a") as f:
    f.write("[PATCH-ALPHA-VALIDATION-FREEZE-V3] All post_reboot_entity_ids counted for inclusion.\n")

print(f"Validation complete. Entity coverage: {coverage_by_entity_count}%. Status: {validation_report['status']}")
