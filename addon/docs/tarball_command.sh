timestamp=$(date +%Y%m%d_%H%M%S) && tar --exclude='.DS_Store' --exclude='.vscode' --exclude='venv' --exclude='.indexvenv' --exclude='.venv' --exclude='__pycache__' --exclude='.mypy_cache' --exclude='.pytest_cache' --exclude='tarballs' --exclude='*.tar.gz' --exclude='*.tar' --exclude='*.zip' -czf ../registry_rehydration_archive/tarballs/registry_rehydration_snapshot_${timestamp}.tar.gz .
# This script creates a tarball of the current project directory, excluding certain files and directories.
# The tarball is saved in the ../registry_rehydration_archive/tarballs/ directory
# with a timestamp in the filename for versioning.
