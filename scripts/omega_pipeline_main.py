#!/usr/bin/env python3
"""
OMEGA-PIPELINE-MAIN: Canonical entrypoint for full Omega Registry generation.
Replaces all previous generator scripts.
"""

import os
import sys
import traceback

from scripts.utils import pipeline_config as cfg
from scripts.utils import provenance

print("==== EXECUTION VERIFICATION ====")
print("Script path:", __file__)
print("Absolute script path:", os.path.abspath(__file__))
print("Python executable:", sys.executable)
print("Args received:", sys.argv)
print("sys.path:", sys.path)
print("--- First 40 lines of this script ---")
with open(os.path.abspath(__file__), "r") as f:
    for i in range(40):
        print(f.readline().rstrip())
print("--- END SCRIPT DUMP ---")
print("[DIAG] Printing stack trace before argparse setup:")
traceback.print_stack()
print("[DIAG] Modules loaded before argparse:")
for name, mod in sorted(sys.modules.items()):
    print(f"{name}: {getattr(mod, '__file__', None)}")
print("Argparse will now parse --contract and --strict correctly.")
print("================================")
from scripts.utils.import_path import set_workspace_root

set_workspace_root(__file__)
import argparse

from scripts.omega_registry.generator import generate

print(
    "[DIAG] generate function loaded from:",
    generate.__module__,
    getattr(generate, "__file__", "NO __file__"),
)
import logging

from scripts.utils.registry_inputs import get_registry_input_files

logging.basicConfig(level=logging.DEBUG)
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.utils.logging import setup_logging

LOG_PATH = cfg.PIPELINE_LOG
setup_logging(LOG_PATH)


