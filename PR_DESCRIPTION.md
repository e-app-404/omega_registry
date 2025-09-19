Title: Consolidate provenance helpers, add tests, and normalize alpha CLI

Summary
-------
This change set centralizes provenance helpers in `scripts/utils/provenance.py`,
adds unit tests for the provenance utilities, normalizes alpha emission CLI flags
to a single `--alpha-mode` option (with legacy `--emit-alpha`/`--emit-alpha-write`
still accepted), and includes minor fixes discovered while running the full
test-suite (area/tier enricher mapping and null_fields handling during
minimization).

Files changed / added
- scripts/utils/provenance.py (existing) — used by writers and pipeline
- scripts/utils/tests/test_provenance.py (new) — pytest unit tests for provenance
- scripts/omega_pipeline_main.py (modified) — add `--alpha-mode`, map to emit flags
- scripts/omega_registry/generator.py (modified) — accept `--alpha-mode` parity
- scripts/enrich/enrichers/area_floor_enricher.py (fix) — area key lookup uses `area_id`
- scripts/enrich/enrichers/tier_enricher.py (fix) — normalize `join_origin` to `tier_enricher`
- scripts/utils/registry.py (fix) — preserve `null_fields` into `_meta` during minimization

Testing
-------
- Ran full test-suite: `PYTHONPATH=. venv/bin/python3 -m pytest -q` — all tests passed (28 passed, 1 skipped).
- Ran the pipeline locally with `--alpha-mode write` to verify runtime behavior.

Notes / rationale
-----------------
- `--alpha-mode` provides a clearer single control for alpha emission: off/dry/write.
  Legacy flags are still supported to avoid breaking existing invocations.
- Provenance helpers are tested to avoid regressions in hashing, timestamps, and manifest I/O.
- The minor fixes to enrichers/minimizer were necessary to keep unit tests stable after consolidation.

Follow-ups
----------
- If you want, I can implement a small file-lock on `upsert_manifest_entry` to make concurrent writer updates safe.
- I can also prepare a proper Git branch/PR if the repository `git` metadata is available in your environment; right now git operations failed because `.git` wasn't found.
