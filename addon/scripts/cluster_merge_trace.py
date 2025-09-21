import json
from pathlib import Path
import re

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def get_base_cluster(cluster_id):
    # Remove known suffixes to get base
    return re.sub(r'_(timeout|sensitivity|illumination)$', '', cluster_id)

def main():
    clusters = load_json("output/fingerprint_entity_clusters.v1.json")
    base_clusters = {}
    merge_trace = []
    fuzzy_override_count = 0  # PATCH-FP-RECON-V2-002: Track fuzzy overrides
    for c in clusters:
        base_id = get_base_cluster(c['cluster_id'])
        # PATCH-FP-RECON-V2-002: Fuzzy merge override logic
        area_score = c.get('area_score', 1.0)
        name_score = c.get('name_score', 0.0)
        device_class_score = c.get('device_class_score', 0.0)
        role_score = c.get('role_score', 0.0)
        allow_merge = False
        merge_reason = None
        if area_score == 0.0 and (name_score + device_class_score + role_score) >= 2.5:
            allow_merge = True
            merge_reason = "fuzzy_area_override"
            fuzzy_override_count += 1
        if base_id not in base_clusters:
            base_clusters[base_id] = {
                **c,
                'merged_from': [],
                'entities_added': list(c['post_reboot_entity_ids'])
            }
            if merge_reason:
                base_clusters[base_id]['merge_reason'] = merge_reason
        else:
            base_clusters[base_id]['entities_added'].extend(c['post_reboot_entity_ids'])
            base_clusters[base_id]['merged_from'].append(c['cluster_id'])
            merge_entry = {
                'base_cluster': base_id,
                'merged_from': [c['cluster_id']],
                'entities_added': c['post_reboot_entity_ids']
            }
            if merge_reason:
                merge_entry['merge_reason'] = merge_reason
            merge_trace.append(merge_entry)
    # Build migration map
    migration_map = []
    for base_id, c in base_clusters.items():
        for eid in c['entities_added']:
            migration_map.append({
                'cluster_id': base_id,
                'post_reboot_entity_id': eid,
                'source': 'cluster_merged',
                'confidence': 0.97
            })
    save_json(migration_map, "output/entity_id_migration_map.annotated.v4.json")
    save_json(merge_trace, "output/cluster_merge_trace.v4.json")
    print(f"Cluster merge complete. Base clusters: {len(base_clusters)}, Migrations: {len(migration_map)}")
    print(f"[PATCH-FP-RECON-V2-002] Fuzzy area override merges: {fuzzy_override_count}")
    # PATCH-FP-RECON-V2-002: Log patch action
    with open("conversation_full_history.log", "a") as logf:
        logf.write(f"[PATCH-FP-RECON-V2-002] Fuzzy area override merges: {fuzzy_override_count}\n")

if __name__ == "__main__":
    main()
