# DEPRECATED — This file has been merged into registry/utils/. Please update references accordingly.

import json

def load_registry(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("data", data)

def load_entity_registry(path):
    return load_registry(path)

def load_device_registry(path):
    return load_registry(path)

def build_device_map(device_registry):
    return {d["id"]: d for d in device_registry}

def build_entity_map(entity_registry):
    return {e["entity_id"]: e for e in entity_registry}

def extract_entities(entity_registry):
    return [e for e in entity_registry if "entity_id" in e]
