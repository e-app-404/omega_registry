#!/usr/bin/env python3
"""
Safe fixer for registry path strings.

Usage examples:
  # Dry-run all tracked files under addon prefix
  python3 scripts/fix_registry_paths.py --include addon --dry-run

  # Apply only to specific files and create backups
  python3 scripts/fix_registry_paths.py --include addon/WORKSPACE_README.md --apply --backup

This script only touches files reported by `git ls-files` (tracked files).
It skips files larger than --max-bytes (default 200000).
"""
import argparse
import subprocess
import sys
from pathlib import Path
import re
import difflib


DEFAULT_MAX_BYTES = 200000


def get_tracked_files():
    p = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if p.returncode != 0:
        print("Error: git ls-files failed", file=sys.stderr)
        sys.exit(2)
    files = [Path(x) for x in p.stdout.splitlines() if x.strip()]
    return files


def load_file(path, max_bytes):
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return None, 'SKIP_TOO_LARGE'
        text = path.read_text(encoding='utf-8')
        return text, None
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding='latin-1')
            return text, None
        except Exception as e:
            return None, f'SKIP_DECODE_ERROR:{e}'
    except Exception as e:
        return None, f'SKIP_ERROR:{e}'


def make_replacements(text, patterns):
    new = text
    applied = []
    for pat, repl, desc in patterns:
        new2, n = re.subn(pat, repl, new)
        if n:
            applied.append((desc, pat, repl, n))
            new = new2
    return new, applied


def unified_diff(a, b, path):
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)
    return ''.join(difflib.unified_diff(a_lines, b_lines, fromfile=str(path), tofile=str(path) + ' (patched)'))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true', help='Do not modify files; only show diffs')
    p.add_argument('--apply', action='store_true', help='Apply replacements to files')
    p.add_argument('--include', default='', help='Only include files whose path contains this substring (comma-separated allowed)')
    p.add_argument('--exclude', default='', help='Exclude files whose path contains this substring (comma-separated allowed)')
    p.add_argument('--backup', action='store_true', help='When applying, write a .bak copy of each modified file')
    p.add_argument('--max-bytes', type=int, default=DEFAULT_MAX_BYTES, help='Skip files larger than this')
    return p.parse_args()


def main():
    args = parse_args()
    include_list = [x for x in args.include.split(',') if x]
    exclude_list = [x for x in args.exclude.split(',') if x]

    # Default replacement patterns (conservative)
    # Order matters: longer absolute paths first.
    repo_root_guess = str(Path('.').resolve())
    patterns = [
        # Replace absolute venv pointing to old registry project
        (re.escape('/Users/evertappels/Projects/registry_rehydration_local/.venv'), repo_root_guess + '/.venv', "abs-old-venv"),
        # Replace absolute project path to point to repo/addon
        (re.escape('/Users/evertappels/Projects/registry_rehydration_local'), repo_root_guess + '/addon', "abs-old-project"),
        # Replace occurrences of registry_rehydration_local_last -> addon
        (r'\bregistry_rehydration_local_last\b', 'addon', 'name-last->addon'),
        # Replace bare registry_rehydration_local -> addon (conservative word-boundary)
        (r'\bregistry_rehydration_local\b', 'addon', 'name->addon'),
    ]

    files = get_tracked_files()

    any_changes = False

    for path in files:
        s = str(path)
        if include_list and not any(inc in s for inc in include_list):
            continue
        if exclude_list and any(exc in s for exc in exclude_list):
            continue
        text, reason = load_file(path, args.max_bytes)
        if text is None:
            # Skip binary/large/undecodable files, but print reason for visibility
            print(f"SKIP {path}: {reason}")
            continue

        new_text, applied = make_replacements(text, patterns)
        if applied:
            any_changes = True
            diff = unified_diff(text, new_text, path)
            print(f"--- Proposed changes for: {path}")
            for desc, pat, repl, n in applied:
                print(f"  - {desc}: pattern={pat!r} replacements={n}")
            print(diff or "(no textual diff available)")

            if args.apply:
                if args.backup:
                    bak = path.with_name(path.name + '.bak')
                    bak.write_text(text, encoding='utf-8')
                    print(f"Wrote backup: {bak}")
                path.write_text(new_text, encoding='utf-8')
                print(f"Applied changes to: {path}")

    if any_changes:
        if args.dry_run and not args.apply:
            print("Dry-run complete: changes proposed but not applied.")
            sys.exit(0)
        elif args.apply:
            print("Apply complete.")
            sys.exit(0)
    else:
        print("No matches found.")
        sys.exit(0)


if __name__ == '__main__':
    main()
