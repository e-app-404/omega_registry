---
id: ADR-0005
Title: "Workspace structure canonicalization and runtime/project separation"
Date: 2025-09-28
Status: Proposed
Authors: Evert Appels
related: ["ADR-0003"]
supersedes: []
tags: ["architecture", "workspace", "structure", "runtime", "project", "separation"]
---

## Context

The Omega Registry workspace has evolved organically over time, resulting in mixed concerns between runtime components (needed for HA add-on functionality) and project-level metadata (development, operations, documentation). This has led to:

1. **Unclear separation** between what's needed for the add-on vs project development
2. **Duplicated functionality** between `addon/` and `scripts/` directories
3. **Mixed input/output concerns** in the `canonical/` directory
4. **Scattered project metadata** across root-level files and various subdirectories

The current structure makes it difficult to package a clean, self-contained HA add-on and complicates development workflows.

## Decision

We will restructure the workspace into two clear domains with explicit input/processing/output flow, **maintaining ADR-0003 import safety and I/O policies**:

### **Primary Structure**

```
omega_registry/
├── addon/                      # Self-contained HA add-on components
│   ├── src/                    # Pure code (import-safe, ADR-0003 compliant)
│   │   ├── utils/              # Pure helpers including paths.py (ADR-0003)
│   │   ├── scripts/            # CLI scripts with I/O guards (ADR-0003)
│   │   └── tests/              # Tests for addon modules
│   ├── data/                   # File I/O concerns (clearly separated)
│   │   ├── registry/           # Registry data processing & storage
│   │   ├── input/              # Input data and fixtures (ADR-0003)
│   │   └── output/             # Output artifacts and results (ADR-0003)
│   ├── support/                # Contracts, schemas, manifests
│   ├── config.yaml            # Runtime configuration
│   └── requirements.txt       # Runtime dependencies
│
├── project/                    # Project metadata & development
│   ├── docs/                   # Documentation & ADRs
│   ├── ops/                    # Operations & deployment scripts
│   │   └── scripts/            # Test helpers and shims (ADR-0003 compliant)
│   ├── workspace/              # VS Code workspaces & dev configs
│   ├── backups/               # Safety bundles (from _backups/)
│   └── releases/              # Release archives (from _tarballs/)
│
├── omega_registry_ha_storage/  # Symlink to HA registry files (external)
│   ├── core.entity_registry    # HA registry data (symlinked)
│   ├── core.device_registry
│   └── core.config_entries
│
├── README.md                   # Project overview
├── workspace_ops_export.yaml   # Operational topology
└── pyproject.toml             # Development tooling configuration
```

### **Data Flow Architecture (ADR-0003 Compliant)**

1. **Input Sources:**
   - `omega_registry_ha_storage/` - Raw HA registry files (symlinked external data)
   - `addon/src/input/` - Canonical input fixtures (ADR-0003)
   - `addon/support/` - Contracts and schemas that guide processing

2. **Processing:**
   - `addon/src/utils/paths.py` - Canonical path resolution (import-safe, ADR-0003)
   - `addon/src/scripts/` - CLI scripts with I/O guards (ADR-0003)
   - `addon/data/registry/` - Registry data processing modules
   - `addon/config.yaml` - Configuration driving the processing

3. **Output Artifacts:**
   - `addon/data/output/` - Canonical output directory (ADR-0003)
   - `omega_registry_master.json`, `derived_views/`, `logs/` - Within data/output/

### **Import Safety Compliance (ADR-0003)**

- **`addon/src/`** - Purely import-safe code (no file I/O at import time)
- **`addon/data/`** - File I/O operations clearly separated
- Heavy I/O operations in `addon/src/scripts/` use proper `if __name__ == '__main__'` guards
- Path resolution centralized in `addon/src/utils/paths.py` (import-safe)
- Tests import safely from `addon/src/` and `project/ops/scripts/` (test helpers)

## Rationale

### **Clear Separation of Concerns**
- **Runtime components** are everything needed for the HA add-on to function
- **Project metadata** includes development tooling, documentation, and operations
- **External data** (HA storage) remains cleanly separated via symlink

### **Input/Output Clarity**
- **Inputs** are clearly separated from **outputs**
- **Processing logic** is consolidated in `runtime/src/`
- **Configuration and contracts** guide the processing pipeline

### **Packaging Benefits**
- The entire `addon/` directory becomes the HA add-on package
- No mixing of development artifacts with runtime components
- Clear dependency boundaries via `addon/requirements.txt`

### **Development Workflow**
- `project/workspace/` contains VS Code configurations
- `project/docs/` maintains all documentation including ADRs
- `project/ops/` handles deployment and packaging scripts

## Implementation Plan

### **Phase 1: Directory Structure (ADR-0003 Compliant)**
1. Create `project/` top-level directory
2. Create `addon/src/` (pure code) and `addon/data/` (file I/O) separation
3. Move `canonical/` content to `addon/data/input/` and `addon/data/output/`
4. Restructure existing code into `addon/src/` (import-safe) vs `addon/data/` (I/O)
5. Move `scripts/` to `project/ops/scripts/` as test helpers
6. Migrate project metadata to `project/` structure

