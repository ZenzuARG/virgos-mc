import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("configure_client", ROOT / "scripts/configure-client.py")
module = importlib.util.module_from_spec(spec)


class ClientKeyDefaultsTest(unittest.TestCase):
    def test_hub_profile_and_independent_registration(self):
        source = (ROOT / "dev/virgos-core/src/codex/java/mc/virgos/codex/VirgosCodex.java").read_text(encoding="utf-8")
        hub = source.split("private static final class HubScreen", 1)[1].split("private static final class TreeScreen", 1)[0]
        self.assertIn('sendCommand("perfil")', hub)
        keys = (ROOT / "dev/virgos-core/src/codex/java/mc/virgos/codex/CodexKeyBindings.java").read_text(encoding="utf-8")
        self.assertIn("RegisterKeyMappingsEvent", keys)
        self.assertIn("consumeClick()", keys)
        profile = (ROOT / "dev/virgos-core/src/codex/java/mc/virgos/codex/ProfileScreen.java").read_text(encoding="utf-8")
        self.assertNotIn('Códice [J]', profile)
        self.assertIn("getTranslatedKeyMessage", profile)

    def test_policy_and_contextual_preservation(self):
        spec.loader.exec_module(module)
        policy = json.loads((ROOT / "pack/keybindings.json").read_text(encoding="utf-8"))
        bindings = policy["bindings"]
        self.assertEqual("key.keyboard.j", bindings["key.virgos_codex.open"]["key"])
        self.assertEqual("key.keyboard.unknown", bindings["key.heracles.open_quests"]["key"])
        self.assertEqual("key.keyboard.f8", bindings["iris.keybind.reload"]["key"])
        self.assertEqual("key.keyboard.f6", bindings["iris.keybind.toggleShaders"]["key"])
        self.assertEqual("key.keyboard.f7", bindings["iris.keybind.shaderPackSelection"]["key"])
        global_keys = [row["key"] for row in bindings.values()
                       if row["context"] == "global" and row["key"] != "key.keyboard.unknown"]
        self.assertEqual(len(global_keys), len(set(global_keys)), "Global defaults must not collide")
        original = "renderDistance:7\nkey_key.forward:key.keyboard.w\nkey_key.jei.showRecipe:key.keyboard.r\n"
        updated = module.apply_defaults(original, policy)
        self.assertIn("renderDistance:7\n", updated)
        self.assertIn("key_key.forward:key.keyboard.w\n", updated)
        self.assertIn("key_key.jei.showRecipe:key.keyboard.r\n", updated)
        self.assertEqual(updated, module.apply_defaults(updated, policy))


if __name__ == "__main__":
    unittest.main()
