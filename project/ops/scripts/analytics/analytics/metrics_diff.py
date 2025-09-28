#!/usr/bin/env python3
# Run with: python -m scripts.analytics.metrics_diff
"""
PATCH: METRICS-DIFF-CHECKER-V1
Compares two pipeline_metrics.json files and surfaces regressions or key metric changes.
Integrates with shared utils. TODO: Update README and manifest for diagnostics tools.
"""
import json
import logging
import sys
from datetime import datetime, timezone

from scripts.utils.logging import setup_logging

setup_logging("canonical/logs/diagnostics/metrics_diff.log")
logging.info("Starting metrics_diff.py run.")

DEFAULT_KEYS_TO_COMPARE = [
    "tier_distribution",
    "device_class_distribution",
    "domain_coverage_by_tier",
    "cluster_sizes_by_area",
]

TRACE_OVERLAY_PATH = "canonical/logs/diagnostics/trace_overlay.omega.json"
TRACE_DEBUG_OVERLAY_PATH = "canonical/logs/diagnostics/trace_debug_overlay.json"


def load_metrics(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def diff_dicts(old, new):
    changes = {}
    keys = set(old.keys()) | set(new.keys())
    for key in keys:
        old_val = old.get(key, 0)
        new_val = new.get(key, 0)
        if old_val != new_val:
            changes[key] = {"from": old_val, "to": new_val}
    return changes


def compare_metrics(old, new, keys):
    report = {}
    for key in keys:
        if key not in old or key not in new:
            continue
        diff = diff_dicts(old[key], new[key])
        if diff:
            report[key] = diff
    return report


def emit_report(diff_report, out_path):
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "timestamp": now,
        "summary": {
            "changed_sections": list(diff_report.keys()),
            "total_changes": sum(len(v) for v in diff_report.values()),
        },
        "diff": diff_report,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✅ Diff report written to {out_path}")


# TODO: Update README and manifest to document metrics_diff.py and diagnostics outputs.


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python metrics_diff.py <old_metrics.json> <new_metrics.json> <output_diff.json>"
        )
        sys.exit(1)
    old_path, new_path, out_path = sys.argv[1:]
    old_metrics = load_metrics(old_path)
    new_metrics = load_metrics(new_path)
    diffs = compare_metrics(old_metrics, new_metrics, DEFAULT_KEYS_TO_COMPARE)
    emit_report(diffs, out_path)


if __name__ == "__main__":
    main()
