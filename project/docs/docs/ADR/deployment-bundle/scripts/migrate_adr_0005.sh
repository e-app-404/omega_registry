#!/bin/bash

# ADR-0005 Machine-Driven Workspace Migration Script
# Fully automated migration from current structure to ADR-0005 compliant workspace
#
# Usage: ./migrate_adr_0005.sh [--dry-run] [--force] [--phase PHASE_NUMBER]
#
# Phases:
#   1: Directory structure and paths.py creation
#   2: Pure library code migration
#   3: Data and I/O migration
#   4: Project metadata migration
#   5: Configuration updates
#   6: Validation and cleanup

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Find the actual git repository root
find_git_root() {
    local dir="$SCRIPT_DIR"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$SCRIPT_DIR/../.."  # Fallback
}
readonly WORKSPACE_ROOT="$(find_git_root)"
readonly LOG_FILE="$WORKSPACE_ROOT/adr_0005_migration.log"
readonly BACKUP_BRANCH="adr-0005-migration-backup-$(date +%Y%m%d_%H%M%S)"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Global variables
DRY_RUN=false
FORCE_MODE=false
TARGET_PHASE=""
CURRENT_PHASE=0
ERRORS_ENCOUNTERED=0
WARNINGS_ENCOUNTERED=0

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Print colored output
print_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
print_success() { echo -e "${GREEN}✅ $*${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
print_error() { echo -e "${RED}❌ $*${NC}"; }
print_phase() { echo -e "${BLUE}🔧 Phase $1: $2${NC}"; }

# Error handling
handle_error() {
    ERRORS_ENCOUNTERED=$((ERRORS_ENCOUNTERED + 1))
    log_error "$@"
    print_error "$@"
}

handle_warning() {
    WARNINGS_ENCOUNTERED=$((WARNINGS_ENCOUNTERED + 1))
    log_warn "$@"
    print_warning "$@"
}

# Help function
show_help() {
    cat << EOF
ADR-0005 Machine-Driven Workspace Migration Script

USAGE:
    $0 [OPTIONS]

DESCRIPTION:
    Fully automated migration from current workspace structure to ADR-0005
    compliant workspace canonicalization with runtime/project separation.

OPTIONS:
    --dry-run          Show what would be done without making changes
    --force            Skip safety checks and confirmations
    --phase NUMBER     Execute specific phase only (1-6)
    --help             Show this help message

PHASES:
    1: Directory structure creation and paths.py implementation
    2: Pure library code migration (addon/src/)
    3: Data and I/O migration (addon/data/)
    4: Project metadata migration (project/)
    5: Configuration file updates and import fixes
    6: Validation, cleanup, and final checks

EXAMPLES:
    # Full migration with dry-run preview
    $0 --dry-run

    # Execute full migration
    $0

    # Execute specific phase only
    $0 --phase 3

    # Force migration without confirmations
    $0 --force

EXIT CODES:
    0   Success
    1   General error
    2   Invalid arguments
    3   Validation failed
    4   Migration failed
    5   Phase execution failed

For more information, see ADR-0005-MIGRATION-PLAN.md
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                log_info "Dry-run mode enabled"
                shift
                ;;
            --force)
                FORCE_MODE=true
                log_info "Force mode enabled"
                shift
                ;;
            --phase)
                if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^[1-6]$ ]]; then
                    print_error "Invalid phase number: $2 (must be 1-6)"
                    exit 2
                fi
                TARGET_PHASE="$2"
                log_info "Target phase: $TARGET_PHASE"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                show_help
                exit 2
                ;;
            *)
                print_error "Unexpected argument: $1"
                show_help
                exit 2
                ;;
        esac
    done
}

