Omega Registry — Add-on Minimal Runtime Contract

Purpose
--------
This document describes the minimal runtime contract for packaging the Omega Registry pipeline as a Home Assistant Supervisor add-on. The goal is to define the smallest set of inputs, outputs, config flags, and runtime behaviors necessary to preserve core functionality (generate/enrich/dry-run) while minimizing the add-on's file and dependency footprint.

Design principles
-----------------
- Keep the add-on's required host mounts minimal and read-only by default.
- Provide opt-in flags for features that write many audit/diagnostic files (analytics, verbose audits, synthetic-device creation).
- Make all heavy analytics and optional diagnostics configurable so CI or operators can run them externally.
- Provide a dry-run mode that performs enrichment and synthetic impact estimation without mutating canonical files.

Required inputs (read-only mounts recommended)
---------------------------------------------
These inputs must be available to the add-on at runtime (mounts or in-container copies). Each input is labeled Required/Optional and minimal schema notes.

- Required: canonical/support/contracts/join_contract.yaml
  - Purpose: join definitions and inference mappings used by the generator/enrichers.
  - Format: YAML mapping; used by generator and enrich orchestrator.

- Required: canonical/support/contracts/area_hierarchy.yaml
  - Purpose: area/floor containment graph used for room/floor inference.
  - Format: YAML contract file.

- Required: canonical/registry_inputs/core.entity_registry
  - Purpose: entity registry source (or equivalent entity list used to build flatmaps).
  - Format: JSON array or object that `load_json_with_extract` can parse. Loader filters non-dict entries.

- Optional (but commonly provided): canonical/registry_inputs/core.device_registry
  - Purpose: device registry used by device-based enrichers. May contain non-dict metadata entries; loader filters these out.
  - Format: JSON (device objects). If malformed entries exist, they will be skipped with warnings.

- Optional: canonical/derived_views/flatmaps/entity_flatmap.json
  - Purpose: precomputed flatmap of entities that speeds up generator.
  - If not present, the add-on can generate it by reading `core.entity_registry`.

- Optional: canonical/logs/analytics/pipeline_metrics.latest.json
  - Purpose: tier analytics used by alpha room generation. If missing, tiers may be unclassified.

Configuration flags exposed to add-on config (mapped to `pipeline_config`)
---------------------------------------------------------------------------
- enable_analytics: boolean (default: false)
  - If true, run analytics step that produces `pipeline_metrics.latest.json` and other analytics logs.
- enable_audit_writes: boolean (default: false)
  - If true, persist audit artifacts into `canonical/logs/audit/`. Otherwise write audits to ephemeral tempfs or skip.
- enable_synthetic_device_creation: boolean (default: false)
  - Controls whether enrichers may create synthetic device entries in dry-run or real runs.
- enrichers: list of strings (default: ["device_enricher","network_tracker_enricher","mobile_app_enricher","join_enricher","area_floor_enricher","name_enricher"])
  - Allows operators to enable/disable specific enrichers.
- read_only_mode: boolean (default: true)
  - If true, the add-on must not overwrite `canonical/omega_registry_master.json` unless a different `output_path` is specified and `write_output` is enabled.
- output_path: string (default: "canonical/omega_registry_master.json")
  - Path inside the container where canonical output will be written if `write_output` is enabled.
- write_output: boolean (default: false)
  - By default the add-on runs in read-only/dry-run. Enable to perform full write-through.

Operations (commands the add-on should support)
------------------------------------------------
- generate
  - Reads required inputs, runs generator, and writes alpha/derived outputs.
  - Respect `read_only_mode` and `write_output` flags.
- enrich
  - Runs enrichment orchestrator on provided entities and emits per-entity enriched results (to STDOUT, API, or files, depending on config).
- dry-run (default)
  - Runs enrichment and the synthetic impact estimator, produces `canonical/logs/audit/synthetic_impact_estimate.json` (unless `enable_audit_writes` is false), but does not overwrite canonical outputs.

Error modes & resilience
------------------------
- Missing optional inputs: proceed with defaults, emit informative warnings and produce partial outputs.
- Malformed input entries (non-dict in registries): loader will filter non-dict entries and the add-on should log count of skipped entries.
- Failure during analytics: log error and continue (analytics is optional).
- Insufficient input to generate rooms: generator should return an empty room list and the add-on should exit with code 0 for dry-run, non-zero only for strict error mode.

Logging & audit
---------------
- Keep logging small by default. Use configurable verbosity in the add-on config.
- When `enable_audit_writes` is false, direct audits to an ephemeral location inside the container and expose them via the service API for ad-hoc retrieval.

Security & mount guidance
-------------------------
- Recommend mounting Home Assistant `.storage` host directory as read-only transforms (if operator grants access). The add-on should not require SSH keys or private host credentials.
- If `write_output` is enabled, require explicit opt-in config and document the exact host path that will be modified.
- Ensure the add-on runs as a non-root user in the container where possible.

Minimal runtime dependencies (addon image)
-----------------------------------------
- python: 3.11 or 3.13 (match project venv if needed). Use an official slim base image.
- pyyaml
- A small JSON-only standard library is sufficient for most logic (no extra deps required unless optional features are enabled).

Acceptance criteria for add-on minimal run
------------------------------------------
- With provided minimal inputs, `generate` produces `alpha_room_registry.v1.json` and either writes it to the configured output path or returns it via STDOUT/API when `read_only_mode` is true.
- `dry-run` produces a synthetic impact estimate and does not modify canonical files when `write_output` is false.
- The add-on honors `enrichers` toggles and `enable_synthetic_device_creation`.

Next steps (implementation guidance)
-----------------------------------
1. Implement a tiny wrapper CLI (`omega_addon_cli.py`) that maps config to `pipeline_config` settings and provides `generate`, `enrich`, and `dry-run` subcommands. The wrapper should be small and import internal functions directly (not run the legacy script dumps).
2. Move docs/dev-only deps out of runtime `requirements.txt` into `requirements-dev.txt`.
3. Refactor tests (like `scripts/qa/test_enrichment_engine.py`) to be non-invasive by allowing injection of an in-memory `omega_rooms` list or by mocking the file reads.
4. Create an addon scaffold (Dockerfile + config.json) that installs minimal runtime deps and runs `omega_addon_cli.py` on startup or exposes a minimal HTTP control API.

Document version: 2025-09-19
