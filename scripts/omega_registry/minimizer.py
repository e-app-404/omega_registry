"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Minimization logic for omega registry entities.
Implements flatten_options_to_voice_assistants, strip_null_fields, contract_minimize_meta, enforce_allowlist.
"""

from scripts.utils.registry import (
    contract_minimize_meta,
    enforce_allowlist,
    flatten_options_to_voice_assistants,
    strip_null_fields,
)

__all__ = [
    "flatten_options_to_voice_assistants",
    "strip_null_fields",
    "contract_minimize_meta",
    "enforce_allowlist",
]
