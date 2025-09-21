#!/usr/bin/env python3
"""
venv_standardize.py — Helper to standardize virtualenv usage in this repo.

This script is intentionally conservative and non-destructive by default.
It can perform these actions:
 - verify existing venvs (repo-level `venv`, repo root `.venv`, addon/.venv)
 - optionally create a `.venv` at repo root by copying/pointing to `venv` (or creating a symlink)
 - update `omega_registry.code-workspace` to point `python.defaultInterpreterPath` to `.venv/bin/python` (if requested)

Usage:
  python3 addon/scripts/venv_standardize.py --status
  python3 addon/scripts/venv_standardize.py --make-dotvenv [--symlink]
  python3 addon/scripts/venv_standardize.py --update-workspace

The script is deliberately explicit; it prints commands to run for the maintainers and can perform safe filesystem ops when flags are provided.
"""

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_FILE = REPO_ROOT / "omega_registry.code-workspace"


def find_venvs():
    candidates = {}
    for name in ("venv", ".venv", "addon/venv", "addon/.venv"):
        p = REPO_ROOT / name
        candidates[name] = p if p.exists() else None
    return candidates


def status():
    print("Repository root:", REPO_ROOT)
    venvs = find_venvs()
    for k, p in venvs.items():
        print(f"{k}: {'present at ' + str(p) if p else 'missing'}")
    if WORKSPACE_FILE.exists():
        print("\nWorkspace file present at", WORKSPACE_FILE)
        data = WORKSPACE_FILE.read_text()
        # print a small excerpt mentioning python.defaultInterpreterPath
        if "python.defaultInterpreterPath" in data:
            for line in data.splitlines():
                if "python.defaultInterpreterPath" in line:
                    print("workspace:", line.strip())
                    break
    else:
        print("\nNo workspace file found at", WORKSPACE_FILE)


def make_dotvenv(symlink=False):
    dotvenv = REPO_ROOT / ".venv"
    repo_venv = REPO_ROOT / "venv"
    if dotvenv.exists():
        print(".venv already exists at", dotvenv)
        return 0
    if not repo_venv.exists():
        print(
            "repo venv missing at",
            repo_venv,
            "\nPlease create it first: python3 -m venv .venv or python3 -m venv venv",
        )
        return 2
    if symlink:
        print("Creating symlink .venv -> venv")
        dotvenv.symlink_to(repo_venv, target_is_directory=True)
        print("Symlink created:", dotvenv, "->", repo_venv)
    else:
        # create a small wrapper that points to the venv - we avoid copying the whole env
        print(
            "Creating .venv as a small marker to reuse venv; this is conservative so we will symlink by default"
        )
        dotvenv.symlink_to(repo_venv, target_is_directory=True)
        print("Created .venv -> venv")
    return 0


def update_workspace_interpreter():
    if not WORKSPACE_FILE.exists():
        print("Workspace file not found:", WORKSPACE_FILE)
        return 2
    data = WORKSPACE_FILE.read_text()
    try:
        # file is jsonc; attempt a simple replace for the python.defaultInterpreterPath line
        new_path = str(REPO_ROOT / ".venv" / "bin" / "python")
        if "python.defaultInterpreterPath" in data:
            out = []
            for line in data.splitlines():
                if "python.defaultInterpreterPath" in line:
                    indent = line.split('"')[0]
                    out.append(
                        f'{indent}"python.defaultInterpreterPath": "{new_path}",'
                    )
                else:
                    out.append(line)
            WORKSPACE_FILE.write_text("\n".join(out) + "\n")
            print("Updated python.defaultInterpreterPath to", new_path)
            return 0
        else:
            print(
                "No python.defaultInterpreterPath found in workspace — skipping"
            )
            return 1
    except Exception as e:
        print("Failed to update workspace:", e)
        return 3


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true")
    p.add_argument("--make-dotvenv", action="store_true")
    p.add_argument("--symlink", action="store_true")
    p.add_argument("--update-workspace", action="store_true")
    args = p.parse_args()

    if args.status:
        status()
        return
    if args.make_dotvenv:
        rc = make_dotvenv(symlink=args.symlink)
        return rc
    if args.update_workspace:
        return update_workspace_interpreter()

    p.print_help()


if __name__ == "__main__":
    raise SystemExit(main())
