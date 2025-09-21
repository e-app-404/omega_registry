#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import yaml
from datetime import datetime

MANIFEST_PATH = "cleanup/retention_manifest.yaml"
TRASH_DIR = "trash"
LOG_PATH = os.path.join(TRASH_DIR, "index.deleted.txt")

parser = argparse.ArgumentParser(description="Manifest-aware project cleanup.")
parser.add_argument("--dry-run", action="store_true", help="Only print what would be deleted/moved.")
parser.add_argument("--delete", action="store_true", help="Permanently delete files instead of moving to trash.")
parser.add_argument("--move-to", default=TRASH_DIR, help="Directory to move deleted files (default: trash/)")
args = parser.parse_args()

with open(MANIFEST_PATH) as f:
    manifest = set(os.path.normpath(p) for p in yaml.safe_load(f)["final_artifacts"])

files_to_remove = []
flagged_for_retention = []

for root, dirs, files in os.walk("."):
    for fname in files:
        rel_path = os.path.normpath(os.path.relpath(os.path.join(root, fname), "."))
        if rel_path.startswith((TRASH_DIR, "cleanup/")):
            continue
        if rel_path in manifest:
            continue
        # Don't delete .git, .venv, .vscode, .DS_Store, or script itself
        if any(rel_path.startswith(x) for x in [".git", ".venv", ".vscode"]) or rel_path.endswith(".DS_Store") or rel_path == __file__:
            continue
        files_to_remove.append(rel_path)

if args.dry_run:
    print(f"[DRY RUN] {len(files_to_remove)} files would be moved to {args.move_to or TRASH_DIR} or deleted.")
    for f in files_to_remove:
        print(f"  - {f}")
    if flagged_for_retention:
        print("\n[INFO] Files flagged for retention (not in manifest, but not deleted):")
        for f in flagged_for_retention:
            print(f"  - {f}")
    sys.exit(0)

os.makedirs(args.move_to, exist_ok=True)
with open(LOG_PATH, "a") as log:
    for f in files_to_remove:
        ts = datetime.now().isoformat()
        if args.delete:
            try:
                os.remove(f)
                log.write(f"{ts} [DELETED] {f}\n")
            except Exception as e:
                log.write(f"{ts} [ERROR] {f} {e}\n")
        else:
            dest = os.path.join(args.move_to, os.path.basename(f))
            try:
                shutil.move(f, dest)
                log.write(f"{ts} [MOVED] {f} -> {dest}\n")
            except Exception as e:
                log.write(f"{ts} [ERROR] {f} {e}\n")
print(f"Cleanup complete. {len(files_to_remove)} files processed. See {LOG_PATH} for details.")
