# Utility: Generic Entity Exporter

## data_export.py — Generic Entity Export Utility

This script provides a generic, reusable CLI for exporting entities from any registry file based on a key-value filter. It supersedes the old `logging.py` extractor logic.

### Usage

```sh
python scripts/utils/data_export.py --source core.entity_registry --key platform --value smartthings
```

- `--source`: Source registry file to parse (e.g., `core.entity_registry`)
- `--key`: Key to filter on (e.g., `platform`)
- `--value`: Value to match (e.g., `smartthings`)
- `--output`: (Optional) Output path. If omitted, output is written to `canonical/data_export/<source>.<key>_<value>.json`.
- `--ids-only`: (Optional) If set, output will be a JSON array of entity_id values only.

### Output

- Default output path: `canonical/data_export/<source>.<key>_<value>.json`
- If `--ids-only` is used, output is a JSON array of entity_id values.
- All outputs include a `_meta` block with provenance and timestamp (unless `--ids-only` is set).

### Example

Export all entities with platform `smartthings`:

```sh
python scripts/utils/data_export.py --source core.entity_registry --key platform --value smartthings
```

Export only entity_id values for platform `smartthings`:

```sh
python scripts/utils/data_export.py --source core.entity_registry --key platform --value smartthings --ids-only
```

---

This utility is the canonical method for extracting and exporting entity subsets for audit, analytics, or downstream processing. It replaces the legacy `logging.py` extractor. See `constants.py` for registry key resolution.
