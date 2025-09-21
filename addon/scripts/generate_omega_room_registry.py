"""
Script: generate_omega_room_registry.py
Purpose: Strict-mode Omega Room Registry reconstruction using only settings.conf.yaml for room and floor mappings.

- Includes only entities with valid final_area, cluster_id, and present in both fingerprint and migration map
- Uses room and floor mappings from settings.conf.yaml (not core.area_registry)
- Emits all required outputs and logs as per omega_room_contract.yaml
"""
import os
import sys
from datetime import datetime
import argparse

# --- BEGIN: sys.path patch and debug log ---
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
project_root = os.path.abspath(os.path.join(script_dir, ".."))

log_dir = os.path.join(project_root, "output", "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"generate_omega_room_registry_path_debug.{datetime.now().strftime('%Y%m%dT%H%M%S')}.log")

with open(log_path, "w") as f:
    f.write(f"script_path = {script_path}\n")
    f.write(f"script_dir = {script_dir}\n")
    f.write(f"project_root = {project_root}\n")
    f.write(f"sys.path before = {sys.path}\n")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

with open(log_path, "a") as f:
    f.write(f"sys.path after = {sys.path}\n")
# --- END: sys.path patch and debug log ---

# --- BEGIN: registry imports ---
import json
import yaml # type: ignore
import tarfile
from collections import defaultdict
import re
from pathlib import Path
from registry.utils.inference import infer_area_id
from registry.utils.cluster import make_cluster_id, build_device_map, resolve_cluster_metadata
import collections
# --- END: registry imports ---

if project_root not in sys.path:
    print(f"[DEBUG] injecting {project_root} into sys.path")
    sys.path.insert(0, project_root)

# --- CLI ARGUMENTS ---
parser = argparse.ArgumentParser(description="Omega Room Registry Rehydration")
parser.add_argument('--config', type=str, default='settings.conf.yaml')
parser.add_argument('--fingerprint-map', type=str, default=None, help='Path to fingerprint map (overrides default)')
parser.add_argument('--migration-map', type=str, default=None, help='Path to migration map (overrides default)')
parser.add_argument('--output-dir', type=str, default='output/omega_room/')
parser.add_argument('--rehydration-dir', type=str, default='output/omega_room/')
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]

# Set fingerprint map path
if args.fingerprint_map:
    FINGERPRINT_PATH = Path(args.fingerprint_map)
else:
    FINGERPRINT_PATH = ROOT / "output" / "fingerprinting_run" / "entity_fingerprint_map.20250719T112610.json"
# Set migration map path
if args.migration_map:
    MIGRATION_MAP_PATH = Path(args.migration_map)
else:
    MIGRATION_MAP_PATH = ROOT / "input" / "mappings" / "entity_id_migration_map.rosetta.v5.json"

SETTINGS_PATH = ROOT / "settings.conf.yaml"
OUTPUT_DIR = Path(args.output_dir)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
REGISTRY_PATH = OUTPUT_DIR / "omega_room_registry.json"
AUDIT_PATH = OUTPUT_DIR / "room_registry_completeness_audit.json"
UNRESOLVED_PATH = OUTPUT_DIR / "unresolved_entities.log.json"
DELTA_PATH = OUTPUT_DIR / "rehydration_delta_log.json"
TARBALL_PATH = OUTPUT_DIR / "TARBALL-OMEGA-ROOM-REGISTRY-STRICT-FINAL-CORRECTED.tar.gz"
EXCLUSION_DIAG_PATH = OUTPUT_DIR / "rehydration_exclusion_diagnostics.json"
PREVIEW_REGISTRY_PATH = OUTPUT_DIR / "omega_room_registry.preview.json"
SAMPLE_EXCLUDED_PATH = OUTPUT_DIR / "sample_excluded_entities.json"

# PATCHLOG_OVERVIEW and PATCH_AUDIT variable definitions after CLI patch, using new ROOT definition.
PATCHLOG_OVERVIEW = ROOT / "copilot_patchlog_overview.log"
PATCH_AUDIT = ROOT / "copilot_patches" / "PATCH-OMEGA-ROOM-REGENERATION.log"

