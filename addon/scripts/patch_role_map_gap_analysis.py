#!/usr/bin/env python3
"""
PATCH-ROLE-MAP-GAP-ANALYSIS-V1: Analyze role coverage gaps and suggest candidate entity mappings.
Outputs:
- migration_map_role_gap_trace.json
- auto_candidate_matches.csv
"""
import json
import csv
import os
import re
from difflib import SequenceMatcher

# --- File paths ---
COVERAGE_REPORT = "output/data/migration_map_role_coverage_report.json"
MIGRATION_MAP = "output/entity_id_migration_map.annotated.v4.full.json"
CLUSTERS = "output/fingerprint_entity_clusters.v1.json"
GAP_TRACE = "output/migration_map_role_gap_trace.json"
CANDIDATE_CSV = "output/auto_candidate_matches.csv"

# --- Load data ---
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def get_roles_below_threshold(coverage, threshold=0.65):
    roles = []
    for role, stats in coverage["role_coverage"].items():
        expected = stats["expected"]
        actual = stats["actual"]
        if expected == 0:
            continue
        if actual == 0 or (actual / expected) < threshold:
            roles.append(role)
    return roles

def get_mapped_clusters(migration_map):
    return set(entry["cluster_id"] for entry in migration_map)

def get_role_for_cluster(cluster_id, migration_map):
    for entry in migration_map:
        if entry["cluster_id"] == cluster_id:
            return entry.get("role")
    return None

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def infer_candidate_entity(cluster, migration_map):
    # Try to infer a candidate entity by slug similarity to mapped entities
    candidates = []
    for entry in migration_map:
        mapped_entity = entry.get("post_reboot_entity_id", "")
        for entity in cluster.get("post_reboot_entity_ids", []):
            score = similar(entity, mapped_entity)
            if score > 0.7:
                candidates.append((entity, mapped_entity, score))
    if candidates:
        candidates.sort(key=lambda x: -x[2])
        return candidates[0][0], "slug_similarity", candidates[0][2]
    return None, None, None

def main():
    coverage = load_json(COVERAGE_REPORT)
    migration_map = load_json(MIGRATION_MAP)
    clusters = load_json(CLUSTERS)
    mapped_clusters = get_mapped_clusters(migration_map)
    roles_below = get_roles_below_threshold(coverage)
    role_gap_trace = {}
    candidate_rows = []

    for role in roles_below:
        unmapped = []
        for cluster in clusters:
            cid = cluster["cluster_id"]
            mapped_role = get_role_for_cluster(cid, migration_map)
            if mapped_role == role:
                continue  # already mapped for this role
            if cid in mapped_clusters:
                continue  # already mapped
            # Try to infer candidate entity
            candidate_entity, match_method, score = infer_candidate_entity(cluster, migration_map)
            unmapped.append({
                "cluster_id": cid,
                "integration_sources": cluster.get("integration_sources", []),
                "post_reboot_entity_ids": cluster.get("post_reboot_entity_ids", []),
                "candidate_entity_id": candidate_entity,
                "match_method": match_method,
                "score": score
            })
            if candidate_entity:
                candidate_rows.append([role, cid, candidate_entity, match_method, score, "auto-inferred"])
        role_gap_trace[role] = unmapped

    # Write outputs
    with open(GAP_TRACE, "w") as f:
        json.dump(role_gap_trace, f, indent=2)
    with open(CANDIDATE_CSV, "a") as f:
        writer = csv.writer(f)
        for row in candidate_rows:
            writer.writerow(row)

if __name__ == "__main__":
    main()
