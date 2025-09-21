import json
import os
import argparse
from pathlib import Path
import sys
from collections import defaultdict
import datetime

print(f"[DEBUG] sys.path before patch: {sys.path}")
print(f"[DEBUG] CWD: {os.getcwd()}")
# --- Ensure project root and CWD are in sys.path for local imports ---
project_root = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(project_root, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)
print(f"[DEBUG] sys.path after patch: {sys.path}")

# --- Local imports (after sys.path patch) ---
from registry.utils.inference import infer_area_id, infer_role, patch_devices
from registry.utils.cluster import make_cluster_id, build_device_map, get_device_area, resolve_cluster_metadata
from registry.utils.config import get_input_path, get_output_path, get_path_from_settings
from registry.utils.constants import COMMON_AREAS

# Remove all hardcoded path constants here. All paths are set after argument parsing.

def main():
    def is_nonempty_json(path):
        try:
            if not Path(path).exists() or Path(path).stat().st_size == 0:
                return False
            with open(path) as f:
                data = json.load(f)
            return bool(data)
        except Exception:
            return False

    # --- Path setup and argument parsing ---
    parser = argparse.ArgumentParser(description="Generate Alpha Tier Registries with robust diagnostics.")
    parser.add_argument('--fingerprint', required=False, help='Path to post-reboot enriched fingerprint map')
    parser.add_argument('--migration', required=True, help='Path to Rosetta v5 migration map')
    parser.add_argument('--output_dir', default='output/alpha_tier/', help='Output directory for all files')
    parser.add_argument('--verbose_stdout', action='store_true', help='Enable verbose stdout logging')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    import glob
    if args.fingerprint:
        FINGERPRINT_PATH = args.fingerprint
    else:
        candidates = glob.glob('input/mappings/entity_fingerprint_map.*.json')
        if not candidates:
            print('[FATAL] No fingerprint map found in input/mappings/.')
            sys.exit(1)
        FINGERPRINT_PATH = sorted(candidates)[-1]
    MIGRATION_PATH = args.migration
    ALPHA_SENSOR_REGISTRY_PATH = os.path.join(args.output_dir, 'alpha_sensor_registry.json')
    ALPHA_LIGHT_REGISTRY_PATH = os.path.join(args.output_dir, 'alpha_light_registry.json')
    CLUSTER_TRACE_PATH = os.path.join(args.output_dir, 'cluster_assignment_trace.json')
    CLUSTER_SKIP_PATH = os.path.join(args.output_dir, 'cluster_skip_trace.json')
    CLUSTER_SCHEMA_REPORT_PATH = os.path.join(args.output_dir, 'alpha_cluster_schema_validation_report.json')
    PATCH_AUDIT_LOG = os.path.join(args.output_dir, 'alpha_registry_patch_audit.log')
    COPILOT_LOG = "copilot_patchlog_overview.log"
    ERROR_DIAG_PATH = os.path.join(args.output_dir, 'alpha_registry_error_diagnostics.log')
    DELTA_LOG_PATH = os.path.join(args.output_dir, 'rehydration_delta_log.alpha.json')
    UNRESOLVED_PATH = os.path.join(args.output_dir, 'unresolved_entities.alpha.log.json')
    SAMPLE_EXCLUDED_PATH = os.path.join(args.output_dir, 'sample_excluded_entities.alpha.json')
    COMPLETENESS_AUDIT_PATH = os.path.join(args.output_dir, 'alpha_registry_completeness_audit.json')
    SUMMARY_LOG_PATH = os.path.join(args.output_dir, 'alpha_registry_summary.log')

    class DebugLogger:
        def __init__(self, path):
            self.f = open(path, "w")
        def log(self, msg):
            print(msg)
            self.f.write(msg + "\n")
        def close(self):
            self.f.close()
    debug_log = DebugLogger("clustering_debug_output.log")

    def log_copilot_patch(msg):
        ts = datetime.datetime.now().isoformat()
        with open(COPILOT_LOG, 'a') as f:
            f.write(f"[{ts}] {msg}\n")

    # --- Input validation ---
    input_errors = []
    if not is_nonempty_json(FINGERPRINT_PATH):
        input_errors.append(f"[FATAL] Fingerprint map missing or empty: {FINGERPRINT_PATH}")
    if not is_nonempty_json(MIGRATION_PATH):
        input_errors.append(f"[FATAL] Migration map missing or empty: {MIGRATION_PATH}")
    if input_errors:
        with open(ERROR_DIAG_PATH, 'w') as f:
            for err in input_errors:
                f.write(err + '\n')
        log_copilot_patch(f"[FATAL] Input validation failed. See {ERROR_DIAG_PATH}: {input_errors}")
        print(f"[FATAL] Input validation failed. See {ERROR_DIAG_PATH}")
        sys.exit(1)

    with open(FINGERPRINT_PATH) as f:
        fingerprint_map = json.load(f)
    with open(MIGRATION_PATH) as f:
        migration_map = json.load(f)

    log_copilot_patch(f"Loaded {len(fingerprint_map)} entities from fingerprint map")
    log_copilot_patch(f"Loaded {len(migration_map)} migration map entries")

    # --- Area registry loading ---
    # Load area_registry_path from settings.conf.yaml if available
    import yaml
    settings_path = 'settings.conf.yaml'
    settings = {}
    if Path(settings_path).exists():
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
    try:
        area_registry_path = get_path_from_settings(settings, 'area_registry')
    except KeyError:
        area_registry_path = 'input/core.area_registry'
    area_ids = None
    if Path(area_registry_path).exists():
        with open(area_registry_path) as f:
            area_registry = json.load(f)
            area_ids = set(a['id'] for a in area_registry.get('data', {}).get('areas', []))
    else:
        area_ids = set(COMMON_AREAS)

    # --- Clustering logic ---
    clusters = defaultdict(list)
    cluster_assignment_trace = []
    skip_trace = []
    cluster_schema_report = []
    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}

    for entity_id, meta in fingerprint_map.items():
        area = infer_area_id(meta, {}, area_ids) or "unknown_area"
        # Patch: ensure area is always hashable (convert dicts to string)
        if isinstance(area, tuple) and len(area) == 2 and isinstance(area[1], dict):
            import json as _json
            area_key = f"{area[0]}|" + _json.dumps(area[1], sort_keys=True)
        else:
            area_key = area
        role = meta.get("role") or "unclassified"
        canonical = meta.get("canonical_entity_key") or "unknown_key"
        debug_log.log(f"  final_area: {area}, role: {role}, key: {canonical}")
        tier = meta.get("tier") or "unknown_tier"
        confidence = meta.get("confidence_score", 0)
        fallback_fields = []
        if meta.get("final_area") in [None, "unknown"]:
            fallback_fields.append("final_area")
        if meta.get("role") in [None, "unknown"]:
            fallback_fields.append("role")
        if meta.get("semantic_role") in [None, "unknown"]:
            fallback_fields.append("semantic_role")
        schema_complete = len(fallback_fields) == 0
        try:
            conf_val = float(confidence) if confidence != "unknown" else 0.0
        except Exception:
            conf_val = 0.0
        if schema_complete and conf_val >= 0.85:
            tier_label = "tier1"
        elif schema_complete:
            tier_label = "tier2"
        else:
            tier_label = "tier3"
        tier_counts[tier_label] += 1
        if not entity_id or not canonical:
            debug_log.log(f"  → SKIPPED: missing critical fields for entity {entity_id}")
            skip_trace.append({
                "entity_id": entity_id,
                "reason": "missing entity_id or canonical_entity_key",
                "meta": meta
            })
            continue
        cluster_key = (area_key, role, canonical)
        debug_log.log(f"  → cluster_key = ({area_key}, {role}, {canonical})")
        clusters[cluster_key].append(entity_id)
        cluster_assignment_trace.append({
            "entity_id": entity_id,
            "cluster_key": cluster_key,
            "tier": tier_label,
            "reason": "assigned",
            "schema_complete": schema_complete,
            "fallback_fields": fallback_fields,
            "meta": meta
        })

    # --- Build alpha_sensor_registry.json ---
    alpha_registry = []
    for cluster_key, entity_ids in clusters.items():
        area, role, canonical = cluster_key
        fallback_fields = []
        if area == "unknown_area":
            fallback_fields.append("final_area")
        if role == "unclassified":
            fallback_fields.append("role")
        if canonical == "unknown_key":
            fallback_fields.append("canonical_entity_key")
        schema_complete = len(fallback_fields) == 0
        cluster_obj = {
            "cluster_id": make_cluster_id(area, role),
            "final_area": area,
            "role": role,
            "canonical_entity_key": canonical,
            "entity_ids": entity_ids,
            "tier": [fingerprint_map[eid].get("tier", "unknown_tier") for eid in entity_ids],
            "confidence_scores": [fingerprint_map[eid].get("confidence_score", 0) for eid in entity_ids],
            "schema_complete": schema_complete,
            "fallback_fields": fallback_fields
        }
        alpha_registry.append(cluster_obj)

    # --- Write outputs ---
    def emit_json(path, obj):
        with open(path, 'w') as f:
            json.dump(obj, f, indent=2)

    def emit_registry_skeleton(path, key):
        with open(path, 'w') as f:
            json.dump({key: {}}, f, indent=2)
            f.write("\n/* __meta__: zero population due to exclusion */\n")

    debug_log.log(f"Wrote {len(alpha_registry)} clusters to alpha_sensor_registry.json")
    emit_json(ALPHA_SENSOR_REGISTRY_PATH, alpha_registry)
    debug_log.log(f"Wrote {len(cluster_assignment_trace)} entities to cluster_assignment_trace.json")
    emit_json(CLUSTER_TRACE_PATH, cluster_assignment_trace)
    debug_log.log(f"Wrote {len(skip_trace)} entities to cluster_skip_trace.json")
    emit_json(CLUSTER_SKIP_PATH, skip_trace)
    debug_log.log(f"Wrote {len(alpha_registry)} clusters to alpha_cluster_schema_validation_report.json")
    emit_json(CLUSTER_SCHEMA_REPORT_PATH, alpha_registry)
    debug_log.close()

    # Log stats
    summary = {
        "total_entities": len(fingerprint_map),
        "total_clusters": len(alpha_registry),
        "tier_counts": tier_counts,
        "skipped": len(skip_trace)
    }
    for log_path in [PATCH_AUDIT_LOG, COPILOT_LOG]:
        with open(log_path, "a") as f:
            f.write(f"[alpha_sensor_registry] {json.dumps(summary)}\n")

    # --- Entity filtering and matching for diagnostics ---
    matched_entities = []
    excluded_entities = []
    roles_seen = set()
    domains_touched = set()
    migration_keys = {e.get('pre_reboot_entity_id') or e.get('old_entity_id') for e in migration_map}
    for entity_id, meta in fingerprint_map.items():
        canonical_key = meta.get('canonical_entity_key')
        role = meta.get('role')
        area = meta.get('final_area')
        present_in_migration = entity_id in migration_keys or canonical_key in migration_keys
        reason = None
        if not present_in_migration:
            reason = 'not_in_migration_map'
        if reason:
            excluded_entities.append({
                'entity_id': entity_id,
                'canonical_entity_key': canonical_key,
                'role': role,
                'area': area,
                'reason_for_exclusion': reason,
                'present_in_migration_map': present_in_migration
            })
        else:
            matched_entities.append(entity_id)
            if role:
                roles_seen.add(role)
            if entity_id and '.' in entity_id:
                domains_touched.add(entity_id.split('.')[0])

    emit_json(DELTA_LOG_PATH, {'matched_entities': matched_entities, 'excluded_entities': excluded_entities})
    log_copilot_patch(f"Emitted delta log: {DELTA_LOG_PATH}")
    emit_json(UNRESOLVED_PATH, excluded_entities)
    log_copilot_patch(f"Emitted unresolved entities: {UNRESOLVED_PATH}")
    emit_json(SAMPLE_EXCLUDED_PATH, excluded_entities[:10])
    log_copilot_patch(f"Emitted sample excluded entities: {SAMPLE_EXCLUDED_PATH}")
    emit_json(COMPLETENESS_AUDIT_PATH, {
        'included': len(matched_entities),
        'excluded': len(excluded_entities),
        'coverage_percent': 0 if not fingerprint_map else round(100 * len(matched_entities) / len(fingerprint_map), 2),
        'roles_seen': sorted(roles_seen),
        'domains_touched': sorted(domains_touched)
    })
    log_copilot_patch(f"Emitted completeness audit: {COMPLETENESS_AUDIT_PATH}")
    emit_registry_skeleton(ALPHA_SENSOR_REGISTRY_PATH, 'sensors')
    log_copilot_patch(f"Emitted alpha sensor registry: {ALPHA_SENSOR_REGISTRY_PATH}")
    emit_registry_skeleton(ALPHA_LIGHT_REGISTRY_PATH, 'lights')
    log_copilot_patch(f"Emitted alpha light registry: {ALPHA_LIGHT_REGISTRY_PATH}")
    summary_diag = {
        'included': len(matched_entities),
        'excluded': len(excluded_entities),
        'coverage_percent': 0 if not fingerprint_map else round(100 * len(matched_entities) / len(fingerprint_map), 2),
        'roles_seen': sorted(roles_seen),
        'domains_touched': sorted(domains_touched)
    }
    with open(SUMMARY_LOG_PATH, 'a') as f:
        f.write(json.dumps(summary_diag) + '\n')
    log_copilot_patch(f"Emitted summary log: {SUMMARY_LOG_PATH}")
    with open(COPILOT_LOG, 'a') as f:
        f.write(f"[alpha_registry] {json.dumps(summary_diag)}\n")
    log_copilot_patch(f"[alpha_registry] {json.dumps(summary_diag)}")

    # --- Verbose/quiet stdout ---
    if args.verbose_stdout:
        print(f"[SUMMARY] Alpha registry generation complete. Included: {len(matched_entities)}, Excluded: {len(excluded_entities)}")
        print(f"[SUMMARY] Output dir: {args.output_dir}")
    else:
        print(f"[SUMMARY] Alpha registry generation complete. See {SUMMARY_LOG_PATH}")

if __name__ == "__main__":
    main()
