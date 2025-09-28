# Omega Registry - AI Coding Assistant Instructions

## Project Overview

This is the **Omega Registry**: a comprehensive Home Assistant device registry management system that processes, enriches, and provides unified views of home automation devices across multiple data sources. The project operates as both a Home Assistant add-on and a data processing pipeline.

## Core Architecture

### **Data Flow Pipeline**

1. **Input**: Home Assistant registry files (`core.entity_registry`, `core.device_registry`, `core.area_registry`)
2. **Processing**: Multi-stage enrichment pipeline with flatmap generation → omega registry join → alpha registry derivation
3. **Output**: Canonical JSON registries with audit trails and provenance tracking

### **Directory Structure**

- `addon/` - Self-contained HA add-on with runtime components
- `addon/src/` - Pure code modules (import-safe, I/O guarded per ADR-0003)
- `addon/data/canonical/` - Input/output data with strict separation
- `project/` - Development metadata, docs, ADRs, operations
- `scripts/` - Legacy scripts (being migrated to addon/src/)

## Essential Development Patterns

### **Module Execution Convention**

Always run generator scripts with proper PYTHONPATH:

```bash
PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2
```

### **Contract-Driven Development**

All data processing is governed by YAML contracts in `addon/data/canonical/support/contracts/`:

- `omega_registry_master.output_contract.yaml` - Primary output schema
- `join_contract.yaml` - Multi-source data joining rules
- Field inference, validation rules, and join confidence thresholds are contract-defined

### **I/O Safety (ADR-0003)**

- Code in `addon/src/` must be import-safe (no I/O on import)
- Use `addon/src/utils/paths.py` for path resolution
- CLI scripts guard I/O operations and validate contracts before execution

### **Pipeline Execution Order**

1. `generate_flatmap.py --type entity/device` - Creates flatmaps from registry inputs
2. `generate_omega_registry_v2.py` - Joins data sources into master registry
3. `generate_alpha_registry.py --type room` - Derives specialized views
4. Analytics/audit scripts for validation

## Key Integration Points

### **Home Assistant Data Model**

- Entities have `device_id`, `area_id`, `floor_id` relationships
- Devices contain manufacturer, model, MAC addresses, connection info
- Areas/floors form hierarchical containment relationships
- Platform/integration indicates data source (zigbee, zwave, etc.)

### **Enrichment Sources**

- Network scans (Fing, router device lists) for MAC/IP correlation
- Custom Hestia registries for room assignments and device groups
- HA trace logs for dynamic behavior analysis

### **Git LFS & Mirroring**

- JSON outputs >50MB use Git LFS (pinned to GitHub)
- NAS mirroring via GitHub Actions (gated by `NAS_SSH_KEY`)
- Safety bundles created before major operations

## Operational Commands

### **Environment Setup**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### **Pipeline Execution**

```bash
# Full pipeline run
PYTHONPATH=. python3 -m scripts.generators.generate_flatmap --type entity
PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2

# Analytics and validation
PYTHONPATH=. python3 -m project.ops.scripts.analytics.analytics
```

### **Safety & Audit**

```bash
# Pre-operation safety bundle
git bundle create ../omega_registry-pre-operation.bundle --all

# Validate hard-coded paths (HA Config workspace)
bash hestia/tools/validators/scan_hardcoded_ha.sh
```

## Important Files to Reference

- `workspace_ops_export.yaml` - Operational topology and workspace conventions
- `config.yaml` - Pipeline configuration flags and contract paths
- `omega_registry_manifest.md` - Auto-generated file manifest with health metrics
- `project/docs/docs/ADDON_CONTRACT.md` - Add-on runtime requirements
- `project/docs/docs/ADR/` - Architecture decision records

## Development Guidelines

1. **Follow ADR-0003** - Import safety and I/O guards in all new code
2. **Use contracts** - Validate against YAML contracts, don't hardcode schemas
3. **Audit trails** - All data transformations must include provenance/lineage
4. **Test with safety** - Create bundles before major changes
5. **Respect workspace separation** - Keep runtime (`addon/`) separate from project metadata

## Model-Specific Guidance & Guardrails

### **GPT-4o Mini - Best For**

- **Quick fixes and small changes** - Contract validation, import fixes, path corrections
- **Iterative development** - Adding fields to existing schemas, extending pipelines
- **Code reviews** - Checking ADR-0003 compliance, validating PYTHONPATH usage
- **Documentation updates** - README updates, inline comments, simple ADR modifications

**Guardrails:**

- ⚠️ **High-stakes operations**: Always verify safety bundle creation before LFS/contract changes
- ⚠️ **Complex pipeline logic**: May miss subtle data flow dependencies - validate with tests
- ⚠️ **Multi-file refactoring**: Prone to breaking import chains - run full pipeline after changes

### **Claude Sonnet - Best For**

- **Architecture analysis** - Understanding complex ADR implications, workspace restructuring
- **Contract design** - Creating new YAML contracts, validation rule updates
- **Pipeline debugging** - Tracing data flow issues, join confidence problems
- **Complex refactoring** - Moving code between `scripts/` and `addon/src/` per ADR-0005

**Guardrails:**

- ⚠️ **Over-engineering**: May suggest complex abstractions - prefer simple, contract-driven solutions
- ⚠️ **Breaking changes**: Excellent at refactoring but may not preserve backward compatibility
- ⚠️ **Performance assumptions**: May optimize prematurely - this pipeline prioritizes audit trails over speed

### **Critical Validation Checklist (All Models)**

Before accepting any AI-generated changes:

```bash
# 1. Verify imports work
PYTHONPATH=. python3 -c "from addon.src.scripts.generators import generate_omega_registry_v2"

# 2. Validate contracts
PYTHONPATH=. python3 -m addon.src.utils.contract_validator

# 3. Check ADR-0003 compliance (no I/O on import)
find addon/src/ -name "*.py" -exec grep -l "open\|json\|yaml" {} \;

# 4. Test pipeline dry-run
PYTHONPATH=. python3 -m scripts.generators.generate_flatmap --type entity --dry-run
```

### **Emergency Recovery Commands**

If AI changes break the pipeline:

```bash
# Restore from safety bundle
git bundle unbundle ../omega_registry-pre-operation.bundle

# Reset to last known good state
git reset --hard HEAD~1

# Validate workspace integrity
python3 -c "import addon.src.utils.paths; print('Paths OK')"
```

## Common Pitfalls

- Don't run scripts without PYTHONPATH - imports will fail
- Don't modify contracts without understanding downstream impacts
- Don't commit large files without LFS - pipeline will break
- Don't bypass I/O guards in `addon/src/` - breaks import safety
- Check `workspace_ops_export.yaml` for operational constraints before major changes
- **Model-specific**: GPT-4o Mini may miss complex dependencies; Claude may over-architect simple fixes
