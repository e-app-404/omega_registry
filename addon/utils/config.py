# DEPRECATED — This file has been merged into registry/utils/. Please update references accordingly.

import yaml # type: ignore
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = PROJECT_ROOT / "settings.conf.yaml"

def load_settings(path=SETTINGS_FILE):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def resolve_config_path(path_str, settings=None):
    if not settings:
        settings = load_settings()
    base_path = PROJECT_ROOT
    return (base_path / path_str).resolve()

def get_input_path(key, settings=None):
    settings = settings or load_settings()
    return resolve_config_path(settings["input_paths"][key], settings)

def get_output_path(key, settings=None):
    settings = settings or load_settings()
    return resolve_config_path(settings["output_paths"][key], settings)
