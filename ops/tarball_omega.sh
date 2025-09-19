#!/bin/bash
set -e

# PATCH PIPELINE-VALIDATION-POST-ANCHOR-CORRECTION-V1
# Archive the entire project directory, robustly excluding venv, cache, and metadata files

# Project root is the directory containing this script
root="$(cd "$(dirname "$0")" && pwd)"
tarballs_dir="$root/tarballs"
mkdir -p "$tarballs_dir"
timestamp=$(date +%Y%m%d_%H%M%S)
archive_path="$tarballs_dir/omega_registry_snapshot_${timestamp}.tar.gz"

# Robust exclude patterns
exclude_args=(
  --exclude='./venv' \
  --exclude='./venv/*' \
  --exclude='*/__pycache__' \
  --exclude='*/.mypy_cache' \
  --exclude='*/.pytest_cache' \
  --exclude='.DS_Store' \
  --exclude='.vscode' \
  --exclude='tarballs' \
  --exclude='tarballs/*' \
  --exclude='*/tarballs' \
  --exclude='*/tarballs/*' \
  --exclude='*.tar.gz' \
  --exclude='*.tar' \
  --exclude='*.zip'
)

tar ${exclude_args[@]} -czf "$archive_path" .

echo "Tarball created at $archive_path"
# PATCH PIPELINE-VALIDATION-POST-ANCHOR-CORRECTION-V1 END
