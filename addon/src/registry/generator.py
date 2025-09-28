"""Compatibility shim for the registry generator.

Re-export the `generate` function from the canonical `registry.omega_registry` package.
"""

from .omega_registry.generator import generate

__all__ = ["generate"]
