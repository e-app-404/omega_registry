# Audit Scripts

---

**Canonical Output Notice:**

- All audit scripts validate only canonical outputs and contracts. Use `omega_registry_master.json` exclusively.
- All references to legacy enriched files and alternate outputs are deprecated unless explicitly qualified as archival or reference material under `registry_alias/`.
- Pretty-printed versions are strictly for human readability and not for programmatic use.

---

## Pipeline Visualization

```txt
[entity_flatmap.json]   [omega_registry_master.json]
           |
[flatmap_inference_signal_audit.py]
           |
[audit_flatmap/flatmap_inference_signal_audit.json]
```

---

## Script Index

- `flatmap_inference_signal_audit.py`
  - **Purpose:** Audits field completeness, signal strength, and entity alignment between the entity flatmap and the omega registry master join graph.
  - **Outputs:**
    - `canonical/logs/audit/audit_flatmap/flatmap_inference_signal_audit.json` (completeness matrix, signal summary, trace notes, meta)
  - **Notes:**
    - Uses a sample of up to 100 aligned entities for root cause analysis.
    - Attaches meta lineage for audit and reproducibility.
    - Useful for diagnosing missing field propagation and contract mapping gaps.

---

## Usage & Troubleshooting

- Run audit scripts after generating the flatmap and omega registry outputs.
- Ensure all required input files exist and are up to date.
- Outputs are written to the canonical audit logs folder for traceability.
- For field propagation or contract mapping issues, review the trace notes and completeness matrix in the audit output.

---

## Machine-Friendly Execution Notes

- To ensure all internal imports (e.g., `from scripts.utils.input_list_extract import extract_data`) resolve correctly, always run audit scripts with the workspace root as PYTHONPATH:

```sh
PYTHONPATH=. python3 scripts/audit/flatmap_inference_signal_audit.py
```

- This applies to all scripts that import from the `scripts` package or submodules.
- For custom or new audit scripts, use the same PYTHONPATH convention if you encounter import errors.

---

## See Also

- Main pipeline scripts: `scripts/generators/`
- Transformation scripts: `scripts/transformation/`
- Analytics scripts: `scripts/analytics/`
- Diagnostics and legacy scripts: `scripts/diagnostics/`
- Contracts and pipeline docs: `canonical/support/contracts/`
- Pipeline overview and troubleshooting: `scripts/generators/README.md`
