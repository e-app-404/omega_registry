import unittest

from scripts.enrich.normalize import normalize_entity_fields


class TestNormalizeEntityFields(unittest.TestCase):
    def test_flatten_integration(self):
        entity = {
            "entity_id": "sensor.test",
            "enriched_integrations": [
                {"integration_domain": "test", "serial_number": "SN123"}
            ],
        }
        norm = normalize_entity_fields(entity.copy())
        self.assertIn("integration_domain", norm)
        self.assertEqual(norm["serial_number"], "SN123")
        self.assertNotIn("enriched_integrations", norm)

    def test_flatten_identifiers(self):
        entity = {"identifiers": [["mac", "AA:BB:CC"]]}
        norm = normalize_entity_fields(entity.copy())
        self.assertEqual(norm["identifier_type"], "mac")
        self.assertEqual(norm["identifier_value"], "AA:BB:CC")

    def test_resolved_name(self):
        entity = {"entity_id": "sensor.x"}
        norm = normalize_entity_fields(entity.copy())
        self.assertEqual(norm["resolved_name"], "sensor.x")


if __name__ == "__main__":
    unittest.main()
