#!/usr/bin/env python3
"""safe_search.py

Search tracked files only (via `git ls-files`), limit file sizes, and avoid scanning binary or very large files.

Usage:
  python3 scripts/safe_search.py PATTERN [path_prefix]

Outputs lines in the format: path:line_number:line
Returns non-zero if any matches found (exit code 0 => no matches; 1 => matches found; 2 => error)
"""

import re
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 200 * 1024  # 200 KB per file
ENCODINGS = ['utf-8', 'latin-1']


def git_ls_files(prefix=None):
    cmd = ['git', 'ls-files']
    if prefix:
        cmd += [prefix]
    try:
        out = subprocess.check_output(cmd, cwd=Path(__file__).resolve().parents[1])
        return out.decode('utf-8').splitlines()
    except subprocess.CalledProcessError:
        return []


def search(pattern, prefix=None):
    rx = re.compile(pattern)
    repo_root = Path(__file__).resolve().parents[1]
    files = git_ls_files(prefix)
    found = 0
    for f in files:
        p = repo_root / f
        try:
            if not p.exists() or not p.is_file():
                continue
            if p.stat().st_size > MAX_BYTES:
                # skip very large files
                continue
            text = None
            for enc in ENCODINGS:
                try:
                    text = p.read_text(encoding=enc)
                    break
                except Exception:
                    continue
            if text is None:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if rx.search(line):
                    print(f"{f}:{i}:{line}")
                    found += 1
        except Exception as e:
            # don't fail hard on single-file errors
            print(f"# skip {f}: {e}", file=sys.stderr)
    return found


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: safe_search.py PATTERN [path_prefix]', file=sys.stderr)
        raise SystemExit(2)
    pattern = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else None
    matches = search(pattern, prefix)
    raise SystemExit(1 if matches else 0)
