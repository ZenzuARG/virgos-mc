"""Pin narrow data repairs against original resources from the installed pack."""
import copy
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/recipe-ingredient-compat"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RecipeIngredientCompatTests(unittest.TestCase):
    def assert_mirrored(self, relative, expected):
        source = ROOT / "kubejs/data" / relative
        packaged = ROOT / "pack/server-overrides/kubejs/data" / relative
        self.assertEqual(read(source), expected)
        self.assertEqual(source.read_bytes(), packaged.read_bytes())

    def test_original_fixtures_are_pinned(self):
        for filename, origin in read(FIXTURES / "origins.json").items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((FIXTURES / filename).read_bytes()).hexdigest(),
                                 origin["resourceSha256"])

    def test_magnolia_alias_keeps_the_original_four_logs(self):
        original = read(FIXTURES / "magnolia-items-original.json")
        self.assertEqual(len(original["values"]), 4)
        self.assertEqual(len(set(original["values"])), 4)
        self.assert_mirrored("regions_unexplored/tags/items/magnolia_logs.json", {
            "replace": False, "values": ["#regions_unexplored:magnolia_logs_item"]})

    def test_dog_food_changes_only_obsolete_meat_tag(self):
        original = read(FIXTURES / "dog-food-original.json")
        base_recipe = read(FIXTURES / "dog-food-farmersdelight-original.json")
        self.assertEqual(original["recipes"][0]["recipe"]["ingredients"][2],
                         {"tag": "farmersdelight:wolf_prey"})
        self.assertEqual(base_recipe["ingredients"][2], {"tag": "forge:raw_meat"})
        expected = copy.deepcopy(original)
        expected["recipes"][0]["recipe"]["ingredients"][2] = base_recipe["ingredients"][2]
        self.assert_mirrored("delightful/recipes/food/cooking/dog_food_from_animal_fat.json", expected)

    def test_cheesecake_retains_mild_choices_and_all_other_fields(self):
        original = read(FIXTURES / "cheesecake-original.json")
        self.assertEqual(original["recipes"][0]["recipe"]["ingredients"][6],
                         [{"tag": "forge:cheese/mild"}, {"tag": "forge:cheese/sweet"}])
        expected = copy.deepcopy(original)
        entry = expected["recipes"][0]
        entry["recipe"]["ingredients"][6] = {"tag": "forge:cheese/mild"}
        entry["conditions"][0] = {"type": "forge:not", "value": {
            "type": "forge:tag_empty", "tag": "forge:cheese/mild"}}
        # Keep the original tag, including future optional mild providers. Do not
        # substitute a concrete item or introduce nonexistent sweet cheese.
        mild = read(FIXTURES / "cheese-mild-original.json")["values"]
        self.assertIn({"id": "brewinandchewin:flaxen_cheese_wedge", "required": False}, mild)
        self.assert_mirrored("delightful/recipes/food/sweet_berry_cheesecake_from_cheese.json", expected)


if __name__ == "__main__":
    unittest.main()
