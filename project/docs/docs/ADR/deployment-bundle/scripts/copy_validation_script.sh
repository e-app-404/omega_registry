#!/bin/bash

# Copy Validation Script Helper
# Copies validation scripts to the ops/ADR directory of target repositories
# Used by the main deployment script and for standalone script deployment.
#
# Usage: ./copy_validation_script.sh [target_repo_path] [source_script_path]

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TARGET_REPO="${1:-}"
readonly SOURCE_SCRIPT="${2:-}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Print functions
print_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
print_success() { echo -e "${GREEN}✅ $*${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
print_error() { echo -e "${RED}❌ $*${NC}"; }

# Help function
show_help() {
    cat << EOF
Copy Validation Script Helper

USAGE:
    $0 [TARGET_REPO_PATH] [SOURCE_SCRIPT_PATH]

DESCRIPTION:
    Copies validation scripts to the ops/ADR directory of target repositories.
    Creates the necessary directory structure and sets appropriate permissions.

ARGUMENTS:
    TARGET_REPO_PATH   Path to target repository (default: auto-detect)
    SOURCE_SCRIPT_PATH Path to source script to copy (default: copy all scripts)

EXAMPLES:
    # Copy all validation scripts to target repository
    $0 /path/to/target/repo

    # Copy specific script
    $0 /path/to/target/repo validate_cross_repo_links.sh

    # Copy to current directory (auto-detect)
    $0

NOTES:
    - Creates ops/ADR directory if it doesn't exist
    - Sets executable permissions on copied scripts
    - Preserves file attributes and timestamps where possible
EOF
}

# Validate arguments
validate_arguments() {
    if [[ "$TARGET_REPO" == "--help" ]] || [[ "$TARGET_REPO" == "-h" ]]; then
        show_help
        exit 0
    fi

    # Auto-detect target repository if not provided
    if [[ -z "$TARGET_REPO" ]]; then
        # Try to find repository root by looking for .git directory
        local current_dir="$(pwd)"
        while [[ "$current_dir" != "/" ]]; do
            if [[ -d "$current_dir/.git" ]]; then
                TARGET_REPO="$current_dir"
                break
            fi
            current_dir="$(dirname "$current_dir")"
        done

        if [[ -z "$TARGET_REPO" ]]; then
            print_error "Could not auto-detect target repository. Please provide path."
            exit 1
        fi
    fi

    # Validate target repository
    if [[ ! -d "$TARGET_REPO" ]]; then
        print_error "Target repository directory does not exist: $TARGET_REPO"
        exit 1
    fi

    if [[ ! -d "$TARGET_REPO/.git" ]]; then
        print_error "Target directory is not a git repository: $TARGET_REPO"
        exit 1
    fi

    print_info "Target repository: $TARGET_REPO"
}

# Create ops/ADR directory structure
create_ops_directory() {
    local ops_adr_dir="$TARGET_REPO/ops/ADR"

    if [[ ! -d "$ops_adr_dir" ]]; then
        print_info "Creating ops/ADR directory..."
        mkdir -p "$ops_adr_dir"
        print_success "Created directory: $ops_adr_dir"
    else
        print_info "ops/ADR directory already exists"
    fi
}

# Copy single script
copy_script() {
    local script_name="$1"
    local source_path="$SCRIPT_DIR/$script_name"
    local target_path="$TARGET_REPO/ops/ADR/$script_name"

    if [[ ! -f "$source_path" ]]; then
        print_error "Source script not found: $source_path"
        return 1
    fi

    print_info "Copying script: $script_name"

    # Copy the script
    cp "$source_path" "$target_path"

    # Make it executable
    chmod +x "$target_path"

    print_success "Copied and made executable: $script_name"
    return 0
}

# Copy all validation scripts
copy_all_scripts() {
    local scripts=(
        "validate_cross_repo_links.sh"
        "post_deploy_validation.sh"
        "copy_validation_script.sh"
    )

    local copied_count=0
    local total_scripts=${#scripts[@]}

    print_info "Copying all validation scripts..."

    for script in "${scripts[@]}"; do
        if copy_script "$script"; then
            copied_count=$((copied_count + 1))
        fi
    done

    if [[ $copied_count -eq $total_scripts ]]; then
        print_success "Successfully copied all $total_scripts validation scripts"
    else
        print_warning "Copied $copied_count out of $total_scripts scripts"
    fi
}

# Verify copied scripts
verify_scripts() {
    local ops_adr_dir="$TARGET_REPO/ops/ADR"

    print_info "Verifying copied scripts..."

    # Find all shell scripts in ops/ADR
    local copied_scripts
    mapfile -t copied_scripts < <(find "$ops_adr_dir" -name "*.sh" -type f 2>/dev/null || true)

    if [[ ${#copied_scripts[@]} -eq 0 ]]; then
        print_warning "No shell scripts found in ops/ADR directory"
        return 1
    fi

    local verified_count=0
    for script in "${copied_scripts[@]}"; do
        local script_name=$(basename "$script")

        # Check if executable
        if [[ -x "$script" ]]; then
            print_success "Verified: $script_name (executable)"
            verified_count=$((verified_count + 1))
        else
            print_warning "Not executable: $script_name"
        fi
    done

    print_info "Verified $verified_count executable scripts"
    return 0
}

# Create basic validation configuration
create_basic_config() {
    local config_file="$TARGET_REPO/ops/ADR/validation-config.env"

    if [[ ! -f "$config_file" ]]; then
        print_info "Creating basic validation configuration..."

        cat > "$config_file" << 'EOF'
# Cross-Repository ADR Validation Configuration
# Environment variables for validation scripts

# URL validation timeout (seconds)
VALIDATION_TIMEOUT=10

# Enable verbose output
VERBOSE=false

# Enable caching of validation results
USE_CACHE=true

# Fail fast on first validation error
FAIL_FAST=false

# GitHub token for API validation (optional)
# GITHUB_TOKEN=your_token_here

# JSON output format
JSON_OUTPUT=false

# Additional validation options
# Add custom configuration as needed
EOF

        print_success "Created validation configuration: validation-config.env"
    else
        print_info "Validation configuration already exists"
    fi
}

# Main function
main() {
    validate_arguments
    create_ops_directory

    if [[ -n "$SOURCE_SCRIPT" ]]; then
        # Copy specific script
        copy_script "$SOURCE_SCRIPT"
    else
        # Copy all scripts
        copy_all_scripts
    fi

    verify_scripts
    create_basic_config

    echo
    print_success "Validation script deployment completed!"
    print_info "Scripts are available in: $TARGET_REPO/ops/ADR/"

    # Show next steps
    echo
    print_info "Next steps:"
    echo "  1. Review and customize validation-config.env"
    echo "  2. Test validation scripts: ./ops/ADR/validate_cross_repo_links.sh --help"
    echo "  3. Add validation to your CI/CD pipeline"
    echo "  4. Run post-deployment validation: ./ops/ADR/post_deploy_validation.sh"
}

# Execute main function
main "$@"