### **Phase 2: Import Safety & Consolidation**
1. Validate all `addon/src/` modules are purely import-safe (no file I/O)
2. Implement `addon/src/utils/paths.py` for canonical path resolution (import-safe)
3. Move file I/O operations to `addon/data/` modules
4. Add I/O guards to `addon/src/scripts/` CLI entry points
5. Eliminate duplication while preserving clear src/data boundaries

### **Phase 3: Configuration & Validation**
1. Update `io_manifest.json` paths to new structure
2. Update `config.yaml` and path resolution
3. Update workspace configurations
4. Implement automated validation checks (token block compliance)
5. Run import safety validation from ADR-0003

## Assumptions & Preconditions

- `omega_registry_ha_storage/` is a symlink to external HA data
- Current `canonical/registry_inputs/` is gitignored and can be removed
- Processing pipeline can read directly from symlinked storage
- HA add-on packaging will use `addon/` as the complete package

## Migration Path

### **Safe Migration Strategy**
1. **Backup current state** - Create bundle before changes
2. **Incremental moves** - Use `git mv` to preserve history
3. **Update references progressively** - Maintain working state
4. **Validate pipeline** - Ensure processing continues to work

### **Validation Criteria**
- Pipeline processes data correctly with new structure
- HA add-on can be packaged from `runtime/` directory only
- All documentation references updated
- Development workflow remains functional

## Risks & Mitigations

**Risk:** Breaking existing processing pipeline
**Mitigation:** Use `git mv` to preserve history, update paths incrementally

**Risk:** Complex path updates across many files
**Mitigation:** Update configuration centrally where possible, validate with test runs

**Risk:** Development workflow disruption
**Mitigation:** Update workspace configurations early, maintain familiar structure within new organization

## Acceptance Criteria

- [ ] New directory structure implemented
- [ ] All files moved with preserved git history
- [ ] Pipeline processes data correctly in new structure
- [ ] - HA add-on packages cleanly from `addon/` directory
- [ ] Documentation updated with new structure
- [ ] Workspace configurations updated
- [ ] No functional regressions in processing

## Machine-Parseable Token Block

```yaml
TOKEN_BLOCK:
  accepted:
    - ADR_WORKSPACE_CANONICALIZATION_OK
    - ADR_RUNTIME_PROJECT_SEPARATION_OK
    - ADR_WORKSPACE_IO_OK  # Inherits from ADR-0003
    - ADR_AUTOMATION_OK    # Inherits from ADR-0003
  requires:
    - ADR-0003  # Import safety and I/O policies
    - ADR-0001  # ADR governance
  produces:
    - WORKSPACE_STRUCTURE_REPORT
    - RUNTIME_PACKAGING_VALIDATION
    - IMPORT_SAFETY_REPORT  # From ADR-0003
  validation_rules:
    - addon/src/ MUST be purely import-safe (no file I/O at import time)
    - addon/data/ MUST contain all file I/O operations
    - addon/src/scripts/ MUST have if __name__ == '__main__' guards
    - addon/src/utils/paths.py MUST exist for path resolution (import-safe)
    - project/ directory MUST NOT be included in addon packaging
    - omega_registry_ha_storage/ MUST be symlink (not regular directory)
  drift_indicators:
    - DRIFT: import_time_io_detected_in_addon_src
    - DRIFT: project_metadata_in_addon_package
    - DRIFT: broken_symlink_ha_storage
    - DRIFT: missing_path_resolution_helpers
```

## Enforcement & Validation

### **Automated Checks**
1. **Import Safety Validation** - Ensure addon/src/ is purely import-safe
2. **I/O Separation** - Verify file I/O operations are in addon/data/
3. **Addon Package Purity** - Ensure no project metadata in addon/
4. **Symlink Validation** - Verify omega_registry_ha_storage/ is proper symlink
5. **Path Resolution** - Validate addon/src/utils/paths.py exists and is import-safe

### **CI Integration**
```bash
# Addon package validation - no project metadata
find addon/ -name "*.md" -o -name "workspace*" -o -name "*.code-workspace" \
  && echo "ERROR: Project metadata found in addon/" && exit 1

# Symlink validation
[ -L "omega_registry_ha_storage" ] || \
  (echo "ERROR: omega_registry_ha_storage must be symlink" && exit 1)

# Import safety - addon/src/ must be purely import-safe
python -c "
import importlib, pkgutil, sys
sys.path.insert(0, 'addon')
for _, name, _ in pkgutil.walk_packages(['src']):
    importlib.import_module('src.' + name)
print('✅ addon/src/ is import-safe')
"

# Structure validation - ensure src/data separation exists
[ -d "addon/src" ] && [ -d "addon/data" ] || \
  (echo "ERROR: addon/ must have both src/ and data/ directories" && exit 1)
```

## Notes

This ADR builds on **ADR-0003** (workspace shape I/O strategy) by providing concrete implementation of the workspace organization principles while **maintaining full compatibility** with established import safety and I/O policies.

Key alignments with ADR-0003:
- Preserves `addon/` as production library code with import safety
- Maintains `addon/scripts/` for CLI tools with I/O guards
- Keeps `scripts/` for test helpers and shims
- Enforces canonical path resolution via `addon/utils/paths.py`
- Inherits machine-parseable validation tokens

The structure enables clear runtime packaging while maintaining comprehensive project development capabilities and established safety policies.
