# DEPRECATED: This script is now merged into fingerprint_entity_reconciliation.py
# All fingerprint map and metrics generation is handled in a single entry point.
# This file is retained for reference only and should not be used in the pipeline.

import json
import sys
from datetime import datetime
from collections import Counter

# Load enriched inference trace as canonical input
with open("data/fingerprint_inference_trace.json") as f:
    trace = json.load(f)

fingerprint_map = {}
areas = set()
roles = set()
conf_scores = []
complete_count = 0
for eid, ent in trace.items():
    area = ent.get("final_area") or ent.get("area_id")
    role = ent.get("role")
    conf = ent.get("confidence_score")
    if area:
        areas.add(area)
    if role:
        roles.add(role)
    if conf is not None:
        conf_scores.append(conf)
    # Validate all fields
    if eid and area and role and conf is not None:
        complete_count += 1
    fingerprint_map[eid] = {
        "entity_id": eid,
        "area": area,
        "role": role,
        "confidence_score": conf
    }

now = datetime.now().strftime("%Y%m%dT%H%M%S")
out_path = f"output/fingerprinting_run/entity_fingerprint_map.{now}.json"
with open(out_path, "w") as f:
    json.dump(fingerprint_map, f, indent=2)

# Metrics
input_entities = len(trace)
output_entities = len(fingerprint_map)
unique_areas = len(areas)
unique_roles = len(roles)
area_success = sum(1 for ent in trace.values() if ent.get("final_area") or ent.get("area_id")) / input_entities
role_success = sum(1 for ent in trace.values() if ent.get("role")) / input_entities
conf_dist = Counter(int((c or 0)*10)/10 for c in conf_scores)

metrics = {
    "input_entities": input_entities,
    "output_entities": output_entities,
    "unique_areas": unique_areas,
    "unique_roles": unique_roles,
    "area_inference_success_rate": round(area_success, 3),
    "role_inference_success_rate": round(role_success, 3),
    "confidence_score_distribution": dict(conf_dist),
    "all_fields_populated": complete_count == input_entities,
    "confidence_score_majority_above_0_80": sum(1 for c in conf_scores if c and c > 0.8) > input_entities/2
}

with open(f"output/fingerprinting_run/fingerprint_consolidation_metrics.{now}.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"[FINGERPRINT MAP] {out_path}")
print(f"[METRICS] output/fingerprinting_run/fingerprint_consolidation_metrics.{now}.json")
