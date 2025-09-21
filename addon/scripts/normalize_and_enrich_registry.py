import json
import re
from copy import deepcopy

# Load registry
with open('omega_device_registry.enriched.canonical.devtools_enriched.json', 'r') as f:
    registry = json.load(f)

change_log = []
blockers = []

# Helper: Replace Greek omega with ASCII 'omega'
def canonicalize_omega(val):
    if isinstance(val, str):
        new_val = val.replace('ω', 'omega')
        if new_val != val:
            change_log.append(f"Canonicalized: '{val}' -> '{new_val}'")
        return new_val
    return val

def enrich_entity(entity):
    enriched = False
    # Enrich name
    if not entity.get('name'):
        for key in ['original_name', 'name_registry', 'name_textfile']:
            if entity.get(key):
                entity['name'] = entity[key]
                change_log.append(f"Enriched entity name from {key}: {entity['entity_id']} -> {entity['name']}")
                enriched = True
                break
    # Enrich device_class
    if not entity.get('device_class') and entity.get('original_device_class'):
        entity['device_class'] = entity['original_device_class']
        change_log.append(f"Enriched device_class from original_device_class: {entity['entity_id']} -> {entity['device_class']}")
        enriched = True
    # Enrich unit_of_measurement
    if not entity.get('unit_of_measurement') and entity.get('unit'):
        entity['unit_of_measurement'] = entity['unit']
        change_log.append(f"Enriched unit_of_measurement from unit: {entity['entity_id']} -> {entity['unit_of_measurement']}")
        enriched = True
    return enriched

def process_device(device):
    # Canonicalize id, canonical_id, name
    for key in ['id', 'canonical_id', 'name', 'internal_name']:
        if key in device and device[key]:
            device[key] = canonicalize_omega(device[key])
    # Entities
    for entity in device.get('entities', []):
        # Canonicalize entity_id
        if 'entity_id' in entity:
            entity['entity_id'] = canonicalize_omega(entity['entity_id'])
        # Canonicalize name fields
        for name_key in ['name', 'original_name', 'name_registry', 'name_textfile']:
            if name_key in entity and entity[name_key]:
                entity[name_key] = canonicalize_omega(entity[name_key])
        # Enrich fields
        enriched = enrich_entity(entity)
        # Blockers for missing fields
        for field in ['name', 'device_class', 'unit_of_measurement']:
            if not entity.get(field):
                blockers.append({
                    'device_id': device.get('id'),
                    'entity_id': entity.get('entity_id'),
                    'missing_field': field
                })
    return device

# Process all devices
for i, device in enumerate(registry.get('devices', [])):
    registry['devices'][i] = process_device(deepcopy(device))

# Write updated registry
with open('omega_device_registry.normalized.enriched.json', 'w') as f:
    json.dump(registry, f, indent=2)

# Write change log
with open('omega_device_registry.normalization_changelog.md', 'w') as f:
    for line in change_log:
        f.write(f"- {line}\n")

# Write blockers CSV
import csv
with open('omega_device_registry.enrichment_blockers.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['device_id', 'entity_id', 'missing_field'])
    writer.writeheader()
    for row in blockers:
        writer.writerow(row)

print(f"Normalization and enrichment complete. {len(change_log)} changes. {len(blockers)} blockers.")
