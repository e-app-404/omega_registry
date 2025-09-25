Phase-1 patch set

This directory contains prepared, review-only patches for Phase-1 of the
repository cleanup and workspace normalization. These patches are conservative
and follow the project's dry-run and --apply policy. None of these patches have
been applied; they are provided for review and optional application.

Included patches and artifacts

- 0001-update-gitignore.patch — Add conservative entries to `.gitignore` for
  `.venv`, caches, backups, `tarballs/`, and `__pycache__/`.
- 0002-clean_worktree.sh.patch — Adds `scripts/clean_worktree.sh`, a dry-run
  first script to find and optionally remove common temporary/compiled files.
- 0003-check_single_venv.patch — Adds `scripts/check_single_venv.py` which
  searches the repo for multiple virtual environment directories and prints a
  recommended `.gitignore` snippet for consolidation to repo-level `.venv`.
  NOTE: This patch is skipped by default because `scripts/check_single_venv.py`
  already exists in the repository. The prepared version was moved to
  `copilot_patches/phase-1/skipped/0003-check_single_venv.patch` for auditing.
- 0004-gitattributes.patch — Adds `.gitattributes` marking archive files and
  `tarballs/**` as binary, and suggesting Git LFS for large bundles.
- 0005-update_gitignore_temp.patch — Adds `scripts/append_gitignore_temp.sh`
  which appends common temp-file ignore patterns to `.gitignore` (dry-run by
  default; use `--apply` to modify files).

How to review

- Inspect the patches under this directory. They are plain patch files that can
  be applied with `git apply` or used as a guide for manual commits.
- All scripts default to dry-run mode and require `--apply` to make changes.

Next steps (after review)

- Option A: Apply the patches on `chore/restructure-to-addon` (I can do this if
  you approve). I will apply them in small, per-change commits, run checks,
  and open a PR using `ops/ADR/PR_DESCRIPTION.md` as the PR body.
- Option B: Request further changes or additional patches before applying.

If you want me to proceed to apply these patches, say "apply Phase-1 patches".
