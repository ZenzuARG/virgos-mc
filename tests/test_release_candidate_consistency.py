import hashlib
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ReleaseCandidateConsistencyTests(unittest.TestCase):
    def read_json(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_candidate_identity_is_coherent_and_separate_from_published_release(self):
        stable = self.read_json("pack/current-release.json")
        selected = self.read_json("pack/candidates/current.json")
        candidate = self.read_json(f"pack/candidates/{selected['version']}/release.json")
        source = (ROOT / "dev/virgos-core/src/shared/java/mc/virgos/update/ClientRelease.java").read_text()
        update = self.read_json("pack/server-overrides/config/virgos/client-update.json")

        self.assertEqual(selected["version"], candidate["version"])
        self.assertEqual(candidate["version"], "3.0.3")
        self.assertEqual(candidate["clientRelease"], candidate["version"])
        self.assertEqual(candidate["clientFingerprint"], "virgos-client-" + candidate["clientRelease"])
        self.assertIn(f'RELEASE = "{candidate["clientRelease"]}"', source)
        self.assertIn(f'FINGERPRINT = "{candidate["clientFingerprint"]}"', source)
        self.assertEqual(update["release"], candidate["clientRelease"])
        self.assertEqual(update["fingerprint"], candidate["clientFingerprint"])
        self.assertEqual(candidate["status"], "release-candidate")
        self.assertEqual(stable["version"], "2.2.2")
        self.assertIsNotNone(stable["published"])

    def test_root_and_candidate_custom_locks_match_each_other(self):
        root_lock = self.read_json("pack/custom-artifacts.lock.json")
        candidate_lock = self.read_json("pack/candidates/3.0.3/custom-artifacts.lock.json")
        root_by_name = {item["filename"]: item for item in root_lock["artifacts"]}
        candidate_by_name = {item["filename"]: item for item in candidate_lock["artifacts"]}

        self.assertEqual(set(root_by_name), set(candidate_by_name))
        for name, root_item in root_by_name.items():
            candidate_item = candidate_by_name[name]
            self.assertEqual(root_item["hash_algorithm"], candidate_item["hash_algorithm"])
            self.assertEqual(root_item["hash"], candidate_item["hash"])
            self.assertEqual(root_item["sides"], candidate_item["sides"])
            source = ROOT / root_item["local_source"]
            self.assertTrue(source.is_file(), name)
            self.assertEqual(source.stat().st_size, root_item["size"])
            self.assertEqual(hashlib.new(root_item["hash_algorithm"], source.read_bytes()).hexdigest(), root_item["hash"])


if __name__ == "__main__":
    unittest.main()
