#!/usr/bin/env python3
"""
fix_venv_refs.py

Conservative tool to find and (optionally) replace absolute references to old venv paths
like `/Users/.../registry_rehydration_local/.venv` in text files with a relative `.venv`
placeholder.

Usage:
  python3 scripts/fix_venv_refs.py        # dry-run, prints proposed replacements
  python3 scripts/fix_venv_refs.py --apply  # apply changes (destructive)

This script only targets files smaller than 200KB and will back up modified files with
a `.bak` suffix before applying changes.
"""

from pathlib import Path
import re
import argparse
import fnmatch

REPO_ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(
    r"/Users/[^\s'\"]*/registry_rehydration_local(?:_last)?/\\.venv"
)

# Default exclude patterns: don't touch venv internals, compiled files, or logs
DEFAULT_EXCLUDES = [
    "*/.venv/**",
    "*/venv/**",
    "**/*.pyc",
    "addon/output/logs/**",
]


def find_hits(include=None, exclude=None):
    include = include or ["**/*"]
    exclude = exclude or DEFAULT_EXCLUDES
    hits = []
    for pattern in include:
        for p in REPO_ROOT.glob(pattern):
            try:
                if p.is_file() and p.stat().st_size < 200_000:
                    skip = False
                    s = str(p)
                    for ex in exclude:
                        if fnmatch.fnmatch(s, ex):
                            skip = True
                            break
                    if skip:
                        continue
                    text = p.read_text(errors="ignore")
                    if PATTERN.search(text):
                        hits.append(p)
            except Exception:
                pass
    # dedupe while preserving order
    seen = set()
    out = []
    for p in hits:
        sp = str(p)
        if sp not in seen:
            seen.add(sp)
            out.append(p)
    return out


def propose_replace(text):
    # Replace absolute venv path with a repo-relative .venv
    return PATTERN.sub(".venv", text)


def run(dry_run=True, include=None, exclude=None):
    hits = find_hits(include=include, exclude=exclude)
    if not hits:
        print(
            "No absolute venv references found (after applying include/exclude)."
        )
        return 0
    for p in hits:
        text = p.read_text(errors="ignore")
        new_text = propose_replace(text)
        if text == new_text:
            continue
        print(f"-- {p} --")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line):
                new_line = PATTERN.sub(".venv", line)
                print(f" {lineno}:")
                print(f"    - {line.strip()}")
                print(f"    + {new_line.strip()}")
        if not dry_run:
            bak = p.with_suffix(p.suffix + ".bak")
            p.rename(bak)
            p.write_text(new_text)
            print("  Applied change; original saved to", bak)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply changes")
    args = ap.parse_args()
    rc = run(dry_run=not args.apply)
    raise SystemExit(rc)
