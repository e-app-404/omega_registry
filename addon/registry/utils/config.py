# Moved from utils/config.py
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

from typing import Optional

def get_path_from_settings(settings: dict, key: str, fallback: Optional[str] = None) -> Path:
    """
    Centralized utility to fetch a path from settings dict by key, searching common locations.
    - Checks settings['general']['input_paths'] and ['output_paths']
    - Checks settings['input_paths'] and ['output_paths']
    - Returns fallback if not found
    """
    for section in (('general', 'input_paths'), ('general', 'output_paths'), ('input_paths',), ('output_paths',)):
        d = settings
        try:
            for s in section:
                d = d[s]
            if key in d:
                return Path(d[key])
        except Exception:
            continue
    if fallback is not None:
        return Path(fallback)
    raise KeyError(f"Path key '{key}' not found in settings.")
