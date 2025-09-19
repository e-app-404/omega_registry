# Omega Registry Generator

---

**Canonical Output Notice:**

- The generator enforces canonical output and contract compliance. `omega_registry_master.json` is the only supported output.
- All references to alternate output paths and legacy outputs are deprecated unless explicitly qualified as archival or reference material under `registry_alias/`.
- Pretty-printed versions are strictly for human readability and not for programmatic use.

---

This folder contains scripts responsible for generating canonical and derived registry artifacts for the Omega Registry pipeline.

---

## Pipeline Overview

## Pipeline Logic Cross-Walk

### 1. CLI Runner: `omega_pipeline_main.py`

- **Location:** `scripts/omega_pipeline_main.py`
- **Role:** Entry point for generating the omega registry. Handles CLI arguments for output path, contract, and input files. Calls the main generator logic.
- **Key Arguments:**
  - `--output`: Output path for `omega_registry_master.json`
  - `--contract`: Path to output contract YAML
  - `--inputs`: List of input entity registry files
- **Calls:** `scripts.omega_registry.generator.generate()`

### 2. Generator Orchestration: `generator.py`

- **Location:** `scripts/omega_registry/generator.py`
- **Role:** Orchestrates the registry generation pipeline. Loads config, contract, and input files; applies minimization, enrichment, and output logic.
- **Calls:** Functions from `minimizer.py`, `writer.py`, `contract.py`, `loaders.py`, and `utils.py`.

### 3. Minimization Logic: `minimizer.py`

- **Location:** `scripts/omega_registry/minimizer.py`
- **Role:** Implements entity minimization, null field offloading, voice_assistants flattening, and contract-driven allowlist enforcement.

### 4. Output Writing: `writer.py`

- **Location:** `scripts/omega_registry/writer.py`
- **Role:** Handles deduplication, compact JSON output, and audit log emission.

### 5. Contract Handling: `contract.py`

- **Location:** `scripts/omega_registry/contract.py`
- **Role:** Loads and validates the output contract, provides the allowlist for minimization.

### 6. Input Loading: `loaders.py`

- **Location:** `scripts/omega_registry/loaders.py`
- **Role:** Loads and filters input registry files, robust to non-dict entries.

### 7. Utilities: `utils.py`

- **Location:** `scripts/omega_registry/utils.py`
- **Role:** Shared helpers for hashing, path resolution, and other common tasks.

---

## Allowlist Enforcement After Minimization

After all minimization steps (null field offloading, `voice_assistants` flattening, meta minimization, etc.), the pipeline enforces a strict allowlist to ensure only contract-valid fields are present in the output.

- **Purpose:**
  - Guarantees that only fields defined in the output contract (from `required_keys` and `optional_keys`) are retained in each registry entity.
  - Removes all legacy, null, or verbose fields not specified by the contract.
- **How it works:**
  - The allowlist is dynamically built by loading the contract YAML and combining `required_keys` and `optional_keys`.
  - After all other minimization logic, each entity is filtered to include only these allowlisted fields.
- **Implementation:**
  - Enforced in the generator pipeline after minimization and before output writing.
  - Ensures output is compact, contract-driven, and ready for downstream consumers.

**See the generator and minimizer modules for details on allowlist enforcement logic.**

---

## 🧠 Purpose of the Minimized Omega Registry — Strategic Context

The minimized omega registry is a contract-driven, canonical base layer designed for governance, traceability, and robust downstream processing. It is intentionally reduced to serve as a stable foundation for all further registry transformations and enrichments.

### 🎯 Primary Purpose

- **Stable, contract-governed canonical base layer** for all downstream transformations, synthesis stages, and alpha/beta view generation.

### 📦 Use Case Alignment

| Use Case                | How Minimization Helps                                                                                   |
|-------------------------|---------------------------------------------------------------------------------------------------------|
| Storage + Portability   | Smaller size reduces I/O, speeds CI/CD, and enables artifact shipping to edge agents or containers.     |
| Contract Validation     | Strict allowlist enforces schema conformance, ensuring type- and schema-safe downstream usage.           |
| Testing & Regression    | Eliminates volatile/transient fields, stabilizing test snapshots and regression control.                 |
| Provenance + Audit      | `_meta` fields capture reduction lineage for trace-based debugging and reconstruction.                   |
| Derivation Triggers     | Alpha registries can declare what was added/inferred, based on what is absent in omega.                 |

### ⚠️ Trade-Off

- The registry is intentionally “very reduced” and not directly usable without enrichment.
- This is by design: the omega registry is a transitional contract layer—a scaffold, not the final structure.

### ✅ Achievements

- Modular, empirically validated, contract-enforced omega generator.
- Logic and metadata supporting synthesis and traceability.
- Foundation for:
  - `alpha_room_registry.v1.json`
  - `device_flatmap.json`
  - Enriched clusters, trace inferences, override hierarchies.

### 🔁 Next Step

- Use the omega registry as a source of truth for what’s not known, allowing alpha and beta registries to layer only what they intentionally inject.

### 🧭 Summary

- The minimization achieves the governance baseline—alpha and enriched views are now cleanly separated and traceable.
- If more data is needed, it should be explicitly enriched and version-tracked, not accidentally retained.

---

**See each module for further details on function signatures and implementation.**
