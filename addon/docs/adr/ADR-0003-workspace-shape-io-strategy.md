---
id: ADR-0003
title: "ADR-0003: Workspace Shape and I/O Strategy"
date: 2025-09-22
status: Accepted
author:
  - "Evert Appels"
related:
  - ADR-0001
  - ADR-0002
supersedes: []
tags: ["workspace", "io", "testing", "adr", "policy", "automation"]
last_updated: 2025-09-22
---

# ADR-0003: Workspace Shape and I/O Strategy

## Table of Contents

1. Context
2. Decision
3. Workspace shape (folders and responsibilities)
4. I/O and import-time policy
5. Test & CI implications
6. Enforcement & lifecycle
7. Machine-parseable token block
8. Examples

## 1. Context

This project contains a mixture of production library code, developer utilities (scripts),
archived data and generated artifacts. Historically some scripts performed significant I/O at
import-time and repository-wide search/replace runs have risked scanning or modifying large
artifacts. This ADR defines a clear workspace layout and rules to avoid accidental I/O when
importing modules (important for tests, linters, and refactoring automation).

Goals:

- Make it safe to import library modules from tests and tooling without triggering heavy I/O.
- Keep developer scripts discoverable and runnable while isolating them from library imports.
- Provide a reproducible I/O strategy for inputs, outputs, and generated artifacts.

## 2. Decision

- Adopt a two-tier layout: `addon/` (production library and long-lived modules) and
  `addon/scripts/` (utility scripts and data-processing entry points). Tests and tooling must
  prefer importing pure library modules from `addon/` and avoid importing `addon/scripts/*`.
- Define canonical directories for data inputs and outputs and require all scripts to resolve
  paths via `addon/utils/paths.py` or equivalent helpers rather than hard-coded relative paths.
- Enforce an import-time I/O policy (see section 4) that disallows non-trivial I/O during
  module import for library modules. Scripts may perform I/O but must guard it behind `if __name__ == "__main__"` or factory functions.

## 3. Workspace shape (folders and responsibilities)

Canonical top-level layout (excerpt):

- `addon/` — production code, packages importable as `addon.*`.

  - `addon/registry/` — core registry library modules (pure functions, types).
  - `addon/utils/` — small pure helpers (path resolution, canonical helpers) safe to import.
  - `addon/scripts/` — CLI scripts and heavy I/O tools (should be non-imported by unit tests).
  - `addon/tests/` — tests for `addon/` modules (no test should import scripts that perform top-level I/O).

- `scripts/` — lightweight, pure test helpers or shims used by tests (safe to import).

- `addon/input/` — canonical location for input fixtures, not for transient large archive files.
- `addon/output/` — canonical output; scripts write here when producing derived artifacts.
- `tarballs/`, `backup/`, `registry/legacy/` — archives and legacy dumps; automation MUST skip these unless explicitly included.

Rules:

- Files in `addon/` must be safe to import in CI/test contexts (no top-level file opens or heavy network/DB calls).
- Long-running or I/O tasks belong in `addon/scripts/` and must be runnable via CLI (entrypoint guarded by `if __name__ == '__main__':`).
- Pure helper code intended for tests should live under `scripts/` (package marker `scripts/__init__.py`) to be easily imported without triggering heavy behavior.

## 4. I/O and import-time policy

Strict rules (enforced by CI checks where practical):

1. Library modules (any path under `addon/` that is imported by production code or tests):

   - MUST NOT perform non-trivial I/O at import time. Non-trivial I/O includes reading large files (>10KB by default), writing files, network calls, or launching subprocesses.
   - If a module needs configuration or paths, expose functions/classes that accept path arguments or a `load_config()` function that callers may call explicitly.

2. Scripts (under `addon/scripts/`):

   - May perform I/O at runtime, but MUST put immediate side-effects behind `main()` and `if __name__ == '__main__': main()` guards.
   - Must use `addon/utils/paths.py` (or equivalent) for canonical path resolution so automation can rewrite behavior centrally.

3. Test helpers and shims (under `scripts/`):

   - Should be pure, import-safe modules with minimal dependencies.

4. Automation scans and bulk operations:
   - Must operate only on `git ls-files` output and skip directories like `tarballs/`, `backup/`, and `registry/legacy/` by default.
   - Must skip files exceeding a configurable size threshold (default 200 KiB).

## 5. Test & CI implications

- CI must set `PYTHONPATH` to project root so `addon` modules import correctly.
- CI should run an import-safety check that attempts to import every `addon.*` module in a controlled subprocess with resource limits; modules that fail the import-safety check are flagged.
- Tests should not import `addon/scripts/*` directly. If a test requires behavior from a script, provide a small pure helper under `scripts/` that implements the function being tested.

Example import-safety check (conceptual):

```sh
# run in CI
python - <<'PY'
import importlib, pkgutil, sys
sys.path.insert(0, '.')
failed = []
for _, name, _ in pkgutil.walk_packages(['addon']):
    try:
        importlib.import_module('addon.' + name)
    except Exception as e:
        failed.append((name, str(e)))
print('failed imports:', failed)
PY
```

## 6. Enforcement & lifecycle

- Violations (modules performing import-time I/O) are treated as quality defects. CI will open an issue or fail the job until a follow-up ADR/patch removes the I/O or relocates the behavior to a script.
- Periodic audit: run import-safety and automation-safety scans quarterly (or on major refactors) and record results in the ADR index.

## 7. Machine-parseable token block

```yaml
TOKEN_BLOCK:
  accepted:
    - ADR_WORKSPACE_IO_OK
    - ADR_AUTOMATION_OK
  requires:
    - ADR-0001
    - ADR-0002
  produces:
    - IMPORT_SAFETY_REPORT
  drift:
    - DRIFT: import_time_io_detected
    - DRIFT: scripts_unimportable
```

## 8. Examples & migration notes

- If a module needs to read `addon/input/some.json` during development, prefer:

```py
def load_my_data(path=None):
    if path is None:
        path = get_input_path('some.json')
    with open(path) as f:
        return json.load(f)

if __name__ == '__main__':
    data = load_my_data()
    # do heavy processing
```

- During migration, use `scripts/fix_registry_paths.py` to update canonical path helpers and only run `--apply` after a reviewed dry-run.

Last updated: 2025-09-22
