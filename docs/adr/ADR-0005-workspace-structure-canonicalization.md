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

We will restructure the workspace into two clear domains with explicit input/processing/output flow:

### **Primary Structure**

```
omega_registry/
├── runtime/                    # Self-contained HA add-on components
│   ├── addon/                  # HA add-on packaging & configuration
│   ├── src/                    # Core processing logic (from scripts/)
│   ├── inputs/                 # Non-HA data sources for enrichment
│   │   └── enrichment_sources/ # Additional data for enrichment
│   ├── outputs/                # Final processed results
│   │   ├── omega_registry_master.json
│   │   ├── derived_views/      # Alpha registries, analytics
│   │   └── logs/               # Processing logs and audit trails
│   ├── support/                # Contracts, schemas, manifests
│   ├── config.yaml            # Runtime configuration
│   └── requirements.txt       # Runtime dependencies
│
├── project/                    # Project metadata & development
│   ├── docs/                   # Documentation & ADRs
│   ├── ops/                    # Operations & deployment scripts
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

### **Data Flow Architecture**

1. **Input Sources:**
   - `omega_registry_ha_storage/` - Raw HA registry files (symlinked external data)
   - `runtime/inputs/enrichment_sources/` - Additional enrichment data
   - `runtime/support/` - Contracts and schemas that guide processing

2. **Processing:**
   - `runtime/src/` - Core pipeline logic (consolidated from `scripts/`)
   - `runtime/config.yaml` - Configuration driving the processing

3. **Output Artifacts:**
   - `runtime/outputs/omega_registry_master.json` - Primary registry output
   - `runtime/outputs/derived_views/` - Alpha registries and analytics
   - `runtime/outputs/logs/` - Processing logs and governance data

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
- The entire `runtime/` directory becomes the HA add-on package
- No mixing of development artifacts with runtime components
- Clear dependency boundaries via `runtime/requirements.txt`

### **Development Workflow**
- `project/workspace/` contains VS Code configurations
- `project/docs/` maintains all documentation including ADRs
- `project/ops/` handles deployment and packaging scripts

## Implementation Plan

### **Phase 1: Directory Structure**
1. Create new directory structure
2. Move `canonical/` content to `runtime/inputs/` and `runtime/outputs/` based on data flow
3. Consolidate `scripts/` into `runtime/src/`
4. Migrate project metadata to `project/` structure

### **Phase 2: Consolidation**
1. Eliminate duplication between `addon/` and `scripts/utils/`
2. Merge overlapping virtual environments
3. Update configuration references

### **Phase 3: Configuration Updates**
1. Update `io_manifest.json` paths
2. Update `config.yaml` references
3. Update workspace configurations
4. Update documentation references

## Assumptions & Preconditions

- `omega_registry_ha_storage/` is a symlink to external HA data
- Current `canonical/registry_inputs/` is gitignored and can be removed
- Processing pipeline can read directly from symlinked storage
- HA add-on packaging will use `runtime/` as the complete package

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
- [ ] HA add-on packages cleanly from `runtime/` directory
- [ ] Documentation updated with new structure
- [ ] Workspace configurations updated
- [ ] No functional regressions in processing

## Notes

This ADR builds on ADR-0003 (workspace shape I/O strategy) by providing concrete implementation of the workspace organization principles. The structure enables clear runtime packaging while maintaining comprehensive project development capabilities.

The symlinked `omega_registry_ha_storage/` approach allows the pipeline to access live HA data without including it in the git repository, supporting both development and production use cases.