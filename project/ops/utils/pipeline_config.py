"""Compatibility stub for scripts.utils.pipeline_config.

Re-exports constants from addon.src.utils.pipeline_config to maintain
compatibility with legacy project ops scripts during ADR-0005 migration.
"""

from addon.src.utils.pipeline_config import *

# Re-export all constants for legacy compatibility
__all__ = [
    "AREA_REGISTRY",
    "ENTITY_SOURCE",
    "FLOOR_REGISTRY",
    "METRICS_FILE",
    "CANONICAL_DIR",
    "DERIVED_VIEWS_DIR",
    "OUTPUTS_DIR",
    "INPUTS_DIR",
    "LOGS_DIR",
    "SUPPORT_DIR",
    "DEFAULT_CONTRACT_PATH",
    "JOIN_CONTRACT",
    "OUTPUT_CONTRACT",
    "ENTITY_FLATMAP",
    "DEVICE_FLATMAP",
    "OMEGA_ROOM_REG",
]
