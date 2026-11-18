import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "pack/server-overrides/plugins/TreeFeller/config.yml"
SCRIPT = ROOT / "scripts/apply-treefeller-config.ps1"


class TreeFellerConfigTests(unittest.TestCase):
    def test_override_excludes_unknown_copper_axe(self):
        text = OVERRIDE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^\s*-\s*COPPER_AXE\s*$")
        for material in (
            "WOODEN_AXE",
            "STONE_AXE",
            "IRON_AXE",
            "GOLDEN_AXE",
            "DIAMOND_AXE",
            "NETHERITE_AXE",
        ):
            self.assertRegex(text, rf"(?m)^\s*-\s*{material}\s*$")

    def test_normalizer_targets_only_tools_copper_entry(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("TreeFeller config normalized", text)
        self.assertIn("^tools:\\s*$", text)
        self.assertIn("^\\s*-\\s*COPPER_AXE\\s*$", text)


if __name__ == "__main__":
    unittest.main()
