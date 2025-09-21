
# Audit Script: audit_cluster_coverage.py

## Purpose

Implements a standalone audit to evaluate which clusterable entities are missing from the alpha sensor registry. It:

- Loads all entities from `core.entity_registry`
- Loads all clusters from `alpha_sensor_registry.json`
- Loads all pattern rules from `settings.conf.yaml` (`role_inference_rules`)
- Determines which entities are clusterable by matching entity_id to role inference rules
- Compares to see which are already included in a cluster
- Emits:
  - `output/unclustered_entity_trace.json`: missing post_reboot_entity_ids with role and metadata
  - `output/cluster_coverage_metrics.json`: count of total clusterable, clustered, unclustered, and % coverage
- Logs summary and paths in `conversation_full_history.log` under `[SCRIPT_RUN audit_cluster_coverage]`

## Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)

## References

- See `scripts/audit_cluster_coverage.py` for implementation details
- See `settings.conf.yaml` for role inference rules

---
