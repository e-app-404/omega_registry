# omega_registry

This repository contains the canonical omega registry artifacts and pipeline for generating and maintaining Home Assistant registry data. It is intentionally self-contained and does not connect to a live Home Assistant instance.

## Quickstart

1. Create a virtual environment:

   `python3 -m venv .venv`
   `source .venv/bin/activate`

2. Install dependencies:

   `pip install -r requirements.txt`

3. Common tasks:

   - `make venv` — create virtualenv
   - `make install` — install requirements
   - `make lint` — run linters (flake8/ruff)
   - `make test` — run tests

## Safety

This project does not write to your live Home Assistant configuration. Do not run any script that writes to `/config` or `.storage/` unless you have explicitly reviewed it.

## Structure

- `addon/` — main pipeline (previously `registry_rehydration_local_last`)
- `canonical/` — canonical registry outputs and contracts
- `scripts/` — pipeline scripts and utilities
- `data/` — sample data and pipeline artifacts
- `docs/` — documentation

If you plan to restructure (rename `registry_rehydration_local_last` → `addon`), follow the migration plan in `WORKSPACE_README.md` and perform moves on a feature branch with a backup tarball.

\*\*\* End of README
