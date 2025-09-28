# ADR-0005 File Migration Mapping

**Date**: 2025-09-28
**Purpose**: Detailed mapping of files to be moved during ADR-0005 workspace canonicalization

## 📂 **File Migration Matrix**

### **Phase 2A: Pure Library Code → addon/src/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `addon/utils/*` | `addon/src/utils/` | Pure helpers | `git mv addon/utils/* addon/src/utils/` | Import-safe utilities |
| `addon/registry/*` | `addon/src/registry/` | Core library | `git mv addon/registry/* addon/src/registry/` | Registry processing logic |
| `scripts/utils/*` | `addon/src/utils/` | Shared utilities | `git mv scripts/utils/* addon/src/utils/` | Merge with addon utils |
| `scripts/omega_registry/*` | `addon/src/registry/` | Registry code | `git mv scripts/omega_registry/* addon/src/registry/` | Core registry modules |
| `addon/tests/*` | `addon/src/tests/` | Test modules | `git mv addon/tests/* addon/src/tests/` | Unit tests |

### **Phase 2B: CLI Scripts → addon/src/scripts/**

| Current Location | Target Location | Type | Git Command | Validation Required |
|------------------|-----------------|------|-------------|-------------------|
| `scripts/generators/*` | `addon/src/scripts/` | CLI generators | `git mv scripts/generators/* addon/src/scripts/` | Check `__main__` guards |
| `scripts/addon/*` | `addon/src/scripts/` | Addon CLI | `git mv scripts/addon/* addon/src/scripts/` | Check `__main__` guards |
| `scripts/tools/*` | `addon/src/scripts/` | Utility tools | `git mv scripts/tools/* addon/src/scripts/` | Check `__main__` guards |
| `scripts/omega_pipeline_main.py` | `addon/src/scripts/` | Main pipeline | `git mv scripts/omega_pipeline_main.py addon/src/scripts/` | Entry point script |

### **Phase 3: Data and I/O → addon/data/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `canonical/*` | `addon/data/` | Canonical data | `git mv canonical/* addon/data/` | All canonical processing |
| `addon/input/*` | `addon/data/input/` | Input data | `git mv addon/input/* addon/data/input/` | Input fixtures |
| `addon/output/*` | `addon/data/output/` | Output data | `git mv addon/output/* addon/data/output/` | Generated outputs |
| `support/*` | `addon/support/` | Support files | `git mv support/* addon/support/` | Contracts, schemas |

### **Phase 4A: Documentation → project/docs/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `docs/*` | `project/docs/` | Documentation | `git mv docs/* project/docs/` | All documentation |

### **Phase 4B: Operations → project/ops/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `scripts/analytics/*` | `project/ops/scripts/analytics/` | Analytics | `git mv scripts/analytics/* project/ops/scripts/analytics/` | Test helpers |
| `scripts/audit/*` | `project/ops/scripts/audit/` | Audit tools | `git mv scripts/audit/* project/ops/scripts/audit/` | Operations scripts |
| `scripts/enrich/*` | `project/ops/scripts/enrich/` | Enrichment | `git mv scripts/enrich/* project/ops/scripts/enrich/` | Development tools |
| `scripts/qa/*` | `project/ops/scripts/qa/` | QA tools | `git mv scripts/qa/* project/ops/scripts/qa/` | Testing utilities |
| `scripts/transformation/*` | `project/ops/scripts/transformation/` | Transform | `git mv scripts/transformation/* project/ops/scripts/transformation/` | Data transformation |
| `scripts/legacy/*` | `project/ops/scripts/legacy/` | Legacy code | `git mv scripts/legacy/* project/ops/scripts/legacy/` | Archived scripts |

### **Phase 4C: Workspace → project/workspace/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `*.code-workspace` | `project/workspace/` | VS Code workspace | `git mv *.code-workspace project/workspace/` | Development configs |
| `.vscode/` | `project/workspace/.vscode/` | VS Code settings | `git mv .vscode project/workspace/` | Editor configuration |

### **Phase 4D: Backups & Releases → project/**

| Current Location | Target Location | Type | Git Command | Notes |
|------------------|-----------------|------|-------------|--------|
| `_backups/*` | `project/backups/` | Backup files | `git mv _backups/* project/backups/` | Safety bundles |
| `_tarballs/*` | `project/releases/` | Release archives | `git mv _tarballs/* project/releases/` | Packaged releases |

## 🔧 **Special Cases & Manual Updates**

### **Files Requiring Import Updates**

| File | Current Imports | New Imports | Manual Update Required |
|------|----------------|-------------|----------------------|
| `scripts/generators/*.py` | `from scripts.utils import X` | `from addon.src.utils import X` | ✅ Yes |
| `scripts/omega_registry/*.py` | `from scripts.utils import Y` | `from addon.src.utils import Y` | ✅ Yes |
| `addon/registry/*.py` | `import scripts.utils.Z` | `import addon.src.utils.Z` | ✅ Yes |
| Various CLI scripts | Hard-coded paths | Use `addon.src.utils.paths` | ✅ Yes |

### **Configuration Files Requiring Path Updates**

| File | Current Paths | New Paths | Update Required |
|------|---------------|-----------|----------------|
| `config.yaml` | `canonical/`, `addon/input/` | `addon/data/`, `addon/data/input/` | ✅ Yes |
| `io_manifest.json` | Various paths | ADR-0005 compliant paths | ✅ Yes |
| `pyproject.toml` | Package discovery | `packages = ["addon.src"]` | ✅ Yes |
| `requirements*.txt` | Dependencies | May need structure updates | ⚠️ Review |

### **Files That Cannot Be Moved**

