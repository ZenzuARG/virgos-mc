"""Exercise real installer updates without downloads or a Minecraft launch."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "PowerShell is required for the installer CLI")
class ClientMipmapUpgradeTest(unittest.TestCase):
    def test_existing_clients_force_zero_without_replacing_other_preferences(self):
        for old_level in ("4", None):
            with self.subTest(old_level=old_level), tempfile.TemporaryDirectory(prefix="virgos-mipmap-") as scratch:
                root = Path(scratch)
                package = root / "package"
                package.mkdir()
                for name in ("instalar-cliente.ps1", "installer-common.ps1", "client-keybindings.ps1"):
                    shutil.copy2(ROOT / "templates" / name, package / name)
                shutil.copy2(ROOT / "pack/keybindings.json", package / "keybindings.json")
                (package / "overrides").mkdir()
                shutil.copy2(ROOT / "pack/client-overrides/config/defaultoptions/options.txt", package / "overrides/options.txt")
                target = root / "existing client"
                (target / "mods").mkdir(parents=True)
                payload = b"offline installer fixture"
                (target / "mods/fixture.jar").write_bytes(payload)
                manifest = {
                    "version": "3.0.6", "minecraft": "1.20.1", "forge": "47.4.22",
                    "files": [{"filename": "fixture.jar", "sha512": hashlib.sha512(payload).hexdigest(),
                               "url": "https://cdn.modrinth.com/fixture.jar", "project": "fixture", "optional": False}],
                }
                (package / "cliente.lock.json").write_text(json.dumps(manifest), encoding="utf-8")
                preferences = ['renderDistance:7', 'lang:es_ar', 'soundCategory_music:0.25',
                               'resourcePacks:["vanilla","file/MyTextures.zip"]',
                               'key_key.virgos_codex.open:key.keyboard.k']
                original = "\r\n".join(preferences + ([] if old_level is None else ["mipmapLevels:" + old_level])) + "\r\n"
                options = target / "options.txt"
                options.write_bytes(original.encode("utf-8"))
                command = [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                           str(package / "instalar-cliente.ps1"), "-Destino", str(target)]
                verification = subprocess.run(command + ["-Verificar"], capture_output=True, text=True, timeout=30)
                self.assertEqual(verification.returncode, 0, verification.stderr)
                self.assertEqual(options.read_bytes(), original.encode("utf-8"), "Verify-only must not rewrite preferences")
                updated = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(updated.returncode, 0, updated.stderr)
                after = options.read_bytes()
                lines = after.decode("utf-8").splitlines()
                self.assertEqual([line for line in lines if line.startswith("mipmapLevels:")], ["mipmapLevels:0"])
                for preference in preferences:
                    self.assertIn(preference, lines, "Unrelated user preference must survive")
                repeated = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                self.assertEqual(options.read_bytes(), after, "Applying the policy twice must be idempotent")


if __name__ == "__main__":
    unittest.main()
