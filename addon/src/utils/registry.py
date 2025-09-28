"""Compatibility shim: re-export registry helpers from deeper utils.registry module.

This shim keeps older imports (`addon.src.utils.registry`) working while the
canonical implementation lives under `addon/src/utils/utils/registry.py`.
"""

from addon.src.utils.utils.registry import (
    write_json_compact,
    minimize_registry_entity,
    minimize_registry,
)

__all__ = [
    "write_json_compact",
    "minimize_registry_entity",
    "minimize_registry",
]
