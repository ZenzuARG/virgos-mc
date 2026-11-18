"""Per-spell balance overrides remain mirrored and intentionally scoped."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {
    "teleport": {"irons_spellbooks:mana_cost_multiplier": 1.15,
                 "irons_spellbooks:cooldown_in_seconds": 20.0},
    "black_hole": {"irons_spellbooks:mana_cost_multiplier": 1.15,
                   "irons_spellbooks:power_multiplier": 0.95,
                   "irons_spellbooks:cooldown_in_seconds": 20.0},
    "starfall": {"irons_spellbooks:mana_cost_multiplier": 1.15,
                 "irons_spellbooks:power_multiplier": 0.95,
                 "irons_spellbooks:cooldown_in_seconds": 25.0},
    "earthquake": {"irons_spellbooks:mana_cost_multiplier": 1.1,
                   "irons_spellbooks:power_multiplier": 0.95,
                   "irons_spellbooks:cooldown_in_seconds": 20.0},
    "summon_vex": {"irons_spellbooks:mana_cost_multiplier": 1.15,
                   "irons_spellbooks:cooldown_in_seconds": 30.0},
}


class MagicBalanceConfigTests(unittest.TestCase):
    def test_scoped_overrides_are_mirrored_and_do_not_change_global_defaults(self):
        global_config = json.loads((ROOT / "config/irons_spellbooks_spell_config/global_config.json").read_text())
        self.assertEqual(set(global_config), {"_comment1", "_comment2", "_comment3"})
        for spell, expected in CONFIGS.items():
            relative = Path("irons_spellbooks_spell_config/irons_spellbooks") / (spell + ".json")
            source = ROOT / "pack/server-overrides/config" / relative
            live = ROOT / "config" / relative
            self.assertEqual(source.read_bytes(), live.read_bytes(), spell)
            data = json.loads(source.read_text())
            self.assertTrue(set(expected).issubset(data), spell)
            for key, value in expected.items():
                self.assertEqual(data[key], value, f"{spell}: {key}")


if __name__ == "__main__":
    unittest.main()
