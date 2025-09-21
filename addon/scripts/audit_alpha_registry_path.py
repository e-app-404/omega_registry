import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
from datetime import datetime
import yaml # type: ignore
from registry.utils.pathing import resolve_path, project_root
from registry.utils.registry import load_json, load_yaml
from registry.utils.constants import SETTINGS_FILE, CONTRACT_FILE

# Find all alpha_sensor_registry.json variants
def find_alpha_sensor_registry_variants(index_entries):
    variants = []
    for entry in index_entries:
        if entry.get('id', '').endswith('alpha_sensor_registry.json'):
            variants.append(entry)
    return variants

# Get file metadata
def get_file_metadata(path):
    p = Path(path)
    if not p.exists():
        return {}
    stat = p.stat()
    return {
        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'size': stat.st_size
    }

# Main audit logic
def main():
    root = project_root()
    # PATCH: Use correct index path at project root (fix for FileNotFoundError)
    index_path = root.parent / 'registry_rehydration_index.log'
    entries = load_json(index_path)
    variants = find_alpha_sensor_registry_variants(entries)
    # Extract metadata and references
    audit = []
    for v in variants:
        meta = get_file_metadata(v.get('absolute_path', v.get('path')))
        audit.append({
            'absolute_path': v.get('absolute_path', ''),
            'relative_path': v.get('path', ''),
            'file_tag': v.get('tags', []),
            'referenced_by': v.get('references', []),
            'created_at': meta.get('created_at'),
            'modified_at': meta.get('modified_at'),
            'size': meta.get('size')
        })
    # PATCH: Use correct config path
    config_path = root / 'settings.conf.yaml'
    if not config_path.exists():
        config_path = root.parent / 'settings.conf.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    output_paths = config.get('output_paths', config.get('settings', {}).get('output_paths', {}))
    input_paths = config.get('input_paths', config.get('settings', {}).get('input_paths', {}))
    referenced_paths = set()
    for k, v in {**output_paths, **input_paths}.items():
        if 'alpha_sensor_registry' in k:
            referenced_paths.add(str(v))
    # Cross-check scripts
    script_refs = set()
    for script in [
        'scripts/emit_alpha_sensor_registry.py',
        'scripts/validate_alpha_sensor_registry.py',
        'scripts/generate_omega_room_registry.py']:
        if Path(root / script).exists():
            with open(root / script) as f:
                for line in f:
                    if 'alpha_sensor_registry' in line:
                        script_refs.add(line.strip())
    # Mark stale/ambiguous/conflicting
    now = datetime.now().isoformat()
    for v in audit:
        v['is_stale'] = v['modified_at'] and v['modified_at'] < now[:10]
        v['is_referenced'] = v['absolute_path'] in referenced_paths
        v['is_script_referenced'] = any(v['relative_path'] in s or v['absolute_path'] in s for s in script_refs)
    # Recommend canonical
    canonical = None
    for v in audit:
        if v['is_referenced'] or v['is_script_referenced']:
            canonical = v['absolute_path']
            break
    report = {
        'variants': audit,
        'referenced_paths': list(referenced_paths),
        'script_refs': list(script_refs),
        'recommended_canonical': canonical
    }
    output_path = root / 'output/data/alpha_registry_path_audit.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    # Log completion
    with open(root / 'output/conversation_full_history.log', 'a') as f:
        f.write('[PATCH-INDEX-AUDIT-ALPHA-SOURCE-V1 COMPLETE]\n')
    print(f'Audit complete. See {output_path}')

if __name__ == '__main__':
    main()

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
