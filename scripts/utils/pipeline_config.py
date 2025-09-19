import logging
import os
from pathlib import Path

import yaml

# === BASE DIRECTORIES ===
CANONICAL_DIR = Path("canonical")
SUPPORT_DIR = CANONICAL_DIR / "support"
INPUTS_DIR = CANONICAL_DIR / "registry_inputs"
OUTPUTS_DIR = CANONICAL_DIR / "outputs"
LOGS_DIR = CANONICAL_DIR / "logs"
DERIVED_VIEWS_DIR = CANONICAL_DIR / "derived_views"
ENRICHMENT_SOURCES_DIR = CANONICAL_DIR / "enrichment_sources"

# === INPUT REGISTRY FILES ===
AREA_REGISTRY = INPUTS_DIR / "core.area_registry"
FLOOR_REGISTRY = INPUTS_DIR / "core.floor_registry"
DEVICE_REGISTRY = INPUTS_DIR / "core.device_registry"
ENTITY_REGISTRY = INPUTS_DIR / "core.entity_registry"
CATEGORY_REGISTRY = INPUTS_DIR / "core.category_registry"
LABEL_REGISTRY = INPUTS_DIR / "core.label_registry"
INTEGRATION_REGISTRY = INPUTS_DIR / "core.config_entries"
STATE_SNAPSHOT = INPUTS_DIR / "core.restore_state"
COUNTER = INPUTS_DIR / "counter"
EXPOSED_ENTITY = INPUTS_DIR / "homeassistant.exposed_entities"
INPUT_BOOLEAN = INPUTS_DIR / "input_boolean"
INPUT_DATETIME = INPUTS_DIR / "input_datetime"
INPUT_NUMBER = INPUTS_DIR / "input_number"
INPUT_TEXT = INPUTS_DIR / "input_text"
PERSON = INPUTS_DIR / "person"
TRACE = INPUTS_DIR / "trace.saved_traces"

# === ONTOLOGY & CONTRACT PATHS ===
JOIN_CONTRACT = SUPPORT_DIR / "contracts/join_contract.yaml"
OUTPUT_CONTRACT = SUPPORT_DIR / "contracts/omega_registry_master.output_contract.yaml"
MANIFEST = SUPPORT_DIR / "manifests/enrichment_manifest.omega.yaml"
AREA_HIERARCHY = SUPPORT_DIR / "contracts/area_hierarchy.yaml"
TIER_DEFINITIONS = SUPPORT_DIR / "contracts/tier_definitions.yaml"

# === OUTPUT ARTIFACTS ===
PIPELINE_METRICS = LOGS_DIR / "analytics/pipeline_metrics.latest.json"
ENTITY_FLATMAP = DERIVED_VIEWS_DIR / "flatmaps/entity_flatmap.json"
DEVICE_FLATMAP = DERIVED_VIEWS_DIR / "flatmaps/device_flatmap.json"
ENRICHED_OUTPUT = DERIVED_VIEWS_DIR / "enriched_registry.json"
TRACE_OVERLAY = DERIVED_VIEWS_DIR / "trace_overlay.json"
OMEGA_REGISTRY_STRICT_ALLOWLIST = [
    "entity_id",
    "domain",
    "platform",
    "device_class",
    "entity_category",
    "name",
    "area_id",
    "floor_id",
    "device_id",
    "entry_id",
    "integration",
    "join_origin",
    "labels",
    "via_device_id",
    "state_snapshot",
    "exposed_to_assistant",
    "suggested_area",
    "hidden_by",
    "disabled_by",
    "original_name",
    "mac",
    "connections",
    "manufacturer",
    "model",
    "_meta",
    "conflict_id",
    "field_inheritance",
    "tier",
    "floor_ref",
    "room_ref",
    "voice_assistants",
]
ENRICHMENT_TARGET_PATHS = {
    "device_registry": str(DERIVED_VIEWS_DIR / "enriched.device_registry.json"),
    "entity_registry": str(DERIVED_VIEWS_DIR / "enriched.entity_registry.json"),
    "area_registry": str(DERIVED_VIEWS_DIR / "enriched.area_registry.json"),
    "floor_registry": str(DERIVED_VIEWS_DIR / "enriched.floor_registry.json"),
    "metrics": str(LOGS_DIR / "analytics/pipeline_metrics.latest.json"),
    "generated_subset": str(
        ENRICHMENT_SOURCES_DIR / "generated/enriched_device_registry_subset.json"
    ),
}
ENRICHMENT_SOURCE_MAP = {"ip_mac_index": "mac"}
ENRICHMENT_INPUT_PATH = str(
    ENRICHMENT_SOURCES_DIR / "generated/enriched_device_registry_subset.json"
)
ENRICHMENT_OUTPUT_PATH = str(
    ENRICHMENT_SOURCES_DIR / "generated/enriched.device_registry.json"
)
PIPELINE_METRICS_PATH = str(LOGS_DIR / "analytics/pipeline_metrics.latest.json")

# === LOGGING ===
PIPELINE_LOG = LOGS_DIR / "omega_pipeline_main.log"
ENRICHMENT_LOG_PATH = ENRICHMENT_SOURCES_DIR / "generated/omega_registry_enrichment.log"
ENRICHED_DEVICE_MAP_PATH = ENRICHMENT_SOURCES_DIR / "generated/enriched_device_map.json"

