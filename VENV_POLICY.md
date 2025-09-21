Venv policy for omega_registry

This repository should have one canonical virtual environment used for running scripts and Makefile targets: `.venv` at the repo root.

- Developers may also find local `venv` or `addon/.venv`; the goal is to normalize on `.venv` (repo root) so tooling and the Makefile are consistent.
- Use the helper script `addon/scripts/venv_standardize.py` to inspect venvs, create a `.venv` that points to `venv` (non-destructive symlink), and update `omega_registry.code-workspace`'s `python.defaultInterpreterPath` to the canonical `.venv` interpreter.

Quick commands

```bash
# from repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r addon/requirements.txt
```

Notes

- The script `addon/scripts/venv_standardize.py` is intentionally conservative. It will not copy or delete virtualenv contents unless you explicitly request symlink creation.
- Historical pipeline snapshots or data files may still reference absolute paths to old venv locations; those files are considered historical and should be left intact unless you want to perform an explicit, tracked update.
