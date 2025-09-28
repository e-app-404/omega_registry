# ADR-0005 Workspace Canonicalization Migration Plan

**Date**: 2025-09-28
**Status**: Draft
**Target**: Complete migration to ADR-0005 workspace structure
**Estimated Duration**: 3-4 days with validation

## 📊 **Current State Analysis**

### **Current Structure Issues**
Based on the ADR-0005 compliance validation, we have **7 critical issues**:

1. ❌ Missing `addon/src/` directory (pure code)
2. ❌ Missing `addon/data/` directory (file I/O operations)
3. ❌ Missing `project/docs/` directory (project metadata)
4. ❌ Missing `project/ops/` directory (operations)
5. ❌ Missing `addon/src/utils/paths.py` (canonical path resolution)
6. ⚠️ `omega_registry_ha_storage/` not found (external data)
7. ⚠️ `addon/src/scripts/` directory not found (CLI scripts)

### **Current File Distribution**
```
📂 Current Structure:
├── addon/                    # Exists but wrong internal structure
│   ├── input/, output/       # Should move to addon/data/
│   ├── registry/, utils/     # Should move to addon/src/
│   └── tests/               # Should move to addon/src/tests/
├── scripts/                  # Should move to project/ops/scripts/
├── canonical/               # Should move to addon/data/
├── docs/                    # Should move to project/docs/
└── [workspace files]        # Should move to project/workspace/
```

### **Key Files Requiring Migration**
- **Pure code modules**: `addon/utils/`, `addon/registry/`, `scripts/utils/`, `scripts/omega_registry/`
- **I/O operations**: `canonical/`, `addon/input/`, `addon/output/`
- **CLI scripts**: `scripts/generators/`, `scripts/addon/`, `scripts/tools/`
- **Project metadata**: `docs/`, `*.code-workspace`, development configs
- **Tests**: `addon/tests/`

## 🗺️ **Migration Strategy**

### **Phase 1: Directory Structure Creation** (Day 1)

#### **Step 1.1: Create New Directory Structure**
```bash
# Create primary directories
mkdir -p addon/src/{utils,scripts,tests}
mkdir -p addon/data/{registry,input,output}
mkdir -p addon/support
mkdir -p project/{docs,ops,workspace,backups,releases}
mkdir -p project/ops/scripts
```

#### **Step 1.2: Create Essential Files**
```bash
# Create __init__.py files for import safety
touch addon/src/__init__.py
touch addon/src/utils/__init__.py
touch addon/src/scripts/__init__.py
touch addon/data/__init__.py
touch project/__init__.py
touch project/ops/__init__.py
```

#### **Step 1.3: Create addon/src/utils/paths.py (Critical)**
This is required by ADR-0005 for canonical path resolution:

```python
# addon/src/utils/paths.py (import-safe)
"""
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

def get_data_path(relative_path: Union[str, Path]) -> Path:
    """Get path in addon/data/ directory."""
    return ADDON_DATA / relative_path

def get_input_path(relative_path: Union[str, Path]) -> Path:
    """Get path in addon/data/input/ directory."""
    return ADDON_DATA / "input" / relative_path

def get_output_path(relative_path: Union[str, Path]) -> Path:
    """Get path in addon/data/output/ directory."""
    return ADDON_DATA / "output" / relative_path

def get_registry_path(relative_path: Union[str, Path]) -> Path:
    """Get path in addon/data/registry/ directory."""
    return ADDON_DATA / "registry" / relative_path

def get_support_path(relative_path: Union[str, Path]) -> Path:
    """Get path in addon/support/ directory."""
    return ADDON_ROOT / "support" / relative_path
```

### **Phase 2: Pure Code Migration** (Day 1-2)