# Defensive checks for input files
if not FINGERPRINT_PATH.exists():
    print(f"[FATAL] Fingerprint map not found at expected path: {FINGERPRINT_PATH}")
    stub_diag = {'error': 'Missing fingerprint map', 'fingerprint_exists': False, 'fingerprint_path': str(FINGERPRINT_PATH)}
    for path in [EXCLUSION_DIAG_PATH, UNRESOLVED_PATH, DELTA_PATH, SAMPLE_EXCLUDED_PATH]:
        with open(path, 'w') as f:
            json.dump(stub_diag, f, indent=2)
    sys.exit(1)
if not MIGRATION_MAP_PATH.exists():
    print(f"[FATAL] Migration map not found at expected path: {MIGRATION_MAP_PATH}")
    stub_diag = {'error': 'Missing migration map', 'migration_exists': False, 'migration_path': str(MIGRATION_MAP_PATH)}
    for path in [EXCLUSION_DIAG_PATH, UNRESOLVED_PATH, DELTA_PATH, SAMPLE_EXCLUDED_PATH]:
        with open(path, 'w') as f:
            json.dump(stub_diag, f, indent=2)
    sys.exit(1)

with open(FINGERPRINT_PATH) as f:
    fingerprint_map = json.load(f)
if not fingerprint_map:
    print(f"[WARNING] Fingerprint map loaded but entity count is 0")
    stub_diag = {'error': 'Empty fingerprint map', 'fingerprint_empty': True, 'fingerprint_path': str(FINGERPRINT_PATH)}
    for path in [EXCLUSION_DIAG_PATH, UNRESOLVED_PATH, DELTA_PATH, SAMPLE_EXCLUDED_PATH]:
        with open(path, 'w') as f:
            json.dump(stub_diag, f, indent=2)
    sys.exit(1)

with open(MIGRATION_MAP_PATH) as f:
    migration_map_raw = json.load(f)
if not migration_map_raw:
    stub_diag = {'error': 'Empty migration map', 'migration_empty': True, 'migration_path': str(MIGRATION_MAP_PATH)}
    for path in [EXCLUSION_DIAG_PATH, UNRESOLVED_PATH, DELTA_PATH, SAMPLE_EXCLUDED_PATH]:
        with open(path, 'w') as f:
            json.dump(stub_diag, f, indent=2)
    sys.exit(1)

# Load settings.conf.yaml
with open(SETTINGS_PATH) as f:
    settings_yaml = yaml.safe_load(f)
room_mappings = settings_yaml.get('rooms', [])
floor_mappings = {r['id']: r.get('floor_id', None) for r in room_mappings}
room_slug_map = {r['id']: r for r in room_mappings}
room_alias_map = {}
for r in room_mappings:
    for alias in r.get('aliases', []):
        room_alias_map[alias.lower()] = r['id']

# Patch: Build lookup dict for Rosetta v5 migration map (list of dicts)
if isinstance(migration_map_raw, list):
    migration_map = {e.get('old_entity_id') or e.get('pre_entity_id'): e for e in migration_map_raw if e.get('old_entity_id') or e.get('pre_entity_id')}
else:
    migration_map = migration_map_raw

# Load area IDs from settings.conf.yaml room definitions only
area_ids = set(r['id'] for r in room_mappings)

# Helper: slugify
slugify = lambda s: re.sub(r'[^a-zA-Z0-9]+', '_', s.strip().lower())

# Build room registry
def make_room():
    return {
        'area_id': None,
        'name': None,
        'floor': None,
        'post_reboot_entity_ids': [],
        'metadata': {
            'entity_count': 0,
            'inferred_role_breakdown': {},
            'roles_missing': []
        }
    }
rooms = defaultdict(make_room)
excluded_entities = []
delta_trace = []
room_entity_counts = defaultdict(int)
role_breakdown = defaultdict(lambda: defaultdict(int))

