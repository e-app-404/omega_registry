# Enrichment Engine

## Overview

The Omega Registry Enrichment Engine is responsible for transforming raw registry data into a fully enriched, contract-compliant canonical registry. It applies join logic, inference, and patch enforcement to ensure all entities are hydrated with the correct metadata, including device, area, floor, domain, and more.

## Pipeline Flow

1. **Input Loading**: Reads all required registries (entity, device, area, floor) and contract files.
2. **Entity Grouping**: Groups entities by area for efficient lookup.
3. **Device and Area Registry Lookup**: Builds fast lookup tables for device and area metadata.
4. **Main Enrichment Loop**: For each entity:
   - **Device→area_id Fallback**: If an entity is missing `area_id` but has a `device_id`, inherits `area_id` from the device. This is logged for auditability.
   - **Area→floor_id Fallback**: If an entity is missing `floor_id` but has an `area_id`, inherits `floor_id` from the area.
   - **Domain Inference**: Infers the domain from the entity_id prefix if missing.
   - **Device Class Inference**: Infers device_class from attributes or known device classes.
   - **Diagnostics**: Computes join health and diagnostics for each anchor field.
   - **Output Preparation**: Ensures all required fields are present and ordered.
5. **Output Writing**: Writes the enriched registry, debug overlays, and recovery reports to disk.
6. **Recovery Mode**: Optionally applies heuristics to fill missing fields if enabled.
7. **Dry Audit Mode**: Optionally audits join paths and outputs a join path audit file.
8. **Contract Audit Enforcement**: After enrichment, checks that all sun sensor entities (e.g., `sensor.sun_next_dawn`) have `area_id == "london"`. Raises an exception if the contract is violated.
9. **Unit-like Test**: Asserts at runtime that all sun sensors have the correct area_id.

## I/O Overview and Tracing

### Inputs

- **Entity Registry** (`--input`): Main input file, e.g. `canonical/omega_registry_master.json`.
- **Device Registry**: `canonical/registry_inputs/core.device_registry`
- **Area Registry**: `canonical/registry_inputs/core.area_registry`
- **Floor Registry** (optional): `canonical/registry_inputs/core.floor_registry`
- **Enrichment Manifest** (`--manifest`): YAML file with enrichment rules.
- **Join Contract, Area Hierarchy, Tier Definitions, Output Contract**: YAML files in `canonical/support/contracts/`.
- **Entity Flatmap**: `canonical/derived_views/flatmaps/entity_flatmap.json`

### Outputs

- **Enriched Registry** (`--output`): Main output file, e.g. `canonical/omega_registry_master.json`.
- **Versioned Output** (`--output-version`): Optional, e.g. `registry_alias/enriched.v1.json`.
- **Trace Overlay** (`--trace`): JSON file with diagnostics and debug overlays.
- **Hydration Recovery Report**: `hydration_recovery_report.json`
- **Join Path Audit** (`--dry-audit`): `join_path_audit.json`
- **Filtered Output**: `omega_registry.enriched.filtered.json`

### Logging and Audit Trail

- **Enforcement Print**: Logs device→area_id inheritance.
- **Contract Audit Exception**: Raises if sun sensor contract is violated.
- **Unit Test Print**: Confirms sun sensors have correct area_id.

### I/O Flow Trace

1. Read all input files.
2. For each entity, apply enrichment, fallback, and inference logic.
3. Write outputs: enriched registry, trace/debug overlays, recovery and audit reports.
4. Enforce contract audit and run unit-like test.

## CLI Flags

- `--input <file>`: Path to the input entity registry JSON. Default: `canonical/omega_registry_master.json`.
- `--output <file>`: Path to the output enriched registry JSON. Default: `canonical/omega_registry_master.json`.
- `--output-version <file>`: Optional versioned output path.
- `--manifest <file>`: Path to the enrichment manifest YAML.
- `--trace <file>`: Path to the trace overlay output file.
- `--min_score <float>`: Minimum join health score for output inclusion.
- `--recovery_mode`: Enable heuristics to fill missing fields.
- `--dry-audit`: Run join path audit only, do not write main registry.
- `--mode <str>`: Enrichment mode (omega, alpha, etc).

## Error Handling

- **Missing Input Files**: If any required input file is missing, the engine will raise an error and halt execution.
- **Malformed JSON/YAML**: If input files are not valid JSON/YAML, a parsing error is raised.
- **Contract Audit Failure**: If any sun sensor entity fails the area_id contract, an exception is raised and the pipeline fails.
- **Join Failures**: All join failures and missing fields are logged in the hydration recovery report and debug overlays.
- **Graceful Degradation**: Optional files (like floor registry) are handled gracefully if missing.
- **Traceability**: All enrichment, fallback, and error events are logged for auditability.

## Patch Logic: Device→area_id Inheritance

If an entity is missing `area_id` and has a `device_id`, the engine attempts to inherit the `area_id` from the device. This is logged for traceability:

```python
print(f"Join [entity={entity['entity_id']}] inherits area_id='{device['area_id']}' from device_id='{entity['device_id']}'")
```

The join is annotated in the entity's `_meta.inferred_fields` for downstream auditing.

## Contract Audit

After enrichment, the engine enforces a contract audit:

- Checks that all sun sensor entities (e.g., `sensor.sun_next_dawn`, `sensor.sun_next_dusk`, etc.) have `area_id == "london"`.
- If any do not, the engine raises an exception and fails the pipeline, ensuring that patch requirements are strictly enforced.

## Usage

Run the enrichment engine as a script:

```sh
python -m scripts.enrich.enrichment_engine --input <input.json> --output <output.json> [--dry-audit] [--recovery_mode]
```

- Use `--dry-audit` to output join path audits without writing the main registry.
- Use `--recovery_mode` to apply additional heuristics for missing fields.

## Extensibility

- The engine is modular and can be extended with new join rules, inference logic, or contract audits as needed.
- All patch and audit actions are logged for full traceability and compliance.
