import json
from collections import Counter

with open('output/fingerprinting_run/area_inference_debug.json') as f:
    d = json.load(f)

area_methods = Counter()
unknown_areas = 0
unique_areas = set()
unique_entities = set()

for entry in d:
    area = entry.get('final_area') or entry.get('matched_area')
    method = entry.get('area_inference_method') or entry.get('matched_reason')
    if area:
        unique_areas.add(area)
    if 'entity_id' in entry:
        unique_entities.add(entry['entity_id'])
    if method:
        area_methods[method] += 1
    if area == 'unknown_area':
        unknown_areas += 1

print('Total entries:', len(d))
print('Unique entities:', len(unique_entities))
print('Unique areas:', len(unique_areas))
print('Area inference methods:', dict(area_methods))
print('Unknown area count:', unknown_areas)
