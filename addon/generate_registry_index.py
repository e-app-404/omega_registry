#!/usr/bin/env python3
import os
import stat
import yaml # type: ignore
import re
from datetime import datetime
from collections import defaultdict

EXCLUDE_DIRS = {'.vscode', 'venv', '.indexvenv', '.venv', '__pycache__', '.mypy_cache', '.pytest_cache'}
EXCLUDE_FILES = {'full_file_index.tmp', 'filtered_file_index.tmp', '.DS_Store'}
ROOT = os.path.abspath('.')

KEY_FILES = {
    'README.md': 'Project documentation and usage instructions.',
    'settings.conf.yaml': 'Configuration for fingerprint matching (weights, thresholds, paths, mappings, etc.).',
}

PIPELINE_TAGS = {
    'scripts': ['pipeline', 'script'],
    'input': ['input'],
    'output': ['output', 'generated'],
    'archive': ['archive'],
    'historical': ['archive', 'historical'],
    'data': ['log', 'metrics'],
}

# Load OUTPUT_DEPENDENCY_MAP from registry/config/output_dependency_map.yaml
with open(os.path.join("registry", "config", "output_dependency_map.yaml")) as f:
    OUTPUT_DEPENDENCY_MAP = yaml.safe_load(f)

OUTPUT_DEPENDENCY_MAP.update({
    "scripts/generate_entity_id_migration_map_rosetta_v5.py": {
      "inputs": [
        "data/entity_fingerprint_map.json",
        "input/pre-reboot.hestia_registries/alpha_sensor_registry.json",
        "input/pre-reboot.hestia_registries/omega_device_registry.json",
        "input/pre-reboot.ha_registries/core.entity_registry"
      ],
      "outputs": [
        "input/mappings/entity_id_migration_map.rosetta.v5.json",
        "output/migration_diagnostics/rosetta_v5_match_summary.json",
        "output/migration_diagnostics/unmatched_pre_reboot_entities.json",
        "output/migration_diagnostics/rosetta_v5_run_summary.log",
        "output/migration_diagnostics/pre_reboot_entity_filtering_diagnostics.json",
        "output/migration_diagnostics/pre_reboot_canonical_id_issues.json",
        "output/migration_diagnostics/pre_reboot_entities_by_source.json"
      ]
    },
    "scripts/delta_analysis_v4_to_v5.py": {
      "inputs": [
        "output/entity_id_migration_map.annotated.v4.full.json",
        "input/mappings/entity_id_migration_map.rosetta.v5.json"
      ],
      "outputs": [
        "output/migration_diagnostics/migration_delta_v4_to_v5/added_in_v5.json",
        "output/migration_diagnostics/migration_delta_v4_to_v5/missing_from_v5.json",
        "output/migration_diagnostics/migration_delta_v4_to_v5/matched_diff.json"
      ]
    }
})

# I/O for diagnostics scripts:
# - emit_advanced_unresolved_cluster_diagnostics.py: input = alpha sensor registry JSON, output = data/advanced_unresolved_cluster_diagnostics_<timestamp>.json
# - analyze_unresolved_cluster_diagnostics.py: input = data/advanced_unresolved_cluster_diagnostics_<timestamp>.json, output = analysis/stats or stdout
# - diagnose_device_without_area.py: input = alpha sensor registry JSON, core.device_registry.json; output = data/clusters_with_device_but_missing_area.<timestamp>.json

# Helper to get file stats
def get_file_info(path):
    st = os.stat(path)
    created = datetime.fromtimestamp(st.st_birthtime).isoformat() + 'Z'
    last_updated = datetime.fromtimestamp(st.st_mtime).isoformat() + 'Z'
    size = st.st_size
    return created, last_updated, size

def human_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def extract_python_dependencies(filepath):
    deps = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # Top-level and in-function/class imports
                m = re.match(r'\s*import ([\w_\.]+)', line)
                if m:
                    deps.add((m.group(1).split('.')[0], 'python_module'))
                m = re.match(r'\s*from ([\w_\.]+) import', line)
                if m:
                    deps.add((m.group(1).split('.')[0], 'python_module'))
                # Script calls (os.system, subprocess, etc.)
                m = re.search(r'(?:os\.system|subprocess\.call|subprocess\.run)\(["\'](python[\w\s\.\/_-]+)', line)
                if m:
                    script = m.group(1).split()[-1]
                    if script.endswith('.py'):
                        deps.add((script, 'script_call'))
    except Exception:
        pass
    # Return as sorted list of dicts by name
    return sorted(({'name': d[0], 'type': d[1]} for d in deps), key=lambda x: x['name'])