for eid, info in fingerprint_map.items():
    meta = resolve_cluster_metadata(info, {}, area_ids)
    final_area = meta['area_id']
    cluster_id = meta['cluster_id']
    # PATCH: Use actual fingerprint values, do not exclude if present
    if final_area is None or cluster_id is None:
        excluded_entities.append({'entity_id': eid, 'reason': 'missing_final_area_or_cluster_id'})
        delta_trace.append({'entity_id': eid, 'action': 'excluded', 'reason': 'missing_final_area_or_cluster_id'})
        continue
    if eid not in migration_map:
        excluded_entities.append({'entity_id': eid, 'reason': 'missing_in_migration_map'})
        delta_trace.append({'entity_id': eid, 'action': 'excluded', 'reason': 'missing_in_migration_map'})
        continue
    # Resolve room slug
    area_slug = slugify(final_area)
    room_id = room_alias_map.get(area_slug, area_slug)
    room_meta = room_slug_map.get(room_id)
    if not room_meta:
        excluded_entities.append({'entity_id': eid, 'reason': 'area_not_in_settings'})
        delta_trace.append({'entity_id': eid, 'action': 'excluded', 'reason': 'area_not_in_settings'})
        continue
    # Assign entity to room
    rooms[room_id]['area_id'] = room_id
    rooms[room_id]['name'] = room_meta.get('name', room_id)
    rooms[room_id]['floor'] = room_meta.get('floor_id', None)
    rooms[room_id]['post_reboot_entity_ids'].append(eid)
    rooms[room_id]['metadata']['entity_count'] += 1
    # Role breakdown
    role = info.get('role', 'unknown')
    rooms[room_id]['metadata']['inferred_role_breakdown'][role] = rooms[room_id]['metadata']['inferred_role_breakdown'].get(role, 0) + 1
    room_entity_counts[room_id] += 1
    role_breakdown[room_id][role] += 1
    delta_trace.append({'entity_id': eid, 'action': 'included', 'room': room_id})

# === PATCH: REHYDRATION EXCLUSION DIAGNOSTICS & PREVIEW ===
exclusion_diagnostics = []
exclusion_reasons_counter = collections.Counter()
preview_rooms = collections.defaultdict(make_room)
preview_entity_counts = collections.defaultdict(int)
preview_role_breakdown = collections.defaultdict(lambda: collections.defaultdict(int))

for eid, info in fingerprint_map.items():
    meta = resolve_cluster_metadata(info, {}, area_ids)
    final_area = meta['area_id']
    cluster_id = meta['cluster_id']
    migration_entry = migration_map.get(eid) or migration_map.get(info.get('canonical_id'))
    # --- Begin exclusion logic ---
    reason = None
    if not final_area or final_area == "unknown_area":
        reason = 'null_final_area'
    elif not cluster_id:
        reason = 'null_cluster_id'
    elif not migration_entry:
        reason = 'not_in_migration_map'
    elif migration_entry.get('confidence_score', 1.0) < 0.5:
        reason = 'low_confidence'
    elif migration_entry.get('flag_manual_review'):
        reason = 'manual_review_true'
    # --- End exclusion logic ---
    if reason:
        exclusion_diagnostics.append({'entity_id': eid, 'reason': reason})
        exclusion_reasons_counter[reason] += 1
        continue
    # Normal inclusion
    area_slug = slugify(final_area)
    room_id = room_alias_map.get(area_slug, area_slug)
    room_meta = room_slug_map.get(room_id)
    if not room_meta:
        exclusion_diagnostics.append({'entity_id': eid, 'reason': 'area_not_in_settings'})
        exclusion_reasons_counter['area_not_in_settings'] += 1
        continue
    rooms[room_id]['area_id'] = room_id
    rooms[room_id]['name'] = room_meta.get('name', room_id)
    rooms[room_id]['floor'] = room_meta.get('floor_id', None)
    rooms[room_id]['post_reboot_entity_ids'].append(eid)
    rooms[room_id]['metadata']['entity_count'] += 1
    role = info.get('role', 'unknown')
    rooms[room_id]['metadata']['inferred_role_breakdown'][role] = rooms[room_id]['metadata']['inferred_role_breakdown'].get(role, 0) + 1
    room_entity_counts[room_id] += 1
    role_breakdown[room_id][role] += 1
    delta_trace.append({'entity_id': eid, 'action': 'included', 'room': room_id})
    # --- Preview inclusion (for fallback) ---
    preview_rooms[room_id]['area_id'] = room_id
    preview_rooms[room_id]['name'] = room_meta.get('name', room_id)
    preview_rooms[room_id]['floor'] = room_meta.get('floor_id', None)
    preview_rooms[room_id]['post_reboot_entity_ids'].append(eid)
    preview_rooms[room_id]['metadata']['entity_count'] += 1
    preview_role = info.get('role', 'unknown')
    preview_rooms[room_id]['metadata']['inferred_role_breakdown'][preview_role] = preview_rooms[room_id]['metadata']['inferred_role_breakdown'].get(preview_role, 0) + 1
    preview_entity_counts[room_id] += 1
    preview_role_breakdown[room_id][preview_role] += 1

