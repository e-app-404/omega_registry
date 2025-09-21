import json
from collections import defaultdict
from pathlib import Path
import sys

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def summarize_aux_field_impact(trace_path, aux_fields, out_path):
    traces = load_json(trace_path)
    field_usage = defaultdict(lambda: {"used_in_role_inference": 0, "used_in_area_inference": 0})
    for eid, trace in traces.items():
        area_fields = trace.get("area", {}).get("source_fields", [])
        role_fields = trace.get("role", {}).get("source_fields", [])
        for f in aux_fields:
            if f in role_fields:
                field_usage[f]["used_in_role_inference"] += 1
            if f in area_fields:
                field_usage[f]["used_in_area_inference"] += 1
    with open(out_path, "w") as f:
        json.dump({"field_usage": field_usage}, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: summarize_aux_field_impact.py <trace_path> <aux_fields_comma_separated> <out_path>")
        sys.exit(1)
    trace_path = sys.argv[1]
    aux_fields = sys.argv[2].split(",")
    out_path = sys.argv[3]
    summarize_aux_field_impact(trace_path, aux_fields, out_path)