def extract_references(filepath, ext):
    refs = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if ext in {'.yaml', '.yml'}:
                    m = re.search(r'!include +([\w\./_-]+)', line)
                    if m:
                        refs.add((m.group(1), 'yaml_include'))
                elif ext == '.json':
                    m = re.search(r'"\$ref"\s*:\s*"([^"]+)"', line)
                    if m:
                        refs.add((m.group(1), 'json_ref'))
                elif ext == '.md':
                    m = re.search(r'\]\(([^)]+)\)', line)
                    if m:
                        ref = m.group(1)
                        if ref.startswith('http'):
                            refs.add((ref, 'external_link'))
                        else:
                            refs.add((ref, 'markdown_link'))
                # Comments with references
                m = re.search(r'#\s*(see|ref|reference):\s*([\w\./_-]+)', line, re.IGNORECASE)
                if m:
                    refs.add((m.group(2), 'comment_ref'))
    except Exception:
        pass
    # Return as sorted list of dicts by path
    return sorted(({'path': r[0], 'type': r[1]} for r in refs), key=lambda x: x['path'])

def infer_type_tags(filename, is_dir, rel_path):
    ext = os.path.splitext(filename)[1].lower()
    tags = set()
    if is_dir:
        tags.add('directory')
        for k, v in PIPELINE_TAGS.items():
            if rel_path.startswith(k):
                tags.update(v)
        # Directory content-based tags
        if os.path.exists(os.path.join(rel_path, '__init__.py')):
            tags.add('package')
        return 'directory', list(tags)
    if filename == '.DS_Store':
        return 'system', ['system', 'macos']
    if ext in {'.yaml', '.yml'}:
        tags.add('yaml')
        tags.add('config')
    if ext == '.json':
        tags.add('json')
    if ext == '.md':
        tags.add('markdown')
        if filename.lower() == 'readme.md':
            tags.add('documentation')
    if ext == '.log':
        tags.add('log')
    if ext == '.py':
        tags.add('python')
        tags.add('script')
        # Entrypoint detection
        try:
            with open(rel_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'def main(' in content and '__name__' in content:
                    tags.add('entrypoint')
                if 'pytest' in content or 'unittest' in content or 'def test_' in content:
                    tags.add('test')
        except Exception:
            pass
    if ext == '.txt':
        tags.add('text')
    if ext in {'.gz', '.zip', '.tar'}:
        tags.add('archive')
    for k, v in PIPELINE_TAGS.items():
        if rel_path.startswith(k):
            tags.update(v)
    if not tags:
        tags.add('file')
    return tags.pop(), list(tags)

def infer_priority(path, tags):
    if 'documentation' in tags or 'config' in tags or 'pipeline' in tags:
        return 'high'
    if 'archive' in tags or 'log' in tags or 'system' in tags or 'generated' in tags:
        return 'low'
    return 'normal'

def infer_status(path, tags):
    if 'archive' in tags or 'historical' in tags:
        return 'archived'
    if 'generated' in tags:
        return 'generated'
    if 'system' in tags:
        return 'ignore'
    return 'active'

def infer_summary(filename, rel_path, tags, default_summary):
    if filename in KEY_FILES:
        return KEY_FILES[filename]
    if filename in OUTPUT_DEPENDENCY_MAP:
        return OUTPUT_DEPENDENCY_MAP[filename].get('summary', default_summary)
    if 'documentation' in tags:
        return 'Project documentation.'
    if 'config' in tags:
        return 'Configuration file.'
    if 'log' in tags:
        return 'Log file.'
    if 'script' in tags:
        return 'Python script.'
    if 'archive' in tags:
        return 'Archive or compressed file.'
    if 'json' in tags:
        return 'JSON data file.'
    if 'markdown' in tags:
        return 'Markdown documentation.'
    if 'system' in tags:
        return 'System or OS file.'
    if 'directory' in tags:
        return 'Directory.'
    return default_summary

def directory_content_summary(dirpath):
    file_count = 0
    dir_count = 0
    types = defaultdict(int)
    for entry in os.scandir(dirpath):
        if entry.is_file():
            file_count += 1
            ext = os.path.splitext(entry.name)[1].lower()
            types[ext or 'noext'] += 1
        elif entry.is_dir():
            dir_count += 1
    return {
        'files': file_count,
        'directories': dir_count,
        'file_types': dict(types)
    }

def aggregate_dir_deps_refs(dirpath):
    deps = []
    refs = []
    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            fpath = os.path.join(root, fname)
            if ext == '.py':
                deps.extend(extract_python_dependencies(fpath))
            if ext in {'.yaml', '.yml', '.json', '.md'}:
                refs.extend(extract_references(fpath, ext))
    # Deduplicate by tuple key
    deps = [dict(t) for t in {tuple(sorted(d.items())) for d in deps}]
    refs = [dict(t) for t in {tuple(sorted(r.items())) for r in refs}]
    return sorted(deps, key=lambda x: x['name']), sorted(refs, key=lambda x: x['path'])

def main():
    index = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        rel_dir = os.path.relpath(dirpath, ROOT)
        # Add directory itself
        if rel_dir != '.':
            full_path = os.path.join(ROOT, rel_dir)
            created, last_updated, size = get_file_info(full_path)
            type_, tags = infer_type_tags(rel_dir, True, rel_dir)
            content_summary = directory_content_summary(full_path)
            deps, refs = aggregate_dir_deps_refs(full_path)
            entry = {
                'id': os.path.basename(rel_dir),
                'path': rel_dir,
                'absolute_path': full_path,
                'type': type_,
                'created': created,
                'last_updated': last_updated,
                'size': human_size(size),
                'contains': content_summary,
                'dependencies': deps,
                'references': refs,
                'tags': tags,
                'summary': infer_summary(os.path.basename(rel_dir), rel_dir, tags, 'Directory.'),
                'status': infer_status(rel_dir, tags),
                'priority': infer_priority(rel_dir, tags)
            }
            index.append(entry)
        for fname in filenames:
            if fname in EXCLUDE_FILES:
                continue
            rel_path = os.path.join(rel_dir, fname) if rel_dir != '.' else fname
            if rel_path.startswith('.indexvenv/'):
                continue
            if fname == '.DS_Store':
                continue
            full_path = os.path.join(ROOT, rel_path)
            try:
                created, last_updated, size = get_file_info(full_path)
            except Exception:
                continue
            type_, tags = infer_type_tags(fname, False, rel_path)
            ext = os.path.splitext(fname)[1].lower()
            dependencies = extract_python_dependencies(full_path) if ext == '.py' else []
            references = extract_references(full_path, ext) if ext in {'.yaml', '.yml', '.json', '.md'} else []
            # Use OUTPUT_DEPENDENCY_MAP for known outputs
            if fname in OUTPUT_DEPENDENCY_MAP:
                depmap = OUTPUT_DEPENDENCY_MAP[fname]
                dependencies = depmap.get('dependencies', dependencies)
                references = depmap.get('references', references)
                tags = list(set(tags) | set(depmap.get('tags', [])))
                summary = depmap.get('summary', infer_summary(fname, rel_path, tags, 'File.'))
                status = 'generated'
            else:
                summary = infer_summary(fname, rel_path, tags, 'File.')
                status = infer_status(rel_path, tags)
            entry = {
                'id': fname,
                'path': rel_path,
                'absolute_path': full_path,
                'type': type_,
                'created': created,
                'last_updated': last_updated,
                'size': human_size(size),
                'dependencies': dependencies,
                'references': references,
                'tags': tags,
                'summary': summary,
                'status': status,
                'priority': infer_priority(rel_path, tags)
            }
            index.append(entry)
    with open('registry_rehydration_index.log', 'w') as f:
        now = datetime.now().isoformat()
        f.write(f'# registry_rehydration_index.log\n')
        f.write(f'# Machine-friendly index of all files in registry_rehydration_local (recursive, excluding .vscode, venv, .indexvenv)\n')
        f.write(f'# Generated at: {now}\n\n')
        yaml.dump(index, f, sort_keys=False, default_flow_style=False)

if __name__ == '__main__':
    main()
