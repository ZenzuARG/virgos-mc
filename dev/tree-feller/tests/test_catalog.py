import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CatalogResources(unittest.TestCase):
    def test_exact_inventory_and_explicit_gaps(self):
        data = json.loads((ROOT / "resources/catalog.json").read_text())
        self.assertEqual(64, len(data["families"]))
        self.assertEqual(64, len({item["id"] for item in data["families"]}))
        self.assertEqual(54, sum(item["status"] == "READY_STATIC" for item in data["families"]))
        self.assertTrue(all(item["runtime"] == "UNPROVEN" for item in data["families"]))
        sources = {item["jar"] for item in data["sources"]}
        for item in data["families"]:
            self.assertIn(item["origin_jar"], sources)
            self.assertTrue(item["evidence"])
            self.assertTrue(all(len(ref["sha256"]) == 64 and ref.get("jar", item["origin_jar"]) in sources for ref in item["evidence"]))
            if item["status"] == "READY_STATIC":
                self.assertTrue(item["trunks"] and item["foliage"] and item["required_foliage"] and item["widths"])
        pin = json.loads((ROOT / "UPSTREAM.json").read_text())
        for name, digest in pin["resources"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / "resources" / name).read_bytes()).hexdigest())

    def test_runtime_rows_match_curated_evidence(self):
        data = json.loads((ROOT / "resources/catalog.json").read_text())
        expected = []
        for item in data["families"]:
            expected.append("\t".join([item["id"], ",".join(item["trunks"]), ",".join(item["foliage"]),
                ",".join(item["seeds"]), item["fallback"], ",".join(map(str, item["widths"])), item["status"], ",".join(item["required_foliage"]), ",".join(map(str, item["planting_widths"])), item["anchor_mode"]]))
        self.assertEqual("\n".join(expected) + "\n", (ROOT / "resources/catalog.tsv").read_text())

if __name__ == "__main__":
    unittest.main()
