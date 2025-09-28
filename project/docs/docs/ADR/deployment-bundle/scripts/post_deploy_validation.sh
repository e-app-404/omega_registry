#!/bin/bash

# Post-Deployment Validation Script
# Validates that the Cross-Repository ADR system was deployed correctly
# and all components are functional.
#
# Usage: ./post_deploy_validation.sh [target_repo_path]

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TARGET_REPO="${1:-$(dirname $(dirname "$SCRIPT_DIR"))}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Validation counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Print functions
print_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
print_success() { echo -e "${GREEN}✅ $*${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
print_error() { echo -e "${RED}❌ $*${NC}"; }
print_check() { echo -e "${BLUE}🔍 Checking: $*${NC}"; }

# Validation functions
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

# Validate directory structure
validate_directory_structure() {
    print_check "Directory structure"

    local required_dirs=(
        "$TARGET_REPO/docs/ADR"
        "$TARGET_REPO/ops/ADR"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            check_passed "Directory exists: $dir"
        else
            check_failed "Missing directory: $dir"
        fi
    done
}

# Validate required files
validate_required_files() {
    print_check "Required files"

    local required_files=(
        "$TARGET_REPO/docs/ADR/ADR-template-enhanced.md"
        "$TARGET_REPO/docs/ADR/ADR-XXXX-cross-repo-standard.md"
        "$TARGET_REPO/docs/ADR/repository-mapping.yaml"
        "$TARGET_REPO/docs/ADR/alignment-status.yaml"
        "$TARGET_REPO/ops/ADR/validate_cross_repo_links.sh"
        "$TARGET_REPO/ops/ADR/post_deploy_validation.sh"
    )

    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            check_passed "File exists: $(basename "$file")"
        else
            check_failed "Missing file: $file"
        fi
    done
}

# Validate script permissions
validate_script_permissions() {
    print_check "Script permissions"

    local scripts=(
        "$TARGET_REPO/ops/ADR/validate_cross_repo_links.sh"
        "$TARGET_REPO/ops/ADR/post_deploy_validation.sh"
    )

    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if [[ -x "$script" ]]; then
                check_passed "Executable: $(basename "$script")"
            else
                check_failed "Not executable: $script"
            fi
        fi
    done
}

# Validate template customization
validate_template_customization() {
    print_check "Template customization"

    local templates=(
        "$TARGET_REPO/docs/ADR/repository-mapping.yaml"
        "$TARGET_REPO/docs/ADR/alignment-status.yaml"
    )

    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            local placeholder_count
            placeholder_count=$(grep -c '{[A-Z_]*}' "$template" 2>/dev/null || true)

            if [[ $placeholder_count -gt 0 ]]; then
                check_warning "Template needs customization: $(basename "$template") ($placeholder_count placeholders)"
            else
                check_passed "Template customized: $(basename "$template")"
            fi
        fi
    done
}

# Validate ADR template integrity
validate_adr_template_integrity() {
    print_check "ADR template integrity"

    local template="$TARGET_REPO/docs/ADR/ADR-template-enhanced.md"

    if [[ -f "$template" ]]; then
        # Check for required sections
        local required_sections=(
            "Cross-Repository Context"
            "Problem Statement"
            "Decision"
            "Alternatives Considered"
            "Implementation Details"
            "Validation Block"
        )

        local missing_sections=()
        for section in "${required_sections[@]}"; do
            if ! grep -q "$section" "$template"; then
                missing_sections+=("$section")
            fi
        done

        if [[ ${#missing_sections[@]} -eq 0 ]]; then
            check_passed "ADR template has all required sections"
        else
            check_failed "ADR template missing sections: ${missing_sections[*]}"
        fi
    fi
}

# Validate configuration file syntax
validate_configuration_syntax() {
    print_check "Configuration file syntax"

    local yaml_files=(
        "$TARGET_REPO/docs/ADR/repository-mapping.yaml"
        "$TARGET_REPO/docs/ADR/alignment-status.yaml"
    )

    for yaml_file in "${yaml_files[@]}"; do
        if [[ -f "$yaml_file" ]]; then
            if command -v yq >/dev/null 2>&1; then
                if yq eval '.' "$yaml_file" >/dev/null 2>&1; then
                    check_passed "Valid YAML syntax: $(basename "$yaml_file")"
                else
                    check_failed "Invalid YAML syntax: $yaml_file"
                fi
            elif command -v python3 >/dev/null 2>&1; then
                if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" >/dev/null 2>&1; then
                    check_passed "Valid YAML syntax: $(basename "$yaml_file")"
                else
                    check_failed "Invalid YAML syntax: $yaml_file"
                fi
            else
                check_warning "Cannot validate YAML syntax (no yq or python3 available)"
            fi
        fi
    done
}

# Test validation scripts
test_validation_scripts() {
    print_check "Validation script functionality"

    local link_validator="$TARGET_REPO/ops/ADR/validate_cross_repo_links.sh"

    if [[ -f "$link_validator" && -x "$link_validator" ]]; then
        # Test the help function
        if "$link_validator" --help >/dev/null 2>&1; then
            check_passed "Link validator help function works"
        else
            check_failed "Link validator help function failed"
        fi

        # Test with non-existent directory (should handle gracefully)
        if "$link_validator" /non/existent/path 2>/dev/null || [[ $? -eq 3 ]]; then
            check_passed "Link validator handles missing directory correctly"
        else
            check_failed "Link validator does not handle missing directory correctly"
        fi
    fi
}

# Check gitignore updates
check_gitignore_updates() {
    print_check ".gitignore updates"

    local gitignore="$TARGET_REPO/.gitignore"

    if [[ -f "$gitignore" ]]; then
        if grep -q "Cross-Repository ADR System" "$gitignore"; then
            check_passed ".gitignore contains ADR patterns"
        else
            check_warning ".gitignore may not contain ADR patterns"
        fi
    else
        check_warning ".gitignore file not found"
    fi
}

# Validate Git repository status
validate_git_status() {
    print_check "Git repository status"

    if [[ -d "$TARGET_REPO/.git" ]]; then
        check_passed "Target is a Git repository"

        # Check for uncommitted changes
        cd "$TARGET_REPO"
        if git diff --quiet && git diff --staged --quiet; then
            check_passed "No uncommitted changes"
        else
            check_warning "Repository has uncommitted changes (expected after deployment)"
        fi
        cd - >/dev/null
    else
        check_failed "Target is not a Git repository"
    fi
}

# Validate cross-repository links (basic test)
validate_basic_cross_repo_links() {
    print_check "Basic cross-repository link validation"

    local link_validator="$TARGET_REPO/ops/ADR/validate_cross_repo_links.sh"

    if [[ -f "$link_validator" && -x "$link_validator" ]]; then
        # Run validation if there are ADR files
        local adr_files
        mapfile -t adr_files < <(find "$TARGET_REPO/docs/ADR" -name "ADR-*.md" -type f 2>/dev/null || true)

        if [[ ${#adr_files[@]} -gt 0 ]]; then
            if "$link_validator" --timeout 5 "$TARGET_REPO/docs/ADR" >/dev/null 2>&1; then
                check_passed "Cross-repository link validation successful"
            else
                local exit_code=$?
                if [[ $exit_code -eq 3 ]]; then
                    check_warning "No ADR files found for validation"
                else
                    check_warning "Cross-repository link validation found issues (exit code: $exit_code)"
                fi
            fi
        else
            check_warning "No ADR files found for cross-repository link validation"
        fi
    fi
}

# Output deployment verification summary
output_summary() {
    echo
    print_info "=== POST-DEPLOYMENT VERIFICATION SUMMARY ==="
    echo "Target Repository: $TARGET_REPO"
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Checks Failed: $CHECKS_FAILED"
    echo "Warnings: $WARNINGS"
    echo "Verification Date: $(date)"
    echo

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        print_success "✅ All critical checks passed!"

        if [[ $WARNINGS -gt 0 ]]; then
            print_warning "⚠️  $WARNINGS warnings require attention"
            echo
            echo "Next steps:"
            echo "  1. Address any warnings above"
            echo "  2. Customize configuration files (remove {PLACEHOLDER} values)"
            echo "  3. Add your ADRs to the alignment status tracking"
            echo "  4. Test validation scripts with your actual ADR files"
            echo "  5. Consider adding ADR validation to your CI/CD pipeline"
        else
            print_success "🎉 Perfect deployment! No issues detected."
        fi
    else
        print_error "❌ $CHECKS_FAILED critical checks failed"
        echo
        echo "Deployment issues detected. Please:"
        echo "  1. Review the failed checks above"
        echo "  2. Re-run the deployment script if necessary"
        echo "  3. Ensure all required files and directories are present"
        echo "  4. Check file permissions for validation scripts"
    fi
}

# Main validation function
main() {
    print_info "Cross-Repository ADR Post-Deployment Validation"
    print_info "Target Repository: $TARGET_REPO"
    echo

    # Run all validation checks
    validate_directory_structure
    validate_required_files
    validate_script_permissions
    validate_template_customization
    validate_adr_template_integrity
    validate_configuration_syntax
    test_validation_scripts
    check_gitignore_updates
    validate_git_status
    validate_basic_cross_repo_links

    # Output summary
    output_summary

    # Exit with appropriate code
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function
main "$@"
