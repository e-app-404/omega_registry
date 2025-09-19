# Generators

---

**Canonical Output Notice:**

- All generator scripts now default to canonical output paths and contracts. `omega_registry_master.json` is the only supported registry master output.
- All references to legacy generator scripts and outputs are deprecated unless explicitly qualified as archival or reference material under `registry_alias/`.
- Pretty-printed versions (e.g., `omega_registry_master.pretty.json`) are strictly for human readability and not for programmatic use.
- All contract references must use the canonical path: `canonical/support/contracts/omega_registry_master.output_contract.yaml`.
- All CLI usage must use module invocation with PYTHONPATH set, e.g., `PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2`.

---

## Pipeline Overview

```txt
[core.entity_registry]   [core.device_registry]   [core.area_registry]   [core.floor_registry]
           |                      |                        |                        |
           |                      |                        |                        |
           +----------------------+------------------------+------------------------+
                                      |
                        [generate_flatmap.py] (entity/device)
                                      |
                        [generate_omega_registry.py]
                                      |
                        [generate_alpha_registry.py]
                                      |
                        [sanitize_alpha_room_registry.py]
                                      |
                        [analytics/audit/QC scripts]
```

---

## `generate_alpha_registry.py`

**Purpose:**
Generates the alpha room registry from canonical sources, contract-driven, supports CLI arguments for type/target selection.

**Pipeline Position:**
Run after omega registry generation and flatmap creation.

**Inputs:**

- `canonical/omega_registry_master.json`
- `canonical/support/contracts/omega_registry_master.output_contract.yaml`

**Outputs:**

- `canonical/derived_views/alpha_room_registry.json`

**CLI Usage:**

```bash
PYTHONPATH=. python3 -m scripts.generators.generate_alpha_registry --type room
```

**Notes:**

- Contract-driven, supports patch and lineage logging.
- Outputs are meta-tagged for audit.

---

## `generate_flatmap.py`

**Purpose:**
Unified flatmap generator for both entity and device registries. Consolidates logic from legacy scripts to provide a single, contract-driven entry point for flatmap generation.

**Pipeline Position:**
Run after canonical registry extraction and contract enrichment, before downstream analytics, audits, or QC phases.

**Upstream Sources:**

- `canonical/registry_inputs/core.entity_registry` (for entity flatmap)
- `canonical/registry_inputs/core.device_registry` (for device flatmap)
- `canonical/support/contracts/omega_registry_master.output_contract.yaml` (for contract-driven inference)

**Downstream Consumers:**

- `canonical/derived_views/flatmaps/entity_flatmap.json`
- `canonical/derived_views/flatmaps/device_flatmap.json`
- `canonical/logs/analytics/entity_flatmap.metrics.json`
- `canonical/logs/analytics/device_flatmap.metrics.json`
- Downstream audit scripts, analytics, and QC tools

**Expected Results:**

- Flatmap JSON output with all key fields (`tier`, `area_id`, `floor_id`, `platform`, etc.) inferred and propagated per contract.
- Metrics JSON summarizing input, output, and skipped entries for full traceability.
- All outputs tagged with meta lineage for audit and reproducibility.

**CLI Arguments:**

- `--type entity` : Generates entity flatmap from `core.entity_registry`.
- `--type device` : Generates device flatmap from `core.device_registry`.

**Usage Example:**

```bash
PYTHONPATH=. python3 -m scripts.generators.generate_flatmap --type entity
PYTHONPATH=. python3 -m scripts.generators.generate_flatmap --type device
```

**Notes:**

- Import path setup is canonized via `scripts/utils/import_path.py` for robust, future-proof module loading.
- All patch actions and lineage are logged under PATCH IMPORT-PATH-CANONICAL-FIX-V1 for full visibility.
- The script is contract-driven: all field inference and propagation is governed by `omega_registry_master.output_contract.yaml`.
- Outputs are always tagged with meta lineage for audit and reproducibility.
- Designed to be idempotent and safe for repeated runs in the pipeline.

---

## `generate_omega_registry.py`

**Purpose:**
Builds the canonical omega registry master join graph, handling multi-source enrichment and contract compliance.

**Pipeline Position:**
Run after flatmap generation, before alpha registry and analytics.