# Pre-flight validation
validate_preconditions() {
    print_info "Validating preconditions..."

    # Check if we're in a git repository
    if [[ ! -d "$WORKSPACE_ROOT/.git" ]]; then
        handle_error "Not in a git repository: $WORKSPACE_ROOT"
        exit 3
    fi

    # Check for uncommitted changes (unless force mode)
    if [[ "$FORCE_MODE" != true ]]; then
        cd "$WORKSPACE_ROOT"
        if ! git diff --quiet || ! git diff --staged --quiet; then
            handle_error "Uncommitted changes detected. Commit or stash changes, or use --force"
            exit 3
        fi
    fi

    # Check for required directories
    local required_dirs=("addon" "scripts" "canonical" "docs")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$WORKSPACE_ROOT/$dir" ]]; then
            handle_error "Required directory missing: $dir"
            exit 3
        fi
    done

    # Check write permissions
    if [[ ! -w "$WORKSPACE_ROOT" ]]; then
        handle_error "No write permissions in workspace: $WORKSPACE_ROOT"
        exit 3
    fi

    print_success "Preconditions validated"
    log_info "Precondition validation passed"
}

# Create backup branch
create_backup() {
    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would create backup branch: $BACKUP_BRANCH"
        return 0
    fi

    print_info "Creating backup branch: $BACKUP_BRANCH"
    cd "$WORKSPACE_ROOT"

    git add -A
    git commit -m "Pre-ADR-0005 migration backup" || true
    git branch "$BACKUP_BRANCH"

    print_success "Backup branch created: $BACKUP_BRANCH"
    log_info "Backup branch created successfully"
}

# Safe directory creation with validation
safe_mkdir() {
    local dir_path="$1"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would create directory: $dir_path"
        return 0
    fi

    if [[ -d "$dir_path" ]]; then
        log_info "Directory already exists: $dir_path"
        return 0
    fi

    mkdir -p "$dir_path"
    if [[ ! -d "$dir_path" ]]; then
        handle_error "Failed to create directory: $dir_path"
        return 1
    fi

    log_info "Created directory: $dir_path"
    return 0
}

# Safe file creation with content validation
safe_create_file() {
    local file_path="$1"
    local content="$2"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would create file: $file_path"
        return 0
    fi

    # Create parent directory if needed
    local parent_dir=$(dirname "$file_path")
    safe_mkdir "$parent_dir"

    # Create file with content
    echo "$content" > "$file_path"
    if [[ ! -f "$file_path" ]]; then
        handle_error "Failed to create file: $file_path"
        return 1
    fi

    log_info "Created file: $file_path"
    return 0
}

# Safe git mv with validation and conflict resolution
safe_git_mv() {
    local source="$1"
    local target="$2"
    local operation_desc="${3:-file move}"

    # Skip if source doesn't exist
    if [[ ! -e "$WORKSPACE_ROOT/$source" ]]; then
        log_info "Source does not exist, skipping: $source"
        return 0
    fi

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would git mv: $source -> $target"
        return 0
    fi

    cd "$WORKSPACE_ROOT"

    # Create target directory if needed
    local target_dir=$(dirname "$target")
    safe_mkdir "$target_dir"

    # Handle different source types
    if [[ -d "$source" ]]; then
        # Directory move - handle contents individually to avoid conflicts
        if [[ -d "$target" ]]; then
            # Target exists, move contents
            find "$source" -maxdepth 1 -mindepth 1 -print0 | while IFS= read -r -d '' item; do
                local item_name=$(basename "$item")
                local target_item="$target/$item_name"

                if [[ -e "$target_item" ]]; then
                    handle_warning "Target exists, skipping: $item -> $target_item"
                else
                    git mv "$item" "$target_item" 2>/dev/null || {
                        handle_warning "Failed to move: $item -> $target_item"
                    }
                fi
            done
        else
            # Target doesn't exist, move entire directory
            git mv "$source" "$target" 2>/dev/null || {
                handle_error "Failed to move directory: $source -> $target"
                return 1
            }
        fi
    else
        # File move
        if [[ -e "$target" ]]; then
            handle_warning "Target file exists, skipping: $source -> $target"
            return 0
        fi

        git mv "$source" "$target" 2>/dev/null || {
            handle_error "Failed to move file: $source -> $target"
            return 1
        }
    fi

    log_info "Successfully moved: $source -> $target ($operation_desc)"
    return 0
}

