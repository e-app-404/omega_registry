Workspace layout

This workspace is used for registry rehydration and analysis. It contains two primary folder entries in the VS Code workspace file `registry_rehydration_local.code-workspace`:

- `/Users/evertappels/Projects/omega_registry_ha_storage` (symlink) — a symbolic link pointing to the Home Assistant `config/.storage` directory on the host system. This path is intentionally referenced in the workspace to allow quick inspection and referencing of HA runtime registry files locally.
- `/Users/evertappels/Projects/registry_rehydration_archive/registry_rehydration_local_last` — the repository and derived artifacts for registry rehydration.

No-modify policy for HA `.storage`

- IMPORTANT: Files under the HA `.storage` directory are runtime Home Assistant state. Do not modify these files from within this project or via the editor.
- The workspace explicitly excludes the symlink path from search and file indexing to reduce accidental edits or heavy indexing overhead.
- The symlink is read-only from the project's perspective. Creation of the symlink was non-destructive and reversible; removing the symlink does not change the HA filesystem.

If you need to make a change to Home Assistant runtime files, do so from the Home Assistant host or with tools that are explicitly intended for HA configuration management. When in doubt, make a backup first.

Contact

If you want me to change the symlink location, add further excludes, or convert the symlink to a safe read-only bind, tell me and I will prepare the commands and docs.
