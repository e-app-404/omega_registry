#!/usr/bin/env python3
import os
import csv
from pathlib import Path

# This script scans the workspace for literal "canonical/" occurrences
# and writes a CSV mapping (file, line, snippet). It skips binary files
# and files larger than MAX_FILE_BYTES to avoid huge outputs.

ROOT = Path(os.getcwd())
OUT = (
    ROOT
    / "registry_rehydration_local_last"
    / "meta"
    / "rehydration"
    / "68b5e5e1-3eb4-8333-8ec4-4389c6239c2e"
    / "canonical_literal_map.csv"
)
# threshold to skip huge files (in bytes)
MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB


def is_binary(path):
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return True
    except Exception:
        return True
    return False


rows = 0
skipped_large = []
with open(OUT, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["file", "line", "snippet"])
    for dirpath, dirnames, filenames in os.walk(ROOT):
        parts = Path(dirpath).parts
        if ".git" in parts or ".venv" in parts or "node_modules" in parts:
            continue
        for fn in filenames:
            fpath = Path(dirpath) / fn
            try:
                if not fpath.exists():
                    continue
                # Skip files that are too large to safely scan
                try:
                    size = fpath.stat().st_size
                except Exception:
                    continue
                if size > MAX_FILE_BYTES:
                    skipped_large.append(str(fpath))
                    continue
                if is_binary(fpath):
                    continue
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, start=1):
                        if "canonical/" in line:
                            snippet = line.strip().replace("\n", "\\n")
                            writer.writerow([str(fpath), i, snippet])
                            rows += 1
            except Exception:
                continue

print(f"Wrote {rows} rows to {OUT}")
if skipped_large:
    print(
        f"Skipped {len(skipped_large)} large files (>{MAX_FILE_BYTES} bytes). Sample: {skipped_large[:5]}"
    )
