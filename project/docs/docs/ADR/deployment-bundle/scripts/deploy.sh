#!/bin/bash

# Cross-Repository ADR Deployment Script
# Deploys the complete ADR system to target repositories with validation and rollback capabilities.
#
# Usage: ./deploy.sh [options] [target_repo_path]
# Options:
#   --dry-run          Show what would be done without making changes
#   --force            Force deployment even if target already has ADR system
#   --rollback         Remove ADR system from target repository
#   --upgrade          Upgrade existing ADR system to latest version
#   --validate-only    Only run validation, don't deploy
#   --help             Show this help message
#
# Environment Variables:
#   GITHUB_TOKEN       GitHub personal access token for validation (optional)
#   DRY_RUN           Set to 'true' to enable dry-run mode
#   FORCE_DEPLOY      Set to 'true' to enable force mode

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BUNDLE_DIR="$(dirname "$SCRIPT_DIR")"
readonly TEMPLATES_DIR="$BUNDLE_DIR/templates"
readonly EXAMPLES_DIR="$BUNDLE_DIR/examples"
readonly LOG_FILE="$BUNDLE_DIR/deployment.log"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Global variables
DRY_RUN=false
FORCE_DEPLOY=false
ROLLBACK_MODE=false
UPGRADE_MODE=false
VALIDATE_ONLY=false
TARGET_REPO=""
START_TIME=$(date +%s)

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
print_step() { echo -e "${BLUE}🔧 $*${NC}"; }

# Help function
show_help() {
    cat << EOF
Cross-Repository ADR Deployment Script

USAGE:
    $0 [OPTIONS] [TARGET_REPO_PATH]

DESCRIPTION:
    Deploys a complete Architecture Decision Record (ADR) system to target
    repositories with cross-repository validation capabilities.

OPTIONS:
    --dry-run          Show what would be done without making changes
    --force            Force deployment even if target already has ADR system
    --rollback         Remove ADR system from target repository
    --upgrade          Upgrade existing ADR system to latest version
    --validate-only    Only run validation, don't deploy
    --help             Show this help message

ARGUMENTS:
    TARGET_REPO_PATH   Path to target repository (default: current directory)

EXAMPLES:
    # Deploy to current directory
    $0

    # Deploy to specific repository
    $0 /path/to/target/repo

    # Dry run to see what would be done
    $0 --dry-run /path/to/target/repo

    # Force deployment over existing system
    $0 --force /path/to/target/repo

    # Rollback deployment
    $0 --rollback /path/to/target/repo

    # Upgrade existing system
    $0 --upgrade /path/to/target/repo

ENVIRONMENT VARIABLES:
    GITHUB_TOKEN       GitHub token for URL validation (optional)
    DRY_RUN           Set to 'true' to enable dry-run mode
    FORCE_DEPLOY      Set to 'true' to enable force mode

EXIT CODES:
    0   Success
    1   General error
    2   Invalid arguments
    3   Pre-deployment validation failed
    4   Deployment failed
    5   Post-deployment validation failed
    6   Rollback failed

For more information, see the deployment bundle README.md
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
                FORCE_DEPLOY=true
                log_info "Force deployment mode enabled"
                shift
                ;;
            --rollback)
                ROLLBACK_MODE=true
                log_info "Rollback mode enabled"
                shift
                ;;
            --upgrade)
                UPGRADE_MODE=true
                log_info "Upgrade mode enabled"
                shift
                ;;
            --validate-only)
                VALIDATE_ONLY=true
                log_info "Validation-only mode enabled"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                echo "Use --help for usage information."
                exit 2
                ;;
            *)
                if [[ -z "$TARGET_REPO" ]]; then
                    TARGET_REPO="$1"
                else
                    print_error "Multiple repository paths specified: $TARGET_REPO and $1"
                    exit 2
                fi
                shift
                ;;
        esac
    done

    # Set default target repository
    if [[ -z "$TARGET_REPO" ]]; then
        TARGET_REPO=$(pwd)
    fi

    # Resolve absolute path
    TARGET_REPO=$(realpath "$TARGET_REPO")
    log_info "Target repository: $TARGET_REPO"

    # Environment variable overrides
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        DRY_RUN=true
    fi
    if [[ "${FORCE_DEPLOY:-false}" == "true" ]]; then
        FORCE_DEPLOY=true
    fi
}

