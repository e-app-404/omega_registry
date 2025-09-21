#!/usr/bin/env python3
import json
import os
import tarfile
import yaml  # Added for YAML support
from collections import defaultdict
from registry.utils.inference import infer_area_id

# Paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, 'output', 'omega_room')
FINGERPRINT_PATH = os.path.join(ROOT, 'output', 'entity_fingerprint_map.json')
MIGRATION_PATH = os.path.join(ROOT, 'output', 'entity_id_migration_map.annotated.v4.full.json')
SETTINGS_PATH = os.path.join(ROOT, 'settings.conf.yaml')

# Load data
with open(FINGERPRINT_PATH, 'r') as f:
    fingerprint_map = json.load(f)
with open(MIGRATION_PATH, 'r') as f:
    migration_map = json.load(f)
with open(SETTINGS_PATH, 'r') as f:
    settings = yaml.safe_load(f)
area_registry = settings.get('rooms', [])

# Load area IDs from core.area_registry if available, else fallback to COMMON_AREAS
area_ids = set(a['id'] for a in area_registry) if area_registry else set()
if not area_ids:
    from registry.utils.constants import COMMON_AREAS
    area_ids = set(COMMON_AREAS)

# Build area resolution sets
area_names = set(a['name'] for a in area_registry)
area_slugs = set(a.get('slug', a['id']) for a in area_registry)
slug_to_area = {a.get('slug', a['id']): a for a in area_registry}
name_to_area = {a['name']: a for a in area_registry}
id_to_area = {a['id']: a for a in area_registry}

# Build sets for fast lookup
fingerprint_entities = set(fingerprint_map.keys())
migration_entities = set(m['entity_id'] for m in migration_map)

# Area resolution helper
def resolve_area(area):
    if not area or not isinstance(area, str) or area.strip() == '' or area == 'unknown_area':
        return None
    if area in area_ids:
        return area
    # Try case-insensitive match
    for a in area_ids:
        if area.lower() == a.lower():
            return a
    return None

# Filter valid entities
valid_entities = []
excluded_entities = []
for m in migration_map:
    eid = m['entity_id']
    inferred_area = infer_area_id(m, {}, area_ids)
    final_area = inferred_area
    cluster_id = m.get('cluster_id')
    area_meta = resolve_area(final_area)
    if (
        eid in fingerprint_entities and
        area_meta and
        cluster_id
    ):
        valid_entities.append({
            **m,
            'resolved_area': area_meta['id'] if isinstance(area_meta, dict) else area_meta,
            'room_slug': area_meta.get('slug', area_meta['id']) if isinstance(area_meta, dict) else area_meta
        })
    else:
        reason = []
        if eid not in fingerprint_entities:
            reason.append('missing_in_fingerprint_map')
        if not area_meta:
            reason.append('invalid_final_area')
        if not cluster_id:
            reason.append('missing_cluster_id')
        excluded_entities.append({'entity_id': eid, 'final_area': final_area, 'reason': ','.join(reason)})

# Group entities by room_slug
room_registry = defaultdict(list)
for ent in valid_entities:
    room_slug = ent['room_slug']
    post_id = ent['post_reboot_entity_id']
    room_registry[room_slug].append(post_id)

# Build omega_room_registry.json
omega_room_registry = {}
for slug, entity_ids in room_registry.items():
    area_meta = slug_to_area.get(slug, {'id': slug, 'name': slug, 'slug': slug})
    omega_room_registry[slug] = {
        'area_id': area_meta['id'],
        'friendly_name': area_meta['name'],
        'slug': area_meta.get('slug', area_meta['id']),
        'entities': entity_ids
    }

# Emit outputs
with open(os.path.join(OUTPUT_DIR, 'omega_room_registry.json'), 'w') as f:
    json.dump(omega_room_registry, f, indent=2)
# Room audit
room_audit = {slug: len(entity_ids) for slug, entity_ids in room_registry.items()}
with open(os.path.join(OUTPUT_DIR, 'room_registry_completeness_audit.json'), 'w') as f:
    json.dump(room_audit, f, indent=2)
with open(os.path.join(OUTPUT_DIR, 'unresolved_entities.log.json'), 'w') as f:
    json.dump(excluded_entities, f, indent=2)
delta_log = valid_entities + excluded_entities
with open(os.path.join(OUTPUT_DIR, 'rehydration_delta_log.json'), 'w') as f:
    json.dump(delta_log, f, indent=2)
archive_path = os.path.join(OUTPUT_DIR, 'TARBALL-OMEGA-ROOM-REGISTRY-STRICT-FINAL-FIXED.tar.gz')
with tarfile.open(archive_path, 'w:gz') as tar:
    for fname in [
        'omega_room_registry.json',
        'room_registry_completeness_audit.json',
        'unresolved_entities.log.json',
        'rehydration_delta_log.json'
    ]:
        tar.add(os.path.join(OUTPUT_DIR, fname), arcname=fname)

# Diagnostics & Logging
summary = (
    f"Omega Room Registry Strict Reconstruction (Area Validation Patch)\n"
    f"Total entities processed: {len(migration_map)}\n"
    f"Total valid entities: {len(valid_entities)}\n"
    f"Rooms created: {len(room_registry)}\n"
    f"Room coverage: { {k: len(v) for k, v in room_registry.items()} }\n"
    f"Entities excluded: {len(excluded_entities)}\n"
)

for log_path in [
    os.path.join(ROOT, 'PATCH-ROUNDTRIP-AUDIT-V2.log'),
    os.path.join(ROOT, 'copilot_patchlog_overview.log'),
    os.path.join(ROOT, 'copilot_patches', 'PATCH-OMEGA-ROOM-REGISTRY-STRICT-MOVE-20250717.log')
]:
    with open(log_path, 'a') as f:
        f.write('\n' + summary)

print('Omega Room Registry strict reconstruction (area validation patch) complete.')