def main():
    parser = argparse.ArgumentParser(
        description="Generate omega_registry_master.json (future-proof pipeline)"
    )
    parser.add_argument(
        "--output",
        required=False,
        default="canonical/omega_registry_master.json",
        help="Output path for omega_registry_master.json (canonical)",
    )
    parser.add_argument(
        "--output-version",
        help="Optional versioned output path (e.g., registry_alias/enriched.v1.json)",
    )
    parser.add_argument(
        "--contract",
        required=False,
        default="canonical/support/manifests/enrichment_manifest.omega.yaml",
        help="Path to output contract YAML",
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        help="Input entity registry files (overrides default)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce required field validation strictly (raise on error)",
    )
    parser.add_argument(
        "--output-profile",
        type=str,
        default=None,
        help="Output profile: slim, default, audit (default: default)",
    )
    parser.add_argument(
        "--with-analytics",
        action="store_true",
        default=True,
        help="Run analytics after registry generation (default: True)",
    )
    parser.add_argument(
        "--emit-alpha",
        action="store_true",
        default=False,
        help="Emit per-domain alpha registries via writer (dry-run by default)",
    )
    parser.add_argument(
        "--emit-alpha-write",
        action="store_true",
        default=False,
        help="When used with --emit-alpha, actually write alpha registry files to disk",
    )
    parser.add_argument(
        "--alpha-mode",
        choices=["off", "dry", "write"],
        default="off",
        help=(
            "Alpha emission mode: 'off' (no alpha outputs), 'dry' (emit but do not write), "
            "or 'write' (emit and write alpha registries). Legacy flags --emit-alpha/--emit-alpha-write "
            "are still accepted and will take precedence if provided."
        ),
    )
    args = parser.parse_args()
    logging.info("Starting omega_pipeline_main.py run.")
    if args.inputs:
        input_files = args.inputs
    else:
        input_files = get_registry_input_files()
    # Log input files and contract with hashes
    for f in input_files + [args.contract]:
        try:
            logging.info(
                f"[PROVENANCE] Input: {os.path.abspath(f)} SHA256={provenance.file_sha256(f)}"
            )
        except Exception as e:
            logging.warning(f"[PROVENANCE] Could not hash input {f}: {e}")
    # Determine emit_alpha / emit_alpha_write from new --alpha-mode with legacy override support
    emit_alpha = False
    emit_alpha_write = False
    # Legacy flags still honored if explicitly used
    if getattr(args, "emit_alpha", False):
        emit_alpha = True
        emit_alpha_write = getattr(args, "emit_alpha_write", False)
    else:
        if args.alpha_mode == "dry":
            emit_alpha = True
            emit_alpha_write = False
        elif args.alpha_mode == "write":
            emit_alpha = True
            emit_alpha_write = True

    result = generate(
        args.output,
        args.contract,
        input_files,
        strict=args.strict,
        profile=args.output_profile or "default",
        emit_alpha=emit_alpha,
        emit_alpha_write=emit_alpha_write,
    )
    # Log output file(s) and pretty print
    output_files = [args.output]
    output_provenance = [
        {
            "path": os.path.abspath(args.output),
            "phase": "generator.py:write_registry",
        }
    ]
    # If generator returned extra outputs (e.g., alpha registries), include them in the provenance lists
    try:
        if isinstance(result, dict):
            extra = result.get("extra_outputs") or []
            for eo in extra:
                # eo is expected to contain absolute 'path', 'sha256', 'phase', and optional 'compliance_report'
                prov_entry = {
                    "path": eo.get("path"),
                    "phase": eo.get("phase", "alpha"),
                }
                if eo.get("compliance_report"):
                    prov_entry["compliance_report"] = eo.get(
                        "compliance_report"
                    )
                output_provenance.append(prov_entry)
                output_files.append(eo.get("path"))
    except Exception:
        logging.warning(
            "Could not merge generator extra_outputs into provenance lists"
        )
    if args.output == "canonical/omega_registry_master.json":
        pretty_path = "canonical/omega_registry_master.pretty.json"
        output_files.append(pretty_path)
    hydrated_json = "canonical/derived_views/hydrated_entities.json"
    hydrated_pretty = "canonical/derived_views/hydrated_entities.pretty.json"
    enriched_registry = "canonical/derived_views/enriched_registry.json"

    for f, phase in [
        (hydrated_json, "enrichment_engine.py:hydration output"),
        (hydrated_pretty, "enrichment_engine.py:hydration output (pretty)"),
        (enriched_registry, "enrichment_engine.py:enriched output"),
    ]:
        if os.path.exists(f):
            output_files.append(f)
            output_provenance.append(
                {"path": os.path.abspath(f), "phase": phase}
            )
    for f in output_files:
        try:
            logging.info(
                f"[PROVENANCE] Output: {os.path.abspath(f)} SHA256={provenance.file_sha256(f)}"
            )
        except Exception as e:
            logging.warning(f"[PROVENANCE] Could not hash output {f}: {e}")
    # Audit device_id and area_id propagation in output
    try:
        with open(args.output, "r") as f:
            entities = json.load(f)
        missing_device = [
            e["entity_id"] for e in entities if not e.get("device_id")
        ]
        missing_area = [
            e["entity_id"] for e in entities if not e.get("area_id")
        ]
        missing_tier = [
            e["entity_id"]
            for e in entities
            if (not e.get("tier"))
            or (str(e.get("tier")).lower() in ["none", "null", "unclassified"])
        ]
        # Build normalized_alpha from outputs (those with 'alpha' in the phase)
        normalized_alpha = [
            p
            for p in output_provenance
            if "alpha" in (p.get("phase") or "").lower()
        ]

        # Attempt to read the writer's provenance manifest (it may be overridden by OMEGA_PROVENANCE_MANIFEST)
        writer_manifest_path = (
            os.getenv("OMEGA_PROVENANCE_MANIFEST")
            or "canonical/omega_registry_master.provenance.json"
        )
        writer_manifest = {}
        try:
            if writer_manifest_path and os.path.exists(writer_manifest_path):
                with open(writer_manifest_path, "r", encoding="utf-8") as wf:
                    writer_manifest = json.load(wf)
        except Exception:
            writer_manifest = {}

        # Enrich normalized_alpha entries with updated_at from writer_manifest when available
        enriched_alpha = []
        for p in normalized_alpha:
            entry = dict(p)
            path_key = entry.get("path")
            updated_at = None
            if path_key:
                candidates = [path_key]
                # try repo-relative and absolute variants
                try:
                    candidates.append(
                        str(Path(path_key).relative_to(Path.cwd()))
                    )
                except Exception:
                    pass
                try:
                    candidates.append(str(Path(path_key).absolute()))
                except Exception:
                    pass
                for c in candidates:
                    if c and c in writer_manifest:
                        updated_at = writer_manifest[c].get("updated_at")
                        break
            if updated_at:
                entry["updated_at"] = updated_at
            enriched_alpha.append(entry)

        # Compute alpha_summary: count and latest_written_at (from updated_at values)
        alpha_summary = {
            "count": len(enriched_alpha),
            "latest_written_at": None,
        }
        try:
            latest_dt = None
            for eo in enriched_alpha:
                ts = eo.get("updated_at")
                if not ts:
                    continue
                try:
                    dt = datetime.fromisoformat(ts)
                    if latest_dt is None or dt > latest_dt:
                        latest_dt = dt
                except Exception:
                    continue
            if latest_dt:
                alpha_summary["latest_written_at"] = latest_dt.astimezone(
                    timezone.utc
                ).isoformat()
        except Exception:
            pass

        logging.info(
            f"[AUDIT] {len(missing_area)} entities missing area_id: {missing_area[:5]}"
        )
        logging.info(
            f"[AUDIT] {len(missing_tier)} entities missing tier: {missing_tier[:5]}"
        )
        print(
            f"[AUDIT] {len(missing_device)} entities missing device_id, {len(missing_area)} missing area_id, {len(missing_tier)} missing tier."
        )
    except Exception as e:
        logging.warning(f"[AUDIT] Could not audit output: {e}")
        normalized_alpha = []
        enriched_alpha = []
        alpha_summary = {"count": 0, "latest_written_at": None}
    # Write provenance manifest
    try:
        manifest = {
            "inputs": [
                {
                    "path": os.path.abspath(f),
                    "sha256": provenance.file_sha256(f),
                }
                for f in input_files + [args.contract]
            ],
            "outputs": [
                {
                    "path": p["path"],
                    "sha256": provenance.file_sha256(p["path"]),
                    "phase": p["phase"],
                    **(
                        {"compliance_report": p.get("compliance_report")}
                        if p.get("compliance_report")
                        else {}
                    ),
                }
                for p in output_provenance
            ],
            # Make alpha_outputs entries self-contained (include sha256, compliance_report and updated_at if present)
            "alpha_outputs": [
                {
                    "path": ea.get("path"),
                    "sha256": (
                        provenance.file_sha256(ea.get("path"))
                        if ea.get("path") and os.path.exists(ea.get("path"))
                        else None
                    ),
                    "phase": ea.get("phase"),
                    **(
                        {"compliance_report": ea.get("compliance_report")}
                        if ea.get("compliance_report")
                        else {}
                    ),
                    **(
                        {"updated_at": ea.get("updated_at")}
                        if ea.get("updated_at")
                        else {}
                    ),
                }
                for ea in enriched_alpha
            ],
            "alpha_summary": alpha_summary,
        }
        manifest_path = "canonical/omega_registry_master.provenance.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logging.info(f"[PROVENANCE] Wrote provenance manifest: {manifest_path}")
    except Exception as e:
        logging.warning(
            f"[PROVENANCE] Could not write provenance manifest: {e}"
        )

    # --- ANALYTICS POST-PROCESSING ---
    analytics_outputs = []
    analytics_run = False
    if args.with_analytics:
        try:
            analytics_script = os.path.join(
                os.path.dirname(__file__),
                "analytics",
                "analyze_omega_registry.py",
            )
            # Prefer audit output if present, else use main output
            audit_output = "canonical/omega_registry_master.audit.json"
            analytics_input = (
                audit_output if os.path.exists(audit_output) else args.output
            )
            analytics_log = (
                "canonical/logs/analytics/analyze_omega_registry.latest.json"
            )
            metrics_path = (
                "canonical/logs/analytics/pipeline_metrics.latest.json"
            )
            cmd = [
                sys.executable,
                analytics_script,
                "--input",
                analytics_input,
                "--log",
                analytics_log,
            ]
            logging.info(f"[ANALYTICS] Running analytics: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            logging.info("[ANALYTICS] Registry analysis completed.")
            # Record analytics outputs
            for analytics_file, phase in [
                (analytics_log, "analyze_omega_registry.py:analytics log"),
                (metrics_path, "analyze_omega_registry.py:pipeline metrics"),
            ]:
                if os.path.exists(analytics_file):
                    analytics_outputs.append(
                        {
                            "path": os.path.abspath(analytics_file),
                            "sha256": provenance.file_sha256(analytics_file),
                            "phase": phase,
                        }
                    )
            analytics_run = True
        except Exception as e:
            logging.error(f"[ANALYTICS] Analytics step failed: {e}")
            analytics_run = False
    # --- Update provenance manifest with analytics outputs ---
    try:
        # Load, update, and rewrite manifest
        manifest_path = "canonical/omega_registry_master.provenance.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        if analytics_outputs:
            manifest.setdefault("outputs", []).extend(analytics_outputs)
        manifest["analytics_run"] = analytics_run
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logging.info(
            f"[PROVENANCE] Updated provenance manifest with analytics: {manifest_path}"
        )
    except Exception as e:
        logging.warning(
            f"[PROVENANCE] Could not update provenance manifest with analytics: {e}"
        )


if __name__ == "__main__":
    main()
