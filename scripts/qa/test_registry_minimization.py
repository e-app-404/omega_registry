#!/usr/bin/env python3
"""
Run as module: python -m scripts.qa.test_registry_minimization
PATCH ABSOLUTE-IMPORT-UTILS-V1: Refactored for absolute imports, added run-as-module comment.
"""
import unittest

from scripts.utils.registry import minimize_registry_entity


class TestRegistryMinimization(unittest.TestCase):

    def setUp(self):
        self.sample_entity = {
            "entity_id": "sensor.sun_next_dawn",
            "area_id": "london",
            "config_entry_id": "01JX8TQYQ734A7A0XMDXT9DSTN",
            "device_id": "820adbe5f9e918790dfa69236d820763",
            "capabilities": None,
            "options": {
                "conversation": {"should_expose": False},
                "cloud.google_assistant": {"should_expose": False},
                "cloud.alexa": {"should_expose": False},
            },
            "tier": "?",
            "floor_id": None,
            "room_ref": None,
            "_meta": {
                "inference_source": "join_contract.yaml",
                "strategy": "multi-key fallback",
                "timestamp": "2025-07-23T11:17:01.309236",
            },
        }
        self.config = {"emit_full_registry_entries": False}

    def test_minimization(self):
        minimized = minimize_registry_entity(self.sample_entity, self.config)

        # Check key presence
        self.assertIn("entity_id", minimized)
        self.assertIn("area_id", minimized)
        self.assertIn("device_id", minimized)

        # Ensure legacy fields removed
        self.assertNotIn("capabilities", minimized)
        self.assertNotIn("config_entry_id", minimized)

        # Ensure options flattened
        self.assertIn("voice_assistants", minimized)
        self.assertNotIn("options", minimized)
        self.assertEqual(
            minimized["voice_assistants"],
            {"conversation": False, "google_assistant": False},
        )

        # Nulls offloaded
        self.assertIn("_meta", minimized)
        self.assertIn("null_fields", minimized["_meta"])
        self.assertIn("floor_id", minimized["_meta"]["null_fields"])

        # Conflict ID exists
        self.assertIn("conflict_id", minimized)


if __name__ == "__main__":
    unittest.main()
