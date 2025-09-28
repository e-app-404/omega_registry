#!/bin/bash

# Cross-Repository ADR Link Validation Script
# Validates cross-repository links in ADR files and reports broken or invalid references.
#
# Usage: ./validate_cross_repo_links.sh [options] [adr_directory]
# Options:
#   --verbose          Enable verbose output
#   --json             Output results in JSON format
#   --fail-fast        Stop on first validation error
#   --timeout SECONDS  Set URL validation timeout (default: 10)
#   --cache            Use cached validation results when available
#   --help             Show this help message

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly CACHE_DIR="$SCRIPT_DIR/.cache"
readonly CACHE_FILE="$CACHE_DIR/link_validation_cache.json"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Global variables
VERBOSE=false
JSON_OUTPUT=false
FAIL_FAST=false
USE_CACHE=false
TIMEOUT=10
ADR_DIRECTORY=""
VALIDATION_RESULTS=()
TOTAL_LINKS=0
VALID_LINKS=0
INVALID_LINKS=0
CACHED_LINKS=0

# Logging functions
log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $*" >&2
    fi
}

print_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
print_success() { echo -e "${GREEN}✅ $*${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
print_error() { echo -e "${RED}❌ $*${NC}"; }

# Help function
show_help() {
    cat << EOF
Cross-Repository ADR Link Validation Script

USAGE:
    $0 [OPTIONS] [ADR_DIRECTORY]

DESCRIPTION:
    Validates cross-repository links in Architecture Decision Record (ADR) files.
    Checks URL accessibility, validates GitHub repository references, and reports
    broken or invalid links.

OPTIONS:
    --verbose          Enable verbose output with detailed validation steps
    --json             Output validation results in JSON format
    --fail-fast        Stop validation on first error encountered
    --timeout SECONDS  Set URL validation timeout in seconds (default: 10)
    --cache            Use cached validation results when available
    --help             Show this help message

ARGUMENTS:
    ADR_DIRECTORY      Directory containing ADR files (default: docs/ADR)

EXAMPLES:
    # Validate ADRs in default directory
    $0

    # Validate with verbose output
    $0 --verbose

    # Validate with JSON output and caching
    $0 --json --cache docs/ADR

    # Quick validation with short timeout
    $0 --timeout 5 --fail-fast

ENVIRONMENT VARIABLES:
    GITHUB_TOKEN       GitHub personal access token for API validation
    NO_COLOR          Set to disable colored output

EXIT CODES:
    0   All links are valid
    1   Some links are invalid
    2   Validation error or invalid arguments
    3   No ADR files found
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --fail-fast)
                FAIL_FAST=true
                shift
                ;;
            --timeout)
                if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^[0-9]+$ ]]; then
                    print_error "Invalid timeout value: $2"
                    exit 2
                fi
                TIMEOUT="$2"
                shift 2
                ;;
            --cache)
                USE_CACHE=true
                shift
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
                if [[ -z "$ADR_DIRECTORY" ]]; then
                    ADR_DIRECTORY="$1"
                else
                    print_error "Multiple ADR directories specified"
                    exit 2
                fi
                shift
                ;;
        esac
    done

    # Set default ADR directory
    if [[ -z "$ADR_DIRECTORY" ]]; then
        ADR_DIRECTORY="$REPO_ROOT/docs/ADR"
    fi

    # Resolve absolute path
    ADR_DIRECTORY=$(realpath "$ADR_DIRECTORY")

    log_verbose "ADR directory: $ADR_DIRECTORY"
    log_verbose "Timeout: ${TIMEOUT}s"
    log_verbose "Cache enabled: $USE_CACHE"
}

# Initialize cache
init_cache() {
    if [[ "$USE_CACHE" == true ]]; then
        mkdir -p "$CACHE_DIR"
        if [[ ! -f "$CACHE_FILE" ]]; then
            echo '{}' > "$CACHE_FILE"
        fi
        log_verbose "Cache initialized: $CACHE_FILE"
    fi
}

# Get cached result
get_cached_result() {
    local url="$1"
    if [[ "$USE_CACHE" == true ]] && command -v jq >/dev/null 2>&1; then
        jq -r --arg url "$url" '.[$url] // "null"' "$CACHE_FILE" 2>/dev/null || echo "null"
    else
        echo "null"
    fi
}

# Cache result
cache_result() {
    local url="$1"
    local result="$2"
    if [[ "$USE_CACHE" == true ]] && command -v jq >/dev/null 2>&1; then
        local temp_file=$(mktemp)
        jq --arg url "$url" --arg result "$result" '.[$url] = $result' "$CACHE_FILE" > "$temp_file" && mv "$temp_file" "$CACHE_FILE"
        log_verbose "Cached result for: $url"
    fi
}

# Validate URL accessibility
validate_url() {
    local url="$1"
    local cached_result

    # Check cache first
    cached_result=$(get_cached_result "$url")
    if [[ "$cached_result" != "null" ]]; then
        log_verbose "Using cached result for: $url"
        CACHED_LINKS=$((CACHED_LINKS + 1))
        echo "$cached_result"
        return
    fi

    log_verbose "Validating URL: $url"

    # Use curl to check URL accessibility
    local result="invalid"
    local status_code

    if command -v curl >/dev/null 2>&1; then
        if status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" -L "$url" 2>/dev/null); then
            if [[ "$status_code" =~ ^[23] ]]; then
                result="valid"
            else
                result="invalid (HTTP $status_code)"
            fi
        else
            result="invalid (connection failed)"
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget --spider --timeout="$TIMEOUT" -q "$url" 2>/dev/null; then
            result="valid"
        else
            result="invalid (wget failed)"
        fi
    else
        result="unknown (no validation tool available)"
    fi

    cache_result "$url" "$result"
    echo "$result"
}

