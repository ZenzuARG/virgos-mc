import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PlantingLayoutMetadata(unittest.TestCase):
    def catalog(self):
        return json.loads((ROOT / "resources/catalog.json").read_text())

    def test_actual_archwoods_separate_mature_core_from_one_seed(self):
        data = self.catalog()
        for color in ("blue", "red", "green", "purple"):
            family = next(item for item in data["families"] if item["id"] == "ars_nouveau:" + color + "_archwood_sapling")
            self.assertIn("ars_nouveau:" + color + "_archwood_log", family["trunks"])
            self.assertIn("ars_nouveau:" + color + "_archwood_leaves", family["foliage"])
            self.assertEqual([2], family.get("mature_widths", family["widths"]), "actual MagicTrunkPlacer core")
            self.assertEqual([1], family.get("planting_widths", family["widths"]), "MagicTree grows from one seed, not four")
            self.assertEqual("UNRESOLVED_ARS_BUTTRESS", family["anchor_mode"], "do not invent an unproven planting anchor")
            self.assertTrue(family["status"].startswith("GAP:"))

    def test_all_six_quark_growers_have_cross_jar_evidence(self):
        data = self.catalog()
        source = next(item for item in data["sources"] if item["jar"] == "Zeta-1.0-31.jar")
        self.assertEqual("cd1786902a79434f8fd762d741019d9c8a79725fef7e30a89c153c934e1e6a9e", source["sha256"])
        families = [item for item in data["families"] if item["id"].startswith("quark:")]
        self.assertEqual(6, len(families))
        for family in families:
            self.assertEqual("READY_STATIC", family["status"])
            self.assertEqual([1], family["planting_widths"])
            self.assertEqual([1], family["mature_widths"])
            self.assertTrue(any(ref.get("jar") == source["jar"] and ref["path"].endswith("PassthroughTreeGrower.class") for ref in family["evidence"]))
            self.assertEqual("UNPROVEN", family["runtime"])

if __name__ == "__main__":
    unittest.main()
