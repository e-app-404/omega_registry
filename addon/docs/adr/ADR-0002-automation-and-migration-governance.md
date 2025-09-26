---
title: "ADR-0002: Automation & Migration Governance"
date: 2025-09-22
status: Accepted
author:
  - "Evert Appels"
related:
  - ADR-0001
supersedes: []
tags:
  - governance
  - automation
  - migration
  - linting
  - adr
last_updated: 2025-09-22
---

# ADR-0002: Automation & Migration Governance

## Table of Contents

1. Context
2. Decision
3. Requirements
4. Guardrails
5. Machine-parseable validation block
6. Lifecycle & enforcement
7. Examples

## 1. Context

This ADR defines the governance, requirements, and guardrails for automated repository-wide
changes (for example: path or package name standardization, lint autofixes, venv standardization,
and bulk text migrations). It explicitly complements ADR-0001 (ADR formatting and token rules).

The repository is large and contains many archived artifacts and generated files. Automation
must be conservative, auditable, and reversible.

## 2. Decision

- Adopt a conservative, tracked-files-only, small-batch automation workflow for repo-wide
  migrations and lint remediation.
- Require dry-run (preview) mode that produces unified diffs before any apply step.
- Require automatic backups for any applied change and per-batch commits on a working branch.
- Enforce a machine-parseable TOKEN_BLOCK in ADRs that define or authorize automated actions.

## 3. Requirements

All automation scripts and CI hooks must meet these requirements:

- Tracked-files only: Automation MUST operate only on files returned by `git ls-files` to avoid
  scanning large artifacts, data, or external directories.

- Size limits: Files larger than 200 KiB MUST be skipped by default and reported in the dry-run.

- Dry-run: Every script that modifies files MUST support a `--dry-run` mode that prints a unified
  diff (git-style) and exits without changing the workspace.

- Backups: When `--apply` is used, a backup MUST be created per file (e.g., `.bak` or commit
  snapshot) before writing changes. Backups MUST be stored alongside changes or committed in a
  dedicated `chore/migration-backups` commit that can be reverted.

- Branching: Automation must run on a feature branch (example: `chore/restructure-to-addon`) and
  produce one logical commit per batch with a clear message describing the automation run.

- Review: Changes produced by automation require human review in a Pull Request before merge.

- Minimal side-effects: Scripts MUST avoid executing project code (no top-level imports that cause
  I/O) and should operate on text only unless explicitly approved.

- Logging & audit: Automation must produce a machine-readable report (JSON) summarizing files
  scanned, files changed, the diffs, auto-fixable counts, and errors encountered.

## 4. Guardrails

- Default conservative settings:

  - Skip files > 200 KiB
  - Process only `git ls-files` output
  - Use `--dry-run` as default; `--apply` must be explicit
  - Create backups when applying

- Safety-first import policy: When automation acts on Python code, it MUST NOT import repository
  packages that perform I/O at import-time. Use small pure text transformations or AST-only
  operations.

- Lint remediation policy:

  - `ruff --fix` MAY be used for trivially fixable rules (unused imports, f-string prefix removal,
    reformatting) but only within a small batch and after a dry-run.
  - Long-line (E501) remediation requires human review because line breaks can alter semantics
    (particularly in long string literals or SQL). When safe, prefer reflowing comments and
    splitting long expressions following established style.

- Test safety: After each automated batch, run a focused test import (or small pytest subset) to catch immediate import/runtime errors. Full test suites should run in CI before merge.

## 5. Machine-parseable validation block

The following token block must be included and used by CI hooks and tooling to authorize automated actions. CI should only permit automation when `AUTOMATION_ALLOWED` is present in the approved ADR token lists.

```yaml
TOKEN_BLOCK:
  accepted:
    - ADR_AUTOMATION_OK
    - ADR_MIGRATION_SAFE
  requires:
    - ADR-0001
  produces:
    - MIGRATION_REPORT_JSON
  drift:
    - DRIFT: automation_disabled
    - DRIFT: missing_backups
```

Validation rules:

- `ADR_AUTOMATION_OK` must be present to allow CI to run `--apply` mode.
- CI must validate `last_updated` and ADR_TOKEN presence before allowing `apply` runs.

## 6. Lifecycle & enforcement

- All automation runs must be reported in the repository (either as artifacts or committed
  backups) and referenced in the PR description.
- Non-compliant automation runs (missing backup files, missing token block, or no dry-run) are
  rejected by CI and flagged for manual review.

## 7. Examples

- Safe `ruff` usage (example): run `ruff check <dir> --format=json > ruff_report.json` then
  inspect `ruff_report.json`, run `ruff --fix <file>` per-file with backup and commit each change.

- Safe replacement usage: `scripts/fix_registry_paths.py --dry-run --include addon/` to preview a
  migration, then `--apply --backup` to write changes.

Last updated: 2025-09-22
