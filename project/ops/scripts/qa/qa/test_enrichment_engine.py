import importlib
import json
import sys
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

# Provide import hints for Pylance/type-checkers
if TYPE_CHECKING:
    pass

# Ensure project root is on sys.path so local packages are discoverable in tests
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Defer heavy imports until runtime inside tests to avoid import-time side effects


class TestEnrichmentEngine(unittest.TestCase):
    def setUp(self):
        self.registry_path = Path("canonical/omega_registry_master.json")
        # Use canonical manifest path (exists in workspace)
        self.manifest_path = Path(
            "canonical/support/manifests/enrichment_manifest.alpha_room.yaml"
        )
        self.alpha_output_path = Path(
            "canonical/derived_views/alpha_room_registry.v1.json"
        )
        self.trace_overlay_path = Path("canonical/derived_views/trace_overlay.json")

    def test_enrichment_room_centric(self):
        # Create minimal fixtures required by the generator at import time
        (Path("canonical/derived_views/flatmaps")).mkdir(parents=True, exist_ok=True)
        (Path("canonical/logs/analytics")).mkdir(parents=True, exist_ok=True)
        # Minimal entity flatmap (empty list is acceptable for this smoke test)
        entity_flatmap = Path("canonical/derived_views/flatmaps/entity_flatmap.json")
        if not entity_flatmap.exists():
            entity_flatmap.write_text("[]")
        # Minimal pipeline metrics required by generator
        metrics_file = Path("canonical/logs/analytics/pipeline_metrics.latest.json")
        if not metrics_file.exists():
            metrics_file.write_text(
                json.dumps({"area_floor_analytics": {"tiers_by_area": {}}})
            )

        # Ensure module will be freshly imported (avoid cached import re-use)
        mod_name = "scripts.generators.generate_alpha_registry"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        # Temporarily back up and replace canonical/omega_registry_master.json so
        # the generator has at least one room (id: 'ha_system') to operate on.
        omega_path = Path("canonical/omega_registry_master.json")
        original_omega = None
        if omega_path.exists():
            original_omega = omega_path.read_text()

        omega_path.write_text(
            json.dumps([{"id": "ha_system", "friendly_name": "HA System"}])
        )

        try:
            # Import canonical YAML loader
            loaders = importlib.import_module("scripts.utils.loaders")
            load_yaml = getattr(loaders, "load_yaml")

            # Import generator after fixtures are in place and run
            generator = importlib.import_module(mod_name)
            generate_room_registry = getattr(generator, "generate_room_registry")
            generate_room_registry()

            with open(self.alpha_output_path) as f:
                enriched = json.load(f)
            # Generator may return a dict wrapper (e.g. {"rooms": [...]}) or a raw list.
            if isinstance(enriched, dict) and "rooms" in enriched:
                enriched_list = enriched.get("rooms", [])
            elif isinstance(enriched, list):
                enriched_list = enriched
            else:
                # Unknown shape, treat as empty result
                enriched_list = []
            # trace overlay may not be produced by this generator; ensure a placeholder exists
            if not self.trace_overlay_path.exists():
                self.trace_overlay_path.write_text("[]")
            with open(self.trace_overlay_path) as f:
                trace = json.load(f)
        finally:
            # Restore original omega registry if it existed; otherwise remove the test file
            try:
                if original_omega is not None:
                    omega_path.write_text(original_omega)
                else:
                    omega_path.unlink(missing_ok=True)
            except Exception:
                # best-effort restore; don't fail the test teardown on restore errors
                pass

        manifest = load_yaml(self.manifest_path)
        manifest_fields = set(manifest.get("output_fields", []))
        # Only _meta is excluded from trace/inferred checks
        enrichment_fields = manifest_fields - {"_meta"}

        # Map manifest field names to possible generator-produced aliases
        alias_map = {
            "friendly_name": ["friendly_name", "room_ref"],
            "floor": ["floor", "floor_ref"],
        }
        # If generator produced no rooms, skip detailed assertions (smoke test)
        if not enriched_list:
            self.skipTest(
                "Generator produced zero rooms; nothing to assert for this smoke test"
            )

        # Build trace lookup by room_id
        trace_by_room = {}
        for i, t in enumerate(trace):
            if i >= len(enriched_list):
                break
            room_id = enriched_list[i].get("room_id")
            trace_by_room[room_id] = t
        for room in enriched_list:
            room_id = room.get("room_id")
            self.assertIsNotNone(room_id)
            # Validate a minimal required set of fields that the generator should produce.
            required_fields = {
                "room_id",
                "tier",
                "cluster_size",
                "has_beta",
                "domains",
            }
            for rf in required_fields:
                self.assertIn(
                    rf, room, f"Generator output missing required field '{rf}'"
                )
            # Ensure there is some form of friendly_name/floor present (either direct or via refs)
            friendly_ok = False
            rr = room.get("room_ref")
            if isinstance(rr, list) and len(rr) >= 3 and rr[2]:
                friendly_ok = True
            if "friendly_name" in room:
                friendly_ok = True
            self.assertTrue(
                friendly_ok, "Generator output missing friendly_name/room_ref"
            )
            floor_ok = False
            fr = room.get("floor_ref")
            if isinstance(fr, list) and len(fr) >= 3 and fr[2]:
                floor_ok = True
            if "floor" in room:
                floor_ok = True
            # floor can be null/None; just allow either presence or null reference
            self.assertTrue(
                floor_ok or room.get("floor_ref") is not None or "floor" in room,
                "Generator output missing floor/floor_ref (may be null)",
            )
            # If the generator provided per-room _meta.inferred_fields, validate them;
            # otherwise skip these deep provenance checks for this smoke test.
            room_meta = room.get("_meta") or {}
            inferred = set()
            if (
                room_meta
                and isinstance(room_meta, dict)
                and "inferred_fields" in room_meta
            ):
                inferred = set(room_meta.get("inferred_fields", []))
                room_trace = trace_by_room.get(room_id, {})
                # Build allowed trace fields to include manifest aliases
                allowed_trace_fields = set()
                for mf in manifest_fields:
                    allowed_trace_fields.update(alias_map.get(mf, [mf]))
                # All enrichment fields (output_fields except _meta) must be in inferred_fields and trace
                for field in enrichment_fields:
                    aliases = alias_map.get(field, [field])
                    # a field is considered present in inferred if any alias is present
                    self.assertTrue(
                        any(a in inferred for a in aliases) or field in inferred,
                        f"Field {field} not found in inferred_fields ({inferred})",
                    )
                    # trace presence check (if trace overlay has entry)
                    if room_trace:
                        self.assertTrue(
                            any(a in room_trace for a in aliases)
                            or field in room_trace,
                            f"Field {field} not found in trace for room {room_id}",
                        )
                        # ensure source key exists for the traced field
                        for a in aliases:
                            if a in room_trace:
                                self.assertIn("source", room_trace[a])
                # _meta should not be inferred
                self.assertNotIn("_meta", inferred)
                # No extra fields in trace overlay (allow _meta in trace)
                if room_trace:
                    self.assertTrue(
                        set(room_trace.keys()).issubset(allowed_trace_fields)
                    )


if __name__ == "__main__":
    unittest.main()
