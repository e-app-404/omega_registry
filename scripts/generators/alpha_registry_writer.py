"""Alpha registry writer helpers.

Provides a small, testable skeleton for writing per-domain alpha registries.

Contract validation is left pluggable via a validate_contract callable.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from scripts.utils import provenance

logger = logging.getLogger("omega_registry")


def normalize_output_shape(
    items: Iterable[Dict[str, Any]], top_key: Optional[str] = None
) -> Dict[str, Any]:
    """Normalize output to the documented container shape.

    If top_key is provided (for domain-specific shapes) the function will use it, otherwise
    it returns {"items": [...], "_meta": {...}}.
    """
    items_list = list(items)
    out: Dict[str, Any] = {
        "items": items_list,
        "_meta": {"count": len(items_list)},
    }
    if top_key:
        return {top_key: items_list, "_meta": {"count": len(items_list)}}
    return out


def write_alpha_registry(
    domain: str,
    items: Iterable[Dict[str, Any]],
    out_path: str | Path,
    contract_path: Optional[str | Path] = None,
    validate_contract: Optional[
        Callable[[Dict[str, Any], Optional[str | Path]], List[str]]
    ] = None,
    write_output: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Generate and optionally write an alpha registry for a domain.

    Args:
        domain: domain name (e.g., "sensor", "room", "lighting").
        items: iterable of entity dicts already enriched/normalized.
        out_path: destination file path to write when write_output=True.
        contract_path: optional contract YAML path (validator may use it).
        validate_contract: optional callable returning a list of validation error strings.
        write_output: if True, write the output file; otherwise operate in dry-run mode.
        strict: when True, validation failures will raise an Exception (exit non-zero intended).

    Returns:
        A dict containing metadata about the operation, e.g. {"written": bool, "errors": [...]}.
    """
    out_obj = normalize_output_shape(items, top_key=None)

    errors: List[str] = []
    if validate_contract:
        try:
            # the repo's validator expects the list of items rather than the whole container
            errors = validate_contract(out_obj.get("items", []), contract_path)
        except (
            Exception
        ) as exc:  # pragma: no cover - surface validator exceptions as errors
            errors = [f"contract-validator-exception: {exc}"]

    result: Dict[str, Any] = {
        "domain": domain,
        "count": len(out_obj.get("items", [])),
        "errors": errors,
    }

    json_bytes = json.dumps(out_obj, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    result["sha256"] = provenance.compute_sha256_bytes(json_bytes)

    if errors and strict:
        # In strict mode, surface validation errors immediately.
        raise RuntimeError(f"Contract validation failed for {domain}: {errors}")

    if write_output:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(json_bytes)
        result["written"] = True
    else:
        result["written"] = False

    # If there are contract errors, write a compliance report (audit) so operators can inspect.
    if errors:
        try:
            report_path = write_compliance_report(
                domain, errors, count=result.get("count", 0)
            )
            # expose the compliance report filename in the result for callers/tests
            result["compliance_report"] = str(report_path)
        except Exception as exc:
            logger.warning(
                f"Failed to write compliance report for {domain}: {exc}"
            )

    # Try to update provenance manifest; failure shouldn't break main flow
    try:
        # Use canonical manifest upsert so pipeline and writers share the same provenance format
        key = str(Path(out_path).absolute())
        entry = {
            "sha256": result["sha256"],
            "domain": domain,
            "updated_at": provenance.tz_now_iso(),
        }
        if result.get("compliance_report"):
            entry["compliance_report"] = result["compliance_report"]
        provenance.upsert_manifest_entry(key, entry)
    except Exception as exc:
        logger.warning(
            f"Failed to update provenance manifest for {out_path}: {exc}"
        )

    return result

    # Legacy local manifest writer removed — central provenance helpers used instead.


def write_compliance_report(
    domain: str, errors: List[str], count: int = 0
) -> Path:
    """Write a small compliance report into `canonical/logs/audit/contract_compliance/`.

    The report filename will include the domain and a short timestamp. This is intentionally
    small and human readable.
    """
    from datetime import datetime, timezone

    audit_dir_env = os.getenv("OMEGA_COMPLIANCE_DIR")
    if audit_dir_env:
        audit_dir = Path(audit_dir_env)
    else:
        audit_dir = Path("canonical/logs/audit/contract_compliance")

    audit_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat().replace(":", "-")
    report_path = audit_dir / f"{domain}_compliance_{ts}.json"
    payload = {
        "domain": domain,
        "count": count,
        "errors": errors,
        "timestamp": ts,
    }
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Return the path so callers can link the compliance report in provenance
    return report_path


__all__ = [
    "write_alpha_registry",
    "normalize_output_shape",
]


def make_validator_from_contract_module() -> Callable[
    [List[Dict[str, Any]], Optional[str | Path]], List[str]
]:
    """Return a callable that wraps the repo's contract.validate_entity_fields function.

    The returned callable matches the signature expected by write_alpha_registry: it accepts
    a list of entities and an optional contract_path and returns a list of error strings.
    """
    try:
        from scripts.omega_registry.contract import validate_entity_fields

        def validator(
            entities: List[Dict[str, Any]],
            contract_path: Optional[str | Path] = None,
        ) -> List[str]:
            try:
                # The repo validator raises on strict mode; call in non-strict mode to collect warnings
                validate_entity_fields(entities, strict=False)
                return []
            except Exception as exc:
                return [str(exc)]

        return validator
    except Exception:
        # Fallback: noop validator
        def noop_validator(
            entities: List[Dict[str, Any]],
            contract_path: Optional[str | Path] = None,
        ) -> List[str]:
            return []

        return noop_validator