# === OTHER OUTPUTS ===
OMEGA_ROOM_REG = INPUTS_DIR / "omega_room_registry.json"
OUTPUT_PATH = DERIVED_VIEWS_DIR / "alpha_room_registry.json"
META_TITLE = "Alpha Room Registry"

# === SCRIPT NAMES ===
SCRIPT_NAME = "generate_alpha_registry.py"

VALID_ANCHOR_TYPES = [
    "device_registry",
    "entity_registry",
    "area_registry",
    "floor_registry",
    "category_registry",
    "label_registry",
    "integration_registry",
    "state_snapshot",
    "sensor_registry",
    "light_registry",
    "person",
    "counter",
    "exposed_entity",
    "input_boolean",
    "input_datetime",
    "input_number",
    "input_text",
    "trace",
]
REGISTRY_SOURCE_FILES = {
    "device_registry": "core.device_registry",
    "entity_registry": "core.entity_registry",
    "area_registry": "core.area_registry",
    "floor_registry": "core.floor_registry",
    "category_registry": "core.category_registry",
    "label_registry": "core.label_registry",
    "integration_registry": "core.config_entries",
    "state_snapshot": "core.restore_state",
    "counter": "counter",
    "exposed_entity": "homeassistant.exposed_entities",
    "input_boolean": "input_boolean",
    "input_datetime": "input_datetime",
    "input_number": "input_number",
    "input_text": "input_text",
    "person": "person",
    "trace": "trace.saved_traces",
}
REGISTRY_SINGLE_KEY = {
    "device": "core.device_registry",
    "entity": "core.entity_registry",
    "area": "core.area_registry",
    "floor": "core.floor_registry",
    "category": "core.category_registry",
    "label": "core.label_registry",
    "integration": "core.config_entries",
    "config": "core.config",
    "restore": "core.restore_state",
    "counter": "counter",
    "exposed": "homeassistant.exposed_entities",
    "boolean": "input_boolean",
    "datetime": "input_datetime",
    "number": "input_number",
    "text": "input_text",
    "person": "person",
    "trace": "trace.saved_traces",
}

METRICS_FILE = "canonical/logs/analytics/pipeline_metrics.latest.json"
ENTITY_SOURCE = "canonical/derived_views/flatmaps/entity_flatmap.json"

ENRICHMENT_FIELD_LIST = ["ipv4", "hostname", "confidence"]
ENRICHED_DEVICE_OUTPUT_FIELDS = [
    "device_id",
    "name",
    "manufacturer",
    "model",
    "mac",
]
ENRICHMENT_LOG_PATH = (
    "canonical/enrichment_sources/generated/omega_registry_enrichment.log"
)
ENRICHED_DEVICE_MAP_PATH = (
    "canonical/enrichment_sources/generated/enriched_device_map.json"
)
DEVICE_TRACKER_ENTITY_TYPE = "device_tracker"
SUBJECT_TYPE = "device"
SOURCE_REGISTRY = "ip_mac_index"

# === SYNTHETIC DEVICE CREATION FLAGS ===
# Controls whether certain enrichers are allowed to create synthetic device ids
# Default: disabled; enables opt-in behavior for riskier heuristics.
ENABLE_SYNTHETIC_DEVICE_CREATION = False
# Per-enricher overrides (fall back to ENABLE_SYNTHETIC_DEVICE_CREATION)
SYNTHETIC_MOBILE_APP = False
SYNTHETIC_NETWORK_TRACKER = False

# === ALPHA EMIT FLAGS ===
# When true, generator may emit per-domain alpha registries via writers.
EMIT_ALPHA_REGISTRIES = False


def _load_central_config():
    """Load central configuration from settings.conf (preferred) or config.yaml.

    Returns a dict with settings or empty dict on failure.
    """
    candidates = ["settings.conf", "config.yaml"]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.warning("Failed to load central config %s: %s", p, e)
    return {}


# Load centralized settings and override defaults if present
_CENTRAL = _load_central_config()
try:
    _synth = _CENTRAL.get("enable_synthetic_device_creation")
    if isinstance(_synth, bool):
        ENABLE_SYNTHETIC_DEVICE_CREATION = _synth
except Exception:
    pass

try:
    # allow per-enricher toggles under a nested key
    synth_overrides = _CENTRAL.get("synthetic_device_overrides", {}) or {}
    if isinstance(synth_overrides, dict):
        SYNTHETIC_MOBILE_APP = synth_overrides.get("mobile_app", SYNTHETIC_MOBILE_APP)
        SYNTHETIC_NETWORK_TRACKER = synth_overrides.get(
            "network_tracker", SYNTHETIC_NETWORK_TRACKER
        )
except Exception:
    pass

# Expose other common centralized flags (fall back to sensible defaults)
EMIT_FULL_REGISTRY_ENTRIES = bool(_CENTRAL.get("emit_full_registry_entries", False))
COMPACT_JSON_OUTPUT = bool(_CENTRAL.get("compact_json_output", True))
DEFAULT_CONTRACT_PATH = _CENTRAL.get("default_contract_path") or str(
    SUPPORT_DIR / "contracts" / "omega_registry_master.output_contract.yaml"
)
