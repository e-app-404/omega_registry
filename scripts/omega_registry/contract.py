"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Contract parsing for omega registry output.
Parses omega_registry_master.output_contract.yaml and exposes get_allowlist().
PATCH-OMEGA-PIPELINE-DEBUG-LOGGING-V1: Adds get_required_keys and expand_contract_if_missing for contract validation and expansion.
"""

import logging

import yaml


def parse_contract(contract_path):
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    required = contract.get("required_keys", [])
    optional = contract.get("optional_keys", [])
    return required, optional


def get_allowlist(contract_path):
    required, optional = parse_contract(contract_path)
    return required + optional


def get_required_keys(contract_path):
    required, _ = parse_contract(contract_path)
    return required


def expand_contract_if_missing(contract_path, missing_keys):
    # Log discrepancies and optionally update contract
    logger = logging.getLogger("omega_registry")
    if not missing_keys:
        return
    logger.warning(
        f"PATCH-OMEGA-PIPELINE-DEBUG-LOGGING-V1: Expanding contract {contract_path} with missing keys: {missing_keys}"
    )
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    required = contract.get("required_keys", [])
    updated = False
    for k in missing_keys:
        if k not in required:
            required.append(k)
            updated = True
    if updated:
        contract["required_keys"] = required
        with open(contract_path, "w") as f:
            yaml.safe_dump(contract, f)
        logger.info(
            f"Contract {contract_path} updated with new required_keys: {required}"
        )
    else:
        logger.info("No contract update needed; all keys present.")


def validate_entity_fields(entities, strict=False):
    required_fields = ["entity_id", "platform", "device_id", "area_id"]
    for e in entities:
        for field in required_fields:
            if field not in e:
                msg = f"[ERROR] Missing required field: {field} in {e.get('entity_id')}"
                if strict:
                    raise Exception(msg)
                else:
                    logging.warning(msg)