# Execute shell glob expansion safely
safe_glob_mv() {
    local source_pattern="$1"
    local target_dir="$2"
    local operation_desc="${3:-glob move}"

    cd "$WORKSPACE_ROOT"

    # Use find to safely handle globs
    local source_dir=$(dirname "$source_pattern")
    local pattern=$(basename "$source_pattern")

    if [[ ! -d "$source_dir" ]]; then
        log_info "Source directory does not exist: $source_dir"
        return 0
    fi

    # Find matching files/directories
    local found_items=()
    while IFS= read -r -d '' item; do
        found_items+=("$item")
    done < <(find "$source_dir" -maxdepth 1 -name "$pattern" -print0 2>/dev/null || true)

    if [[ ${#found_items[@]} -eq 0 ]]; then
        log_info "No items match pattern: $source_pattern"
        return 0
    fi

    # Move each found item
    local success_count=0
    for item in "${found_items[@]}"; do
        local relative_item=${item#$WORKSPACE_ROOT/}
        local item_name=$(basename "$item")
        local target_path="$target_dir/$item_name"

        if safe_git_mv "$relative_item" "$target_path" "$operation_desc"; then
            success_count=$((success_count + 1))
        fi
    done

    log_info "Moved $success_count/${#found_items[@]} items matching: $source_pattern"
    return 0
}

# Phase 1: Directory Structure Creation
phase1_directory_structure() {
    print_phase 1 "Directory Structure Creation"

    # Create main directory structure
    local directories=(
        "addon/src/utils"
        "addon/src/registry"
        "addon/src/scripts"
        "addon/src/tests"
        "addon/data/input"
        "addon/data/output"
        "addon/data/registry"
        "addon/support"
        "project/docs"
        "project/ops/scripts/analytics"
        "project/ops/scripts/audit"
        "project/ops/scripts/enrich"
        "project/ops/scripts/qa"
        "project/ops/scripts/transformation"
        "project/ops/scripts/legacy"
        "project/workspace"
        "project/backups"
        "project/releases"
    )

    for dir in "${directories[@]}"; do
        safe_mkdir "$WORKSPACE_ROOT/$dir"
    done

    # Create __init__.py files for Python packages
    local init_files=(
        "addon/src/__init__.py"
        "addon/src/utils/__init__.py"
        "addon/src/registry/__init__.py"
        "addon/src/scripts/__init__.py"
        "addon/src/tests/__init__.py"
        "addon/data/__init__.py"
        "project/__init__.py"
        "project/ops/__init__.py"
    )

    for init_file in "${init_files[@]}"; do
        safe_create_file "$WORKSPACE_ROOT/$init_file" "# Package marker"
    done

    # Create critical addon/src/utils/paths.py
    local paths_py_content='"""
Canonical path resolution for Omega Registry.
Import-safe path helpers following ADR-0003 and ADR-0005.
"""
from pathlib import Path
from typing import Union

# Base paths (computed at import time, no I/O)
ADDON_ROOT = Path(__file__).parent.parent.parent
PROJECT_ROOT = ADDON_ROOT.parent
ADDON_SRC = ADDON_ROOT / "src"
ADDON_DATA = ADDON_ROOT / "data"

def get_data_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/ directory."""
    return ADDON_DATA / relative_path

def get_input_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/input/ directory."""
    return ADDON_DATA / "input" / relative_path

def get_output_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/output/ directory."""
    return ADDON_DATA / "output" / relative_path

def get_registry_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/registry/ directory."""
    return ADDON_DATA / "registry" / relative_path

def get_support_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/support/ directory."""
    return ADDON_ROOT / "support" / relative_path

def get_project_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in project/ directory."""
    return PROJECT_ROOT / "project" / relative_path
'

    safe_create_file "$WORKSPACE_ROOT/addon/src/utils/paths.py" "$paths_py_content"

    print_success "Phase 1 completed: Directory structure created"
    log_success "Phase 1: Directory structure creation completed successfully"
}

# Phase 2: Pure Library Code Migration
phase2_pure_code_migration() {
    print_phase 2 "Pure Library Code Migration"

    # Phase 2A: Library code to addon/src/
    print_info "Phase 2A: Moving pure library code..."

    # Move utilities (merge multiple sources)
    safe_glob_mv "addon/utils/*" "addon/src/utils" "addon utilities"
    safe_glob_mv "scripts/utils/*" "addon/src/utils" "scripts utilities"

    # Move registry code (merge multiple sources)
    safe_glob_mv "addon/registry/*" "addon/src/registry" "addon registry"
    safe_glob_mv "scripts/omega_registry/*" "addon/src/registry" "scripts registry"

    # Move tests
    safe_glob_mv "addon/tests/*" "addon/src/tests" "test modules"

    # Phase 2B: CLI scripts to addon/src/scripts/
    print_info "Phase 2B: Moving CLI scripts..."

    safe_glob_mv "scripts/generators/*" "addon/src/scripts" "generator scripts"
    safe_glob_mv "scripts/addon/*" "addon/src/scripts" "addon CLI scripts"
    safe_glob_mv "scripts/tools/*" "addon/src/scripts" "utility tools"
    safe_git_mv "scripts/omega_pipeline_main.py" "addon/src/scripts/omega_pipeline_main.py" "main pipeline"

    print_success "Phase 2 completed: Pure code migration"
    log_success "Phase 2: Pure library code migration completed successfully"
}

# Phase 3: Data and I/O Migration
phase3_data_migration() {
    print_phase 3 "Data and I/O Migration"

    # Move canonical data
    safe_glob_mv "canonical/*" "addon/data" "canonical data"

    # Move I/O directories
    safe_glob_mv "addon/input/*" "addon/data/input" "input data"
    safe_glob_mv "addon/output/*" "addon/data/output" "output data"

    # Move support files
    safe_glob_mv "support/*" "addon/support" "support files"

    print_success "Phase 3 completed: Data migration"
    log_success "Phase 3: Data and I/O migration completed successfully"
}

# Phase 4: Project Metadata Migration
phase4_metadata_migration() {
    print_phase 4 "Project Metadata Migration"

    # Phase 4A: Documentation
    print_info "Phase 4A: Moving documentation..."
    safe_glob_mv "docs/*" "project/docs" "documentation"

    # Phase 4B: Operations scripts
    print_info "Phase 4B: Moving operations scripts..."
    safe_glob_mv "scripts/analytics/*" "project/ops/scripts/analytics" "analytics scripts"
    safe_glob_mv "scripts/audit/*" "project/ops/scripts/audit" "audit scripts"
    safe_glob_mv "scripts/enrich/*" "project/ops/scripts/enrich" "enrichment scripts"
    safe_glob_mv "scripts/qa/*" "project/ops/scripts/qa" "QA scripts"
    safe_glob_mv "scripts/transformation/*" "project/ops/scripts/transformation" "transformation scripts"
    safe_glob_mv "scripts/legacy/*" "project/ops/scripts/legacy" "legacy scripts"

    # Phase 4C: Workspace configurations
    print_info "Phase 4C: Moving workspace configurations..."
    safe_glob_mv "*.code-workspace" "project/workspace" "VS Code workspaces"
    safe_git_mv ".vscode" "project/workspace/.vscode" "VS Code settings"

    # Phase 4D: Backups and releases
    print_info "Phase 4D: Moving backups and releases..."
    safe_glob_mv "_backups/*" "project/backups" "backup files"
    safe_glob_mv "_tarballs/*" "project/releases" "release archives"

    print_success "Phase 4 completed: Project metadata migration"
    log_success "Phase 4: Project metadata migration completed successfully"
}

# Phase 5: Configuration Updates
phase5_configuration_updates() {
    print_phase 5 "Configuration Updates"

    print_info "Phase 5A: Updating import statements..."

    # Find and update Python files with old import patterns
    if [[ "$DRY_RUN" != true ]]; then
        cd "$WORKSPACE_ROOT"

        # Update import statements
        find addon/src -name "*.py" -type f -exec sed -i '' \
            -e 's/from scripts\.utils/from addon.src.utils/g' \
            -e 's/import scripts\.utils/import addon.src.utils/g' \
            -e 's/from scripts\.omega_registry/from addon.src.registry/g' \
            -e 's/import scripts\.omega_registry/import addon.src.registry/g' \
            {} \; 2>/dev/null || true

        log_info "Updated import statements in addon/src/"
    else
        print_info "Would update import statements in Python files"
    fi

    print_info "Phase 5B: Updating configuration files..."

    # Update pyproject.toml if it exists
    if [[ -f "$WORKSPACE_ROOT/pyproject.toml" && "$DRY_RUN" != true ]]; then
        # Add addon.src to packages if not present
        if ! grep -q "addon.src" "$WORKSPACE_ROOT/pyproject.toml"; then
            sed -i '' 's/packages = \[/packages = ["addon.src", /' "$WORKSPACE_ROOT/pyproject.toml" 2>/dev/null || true
            log_info "Updated pyproject.toml packages configuration"
        fi
    fi

    # Update .gitignore patterns if needed
    if [[ -f "$WORKSPACE_ROOT/.gitignore" && "$DRY_RUN" != true ]]; then
        # Add new structure patterns
        echo -e "\n# ADR-0005 structure patterns\naddon/data/.cache/\nproject/workspace/.vscode/settings.json" >> "$WORKSPACE_ROOT/.gitignore" 2>/dev/null || true
        log_info "Updated .gitignore with new structure patterns"
    fi

    print_success "Phase 5 completed: Configuration updates"
    log_success "Phase 5: Configuration updates completed successfully"
}

# Phase 6: Validation and Cleanup
phase6_validation_cleanup() {
    print_phase 6 "Validation and Cleanup"

    # Run ADR-0005 compliance validation
    if [[ -f "$WORKSPACE_ROOT/docs/ADR/deployment-bundle/scripts/validate_adr_0005_compliance.sh" ]]; then
        print_info "Running ADR-0005 compliance validation..."
        if [[ "$DRY_RUN" != true ]]; then
            cd "$WORKSPACE_ROOT"
            if ./docs/ADR/deployment-bundle/scripts/validate_adr_0005_compliance.sh; then
                print_success "ADR-0005 compliance validation passed"
                log_success "ADR-0005 compliance validation successful"
            else
                handle_error "ADR-0005 compliance validation failed"
            fi
        else
            print_info "Would run ADR-0005 compliance validation"
        fi
    else
        handle_warning "ADR-0005 compliance validator not found"
    fi

    # Test import safety
    print_info "Testing import safety for addon/src/..."
    if [[ "$DRY_RUN" != true ]]; then
        cd "$WORKSPACE_ROOT"
        if python3 -c "
import importlib, pkgutil, sys
sys.path.insert(0, '.')
failed = []
try:
    for _, name, _ in pkgutil.walk_packages(['addon/src']):
        try:
            importlib.import_module('addon.src.' + name)
        except Exception as e:
            failed.append((name, str(e)))
    if failed:
        print('Failed imports:', failed)
        exit(1)
    else:
        print('✅ All addon/src/ modules import safely')
except Exception as e:
    print('Import safety test failed:', e)
    exit(1)
" 2>/dev/null; then
            print_success "Import safety validation passed"
            log_success "Import safety validation successful"
        else
            handle_error "Import safety validation failed"
        fi
    else
        print_info "Would test import safety"
    fi

    # Clean up empty directories
    if [[ "$DRY_RUN" != true ]]; then
        cd "$WORKSPACE_ROOT"

        # Remove empty source directories
        for dir in "scripts" "canonical" "addon/input" "addon/output" "addon/utils" "addon/registry" "addon/tests" "support" "_backups" "_tarballs"; do
            if [[ -d "$dir" && -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
                rmdir "$dir" 2>/dev/null || true
                log_info "Removed empty directory: $dir"
            fi
        done
    else
        print_info "Would clean up empty directories"
    fi

    print_success "Phase 6 completed: Validation and cleanup"
    log_success "Phase 6: Validation and cleanup completed successfully"
}

# Execute specific phase
execute_phase() {
    local phase_num="$1"

    CURRENT_PHASE="$phase_num"

    case "$phase_num" in
        1)
            phase1_directory_structure
            ;;
        2)
            phase2_pure_code_migration
            ;;
        3)
            phase3_data_migration
            ;;
        4)
            phase4_metadata_migration
            ;;
        5)
            phase5_configuration_updates
            ;;
        6)
            phase6_validation_cleanup
            ;;
        *)
            handle_error "Invalid phase number: $phase_num"
            exit 5
            ;;
    esac
}

# Main migration execution
main_migration() {
    local start_time=$(date +%s)

    print_info "ADR-0005 Machine-Driven Workspace Migration"
    print_info "Workspace: $WORKSPACE_ROOT"
    print_info "Log file: $LOG_FILE"

    if [[ "$DRY_RUN" == true ]]; then
        print_warning "DRY RUN MODE - No changes will be made"
    fi

    # Execute phases
    if [[ -n "$TARGET_PHASE" ]]; then
        print_info "Executing specific phase: $TARGET_PHASE"
        execute_phase "$TARGET_PHASE"
    else
        print_info "Executing full migration (phases 1-6)"
        for phase in {1..6}; do
            execute_phase "$phase"
        done
    fi

    # Final summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo
    print_success "=== MIGRATION SUMMARY ==="
    echo "Workspace: $WORKSPACE_ROOT"
    echo "Mode: $(if [[ "$DRY_RUN" == true ]]; then echo "DRY RUN"; else echo "LIVE"; fi)"
    echo "Phases executed: $(if [[ -n "$TARGET_PHASE" ]]; then echo "$TARGET_PHASE"; else echo "1-6"; fi)"
    echo "Duration: ${duration}s"
    echo "Errors: $ERRORS_ENCOUNTERED"
    echo "Warnings: $WARNINGS_ENCOUNTERED"
    echo "Log file: $LOG_FILE"

    if [[ $ERRORS_ENCOUNTERED -gt 0 ]]; then
        print_error "Migration completed with $ERRORS_ENCOUNTERED errors"
        echo "Review log file for details: $LOG_FILE"
        exit 4
    elif [[ "$DRY_RUN" == true ]]; then
        print_info "Dry run completed successfully"
        print_info "Run without --dry-run to execute actual migration"
    else
        print_success "Migration completed successfully!"
        print_info "Backup branch available: $BACKUP_BRANCH"
    fi

    log_success "Migration completed in ${duration}s with $ERRORS_ENCOUNTERED errors, $WARNINGS_ENCOUNTERED warnings"
}

# Main execution function
main() {
    # Initialize log file
    echo "=== ADR-0005 Machine-Driven Migration Log ===" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"

    parse_arguments "$@"
    validate_preconditions

    if [[ "$DRY_RUN" != true ]]; then
        create_backup
    fi

    main_migration
}

# Error handling and signal trapping
trap 'print_error "Migration interrupted"; exit 130' INT TERM
trap 'if [[ $? -ne 0 ]]; then print_error "Migration failed with exit code $?"; fi' ERR

# Execute main function with all arguments
main "$@"
