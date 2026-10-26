import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class BuildContract(unittest.TestCase):
    def builder(self):
        spec = importlib.util.spec_from_file_location("forestry_build", ROOT / "build.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_patches_require_exact_single_context(self):
        build = self.builder()
        self.assertEqual("aYc", build.replace_once("abc", "b", "Y"))
        for text in ("ac", "abbc"):
            with self.assertRaises(ValueError):
                build.replace_once(text, "b", "Y")

    def test_unknown_overlay_class_rejected(self):
        build = self.builder()
        self.assertTrue(build.allowed_class("mc/virgos/forestry/NativeGuard.class"))
        self.assertTrue(build.allowed_class("com/thizthizzydizzy/treefeller/TreeFeller$1.class"))
        self.assertFalse(build.allowed_class("mc/virgos/forestry/Forestry$Unknown.class"))
        self.assertFalse(build.allowed_class("net/minecraft/server/Bad.class"))
        self.assertFalse(build.allowed_class("com/thizthizzydizzy/treefeller/FellBehavior.class"))

    def test_source_zip_rejects_traversal(self):
        build = self.builder()
        for name in ("../escape", "/absolute", "root/../../escape", "C:/escape", "root\\escape"):
            self.assertFalse(build.safe_entry(name), name)
        self.assertTrue(build.safe_entry("root/src/TreeFeller.java"))

if __name__ == "__main__":
    unittest.main()
