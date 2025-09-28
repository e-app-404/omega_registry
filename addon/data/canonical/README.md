Top-Level Pipeline Entrypoint
omega_pipeline_main.py: Orchestrates the full registry pipeline.
Key Submodules and Their Focus
analytics/:

Registry analysis, metrics, validation, and repair scripts (e.g., analyze_omega_registry.py, metrics_diff.py, validate_registry_quality.py).
audit/:

Auditing and compliance checking (e.g., audit_contract_compliance.py, audit_pipeline.py).
enrich/:

Enrichment logic, orchestrators, field contracts, and normalization (e.g., enrich_orchestrator.py, label_enricher.py, field_contracts.py).
generators/:

Scripts for generating various registry artifacts (e.g., generate_omega_registry.py, generate_alpha_registry.py).
legacy/:

Legacy enrichment and engine scripts (e.g., enrich_device_registry.py, enrichment_engine.py).
omega_registry/:

Core registry logic: generator, contract, minimizer, loaders, writer, and audit writer.
qa/:

Quality assurance and test scripts (e.g., test_enrichment_engine.py, test_registry_minimization.py).
tools/:

Meta build and manifest tools (e.g., meta_build_manifest.py, meta_build_readme.py).
transformation/:

Transformation, cross-referencing, data export, enrichment, and tier logic (e.g., omega_enrichment_metadata.py, build_enriched_device_map.py, tiers.py).
utils/:

Utilities for config, logging, file handling, input/output, architecture, and validation (e.g., pipeline_config.py, logging.py, registry_inputs.py, output_contract_enforcer.py).
