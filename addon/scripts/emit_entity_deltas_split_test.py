import json
import sys

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def emit_entity_deltas(trace_a_path, trace_b_path, out_path):
    trace_a = load_json(trace_a_path)
    trace_b = load_json(trace_b_path)
    deltas = []
    for eid in trace_b:
        a = trace_a.get(eid, {})
        b = trace_b.get(eid, {})
        delta = {"entity_id": eid}
        for key in ["final_area", "role", "semantic_role", "confidence_score", "role_inference_method"]:
            a_val = a.get(key)
            b_val = b.get(key)
            if a_val != b_val:
                delta[key] = {"branch_a": a_val, "branch_b": b_val}
        if len(delta) > 1:
            deltas.append(delta)
    with open(out_path, "w") as f:
        json.dump(deltas, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: emit_entity_deltas.py <trace_a_path> <trace_b_path> <out_path>")
        sys.exit(1)
    emit_entity_deltas(sys.argv[1], sys.argv[2], sys.argv[3])
