"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Shared utilities for omega registry generator.
Includes conflict_id generator and timestamp helpers.
"""

from datetime import datetime


def generate_conflict_id(entity_id):
    return "sha256-" + (entity_id or "none")


def current_timestamp():
    return datetime.now().isoformat()
