"""Compatibility shims for `scripts.enrich` package.

This module re-exports submodules from `project.ops.scripts.enrich.enrich` so
imports like `from addon.src.scripts.enrich import ...` work after the code
was reorganized per ADR-0005.
"""

try:
    from project.ops.scripts.enrich.enrich import (
        enrich_orchestrator as enrich_orchestrator,
    )
    from project.ops.scripts.enrich.enrich import normalize as normalize
    from project.ops.scripts.enrich.enrich import enrichers as enrichers

    __all__ = ["enrich_orchestrator", "normalize", "enrichers"]
except ImportError:
    # Graceful degradation if project modules aren't available
    __all__ = []