# Validate bundle integrity
validate_bundle() {
    print_step "Validating deployment bundle integrity..."

    local missing_files=()

    # Required files
    local required_files=(
        "$BUNDLE_DIR/README.md"
        "$BUNDLE_DIR/COPILOT-INSTRUCTIONS.md"
        "$BUNDLE_DIR/MANIFEST.md"
        "$TEMPLATES_DIR/ADR-template-enhanced.md"
        "$TEMPLATES_DIR/ADR-XXXX-cross-repo-standard.md"
        "$TEMPLATES_DIR/repository-mapping.yaml.template"
        "$TEMPLATES_DIR/alignment-status.yaml.template"
        "$TEMPLATES_DIR/gitignore-additions.txt"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done

    # Required directories
    local required_dirs=(
        "$TEMPLATES_DIR"
        "$SCRIPT_DIR"
        "$EXAMPLES_DIR"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            missing_files+=("$dir/")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "Bundle integrity check failed. Missing files/directories:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        log_error "Bundle integrity validation failed: ${#missing_files[@]} missing files"
        exit 3
    fi

    print_success "Bundle integrity validated"
    log_info "Bundle integrity check passed"
}

# Validate target repository
validate_target_repository() {
    print_step "Validating target repository..."

    # Check if directory exists
    if [[ ! -d "$TARGET_REPO" ]]; then
        print_error "Target repository directory does not exist: $TARGET_REPO"
        log_error "Target repository validation failed: directory not found"
        exit 3
    fi

    # Check if it's a git repository
    if [[ ! -d "$TARGET_REPO/.git" ]]; then
        print_error "Target directory is not a git repository: $TARGET_REPO"
        log_error "Target repository validation failed: not a git repository"
        exit 3
    fi

    # Check write permissions
    if [[ ! -w "$TARGET_REPO" ]]; then
        print_error "No write permissions for target repository: $TARGET_REPO"
        log_error "Target repository validation failed: no write permissions"
        exit 3
    fi

    # Check for existing ADR system
    local adr_dir="$TARGET_REPO/docs/ADR"
    local ops_adr_dir="$TARGET_REPO/ops/ADR"

    if [[ -d "$adr_dir" ]] && [[ ! "$FORCE_DEPLOY" == true ]] && [[ ! "$UPGRADE_MODE" == true ]]; then
        print_error "ADR system already exists in target repository"
        print_info "Use --force to overwrite or --upgrade to update existing system"
        log_error "Target repository validation failed: ADR system already exists"
        exit 3
    fi

    print_success "Target repository validated"
    log_info "Target repository validation passed"
}

# Create directory structure
create_directory_structure() {
    print_step "Creating directory structure..."

    local dirs=(
        "$TARGET_REPO/docs/ADR"
        "$TARGET_REPO/ops/ADR"
    )

    for dir in "${dirs[@]}"; do
        if [[ "$DRY_RUN" == true ]]; then
            print_info "Would create directory: $dir"
        else
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done

    print_success "Directory structure created"
}

# Deploy templates
deploy_templates() {
    print_step "Deploying ADR templates..."

    # Enhanced ADR template
    local adr_template_source="$TEMPLATES_DIR/ADR-template-enhanced.md"
    local adr_template_target="$TARGET_REPO/docs/ADR/ADR-template-enhanced.md"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would copy: $adr_template_source -> $adr_template_target"
    else
        cp "$adr_template_source" "$adr_template_target"
        log_info "Deployed ADR template: $adr_template_target"
    fi

    # Cross-repository standard template
    local standard_template_source="$TEMPLATES_DIR/ADR-XXXX-cross-repo-standard.md"
    local standard_template_target="$TARGET_REPO/docs/ADR/ADR-XXXX-cross-repo-standard.md"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would copy: $standard_template_source -> $standard_template_target"
    else
        cp "$standard_template_source" "$standard_template_target"
        log_info "Deployed standard template: $standard_template_target"
    fi

    print_success "Templates deployed"
}

# Deploy configuration files
deploy_configuration() {
    print_step "Deploying configuration files..."

    # Repository mapping configuration
    local mapping_source="$TEMPLATES_DIR/repository-mapping.yaml.template"
    local mapping_target="$TARGET_REPO/docs/ADR/repository-mapping.yaml"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would copy: $mapping_source -> $mapping_target"
    else
        cp "$mapping_source" "$mapping_target"
        log_info "Deployed repository mapping: $mapping_target"
    fi

    # Alignment status configuration
    local alignment_source="$TEMPLATES_DIR/alignment-status.yaml.template"
    local alignment_target="$TARGET_REPO/docs/ADR/alignment-status.yaml"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would copy: $alignment_source -> $alignment_target"
    else
        cp "$alignment_source" "$alignment_target"
        log_info "Deployed alignment status: $alignment_target"
    fi

    print_success "Configuration files deployed"
}

# Deploy validation scripts
deploy_validation_scripts() {
    print_step "Deploying validation scripts..."

    # Copy all scripts from the scripts directory
    local scripts=(
        "validate_cross_repo_links.sh"
        "post_deploy_validation.sh"
        "copy_validation_script.sh"
    )

    for script in "${scripts[@]}"; do
        local script_source="$SCRIPT_DIR/$script"
        local script_target="$TARGET_REPO/ops/ADR/$script"

        if [[ -f "$script_source" ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                print_info "Would copy: $script_source -> $script_target"
                print_info "Would make executable: $script_target"
            else
                cp "$script_source" "$script_target"
                chmod +x "$script_target"
                log_info "Deployed and made executable: $script_target"
            fi
        fi
    done

    print_success "Validation scripts deployed"
}

# Update gitignore
update_gitignore() {
    print_step "Updating .gitignore..."

    local gitignore_file="$TARGET_REPO/.gitignore"
    local gitignore_additions="$TEMPLATES_DIR/gitignore-additions.txt"

    if [[ ! -f "$gitignore_additions" ]]; then
        print_warning "Gitignore additions template not found, skipping"
        return
    fi

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would append ADR patterns to: $gitignore_file"
    else
        echo "" >> "$gitignore_file"
        echo "# Cross-Repository ADR System (added by deployment script)" >> "$gitignore_file"
        cat "$gitignore_additions" >> "$gitignore_file"
        log_info "Updated .gitignore with ADR patterns"
    fi

    print_success ".gitignore updated"
}

# Deploy examples
deploy_examples() {
    print_step "Deploying examples..."

    if [[ ! -d "$EXAMPLES_DIR" ]]; then
        print_warning "Examples directory not found, skipping"
        return
    fi

    local examples_target="$TARGET_REPO/docs/ADR/examples"

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would create directory: $examples_target"
        print_info "Would copy examples from: $EXAMPLES_DIR"
    else
        mkdir -p "$examples_target"
        cp -r "$EXAMPLES_DIR"/* "$examples_target/" 2>/dev/null || true
        log_info "Deployed examples to: $examples_target"
    fi

    print_success "Examples deployed"
}

# Run post-deployment validation
run_post_deployment_validation() {
    print_step "Running post-deployment validation..."

    local validation_script="$TARGET_REPO/ops/ADR/post_deploy_validation.sh"

    if [[ ! -f "$validation_script" ]]; then
        print_warning "Post-deployment validation script not found, skipping"
        return
    fi

    if [[ "$DRY_RUN" == true ]]; then
        print_info "Would run: $validation_script"
    else
        if bash "$validation_script" "$TARGET_REPO"; then
            print_success "Post-deployment validation passed"
            log_info "Post-deployment validation successful"
        else
            print_error "Post-deployment validation failed"
            log_error "Post-deployment validation failed"
            exit 5
        fi
    fi
}

# Rollback deployment
rollback_deployment() {
    print_step "Rolling back ADR deployment..."

    local paths_to_remove=(
        "$TARGET_REPO/docs/ADR"
        "$TARGET_REPO/ops/ADR"
    )

    for path in "${paths_to_remove[@]}"; do
        if [[ -e "$path" ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                print_info "Would remove: $path"
            else
                rm -rf "$path"
                log_info "Removed: $path"
            fi
        fi
    done

    # Remove gitignore entries (simplified - just warn user)
    print_warning "Manual cleanup required: Remove ADR patterns from $TARGET_REPO/.gitignore"

    print_success "Rollback completed"
    log_info "Rollback deployment completed"
}

# Print deployment summary
print_deployment_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    echo
    print_success "=== DEPLOYMENT SUMMARY ==="
    echo "Target Repository: $TARGET_REPO"
    echo "Mode: $(if [[ "$DRY_RUN" == true ]]; then echo "DRY RUN"; elif [[ "$ROLLBACK_MODE" == true ]]; then echo "ROLLBACK"; elif [[ "$UPGRADE_MODE" == true ]]; then echo "UPGRADE"; else echo "DEPLOY"; fi)"
    echo "Duration: ${duration}s"
    echo "Log File: $LOG_FILE"
    echo

    if [[ "$DRY_RUN" == true ]]; then
        print_info "This was a dry run. No changes were made."
        print_info "Run without --dry-run to perform actual deployment."
    elif [[ "$ROLLBACK_MODE" == true ]]; then
        print_success "ADR system successfully removed from target repository."
    else
        print_success "ADR system successfully deployed to target repository."
        print_info "Next steps:"
        echo "  1. Customize repository-mapping.yaml for your ecosystem"
        echo "  2. Customize alignment-status.yaml with your ADRs"
        echo "  3. Review and customize ADR templates"
        echo "  4. Run validation scripts to verify setup"
        echo "  5. Add ADR validation to your CI/CD pipeline"
    fi

    log_success "Deployment completed successfully in ${duration}s"
}

# Main deployment function
main_deploy() {
    validate_bundle
    validate_target_repository

    if [[ "$VALIDATE_ONLY" == true ]]; then
        print_success "Validation completed successfully"
        exit 0
    fi

    if [[ "$ROLLBACK_MODE" == true ]]; then
        rollback_deployment
    else
        create_directory_structure
        deploy_templates
        deploy_configuration
        deploy_validation_scripts
        update_gitignore
        deploy_examples
        run_post_deployment_validation
    fi
}

# Error handling
trap 'print_error "Deployment failed with exit code $?"; exit 1' ERR

# Signal handling
trap 'print_warning "Deployment interrupted"; exit 130' INT TERM

# Main execution
main() {
    # Initialize log file
    echo "=== Cross-Repository ADR Deployment Log ===" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"

    parse_arguments "$@"

    print_info "Cross-Repository ADR Deployment Script"
    print_info "Bundle Directory: $BUNDLE_DIR"
    print_info "Target Repository: $TARGET_REPO"

    if [[ "$DRY_RUN" == true ]]; then
        print_warning "DRY RUN MODE - No changes will be made"
    fi

    main_deploy
    print_deployment_summary
}

# Execute main function with all arguments
main "$@"