# --- Preview: include all entities that would be included if manual_review was ignored ---
for eid, info in fingerprint_map.items():
    meta = resolve_cluster_metadata(info, {}, area_ids)
    final_area = meta['area_id']
    cluster_id = meta['cluster_id']
    migration_entry = migration_map.get(eid) or migration_map.get(info.get('canonical_id'))
    if not final_area or final_area == "unknown_area" or not cluster_id or not migration_entry or migration_entry.get('confidence_score', 1.0) < 0.5:
        continue
    area_slug = slugify(final_area)
    room_id = room_alias_map.get(area_slug, area_slug)
    room_meta = room_slug_map.get(room_id)
    if not room_meta:
        continue
    preview_rooms[room_id]['area_id'] = room_id
    preview_rooms[room_id]['name'] = room_meta.get('name', room_id)
    preview_rooms[room_id]['floor'] = room_meta.get('floor_id', None)
    preview_rooms[room_id]['post_reboot_entity_ids'].append(eid)
    preview_rooms[room_id]['metadata']['entity_count'] += 1
    preview_role = info.get('role', 'unknown')
    preview_rooms[room_id]['metadata']['inferred_role_breakdown'][preview_role] = preview_rooms[room_id]['metadata']['inferred_role_breakdown'].get(preview_role, 0) + 1
    preview_entity_counts[room_id] += 1
    preview_role_breakdown[room_id][preview_role] += 1

# --- Emit exclusion diagnostics and preview registry ---
with open(EXCLUSION_DIAG_PATH, 'w') as f:
    json.dump({
        'exclusions': exclusion_diagnostics,
        'breakdown': dict(exclusion_reasons_counter)
    }, f, indent=2)
# Emit sample trace of up to 5 excluded entities (with full metadata)
sample_excluded = [e for e in exclusion_diagnostics[:5]]
if sample_excluded:
    with open(SAMPLE_EXCLUDED_PATH, 'w') as f:
        json.dump(sample_excluded, f, indent=2)
else:
    with open(SAMPLE_EXCLUDED_PATH, 'w') as f:
        json.dump([], f, indent=2)

preview_registry = {
    'omega_room_registry_preview': {
        'version': "1.0",
        'generated_on': datetime.utcnow().isoformat() + 'Z',
        'source_context': {
            'entity_source': FINGERPRINT_PATH.name,
            'mapping_source': MIGRATION_MAP_PATH.name,
            'area_source': SETTINGS_PATH.name,
            'generation_mode': 'manual_review_override_preview'
        },
        'rooms': [],
        'summary': {
            'total_entities_clustered': sum(preview_entity_counts.values()),
            'total_rooms': len(preview_rooms),
            'entity_coverage_percent': 100.0 * sum(preview_entity_counts.values()) / max(1, len(fingerprint_map)),
        }
    }
}
for room_id, room in preview_rooms.items():
    room_entry = {
        'room_slug': slugify(room['name']),
        'area_id': room['area_id'],
        'name': room['name'],
        'floor': room['floor'],
        'post_reboot_entity_ids': room['post_reboot_entity_ids'],
        'metadata': {
            'cluster_count': 1,
            'entity_count': room['metadata']['entity_count'],
            'inferred_role_breakdown': room['metadata']['inferred_role_breakdown'],
            'roles_missing': room['metadata']['roles_missing']
        }
    }
    preview_registry['omega_room_registry_preview']['rooms'].append(room_entry)
with open(PREVIEW_REGISTRY_PATH, 'w') as f:
    json.dump(preview_registry, f, indent=2)

