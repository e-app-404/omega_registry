# Omega Registry Manifest Builder

---

**Canonical Output Notice:**

- The manifest builder only supports canonical registry outputs. `omega_registry_master.json` is the only supported registry master.
- All references to deprecated sections and alternate outputs are removed unless explicitly qualified as archival or reference material under `registry_alias/`.
- All contract and schema references must point only to canonical pipeline artifacts.

## Overview

This tool generates a comprehensive, human- and machine-friendly registry manifest for the Omega system, aligning output with a contract and schema for full auditability and extensibility.

## Key Features

- **Section Order:** Manifest sections are rendered strictly according to the contract, with File Duplications and Expanded Manifest Details at the end.
- **Entry Formatting:** File entries use HTML blocks for file path, filetype, size, and last edit time. Contrast and color are optimized for accessibility.
- **Filetype Mapping:** Filetype tags are assigned using a mapping in `constants.py` and rendered via `tagging.py`.
- **Tag Rendering:** Tags are colored and styled using `scripts/utils/tagging.py`, with colors adjustable per tag.
- **No Deprecated Sections:** Filter UI and duplicate Tarballs sections are removed for clarity.
- **Extensible Contract/Schema:** Output contract and schema document all formatting conventions, tag logic, and section order for 1:1 alignment.

## Usage

Run the manifest builder:

```bash
python -m scripts.tools.meta_build_manifest
```

## Output Contract & Schema Alignment

- Ensure `manifest_tool.contract.yaml` and `manifest_tool.schema.md` match the latest markdown output:
  - Section order and names
  - Entry formatting (HTML blocks, color, filetype, tags)
  - Tag logic and color mapping via `tagging.py`
  - No deprecated sections

## Tagging & Filetype Logic

- Filetype tags are mapped in `constants.py` and rendered via `tagging.py`.
- Tag colors are set in `tagging.py` and can be customized.

## Extending the Manifest

- To add new sections, update the contract and schema.
- To add new filetypes or tags, update `constants.py` and `tagging.py`.

## Audit Trail

- All changes and script runs are logged in patch files for full traceability.

## Support

For schema/contract updates, see `manifest_tool.schema.md` and `manifest_tool.contract.yaml`.
For tag logic, see `scripts/utils/tagging.py`.