| File | Reason | Action |
|------|--------|--------|
| `.env` | Environment config | Keep in root |
| `.gitignore` | Git configuration | Keep in root, update patterns |
| `pyproject.toml` | Project configuration | Keep in root, update paths |
| `README.md` | Project entry point | Keep in root, update content |
| `workspace_ops_export.yaml` | Operational topology | Keep in root |

## 🚨 **Critical Dependencies & Validation**

### **Import Safety Validation Required**
All files moving to `addon/src/` MUST be validated for import safety:

```bash
# Files requiring import safety validation
addon/src/utils/*.py
addon/src/registry/*.py
addon/src/tests/*.py
```

### **CLI Script Guard Validation**
All files moving to `addon/src/scripts/` MUST have proper guards:

```bash
# Files requiring __main__ guard validation
addon/src/scripts/*.py
```

### **Path Resolution Updates**
Files with hard-coded paths need updates to use `addon.src.utils.paths`:

```bash
# Common patterns to replace:
"canonical/" → get_data_path("")
"addon/input/" → get_input_path("")
"addon/output/" → get_output_path("")
"canonical/registry_inputs/" → get_data_path("registry_inputs")
"canonical/derived_views/" → get_data_path("derived_views")
```

## 🤖 **Machine-Driven Execution**

### **Automated Migration Script**
```bash
# Full automated migration with dry-run preview
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --dry-run

# Execute full migration (all phases)
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh

# Execute specific phase only
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --phase 3

# Force migration without confirmations
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --force
```

### **Manual Preparation (if needed)**
```bash
# Only needed if not using automated script
git checkout -b adr-0005-migration-backup
git add -A && git commit -m "Pre-migration backup"

# Directory creation handled by migration script
# No manual preparation required
```

### **Automated Phase Execution**

**Phase 1: Directory Structure Creation**
- ✅ Automated directory creation with conflict detection
- ✅ Automatic `__init__.py` file generation
- ✅ Critical `addon/src/utils/paths.py` implementation
- ✅ Comprehensive error handling and validation

**Phase 2: Pure Library Code Migration**
- ✅ Safe `git mv` operations with conflict resolution
- ✅ Multiple source merging (addon/utils + scripts/utils)
- ✅ Registry code consolidation (addon/registry + scripts/omega_registry)
- ✅ Import safety validation during moves

**Phase 3: Data and I/O Migration**
- ✅ Canonical data preservation with history
- ✅ I/O directory consolidation under addon/data/
- ✅ Support file migration with validation
- ✅ Path reference integrity checking

**Phase 4: Project Metadata Migration**
- ✅ Documentation migration to project/docs/
- ✅ Operations script categorization
- ✅ Workspace configuration preservation
- ✅ Backup and release archive migration

**Phase 5: Configuration Updates**
- ✅ Automated import statement updates
- ✅ Configuration file path corrections
- ✅ Package discovery updates in pyproject.toml
- ✅ Git ignore pattern additions

**Phase 6: Validation and Cleanup**
- ✅ ADR-0005 compliance validation
- ✅ Import safety testing
- ✅ Empty directory cleanup
- ✅ Comprehensive migration report

## ✅ **Automated Validation System**

### **Continuous Validation During Migration**
- ✅ **Phase-by-Phase Validation**: Each phase validates before proceeding
- ✅ **Error Detection**: Immediate failure detection with detailed logging
- ✅ **Conflict Resolution**: Automatic handling of file conflicts
- ✅ **Progress Tracking**: Real-time migration status with error counts

### **Comprehensive Final Validation**
```bash
# All validation automated within migration script
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh

# Manual validation (if needed)
./docs/ADR/deployment-bundle/scripts/validate_adr_0005_compliance.sh
./docs/ADR/deployment-bundle/scripts/validate_cross_repo_links.sh docs/ADR
```

### **Machine-Readable Validation Output**
- ✅ **Structured Logging**: Timestamped log file with machine-parseable format
- ✅ **Exit Codes**: Standard exit codes for integration with CI/CD
- ✅ **JSON Reports**: Optional JSON output for automated processing
- ✅ **Rollback Information**: Automatic backup branch creation for recovery

## 🤖 **Machine Execution Features**

### **Automated Execution Capabilities**
- ✅ **Dry-Run Mode**: Preview all changes without modification (`--dry-run`)
- ✅ **Phase-Specific Execution**: Execute individual phases (`--phase N`)
- ✅ **Force Mode**: Skip confirmations and safety checks (`--force`)
- ✅ **Comprehensive Logging**: Detailed timestamped logs for audit trail
- ✅ **Error Recovery**: Automatic rollback capabilities with git branches
- ✅ **Progress Reporting**: Real-time status with error and warning counts

### **Integration Features**
- ✅ **CI/CD Compatible**: Standard exit codes and structured output
- ✅ **JSON Output**: Machine-parseable results for automation
- ✅ **Git History Preservation**: All moves preserve file history
- ✅ **Atomic Operations**: Each phase can be rolled back independently
- ✅ **Safety Validation**: Pre-flight checks and continuous validation

### **Usage Examples**
```bash
# Preview full migration
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --dry-run

# Execute full migration
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh

# Execute specific phase with force
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --phase 2 --force

# Check migration script help
./docs/ADR/deployment-bundle/scripts/migrate_adr_0005.sh --help
```

---

**Migration Status**: ✅ **FULLY AUTOMATED**
**Execution Mode**: Machine-Driven with Human Oversight
**Risk Assessment**: Low (comprehensive automation, rollback available, dry-run testing)
**Estimated Duration**: 30 minutes automated execution + validation
**Dependencies**: Git repository, bash 4.0+, Python 3.6+
**Rollback Strategy**: Automatic git branch backup with phase-by-phase recovery
