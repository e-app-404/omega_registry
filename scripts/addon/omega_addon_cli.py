"""Minimal add-on CLI wrapper for Omega Registry.

Provides small, safe wrapper commands to run generation and dry-run enrichment.
This wrapper intentionally keeps behavior minimal and defers heavy I/O flags
to the underlying generator functions. It uses the existing code paths.
"""

import argparse
import json
import os
from pathlib import Path

from scripts.utils import pipeline_config as cfg


def call_generate(
    output=None,
    contract=None,
    inputs=None,
    strict=False,
    profile=None,
    write_output=False,
):
    # Import the generator function lazily to avoid side-effects at import time
    from scripts.omega_registry.generator import generate

    # Determine defaults from pipeline_config
    output_path = output or str(cfg.OUTPUTS_DIR / "omega_registry_master.json")
    contract_path = contract or str(cfg.OUTPUT_CONTRACT)
    if inputs:
        input_paths = inputs
    else:
        # default: read registry_inputs dir listing
        inputs_dir = Path(cfg.INPUTS_DIR)
        if inputs_dir.exists():
            input_paths = [str(inputs_dir / p) for p in os.listdir(inputs_dir)]
        else:
            input_paths = []
    # Respect read_only behavior: if write_output is False, write to a temp path
    if not write_output:
        tmp_dir = Path("/tmp/omega_addon")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(tmp_dir / Path(output_path).name)
    print(
        f"[addon-cli] Running generate(output={output_path}, contract={contract_path}, inputs={input_paths}, profile={profile}, strict={strict})"
    )
    generate(output_path, contract_path, input_paths, strict=strict, profile=profile)
    # Read back the produced file and print summary
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = None
    if data is None:
        print("[addon-cli] No output produced (check logs).")
        return 1
    if isinstance(data, dict) and "rooms" in data:
        count = len(data["rooms"])
    elif isinstance(data, list):
        count = len(data)
    else:
        count = 0
    print(f"[addon-cli] Generated {count} top-level entities/rooms.")
    return 0


def call_dry_run(inputs=None, enable_synthetic=False):
    """Perform a dry-run enrichment and synthetic impact estimate without writing canonical files.
    Uses the enrichment orchestrator to process inputs and prints a small JSON summary to stdout.
    """
    # Lazy imports
    from scripts.enrich.enrich_orchestrator import run_enrichment_pipeline
    from scripts.utils.loaders import load_json_with_extract

    # Load inputs
    input_paths = inputs or []
    entities = []
    for p in input_paths:
        entities.extend(load_json_with_extract(p))
    summary = {
        "input_count": len(entities),
        "synthetic_enabled": bool(enable_synthetic),
        "processed": 0,
        "skipped_non_dict": 0,
    }
    # Minimal context from pipeline_config
    # Note: pipeline_config not needed in dry-run summary; keep context minimal
    context = {
        "device_registry": {},
        "area_registry": {},
        "config_registry": {},
        "lookups": {},
        "join_chains": {},
        "join_stats": {},
        "join_blocked": {},
    }
    processed = 0
    for ent in entities:
        if not isinstance(ent, dict):
            summary["skipped_non_dict"] += 1
            continue
        try:
            # run enrichment for side-effects and estimation only; we don't keep the result here
            _ = run_enrichment_pipeline(ent, context)
            processed += 1
        except Exception as e:
            print(f"[addon-cli] Warning: enricher raised: {e}")
    summary["processed"] = processed
    print(json.dumps(summary, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="omega_addon_cli", description="Minimal Omega Registry Addon CLI"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_gen = sub.add_parser(
        "generate", help="Run full generator (respects write_output flag)"
    )
    p_gen.add_argument("--output", help="Output path")
    p_gen.add_argument("--contract", help="Contract path")
    p_gen.add_argument("--inputs", nargs="+", help="Input files (override)")
    p_gen.add_argument("--profile", help="Output profile")
    p_gen.add_argument("--strict", action="store_true", help="Strict validation")
    p_gen.add_argument(
        "--write-output",
        action="store_true",
        help="Allow writing into canonical output path",
    )

    p_dry = sub.add_parser(
        "dry-run", help="Run a dry-run enrichment (no canonical writes)"
    )
    p_dry.add_argument("--inputs", nargs="+", help="Input files (override)")
    p_dry.add_argument(
        "--synthetic",
        action="store_true",
        help="Enable synthetic device creation in dry-run",
    )

    args = parser.parse_args()
    if args.cmd == "generate":
        return call_generate(
            output=args.output,
            contract=args.contract,
            inputs=args.inputs,
            strict=args.strict,
            profile=args.profile,
            write_output=args.write_output,
        )
    elif args.cmd == "dry-run":
        inputs = args.inputs or []
        return call_dry_run(inputs=inputs, enable_synthetic=args.synthetic)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
