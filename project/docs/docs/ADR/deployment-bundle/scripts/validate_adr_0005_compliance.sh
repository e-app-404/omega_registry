#!/bin/bash

# ADR-0005 Workspace Structure Compliance Validator
# Validates that the workspace structure follows ADR-0005 canonicalization requirements
#
# Usage: ./validate_adr_0005_compliance.sh [workspace_root]

set -euo pipefail

# Configuration
readonly WORKSPACE_ROOT="${1:-$(pwd)}"
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Validation counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

print_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
print_success() { echo -e "${GREEN}✅ $*${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
print_error() { echo -e "${RED}❌ $*${NC}"; }

check_passed() {
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    print_success "$*"
}

check_failed() {
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    print_error "$*"
}

check_warning() {
    WARNINGS=$((WARNINGS + 1))
    print_warning "$*"
}

# Validate ADR-0005 directory structure
validate_directory_structure() {
    print_info "Validating ADR-0005 directory structure..."

    # Required directories per ADR-0005
    local required_dirs=(
        "$WORKSPACE_ROOT/addon/src"
        "$WORKSPACE_ROOT/addon/data"
        "$WORKSPACE_ROOT/project/docs"
        "$WORKSPACE_ROOT/project/ops"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            check_passed "Directory exists: $(basename "$(dirname "$dir")")/$(basename "$dir")"
        else
            check_failed "Missing required directory: $dir"
        fi
    done

    # Check for omega_registry_ha_storage symlink
    if [[ -L "$WORKSPACE_ROOT/omega_registry_ha_storage" ]]; then
        check_passed "omega_registry_ha_storage is a symlink (external data separation)"
    elif [[ -d "$WORKSPACE_ROOT/omega_registry_ha_storage" ]]; then
        check_warning "omega_registry_ha_storage should be a symlink, not a directory"
    else
        check_warning "omega_registry_ha_storage not found (may not be applicable)"
    fi
}

# Validate import safety in addon/src/
validate_import_safety() {
    print_info "Validating import safety in addon/src/..."

    if [[ ! -d "$WORKSPACE_ROOT/addon/src" ]]; then
        check_warning "addon/src/ directory not found, skipping import safety validation"
        return
    fi

    # Check for Python files that might have import-time I/O
    local unsafe_patterns=(
        "open("
        "with open"
        "pathlib.*read"
        "pathlib.*write"
        "json.load"
        "yaml.load"
    )

    local unsafe_files=()
    for pattern in "${unsafe_patterns[@]}"; do
        while IFS= read -r -d '' file; do
            # Skip files with proper guards
            if ! grep -q "if __name__ == ['\"]__main__['\"]" "$file"; then
                unsafe_files+=("$file:$pattern")
            fi
        done < <(find "$WORKSPACE_ROOT/addon/src" -name "*.py" -exec grep -l "$pattern" {} \; 2>/dev/null | tr '\n' '\0')
    done

    if [[ ${#unsafe_files[@]} -eq 0 ]]; then
        check_passed "No import-time I/O detected in addon/src/"
    else
        check_failed "Potential import-time I/O in addon/src/:"
        for file_pattern in "${unsafe_files[@]}"; do
            echo "  - ${file_pattern}"
        done
    fi
}

# Validate src/data separation
validate_src_data_separation() {
    print_info "Validating src/data separation..."

    # Check that addon/src/ contains only pure code
    if [[ -d "$WORKSPACE_ROOT/addon/src" ]]; then
        # Look for data files in src/
        local data_files_in_src=()
        while IFS= read -r -d '' file; do
            data_files_in_src+=("$file")
        done < <(find "$WORKSPACE_ROOT/addon/src" -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.csv" -o -name "*.txt" \) -print0 2>/dev/null || true)

        if [[ ${#data_files_in_src[@]} -eq 0 ]]; then
            check_passed "No data files found in addon/src/ (pure code separation)"
        else
            check_warning "Data files found in addon/src/ (should be in addon/data/):"
            for file in "${data_files_in_src[@]}"; do
                echo "  - $(basename "$file")"
            done
        fi
    fi

    # Check that addon/data/ exists for I/O operations
    if [[ -d "$WORKSPACE_ROOT/addon/data" ]]; then
        check_passed "addon/data/ directory exists for I/O operations"
    else
        check_failed "addon/data/ directory missing (required for I/O separation)"
    fi
}

# Validate project metadata separation
validate_project_metadata_separation() {
    print_info "Validating project metadata separation..."

    # Check for project metadata in addon/
    local project_files_in_addon=()
    while IFS= read -r -d '' file; do
        project_files_in_addon+=("$file")
    done < <(find "$WORKSPACE_ROOT/addon" -type f \( -name "*.md" -o -name "*.code-workspace" -o -name "workspace*" \) -print0 2>/dev/null || true)

    if [[ ${#project_files_in_addon[@]} -eq 0 ]]; then
        check_passed "No project metadata found in addon/ (clean packaging)"
    else
        check_failed "Project metadata found in addon/ (should be in project/):"
        for file in "${project_files_in_addon[@]}"; do
            echo "  - $(basename "$file")"
        done
    fi

    # Check that project/ contains expected metadata
    if [[ -d "$WORKSPACE_ROOT/project" ]]; then
        check_passed "project/ directory exists for metadata separation"
    else
        check_failed "project/ directory missing (required for metadata separation)"
    fi
}

# Validate paths.py canonical path resolution
validate_canonical_paths() {
    print_info "Validating canonical path resolution..."

    local paths_file="$WORKSPACE_ROOT/addon/src/utils/paths.py"
    if [[ -f "$paths_file" ]]; then
        check_passed "addon/src/utils/paths.py exists for canonical path resolution"

        # Check if it's import-safe (no direct I/O at module level)
        if grep -q "if __name__ == ['\"]__main__['\"]" "$paths_file" || ! grep -q -E "(open\(|with open|pathlib.*read|pathlib.*write)" "$paths_file"; then
            check_passed "paths.py appears to be import-safe"
        else
            check_warning "paths.py may contain import-time I/O (review needed)"
        fi
    else
        check_failed "addon/src/utils/paths.py missing (required for ADR-0005)"
    fi
}

# Validate ADR-0003 compliance inheritance
validate_adr_0003_compliance() {
    print_info "Validating ADR-0003 compliance inheritance..."

    # Check for CLI scripts with proper guards
    if [[ -d "$WORKSPACE_ROOT/addon/src/scripts" ]]; then
        local unguarded_scripts=()
        while IFS= read -r -d '' script; do
            if ! grep -q "if __name__ == ['\"]__main__['\"]" "$script"; then
                unguarded_scripts+=("$script")
            fi
        done < <(find "$WORKSPACE_ROOT/addon/src/scripts" -name "*.py" -print0 2>/dev/null || true)

        if [[ ${#unguarded_scripts[@]} -eq 0 ]]; then
            check_passed "All CLI scripts in addon/src/scripts/ have proper guards"
        else
            check_failed "CLI scripts missing __main__ guards:"
            for script in "${unguarded_scripts[@]}"; do
                echo "  - $(basename "$script")"
            done
        fi
    else
        check_warning "addon/src/scripts/ directory not found"
    fi
}

# Main validation function
main() {
    print_info "ADR-0005 Workspace Structure Compliance Validation"
    print_info "Workspace: $WORKSPACE_ROOT"
    echo

    validate_directory_structure
    validate_import_safety
    validate_src_data_separation
    validate_project_metadata_separation
    validate_canonical_paths
    validate_adr_0003_compliance

    echo
    print_info "=== VALIDATION SUMMARY ==="
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Checks Failed: $CHECKS_FAILED"
    echo "Warnings: $WARNINGS"
    echo

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        print_success "✅ ADR-0005 compliance validation passed!"
        if [[ $WARNINGS -gt 0 ]]; then
            print_warning "$WARNINGS warnings require attention"
        fi
    else
        print_error "❌ $CHECKS_FAILED compliance issues found"
        echo
        echo "ADR-0005 compliance issues detected. Please:"
        echo "  1. Review failed checks above"
        echo "  2. Ensure addon/src/ contains only import-safe pure code"
        echo "  3. Move file I/O operations to addon/data/"
        echo "  4. Move project metadata to project/ directory"
        echo "  5. Implement addon/src/utils/paths.py for canonical path resolution"
    fi

    # Exit with appropriate code
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function
main "$@"