# Extract cross-repository links from ADR file
extract_cross_repo_links() {
    local adr_file="$1"
    local links=()

    log_verbose "Extracting links from: $adr_file"

    # Extract GitHub repository links
    while IFS= read -r line; do
        if [[ "$line" =~ https://github\.com/[^/]+/[^/]+ ]]; then
            local url="${BASH_REMATCH[0]}"
            # Clean up trailing punctuation
            url="${url%[)[:space:]]*}"
            url="${url%,}"
            url="${url%.}"
            links+=("$url")
        fi
    done < "$adr_file"

    # Extract links from YAML cross-reference blocks
    local in_yaml_block=false
    while IFS= read -r line; do
        if [[ "$line" =~ ^```yaml ]]; then
            in_yaml_block=true
        elif [[ "$line" =~ ^``` ]] && [[ "$in_yaml_block" == true ]]; then
            in_yaml_block=false
        elif [[ "$in_yaml_block" == true ]] && [[ "$line" =~ repo:.*\"([^\"]+)\" ]]; then
            local repo="${BASH_REMATCH[1]}"
            if [[ "$repo" =~ ^[^/]+/[^/]+$ ]]; then
                links+=("https://github.com/$repo")
            fi
        fi
    done < "$adr_file"

    # Remove duplicates and return
    printf '%s\n' "${links[@]}" | sort -u
}

# Validate single ADR file
validate_adr_file() {
    local adr_file="$1"
    local file_results=()

    log_verbose "Validating ADR file: $adr_file"

    # Extract cross-repository links
    local links
    mapfile -t links < <(extract_cross_repo_links "$adr_file")

    if [[ ${#links[@]} -eq 0 ]]; then
        log_verbose "No cross-repository links found in: $adr_file"
        return 0
    fi

    # Validate each link
    for link in "${links[@]}"; do
        if [[ -n "$link" ]]; then
            TOTAL_LINKS=$((TOTAL_LINKS + 1))
            local validation_result
            validation_result=$(validate_url "$link")

            if [[ "$validation_result" == "valid" ]]; then
                VALID_LINKS=$((VALID_LINKS + 1))
                if [[ "$VERBOSE" == true ]]; then
                    print_success "Valid: $link"
                fi
            else
                INVALID_LINKS=$((INVALID_LINKS + 1))
                print_error "Invalid: $link ($validation_result)"
                file_results+=("{\"file\": \"$adr_file\", \"url\": \"$link\", \"status\": \"$validation_result\"}")

                if [[ "$FAIL_FAST" == true ]]; then
                    print_error "Validation failed (fail-fast mode enabled)"
                    exit 1
                fi
            fi

            VALIDATION_RESULTS+=("{\"file\": \"$adr_file\", \"url\": \"$link\", \"status\": \"$validation_result\"}")
        fi
    done

    return 0
}

# Find and validate all ADR files
validate_all_adrs() {
    if [[ ! -d "$ADR_DIRECTORY" ]]; then
        print_error "ADR directory not found: $ADR_DIRECTORY"
        exit 3
    fi

    # Find all ADR markdown files
    local adr_files
    mapfile -t adr_files < <(find "$ADR_DIRECTORY" -name "ADR-*.md" -type f | sort)

    if [[ ${#adr_files[@]} -eq 0 ]]; then
        print_warning "No ADR files found in: $ADR_DIRECTORY"
        exit 3
    fi

    print_info "Found ${#adr_files[@]} ADR files to validate"

    # Validate each ADR file
    for adr_file in "${adr_files[@]}"; do
        validate_adr_file "$adr_file"
    done
}

# Output results in JSON format
output_json_results() {
    local json_output="{
        \"summary\": {
            \"total_links\": $TOTAL_LINKS,
            \"valid_links\": $VALID_LINKS,
            \"invalid_links\": $INVALID_LINKS,
            \"cached_links\": $CACHED_LINKS,
            \"validation_date\": \"$(date --iso-8601=seconds)\"
        },
        \"results\": ["

    local first=true
    for result in "${VALIDATION_RESULTS[@]}"; do
        if [[ "$first" == true ]]; then
            first=false
        else
            json_output+=","
        fi
        json_output+="$result"
    done

    json_output+="]}"
    echo "$json_output"
}

# Output validation summary
output_summary() {
    if [[ "$JSON_OUTPUT" == true ]]; then
        output_json_results
    else
        echo
        print_info "=== VALIDATION SUMMARY ==="
        echo "Total links validated: $TOTAL_LINKS"
        echo "Valid links: $VALID_LINKS"
        echo "Invalid links: $INVALID_LINKS"
        if [[ "$USE_CACHE" == true ]]; then
            echo "Cached links: $CACHED_LINKS"
        fi
        echo "ADR directory: $ADR_DIRECTORY"
        echo "Validation date: $(date)"

        if [[ $INVALID_LINKS -eq 0 ]]; then
            print_success "All cross-repository links are valid!"
        else
            print_error "$INVALID_LINKS invalid links found"
        fi
    fi
}

# Main function
main() {
    parse_arguments "$@"
    init_cache

    if [[ "$JSON_OUTPUT" == false ]]; then
        print_info "Cross-Repository ADR Link Validation"
        print_info "Validating ADRs in: $ADR_DIRECTORY"

        if [[ "$USE_CACHE" == true ]]; then
            print_info "Using cached results when available"
        fi
    fi

    validate_all_adrs
    output_summary

    # Exit with appropriate code
    if [[ $INVALID_LINKS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function
main "$@"
