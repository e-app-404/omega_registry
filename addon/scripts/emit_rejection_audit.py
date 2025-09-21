import json
from collections import defaultdict

# Load entity fingerprint map
with open('output/entity_fingerprint_map.json') as f:
    entity_map = json.load(f)

# Load migration map
with open('output/entity_id_migration_map.annotated.v4.full.json') as f:
    migration_map = json.load(f)

migration_entity_ids = set(e['entity_id'] for e in migration_map)

rejection_audit = []
stats = defaultdict(int)

for entity_id, entity in entity_map.items():
    reasons = []
    # Check final_area
    if entity.get('final_area') in (None, 'unknown_area'):
        reasons.append('final_area == unknown_area')
    # Check cluster_id
    cluster_id = None
    # Try to get cluster_id from migration map
    migration_entry = next((e for e in migration_map if e['entity_id'] == entity_id), None)
    if migration_entry:
        cluster_id = migration_entry.get('cluster_id')
    if not cluster_id or cluster_id == 'unknown':
        reasons.append('missing_cluster_id')
    # Check migration presence
    if entity_id not in migration_entity_ids:
        reasons.append('migration_absent')
    # Record rejection
    if reasons:
        rejection_audit.append({
            'entity_id': entity_id,
            'rejection_reasons': reasons
        })
        if len(reasons) > 1:
            stats['multi_failure'] += 1
        for reason in reasons:
            if reason == 'final_area == unknown_area':
                stats['rejected_due_to_final_area_unknown'] += 1
            if reason == 'missing_cluster_id':
                stats['rejected_due_to_missing_cluster_id'] += 1
            if reason == 'migration_absent':
                stats['rejected_due_to_migration_absent'] += 1
    else:
        stats['fully_accepted'] += 1

stats['total_entities'] = len(entity_map)

# Emit audit file
with open('output/omega_room/unresolved_entity_rejection_audit.json', 'w') as f:
    json.dump({'rejections': rejection_audit, 'summary_stats': dict(stats)}, f, indent=2)