#### **Step 2.1: Move Pure Library Code**
```bash
# Move pure utilities (import-safe)
git mv addon/utils/* addon/src/utils/ 2>/dev/null || true
git mv scripts/utils/* addon/src/utils/ 2>/dev/null || true

# Move registry library code (pure functions)
git mv addon/registry/* addon/src/registry/ 2>/dev/null || true
mkdir -p addon/src/registry
git mv scripts/omega_registry/* addon/src/registry/ 2>/dev/null || true

# Move tests
git mv addon/tests/* addon/src/tests/ 2>/dev/null || true
```

#### **Step 2.2: Move CLI Scripts with Guards**
```bash
# Create addon/src/scripts/ and move CLI entry points
mkdir -p addon/src/scripts
git mv scripts/generators/* addon/src/scripts/ 2>/dev/null || true
git mv scripts/addon/* addon/src/scripts/ 2>/dev/null || true
git mv scripts/tools/* addon/src/scripts/ 2>/dev/null || true

# Note: These scripts need if __name__ == '__main__' guards verification
```

#### **Step 2.3: Validate Import Safety**
```bash
# Test that addon/src/ is purely import-safe
python -c "
import importlib, pkgutil, sys
sys.path.insert(0, '.')
failed = []
for _, name, _ in pkgutil.walk_packages(['addon/src']):
    try:
        importlib.import_module('addon.src.' + name)
    except Exception as e:
        failed.append((name, str(e)))
if failed:
    print('❌ Failed imports:', failed)
    exit(1)
else:
    print('✅ addon/src/ is import-safe')
"
```

### **Phase 3: Data and I/O Migration** (Day 2)

#### **Step 3.1: Move Data Directories**
```bash
# Move canonical data to addon/data/
git mv canonical/* addon/data/ 2>/dev/null || true

# Move existing addon I/O directories
git mv addon/input/* addon/data/input/ 2>/dev/null || true
git mv addon/output/* addon/data/output/ 2>/dev/null || true

# Move support files
git mv support/* addon/support/ 2>/dev/null || true
```

#### **Step 3.2: Create External Data Symlink**
```bash
# Create symlink to external HA data (if applicable)
if [ -d "/path/to/ha/storage" ]; then
    ln -sf "/path/to/ha/storage" omega_registry_ha_storage
else
    echo "⚠️ External HA storage path needs to be configured"
fi
```

### **Phase 4: Project Metadata Migration** (Day 2-3)

#### **Step 4.1: Move Documentation**
```bash
# Move documentation to project/
git mv docs/* project/docs/ 2>/dev/null || true

# Move workspace configurations
git mv *.code-workspace project/workspace/ 2>/dev/null || true
git mv .vscode project/workspace/ 2>/dev/null || true
```

#### **Step 4.2: Move Operations and Scripts**
```bash
# Move remaining utility scripts to project/ops/scripts/
git mv scripts/* project/ops/scripts/ 2>/dev/null || true

# Move backups and releases
git mv _backups/* project/backups/ 2>/dev/null || true
git mv _tarballs/* project/releases/ 2>/dev/null || true
```

### **Phase 5: Configuration Updates** (Day 3)

#### **Step 5.1: Update Path References**
Key files to update:
- `config.yaml` - Update paths to use new structure
- `io_manifest.json` - Update paths to addon/data/ structure
- `pyproject.toml` - Update package discovery paths
- `requirements*.txt` - Ensure correct structure

#### **Step 5.2: Update Import Statements**
Search and replace import patterns:
```bash
# Find files with old import patterns
grep -r "from scripts" . || true
grep -r "import scripts" . || true
grep -r "from addon" . || true

# Update to new import patterns:
# OLD: from scripts.utils import X
# NEW: from addon.src.utils import X
# OLD: from scripts.omega_registry import Y
# NEW: from addon.src.registry import Y
```

### **Phase 6: Validation and Testing** (Day 3-4)

#### **Step 6.1: Run Comprehensive Validation**
```bash
# ADR-0005 compliance validation
./ops/ADR/validate_adr_0005_compliance.sh

# Cross-repository ADR validation
./ops/ADR/validate_cross_repo_links.sh docs/ADR

# Post-deployment validation
./ops/ADR/post_deploy_validation.sh

# Import safety validation
python -c "
import importlib, pkgutil, sys
sys.path.insert(0, '.')
for _, name, _ in pkgutil.walk_packages(['addon/src']):
    importlib.import_module('addon.src.' + name)
print('✅ All addon/src/ modules import safely')
"
```

