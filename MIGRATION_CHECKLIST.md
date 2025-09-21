Migration checklist - chore/restructure-to-addon

This file documents the remaining safe steps to finish the restructure from
`registry_rehydration_local_last` -> `addon` and moving non-runtime folders to top-level.

Steps performed so far
- Created branch: chore/restructure-to-addon
- Created lightweight backup tarball (placed one level above repo)
- Verified path helper exists at `addon/utils/paths.py` and resolves roots
- Merged logs into `addon/canonical/logs/` (rsync --update; reports saved under `addon/meta/rehydration/...`)
- Refactored three core scripts to use `addon.utils.paths.canonical_path`:
  - `addon/scripts/generate_omega_registry.py`
  - `addon/scripts/hestia_pre_reboot_parser.py`
  - `addon/scripts/analytics/analyze_omega_registry.py`
- Committed refactor changes on branch `chore/restructure-to-addon`

Remaining cautious steps (recommended)
1. Dry-run and finalize file moves
   - Decide exact mapping for non-runtime folders (docs/, data/, reports/, tools/, scripts/, tests/, contracts/, shared/)
   - Make sure no top-level name collisions exist
   - Use `git mv` for each move to preserve history

2. Replace any remaining absolute references in meta/reports that encode the old path
   - Files under `addon/meta/rehydration/...` contain absolute paths referencing `registry_rehydration_local_last`; update them only if you want the artifact to reference `addon` instead.
   - Note: It's safe to leave historical artifacts as-is; they reflect the historical layout.

3. Update workspace files
   - Ensure `omega_registry.code-workspace` references `addon` (it already does)
   - Confirm VS Code excludes/search excludes the HA symlink path

4. Run CI / linters / tests
   - Install dev dependencies in a virtualenv and run `make lint` and `make test`
   - Run select pipeline scripts as dry runs to ensure runtime behavior unchanged

5. Push and open PR
   - Push branch and open a PR with the migration description and safety notes

Acceptance criteria
- `addon` contains runtime-critical assets (notably canonical)
- Non-runtime content is present at top-level in chosen folders (or mapped)
- Workspace files reference `addon` correctly and includes excludes for HA symlink
- `addon/utils/paths.py` is present and used in core scripts (no hard-coded `canonical/...` paths remain in the 3 core scripts)
- Tests / smoke checks pass and no HA `.storage` files were modified during the process

Notes
- Historical artifacts in `addon/meta/rehydration` will still reference `registry_rehydration_local_last`; this is expected and acceptable for auditability.
- If you'd like me to continue and perform the git mv moves now, I can run them in small batches (dry-run listing first) and commit per batch.
