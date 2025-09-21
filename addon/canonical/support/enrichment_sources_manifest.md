# Enrichment Sources Manifest

This document describes the canonical structure and semantics of the `canonical/enrichment_sources/` folder, as formalized in PATCH-JOIN-PIPELINE-HESTIA-V1.

## Structure

- `ha_registries/`
  - `post-reboot/`: Home Assistant .storage exports after reboot
  - `pre-reboot/`: Home Assistant .storage exports prior to reboot or reset
- `hestia/`
  - `post-reboot/`: Cleaned output from `omega_device_registry.cleaned.v2.json`
  - `pre-reboot/`: All pre-reboot legacy registries and configs
- `network/`: MAC/IP/hostname/device_id cross-reference lists, exportable from Fing, router UI, or HA Dev Tools
- `manual/`: Manually created JSON/YAML enrichments not derivable from other sources
- `state/`: State dumps, backups, or parsed templates (e.g., historical `states` or runtime cache rebuilds)

## Semantics

- All enrichment sources not emitted directly from the pipeline must reside in this folder.
- The join pipeline must resolve enrichment files from here, not from `derived_views/`.
- `network` and `manual` folders are scanned only if integration targets exist for their contents.
- Each subfolder is semantically partitioned to prevent confusion between raw/canonical inputs, derived joins, and third-party/network enrichments.

## Contract Alignment

- All joins referencing enrichment files must use paths under `enrichment_sources/`.
- The join contract (`join_contract.yaml`) is updated to reflect this structure.
- Fallback logic relying on historical `derived_views` is retired.
- Anchors or source definitions matching this structure are tagged with `source_class: enrichment`.

---

### _Last updated: 2025-07-21 by Copilot (PATCH-JOIN-PIPELINE-HESTIA-V1)_
