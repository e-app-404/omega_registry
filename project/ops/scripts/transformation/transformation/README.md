# Transformation Scripts

---

**Canonical Output Notice:**

- All transformation scripts must use canonical registry outputs. `omega_registry_master.json` is the only supported registry master.
- All references to legacy enrichment or derived views are deprecated unless explicitly qualified as archival or reference material under `registry_alias/`.
- Pretty-printed versions are strictly for human readability and not for programmatic use.

---

## Pipeline Visualization

```txt
[core.entity_registry]   [core.device_registry]   [enrichment logs]   [legacy Hestia registries]
           |                      |                      |                        |
           +----------------------+----------------------+------------------------+
                                      |
                        [build_enriched_device_map.py]
                                      |
                        [refine_enriched_device_registry.py]
                                      |
                        [omega_enrichment_metadata.py]
                                      |
                        [crossref.py]   [hestia_pre_reboot_parser.py]
                                      |
                        [derived_views, logs, diagnostics]
```

---

## Script Index

- `build_enriched_device_map.py`
  - **Purpose:** Generates enriched device maps from canonical sources and enrichment logs.
  - **Outputs:**
    - `canonical/derived_views/enriched_device_map.json`
  - **Notes:**
    - Contract-driven enrichment, meta-tagged for audit.

- `crossref.py`
  - **Purpose:** Performs cross-referencing and join logic between registry artifacts, ensuring contract alignment and provenance.
  - **Outputs:**
    - `canonical/logs/scratch/enrichment_device_registry_macip_*.json`
  - **Notes:**
    - Useful for enrichment audit and join diagnostics.

- `hestia_pre_reboot_parser.py`
  - **Purpose:** Parses and normalizes legacy Hestia registry data for compatibility with canonical pipeline.
  - **Outputs:**
    - `canonical/diagnostics/legacy_registry_enrichment_summary.yaml`
    - `canonical/joins/pre_reboot_field_join_hints.json`
    - `canonical/logs/hestia_pre_reboot_field_diagnostics.log`
    - `canonical/logs/hestia_pre_reboot_schema_drift.json`
  - **Notes:**
    - Enables legacy-to-canonical migration and audit.

- `omega_enrichment_metadata.py`
  - **Purpose:** Aggregates and analyzes enrichment metadata for devices and entities, supporting contract-driven provenance.
  - **Outputs:**
    - `canonical/derived_views/enriched.device_registry.json`
    - `canonical/logs/analytics/pipeline_metrics.latest.json`
  - **Notes:**
    - Merges, validates, and logs enrichment actions with meta lineage.

- `refine_enriched_device_registry.py`
  - **Purpose:** Filters and refines enriched device registry outputs, emitting contract-compliant subsets.
  - **Outputs:**
    - `canonical/derived_views/enriched_device_registry_subset.json`
  - **Notes:**
    - Skips unenriched devices, emits only contract-compliant entries.

---

## Usage & Troubleshooting

- Run transformation scripts after generating canonical registry and enrichment logs.
- Ensure all required input files exist and are up to date.
- Outputs are written to canonical derived_views or logs folders for traceability.
- For enrichment or cross-referencing issues, review the logs and meta fields in the outputs.

---

## Machine-Friendly Execution Notes

- To ensure all internal imports (e.g., `from scripts.utils.import_path import set_workspace_root`) resolve correctly, always run transformation scripts with the workspace root as PYTHONPATH:

```sh
PYTHONPATH=. python3 scripts/transformation/omega_enrichment_metadata.py
```

- This applies to all scripts that import from the `scripts` package or submodules.
- For enrichment, crossref, or legacy transformation scripts, use the same PYTHONPATH convention if you encounter import errors.

---

## Data Export Utility

`data_export.py` provides a generic CLI utility for exporting entities from any Home Assistant registry file based on a key-value filter.

### Usage

```sh
python scripts/transformation/data_export.py --source core.entity_registry --key platform --value smartthings
```

- `--source`: The registry file to parse (e.g., `core.entity_registry`)
- `--key`: The key to filter on (e.g., `platform`)
- `--value`: The value to match (e.g., `smartthings`)

### Output

- Output is written to: `canonical/data_export/<source>.<key>_<value>.json`
  - Example: `canonical/data_export/entity.platform_smartthings.json`
- The `<source>` is derived from the registry key for brevity (e.g., `entity` for `core.entity_registry`).

### Example

Export all entities with platform `smartthings`:

```sh
python scripts/transformation/data_export.py --source core.entity_registry --key platform --value smartthings
```

---

## See Also

- Main pipeline scripts: `scripts/generators/`
- Analytics scripts: `scripts/analytics/`
- Audit scripts: `scripts/audit/`
- Diagnostics and legacy scripts: `scripts/diagnostics/`
- Contracts and pipeline docs: `canonical/support/contracts/`
- Pipeline overview and troubleshooting: `scripts/generators/README.md`