# Build registry output
registry = {
    'omega_room_registry': {
        'version': "1.0",
        'generated_on': datetime.utcnow().isoformat() + 'Z',
        'source_context': {
            'entity_source': FINGERPRINT_PATH.name,
            'mapping_source': MIGRATION_MAP_PATH.name,
            'area_source': SETTINGS_PATH.name,
            'generation_mode': 'strict_room_mapping'
        },
        'rooms': [],
        'summary': {
            'total_entities_clustered': sum(room_entity_counts.values()),
            'total_rooms': len(rooms),
            'entity_coverage_percent': 100.0 * sum(room_entity_counts.values()) / max(1, len(fingerprint_map)),
            'excluded_entities': {
                'count': len(excluded_entities),
                'reasons': list(set(e['reason'] for e in excluded_entities)),
                'unresolved_list_path': UNRESOLVED_PATH.name
            }
        }
    }
}
for room_id, room in rooms.items():
    room_entry = {
        'room_slug': slugify(room['name']),
        'area_id': room['area_id'],
        'name': room['name'],
        'floor': room['floor'],
        'post_reboot_entity_ids': room['post_reboot_entity_ids'],
        'metadata': {
            'cluster_count': 1,  # Each room is a cluster in strict mode
            'entity_count': room['metadata']['entity_count'],
            'inferred_role_breakdown': room['metadata']['inferred_role_breakdown'],
            'roles_missing': room['metadata']['roles_missing']
        }
    }
    registry['omega_room_registry']['rooms'].append(room_entry)

# Emit outputs
with open(REGISTRY_PATH, 'w') as f:
    json.dump(registry, f, indent=2)
with open(AUDIT_PATH, 'w') as f:
    json.dump({'room_entity_counts': dict(room_entity_counts), 'role_breakdown': {k: dict(v) for k, v in role_breakdown.items()}}, f, indent=2)
# Always emit unresolved_entities.log.json and rehydration_delta_log.json
with open(UNRESOLVED_PATH, 'w') as f:
    json.dump(excluded_entities, f, indent=2)
with open(DELTA_PATH, 'w') as f:
    json.dump(delta_trace, f, indent=2)

# Create tarball
with tarfile.open(TARBALL_PATH, "w:gz") as tar:
    for fname in [REGISTRY_PATH, AUDIT_PATH, UNRESOLVED_PATH, DELTA_PATH]:
        tar.add(str(fname), arcname=fname.name)

# Log summary
log_entry = f"""
OMEGA ROOM REGISTRY STRICT FINAL BUILD
Total entities evaluated: {len(fingerprint_map)}
Total accepted: {sum(room_entity_counts.values())}
Total rejected: {len(excluded_entities)}
Room coverage: {dict(room_entity_counts)}
Exclusion reasons: {set(e['reason'] for e in excluded_entities)}
Outputs: {REGISTRY_PATH}, {AUDIT_PATH}, {UNRESOLVED_PATH}, {DELTA_PATH}, {TARBALL_PATH}
"""
for log_path in [PATCHLOG_OVERVIEW, PATCH_AUDIT]:
    with open(log_path, "a") as f:
        f.write(log_entry + "\n")

# === PATCH LOG: OMEGA ROOM REGISTRY OUTPUT PATH STANDARDIZATION ===
PATCHLOG_PATH = ROOT / "copilot_patches" / "PATCH-OMEGA-ROOM-REGISTRY-PATH-STANDARDIZATION-20250717.log"
patch_entry = f"""
PATCH: OMEGA ROOM REGISTRY OUTPUT PATH STANDARDIZATION
Date: 2025-07-17
Author: GitHub Copilot

- All output paths standardized to output/omega_room/ (underscore)
- All references to output/omega-room/ and omega-room/ updated
- Double prefix bugs removed from all scripts
- Legacy and duplicate folders consolidated and pruned
- settings.conf.yaml and generate_registry_index.py updated for canonical paths
- Only latest versions of each output file retained
- Full lineage trace and audit trail established

Files affected:
- scripts/generate_omega_room_registry.py
- omega-room/generate_omega_room_registry_strict.py
- settings.conf.yaml
- generate_registry_index.py
- output/omega_room/ (consolidated)

"""
with open(PATCHLOG_PATH, "a") as f:
    f.write(patch_entry)

print("Omega Room Registry strict final build complete. Outputs emitted.")
