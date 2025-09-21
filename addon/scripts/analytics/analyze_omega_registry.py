#!/usr/bin/env python3
"""
ANALYTICS TOOLBOX FOR OMEGA REGISTRY
Script: analyze_omega_registry.py
Version: 1.0 (2025-07-21)
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
import yaml

from addon.utils.paths import canonical_path

sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from utils.input_list_extract import extract_data

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze omega_registry_master.json for structural health and completeness.")
    parser.add_argument('--input', required=True, help='Path to omega_registry_master.json')
    parser.add_argument('--log', required=True, help='Path to cumulative analytics log file')
    return parser.parse_args()

def safe_load_json(path):
    with open(path) as f:
        return json.load(f)

def analyze_core_entity_registry_device_class_breakdown(entity_registry_path):
    """
    Analyze core.entity_registry for non-null device_class and original_device_class entries and provide a breakdown.
    Uses the centralized extract_data utility for robust extraction.
    Returns a dict with the breakdown.
    """
    import json
    from collections import Counter
    from datetime import datetime
    # Load the file as JSON
    with open(entity_registry_path) as f:
        try:
            content = json.load(f)
        except Exception:
            f.seek(0)
            content = [json.loads(line) for line in f if line.strip()]
    # Use the centralized extractor
    entries = extract_data(entity_registry_path, content)

    device_class_counter = Counter()
    total_with_device_class = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        dc = entry.get('device_class')
        odc = entry.get('original_device_class')
        # Count both fields, prefer device_class if both present
        if dc is not None:
            device_class_counter[dc] += 1
            total_with_device_class += 1
        elif odc is not None:
            device_class_counter[odc] += 1
            total_with_device_class += 1

    return {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'input_file': os.path.abspath(entity_registry_path),
        'total_with_device_class': total_with_device_class,
        'device_class_breakdown': dict(device_class_counter),
    }

def analyze_connections_breakdown(entities):
    """
    Analyze the 'connections' field in omega_registry_master.json entities.
    Returns a dict with identifier types, frequency, and example values.
    """
    from collections import Counter, defaultdict
    id_type_counter = Counter()
    id_type_examples = defaultdict(list)
    for e in entities:
        conns = e.get('connections', [])
        for conn in conns:
            if isinstance(conn, (list, tuple)) and len(conn) == 2:
                id_type = conn[0]
                id_type_counter[id_type] += 1
                if len(id_type_examples[id_type]) < 2:
                    id_type_examples[id_type].append(conn[1])
    return {
        'identifier_type_counts': dict(id_type_counter),
        'identifier_type_examples': {k: v for k, v in id_type_examples.items()}
    }

def main():
    args = parse_args()
    data = safe_load_json(args.input)
    now = datetime.now().isoformat(timespec='seconds')
    script_version = '1.0'

    # --- Metrics ---
    entity_count = len(data)

    # Join Origin Coverage
    join_origin_counter = Counter()
    for e in data:
        jo = tuple(e.get('join_origin', []))
        join_origin_counter[jo] += 1

    # Join Confidence Stats
    join_confidences = [e.get('join_confidence') for e in data if 'join_confidence' in e]
    join_conf_counter = Counter(join_confidences)
    join_conf_numeric = [jc for jc in join_confidences if isinstance(jc, (int, float))]
    join_conf_stats = {
        'min': min(join_conf_numeric) if join_conf_numeric else None,
        'max': max(join_conf_numeric) if join_conf_numeric else None,
        'mean': sum(join_conf_numeric)/len(join_conf_numeric) if join_conf_numeric else None,
        'counts': dict(join_conf_counter)
    }

    # Canonical fields to check
    canonical_fields = [
        'name', 'device_class', 'floor_id', 'connections', 'labels', 'manufacturer',
        'model', 'mac', 'area_id', 'suggested_area', 'device_id', 'entry_id',
        'integration', 'via_device_id', 'state_snapshot', 'exposed_to_assistant',
        'join_confidence', 'join_origin', 'enrichment_depth', 'field_inheritance', 'source'
    ]
    field_completeness = {}
    for field in canonical_fields:
        non_null = 0
        empty_list = 0
        missing = 0
        for e in data:
            if field not in e:
                missing += 1
            elif e[field] is None:
                pass
            elif isinstance(e[field], list) and len(e[field]) == 0:
                empty_list += 1
            else:
                non_null += 1
        field_completeness[field] = {
            'percent_non_null': round(100 * non_null / entity_count, 2),
            'percent_empty_list': round(100 * empty_list / entity_count, 2),
            'percent_missing': round(100 * missing / entity_count, 2)
        }

    # Enrichment Depth Distribution
    enrichment_depths = [e.get('enrichment_depth') for e in data if 'enrichment_depth' in e]
    enrichment_depth_hist = dict(Counter(enrichment_depths))

    # Missing Critical Fields
    malformed = []
    for idx, e in enumerate(data):
        missing = [k for k in ['entity_id', 'domain', 'platform'] if k not in e or e[k] is None]
        if missing:
            malformed.append({'index': idx, 'missing': missing})

    # --- Output Block ---
    # Reformat join_origin_coverage for YAML list of dicts
    join_origin_coverage = []
    for k, v in join_origin_counter.items():
        join_origin_coverage.append({'origins': list(k), 'count': v})
    block = {
        'timestamp': now,
        'script_version': script_version,
        'input_file': os.path.abspath(args.input),
        'entity_count': entity_count,
        'join_origin_coverage': join_origin_coverage,
        'join_confidence_stats': join_conf_stats,
        'field_completeness': field_completeness,
        'enrichment_depth_histogram': enrichment_depth_hist,
        'malformed_entities': malformed,
        'connections_breakdown': analyze_connections_breakdown(data),  # PATCH: add to output
    }

    # --- Source Analytics Section ---
    entity_registry_path = str(canonical_path('registry_inputs', 'core.entity_registry'))
    if os.path.exists(entity_registry_path):
        block['source_analytics'] = {
            'core_entity_registry_device_class': analyze_core_entity_registry_device_class_breakdown(entity_registry_path)
        }
        print("[INFO] Source analytics (device_class breakdown) complete. Appended to output block.")
    else:
        print(f"[WARN] core.entity_registry not found at {entity_registry_path}, skipping source analytics.")

    # Append as YAML block
    with open(args.log, 'a') as f:
        f.write('\n---\n')
        yaml.dump(block, f, sort_keys=False)

    print(f"[INFO] Omega registry analytics complete. Entity count: {entity_count}. Appended to log.")

if __name__ == '__main__':
    main()
