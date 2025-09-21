import sys
import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from registry.utils.registry import load_json
from registry.utils.inference import infer_area_id
from registry.utils.cluster import make_cluster_id, build_device_map, resolve_cluster_metadata

def infer_cluster_role(entity):
    for key in ['device_class', 'original_device_class']:
        if entity.get(key):
            return entity[key]
    if entity.get('original_name'):
        return entity['original_name'].split()[0].lower()
    eid = entity.get('entity_id', '')
    for token in ['motion', 'occupancy', 'temperature', 'humidity', 'button', 'switch', 'light', 'media_player', 'alarm', 'timestamp']:
        if token in eid:
            return token
    return 'unknown'

def main():
    settings_path = Path(__file__).parent.parent / "settings.conf.yaml"
    with open(settings_path) as f:
        settings_yaml = yaml.safe_load(f)
    settings = settings_yaml.get("settings", settings_yaml)
    input_paths = settings["general"]["input_paths"]
    # PATCH: Load enriched fingerprint map instead of raw entity registry
    fingerprint_map_path = Path(__file__).parent.parent / "output/fingerprinting_run/entity_fingerprint_map.json"
    with open(fingerprint_map_path) as f:
        fingerprint_map = json.load(f)
    entities = list(fingerprint_map.values())
    clusters = defaultdict(list)
    area_ids = None
    # PATCH: Use areas from settings.conf.yaml instead of area_registry_path
    area_ids = set()
    if "rooms" in settings:
        area_ids = set(room["id"] for room in settings["rooms"])
    elif "settings" in settings and "rooms" in settings["settings"]:
        area_ids = set(room["id"] for room in settings["settings"]["rooms"])
    else:
        from registry.utils.constants import COMMON_AREAS
        area_ids = set(COMMON_AREAS)
    # PATCH END
    # PATCH: Debug log for 2–3 sample entities
    sample_indices = random.sample(range(len(entities)), min(3, len(entities)))
    for idx, e in enumerate(entities):
        meta = resolve_cluster_metadata(e, {}, area_ids)  # device_map not needed for enriched
        if idx in sample_indices:
            print(f"[DEBUG] Sample entity: entity_id={e.get('entity_id')}, final_area={e.get('final_area')}, role={e.get('role')}, cluster_id={meta.get('cluster_id')}")
        cluster_id = meta['cluster_id']
        if not cluster_id:
            reason = []
            if not e.get('final_area'):
                reason.append('missing area')
            if not e.get('role'):
                reason.append('missing role')
            print(f"[DEBUG] Entity {e.get('entity_id')} missing cluster_id: {', '.join(reason) if reason else 'unknown reason'}")
            continue  # Skip entities with missing cluster_id
        clusters[cluster_id].append(e)
    cluster_summaries = []
    role_counter = Counter()
    cross_device_count = 0
    cross_platform_count = 0
    for cluster_id, members in clusters.items():
        if not cluster_id or not isinstance(cluster_id, str) or '_' not in cluster_id:
            continue  # Skip malformed cluster_id
        device_ids = set()
        platforms = set()
        for e in members:
            if e.get('device_id'):
                device_ids.add(e['device_id'])
            if e.get('platform'):
                platforms.add(e['platform'])
        is_cross_device = len(device_ids) > 1
        is_cross_platform = len(platforms) > 1
        if is_cross_device:
            cross_device_count += 1
        if is_cross_platform:
            cross_platform_count += 1
        sample_entity_ids = [e['entity_id'] for e in members[:5]]
        # Parse cluster_role and area_id from cluster_id
        try:
            area_id, cluster_role = cluster_id.split('_', 1)
        except Exception:
            area_id, cluster_role = 'null', 'unknown'
        role_counter[cluster_role] += 1
        cluster_summaries.append({
            "cluster_id": cluster_id,
            "entity_count": len(members),
            "device_ids": list(device_ids),
            "platforms": list(platforms),
            "is_cross_device": is_cross_device,
            "is_cross_platform": is_cross_platform,
            "sample_entity_ids": sample_entity_ids,
            "cluster_role": cluster_role,
            "area_id": None if area_id == 'null' else area_id
        })
    summary = {
        "total_clusters": len(clusters),
        "cross_device_clusters": cross_device_count,
        "cross_platform_clusters": cross_platform_count,
        "roles": dict(role_counter)
    }
    out = {
        "clusters": cluster_summaries,
        "summary": summary
    }
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = Path(__file__).parent.parent / f"data/cluster_summary.{ts}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    # Log output file path
    log_msg = f"[CLUSTER-SUMMARY] Output: {out_path}\n"
    with open(Path(__file__).parent.parent / "copilot_patchlog_overview.log", "a") as log:
        log.write(log_msg)
    patchlog_path = Path(__file__).parent.parent / "copilot_patches/PATCH-CLUSTER-ROLE-COVERAGE-SUMMARY.log"
    os.makedirs(patchlog_path.parent, exist_ok=True)
    with open(patchlog_path, "a") as log:
        log.write(log_msg)
    print(f"Cluster summary complete. Results written to {out_path}")

if __name__ == "__main__":
    main()
