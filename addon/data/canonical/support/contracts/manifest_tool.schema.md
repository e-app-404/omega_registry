# Manifest Entry Formatting Reference

## Omega Registry Manifest Entry Formatting Guide

**Purpose:**
This section provides the canonical, unified rules for formatting all entries in the Omega Registry manifest. It ensures consistency, machine-readability, and ease of automation for manifest generation, validation, and consumption.

**Scope:**

- Applies to all file, script, documentation, and tracker entries in the manifest.
- Defines required and optional fields, metadata, and layout conventions.
- Supports both human and automated workflows.

---

### New/Updated Fields (2025-07-25)

- `description` (string, optional): Short summary for major files, scripts, or sections.
- `actions` (array, optional): List of available actions for each file (e.g., open, download, view_history, compare_duplicates).
- `tags` (array, optional): Filetype and semantic tags, colored and styled via `scripts/utils/tagging.py`.
- `manifest_options` (object): Sorting/filtering options for manifest rendering.
- `project_health` (object): Project health indicators and visualization options.

---

### File Entry

- **Format:**
  - `filename [— full_path] [— size] [— date] [— link] [— tags] [— description]`
  - Example: `[alpha_room_registry.json](canonical/alpha_room_registry.json) — 0.8 KB — 2025-07-22 — #canonical #active — "Room registry for Alpha system"`
- **Expandable Details:**
  - Each file entry may have an expandable section showing hash, creation/modification timestamps, actions, tags, and other metadata.
- **Actions:**
  - Render as buttons/links in the manifest (open, download, view_history, compare_duplicates).
- **Tags:**
  - Filetype and semantic tags are assigned via `constants.py` and rendered/styled via `tagging.py`.

---

### Sorting/Filtering

- Manifest supports sorting by last update, size, creation date.
- Filtering by file type, section, tags.
- UI elements (dropdowns/buttons) should be rendered at the top of the manifest.

---

### Project Health Visualization

- Render summary indicators (progress bars, pie charts, badges) for:
  - Documentation coverage
  - Test presence
  - Last update recency
  - Duplicate file risk
- Place visualizations in the manifest header.

---

### Duplications Section

- Unified table/accordion format.
- Highlight similarities/differences for each duplicate group.
- "Modified" column must match file metadata.
- Tags and actions are included for each duplicate entry.

---

### Uncaptured Files Section

- No file should appear more than once.
- Render as markdown table or downloadable CSV.
- Support sorting by size, last update, creation date.

---

### Tag Logic & Filetype Mapping

- Filetype tags are mapped in `constants.py` and rendered via `tagging.py`.
- Tag colors and styles are set in `tagging.py` and can be customized.
- All tag logic is documented in the contract and schema for extensibility.

---

### HTML Block Layout for File Entries (2025-08-02, parked for future use)

For modern, visually clear manifest rendering, file entries can use a compact HTML block layout:

```html
<!-- File: example.json -->
<div style='margin-bottom:18px;'>
  <span style='color:#888;background:#303340;padding:2px 6px;border-radius:6px;margin-right:2px'>canonical</span>
  · <span style='background:#0377A9;color:#fff;padding:2px 6px;border-radius:6px;'>JSON</span>
  · <span style='background:#DF2A91;color:#fff;padding:2px 6px;border-radius:6px;'>329.1 KB</span><br>
  <b>example.json</b>
  &nbsp;·&nbsp;
  <i><span style='color:#888'><FontAwesomeIcon :icon="byPrefixAndName.fad['pen-to-square']" /> last edited: 0hr, 0min ago</span></i>
  <br>
  <details style='margin-top:4px;'><summary>More details</summary>
    <ul style='margin-left:0;'>
      <li>Hash: ...</li>
      <li>Created: ...</li>
      <li>Last Updated: ...</li>
      <li>Description: ...</li>
      <li>Actions: <a href='#'>Open</a> | <a href='#'>Download</a> | <a href='#'>View History</a> | <a href='#'>Compare Duplicates</a></li>
    </ul>
  </details>
</div>
```

- All tags (location, type, size) are on the first line.
- File name and last edited info are on the second line.
- A break space follows, then the expandable "more details" block.
- This layout is suitable for both human and automated consumption, and can be styled further via CSS or JS frameworks.
- See patch log 2025-08-02 for rationale and implementation notes.

---

### File Entry (HTML Block Layout, as of 2025-08-02)

- **Format:**
  - All file entries in major manifest sections (General Files, Data pipeline, etc.) must use the following HTML block layout:

```html
<div style='margin-bottom:18px;'>
  <span style='color:#888;background:#303340;padding:2px 6px;border-radius:6px;margin-right:2px'>{location_tag}</span>
  · <span style='background:#0377A9;color:#fff;padding:2px 6px;border-radius:6px;'>{filetype_tag}</span>
  · <span style='background:#DF2A91;color:#fff;padding:2px 6px;border-radius:6px;'>{size}</span><br>
  <b>{filename}</b>
  &nbsp;·&nbsp;
  <i><span style='color:#888'><FontAwesomeIcon :icon="byPrefixAndName.fad['pen-to-square']" /> last edited: {last_edited}</span></i>
  <br>
  <details style='margin-top:4px;'><summary>More details</summary>
    <ul style='margin-left:0;'>
      <li>Hash: ...</li>
      <li>Created: ...</li>
      <li>Last Updated: ...</li>
      <li>Description: ...</li>
      <li>Actions: <a href='#'>Open</a> | <a href='#'>Download</a> | <a href='#'>View History</a> | <a href='#'>Compare Duplicates</a></li>
    </ul>
  </details>
</div>
```

- All tags (location, type, size) are on the first line.
- File name and last edited info are on the second line.
- A break space follows, then the expandable "more details" block.
- This layout is required for all file entries in major manifest sections.

---

## [PATCH LOG]

2025-07-25: Updated schema for new fields (description, actions, tags, manifest_options, project_health), clarified tag logic, filetype mapping, expandable details, sorting/filtering, project health visualization, and duplications section as per patch-manifest-builder-improvements-v2.
