import json
from collections import Counter
import datetime

# Load the entity registry
with open('input/core.entity_registry') as f:
    data = json.load(f)
entities = data['data']['entities']

def field_stats(field):
    total = len(entities)
    non_null = sum(1 for e in entities if e.get(field) not in (None, [], {}, ""))
    percent = (non_null / total) * 100 if total else 0
    return non_null, total, percent

# List of auxiliary fields to check
aux_fields = [
    'aliases', 'area_id', 'categories', 'capabilities', 'config_entry_id', 'config_subentry_id',
    'created_at', 'device_class', 'device_id', 'disabled_by', 'entity_category', 'hidden_by',
    'icon', 'id', 'has_entity_name', 'labels', 'modified_at', 'name', 'options',
    'original_device_class', 'original_icon', 'previous_unique_id', 'suggested_object_id',
    'supported_features', 'translation_key', 'unique_id', 'unit_of_measurement'
]

print(f"{'Field':30} {'Non-null':>8} {'Total':>8} {'Percent':>8}")
for field in aux_fields:
    non_null, total, percent = field_stats(field)
    print(f"{field:30} {non_null:8} {total:8} {percent:8.2f}")

timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
out_path = f'data/aux_field_stats.{timestamp}.txt'

with open(out_path, 'w') as out:
    out.write(f"{'Field':30} {'Non-null':>8} {'Total':>8} {'Percent':>8}\n")
    for field in aux_fields:
        non_null, total, percent = field_stats(field)
        out.write(f"{field:30} {non_null:8} {total:8} {percent:8.2f}\n")

print(f"Stats written to {out_path}")
