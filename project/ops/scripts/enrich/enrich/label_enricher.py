"""
label_enricher.py

Enricher for human-readable label attribution.
Implements Directive D: Label Attribution Heuristic.
"""

import logging
import re

logger = logging.getLogger(__name__)


def clean_label(name):
    # Lowercase, replace underscores/camel case, remove special chars
    if not name:
        return None
    # Replace underscores and hyphens with space
    label = re.sub(r"[_\-]+", " ", name)
    # Split camel case
    label = re.sub(r"(?<!^)(?=[A-Z])", " ", label)
    # Lowercase
    label = label.lower()
    # Remove non-alphanumeric except space
    label = re.sub(r"[^a-z0-9 ]+", "", label)
    # Collapse whitespace
    label = re.sub(r"\s+", " ", label).strip()
    return label


def enrich_labels(entity):
    # Do not override existing labels
    if "labels" in entity and entity["labels"]:
        logger.debug(
            f"Entity {entity.get('entity_id')} already has labels, skipping label_enricher."
        )
        return entity
    name = entity.get("resolved_name") or entity.get("original_name")
    labels = []
    if name:
        cleaned = clean_label(name)
        if cleaned:
            labels.append(cleaned)
    # Optionally add domain/platform if present
    for key in ("domain", "platform"):
        val = entity.get(key)
        if val and val not in labels:
            labels.append(str(val).lower())
    # Ensure non-empty
    if labels:
        entity["labels"] = labels
        # Annotate _meta.inferred_fields
        meta = entity.setdefault("_meta", {})
        inferred = meta.setdefault("inferred_fields", {})
        inferred["labels"] = {
            "source": "label_enricher_heuristic",
            "inputs": {
                "resolved_name": entity.get("resolved_name"),
                "original_name": entity.get("original_name"),
                "domain": entity.get("domain"),
                "platform": entity.get("platform"),
            },
        }
        logger.debug(f"Entity {entity.get('entity_id')} assigned labels: {labels}")
    else:
        logger.warning(f"Entity {entity.get('entity_id')} could not generate labels.")
    return entity
