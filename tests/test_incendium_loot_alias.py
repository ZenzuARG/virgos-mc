import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ALIAS = Path("kubejs/data/incendium/loot_tables/steam/rare.json")
OVERRIDE = Path("pack/server-overrides/kubejs/data/incendium/loot_tables/steam/rare.json")


class IncendiumLootAliasTest(unittest.TestCase):
    def test_steam_rare_alias_targets_pipeline_rare_in_runtime_and_release_override(self):
        runtime = json.loads((ROOT / ALIAS).read_text(encoding="utf-8"))
        override = json.loads((ROOT / OVERRIDE).read_text(encoding="utf-8"))
        expected = {
            "pools": [{
                "rolls": 1,
                "entries": [{"type": "minecraft:loot_table", "name": "incendium:pipeline/rare"}],
            }]
        }
        self.assertEqual(runtime, expected)
        self.assertEqual(override, expected)


if __name__ == "__main__":
    unittest.main()