#### **Step 6.2: Test Pipeline Functionality**
```bash
# Test that the omega registry pipeline still works
python -m addon.src.scripts.omega_pipeline_main --help
python -m addon.src.scripts.generate_omega_registry --dry-run

# Validate output structure
ls -la addon/data/output/
```

## 🚨 **Critical Migration Issues & Solutions**

### **Issue 1: Import Path Updates**
**Problem**: Many files use `from scripts.utils import X`
**Solution**: Update to `from addon.src.utils import X` and ensure PYTHONPATH includes addon/

### **Issue 2: Hard-coded Path References**
**Problem**: Scripts use hard-coded paths like `"canonical/output"`
**Solution**: Update to use `addon.src.utils.paths.get_output_path()`

### **Issue 3: CLI Script Guards**
**Problem**: Scripts may lack proper `if __name__ == '__main__'` guards
**Solution**: Add guards to all scripts in `addon/src/scripts/`

### **Issue 4: Test Import Safety**
**Problem**: Tests may import scripts with I/O side effects
**Solution**: Move test helpers to `project/ops/scripts/` and update test imports

## 🔄 **Rollback Strategy**

### **Emergency Rollback Plan**
```bash
# Create backup before migration
git branch adr-0005-backup-$(date +%Y%m%d)
git add -A && git commit -m "Pre-ADR-0005 migration backup"

# If rollback needed:
git reset --hard adr-0005-backup-$(date +%Y%m%d)
```

### **Incremental Rollback**
- Each phase can be rolled back independently using git
- Keep original directory structure until validation passes
- Use `git mv` to preserve file history

## ✅ **Success Criteria**

### **Phase Completion Checkpoints**
- [ ] **Phase 1**: All required directories created, paths.py implemented
- [ ] **Phase 2**: All pure code moved to addon/src/, imports working
- [ ] **Phase 3**: All I/O operations moved to addon/data/
- [ ] **Phase 4**: All project metadata moved to project/
- [ ] **Phase 5**: All configuration files updated, paths resolved
- [ ] **Phase 6**: All validation passes, pipeline functional

### **Final Validation Requirements**
- [ ] ADR-0005 compliance validator passes (0 failures)
- [ ] Import safety validation passes for addon/src/
- [ ] Cross-repository ADR validation passes
- [ ] Omega registry pipeline runs successfully
- [ ] All tests pass with new structure
- [ ] No project metadata in addon/ directory
- [ ] addon/src/utils/paths.py exists and is import-safe

## 📋 **Migration Execution Checklist**

### **Pre-Migration**
- [ ] Create git backup branch
- [ ] Document current working directory structure
- [ ] Test current pipeline functionality
- [ ] Identify all import dependencies

### **During Migration**
- [ ] Execute phases sequentially
- [ ] Validate each phase before proceeding
- [ ] Update imports and path references
- [ ] Test import safety after each code move

### **Post-Migration**
- [ ] Run full validation suite
- [ ] Test pipeline end-to-end
- [ ] Update documentation
- [ ] Clean up empty directories
- [ ] Commit final structure

## 🎯 **Next Steps**

1. **Immediate**: Create backup and begin Phase 1 (directory structure)
2. **Day 1**: Complete Phases 1-2 (structure + pure code migration)
3. **Day 2**: Complete Phases 3-4 (data + metadata migration)
4. **Day 3**: Complete Phase 5 (configuration updates)
5. **Day 4**: Complete Phase 6 (validation + testing)

---

**Migration Lead**: TBD
**Expected Completion**: 2025-10-01
**Risk Level**: Medium (good rollback strategy, incremental approach)
**ADR Compliance**: ADR-0003 (import safety), ADR-0005 (workspace structure)
