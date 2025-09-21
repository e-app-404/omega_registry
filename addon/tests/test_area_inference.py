import unittest
from scripts.fingerprint_entity_reconciliation import infer_area_from_slug

class TestAreaInference(unittest.TestCase):
    def setUp(self):
        self.valid_areas_set = {"living_room", "bedroom", "kitchen"}
        self.area_alias_map = {"living room": "living_room", "salon": "living_room"}
        self.area_synonyms = {"lounge": "living_room"}

    def test_prefix_resolution(self):
        area, reason = infer_area_from_slug("living_room_occupancy", self.valid_areas_set, self.area_alias_map, self.area_synonyms)
        self.assertEqual(area, "living_room")
        self.assertEqual(reason, "fallback_prefix_match")

    def test_synonym_resolution(self):
        area, reason = infer_area_from_slug("lounge_occupancy", self.valid_areas_set, self.area_alias_map, self.area_synonyms)
        self.assertEqual(area, "living_room")
        self.assertEqual(reason, "synonym_fallback")

    def test_no_match(self):
        area, reason = infer_area_from_slug("garage_motion", self.valid_areas_set, self.area_alias_map, self.area_synonyms)
        self.assertEqual(area, "unknown_area")
        self.assertEqual(reason, "no_area_found")

if __name__ == "__main__":
    unittest.main()
