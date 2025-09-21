#!/usr/bin/env python3
"""
check_single_venv.py

Scans the repository for multiple virtualenv directories and for files that embed absolute paths to venvs.

Outputs a JSON-friendly report to stdout and an exit code:
 - 0: no problems found (only one canonical venv present and no absolute references)
 - 1: non-fatal warnings (multiple venvs found but they look intentional)
 - 2: fatal (multiple venvs and absolute references found)

This script is conservative and read-only.
"""

from pathlib import Path
import re
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_NAMES = [".venv", "venv", "addon/.venv", "addon/venv"]
ABS_VENV_PATTERN = re.compile(
    r"/Users/[^\s'\"]*/registry_rehydration_local(?:_last)?/.venv"
)


def find_venvs():
    found = {}
    for name in CANDIDATE_NAMES:
        p = REPO_ROOT / name
        if p.exists():
            found[name] = str(p.resolve())
    return found


def scan_files_for_absolute_refs():
    hits = []
    for p in REPO_ROOT.rglob("*"):
        try:
            if (
                p.is_file() and p.stat().st_size < 200_000
            ):  # skip very large files
                text = p.read_text(errors="ignore")
                if ABS_VENV_PATTERN.search(text):
                    hits.append(str(p))
        except Exception:
            pass
    return hits


def main():
    venvs = find_venvs()
    hits = scan_files_for_absolute_refs()
    report = {"venvs": venvs, "absolute_refs": hits}
    print(json.dumps(report, indent=2))
    if len(venvs) > 1 and hits:
        return 2
    if len(venvs) > 1:
        return 1
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
