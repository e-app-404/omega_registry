#!/usr/bin/env python3
"""
Scan the workspace for all directories named 'canonical', compute per-file sha256, size, mtime,
and produce JSON manifests plus a comparison summary that highlights files present in multiple
canonical roots and whether they are identical or different.

Writes outputs to the same directory as this script.
"""

import os
import hashlib
import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = (
    Path(__file__).resolve().parents[4]
)  # repo root (../../../../.. from meta/rehydration/...)
OUT_DIR = Path(__file__).resolve().parent


def sha256_file(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_canonical_dirs(root):
    res = []
    for dirpath, dirs, files in os.walk(root):
        base = os.path.basename(dirpath)
        if base == "canonical":
            res.append(Path(dirpath))
    return sorted(res)


def build_manifest(canonical_dir):
    manifest = []
    for dirpath, dirs, files in os.walk(canonical_dir):
        for fname in files:
            fpath = Path(dirpath) / fname
            try:
                stat = fpath.stat()
                sha = sha256_file(fpath)
                rel = fpath.relative_to(canonical_dir).as_posix()
                manifest.append(
                    {
                        "relpath": rel,
                        "abs_path": str(fpath),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "sha256": sha,
                    }
                )
            except Exception as e:
                manifest.append(
                    {
                        "relpath": str(fpath),
                        "abs_path": str(fpath),
                        "error": str(e),
                    }
                )
    return sorted(manifest, key=lambda x: x.get("relpath", ""))


def safe_name_for_dir(p: Path):
    return p.as_posix().lstrip("/").replace("/", "_")


def main():
    print(f"Scanning repository root: {ROOT}")
    canon_dirs = find_canonical_dirs(ROOT)
    if not canon_dirs:
        print("No canonical/ directories found.")
        return 1
    print(f"Found {len(canon_dirs)} canonical directories:")
    for d in canon_dirs:
        print(" -", d)

    # store manifests and mapping relpath->list
    relmap = defaultdict(list)
    manifests = {}
    for d in canon_dirs:
        print(f"Building manifest for {d}...")
        m = build_manifest(d)
        manifests[str(d)] = m
        out_path = OUT_DIR / f"manifest_{safe_name_for_dir(d)}.json"
        with open(out_path, "w") as f:
            json.dump(m, f, indent=2)
        print(f"Wrote manifest: {out_path}")
        for e in m:
            if "relpath" in e and "sha256" in e:
                relmap[e["relpath"]].append(
                    {
                        "canonical_root": str(d),
                        "sha256": e["sha256"],
                        "size": e["size"],
                        "mtime": e["mtime"],
                        "abs_path": e["abs_path"],
                    }
                )

    # build comparison summary
    identical = []
    differing = []
    unique = []
    for rel, entries in relmap.items():
        if len(entries) == 1:
            unique.append({"relpath": rel, "entry": entries[0]})
        else:
            # check if all sha equal
            shas = {e["sha256"] for e in entries}
            if len(shas) == 1:
                identical.append({"relpath": rel, "entries": entries})
            else:
                differing.append({"relpath": rel, "entries": entries})

    summary = {
        "found_canonical_dirs": [str(d) for d in canon_dirs],
        "total_distinct_relpaths": len(relmap),
        "unique_files": len(unique),
        "identical_files": len(identical),
        "differing_files": len(differing),
        "unique_list_sample": unique[:20],
        "identical_list_sample": [x["relpath"] for x in identical[:50]],
        "differing_list_sample": [x["relpath"] for x in differing[:50]],
    }

    summary_path = OUT_DIR / "canonical_comparison_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote comparison summary: {summary_path}")

    # Also write detailed differing list
    detailed_diff_path = OUT_DIR / "canonical_differing_details.json"
    with open(detailed_diff_path, "w") as f:
        json.dump(differing, f, indent=2)
    print(f"Wrote differing details: {detailed_diff_path}")

    # And unique list
    unique_path = OUT_DIR / "canonical_unique_details.json"
    with open(unique_path, "w") as f:
        json.dump(unique, f, indent=2)
    print(f"Wrote unique details: {unique_path}")

    print("\nSummary:")
    print(json.dumps(summary, indent=2))
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