**Inputs:**

- `canonical/derived_views/flatmaps/entity_flatmap.json`
- `canonical/derived_views/flatmaps/device_flatmap.json`
- `canonical/registry_inputs/core.area_registry`
- `canonical/registry_inputs/core.floor_registry`
- `canonical/support/contracts/omega_registry_master.output_contract.yaml`

**Outputs:**

- `canonical/omega_registry_master.json`
- `canonical/logs/scratch/debug_join_graph_omega_registry.jsonl`

**CLI Usage:**

```bash
PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2
```

**Notes:**

- Handles multi-source enrichment, join tracing, and field inheritance as per contract definitions.
- Requires correct PYTHONPATH for import resolution.
- Outputs are meta-tagged and patch-logged.

---

## `sanitize_alpha_room_registry.py`

**Purpose:**
Sanitizes and regenerates alpha room registry artifacts as per contract and patch instructions.

**Pipeline Position:**
Run after alpha registry generation, before final analytics or export.

**Inputs:**

- `canonical/derived_views/alpha_room_registry.json`
- `canonical/support/contracts/omega_registry_master.output_contract.yaml`

**Outputs:**

- `canonical/derived_views/alpha_room_registry.sanitized.v1.json`

**CLI Usage:**

```bash
PYTHONPATH=. python3 -m scripts.generators.sanitize_alpha_room_registry
```

**Notes:**

- Applies contract-driven sanitization and patch lineage.
- Outputs are meta-tagged for audit.

---

## Troubleshooting & Tips

- **Import Errors:**
  - Always run scripts with the workspace root as PYTHONPATH, e.g., `PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2`.
  - Ensure all dependencies are installed and virtualenv is activated.
- **Missing Source Files:**
  - Check that all required registry and contract files exist in the canonical/registry_inputs and canonical/support/contracts folders.
- **Contract Updates:**
  - Contracts are found in `canonical/support/contracts/`. Update these to change field inference, join logic, or spatial relationships.
- **Audit & Lineage:**
  - All outputs are meta-tagged and patch-logged for reproducibility. Check logs in `canonical/logs/` for details.
- **Pipeline Flow:**
  - Follow the pipeline diagram above for correct script execution order.

---

## Machine-Friendly Execution Notes

- To ensure all internal imports (e.g., `from scripts.utils.import_path import set_workspace_root`) resolve correctly, always run generator scripts with the workspace root as PYTHONPATH:

```sh
PYTHONPATH=. python3 -m scripts.generators.generate_omega_registry_v2
```

- This applies to all scripts that import from the `scripts` package or submodules.
- For analytics and downstream scripts, use the same PYTHONPATH convention if you encounter import errors.

---

## Compliance reports and provenance fields

Writers for alpha registries (e.g. alpha sensors, alpha rooms, alpha lighting) may emit an optional compliance report when validation detects contract deviations. The pipeline records these in the writer-level provenance manifest and the pipeline-level provenance.

- `compliance_report` (string, optional): absolute path to a JSON file containing the contract compliance errors for that output. Present when the writer's validator returns errors.

Alpha outputs in the pipeline provenance now include the following fields when available:

- `path` (string): absolute path to the alpha output file
- `sha256` (string|null): SHA256 hex digest of the file, or null if not present
- `phase` (string): producer phase or writer identifier
- `updated_at` (string, ISO8601 TZ-aware, optional): timestamp when the writer updated the individual alpha artifact (copied from the writer-level provenance)
- `compliance_report` (string, optional): absolute path to the compliance report for that artifact

To run the pipeline while isolating writer provenance and compliance output to a temporary location (useful for tests or CI):

```sh
# Direct pipeline to write writer-level provenance and compliance reports into a temp dir
OMEGA_PROVENANCE_MANIFEST=/tmp/omega_prov.json OMEGA_COMPLIANCE_DIR=/tmp/omega_compliance \
PYTHONPATH=. venv/bin/python3 scripts/omega_pipeline_main.py --emit-alpha --emit-alpha-write
```

This will cause per-writer provenance entries to be stored at the path given in `OMEGA_PROVENANCE_MANIFEST` and compliance reports under `OMEGA_COMPLIANCE_DIR`.

---
