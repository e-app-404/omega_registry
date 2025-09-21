#!/bin/bash
set -e

timestamp=$(date +%Y%m%d_%H%M%S)
manifest=canonical_manifest.txt
archive_path="omega_registry_canonical_${timestamp}.tar.gz"

workdir=$(mktemp -d)

awk 'NF && $1 !~ /^#/' "$manifest" | while read -r file; do
  if [ -f "$file" ]; then
    mkdir -p "$workdir/$(dirname "$file")"
    cp "$file" "$workdir/$file"
  fi
done

(cd "$workdir" && tar --exclude='.DS_Store' --exclude='.vscode' --exclude='venv' --exclude='.indexvenv' --exclude='.venv' --exclude='__pycache__' --exclude='.mypy_cache' --exclude='.pytest_cache' --exclude='tarballs' --exclude='*.tar.gz' --exclude='*.tar' --exclude='*.zip' -czf "$archive_path" .)

cp "$workdir/$archive_path" . 2>/dev/null || true  # No need to copy, tarball is already in current dir
rm -rf "$workdir"
echo "Tarball created at $archive_path"
