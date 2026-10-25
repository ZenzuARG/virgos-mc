"""Offline regression checks for release downloads; never touch the live runtime."""
import hashlib
import http.client
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("fetcher", Path(__file__).with_name("fetch-locked-client-deps.py"))
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class FetchTests(unittest.TestCase):
    def test_optional_dh_inputs_and_legacy_absence(self):
        import json
        with tempfile.TemporaryDirectory(prefix='virgos-fetch-plan-') as directory:
            root = Path(directory); (root / 'pack').mkdir()
            self.assertEqual(fetcher.dh_targets(root), [])
            record = {'schema': 1, 'filename': 'DH.jar', 'url': 'https://example.test/dh', 'hash_algorithm': 'sha256', 'hash': 'a' * 64,
                      'asm': {'file': 'asm.jar', 'url': 'https://example.test/asm', 'hash': 'b' * 64},
                      'source_archives': [{'filename': n, 'url': 'https://example.test/source', 'sha256': 'c' * 64} for n in ['main.zip', 'core.zip']]}
            (root / 'pack/dh-upstream.lock.json').write_text(json.dumps(record))
            pairs = fetcher.dh_targets(root)
            self.assertEqual([str(p.relative_to(root)).replace('\\', '/') for _, p in pairs],
                             ['.cache/pack/downloads/DH.jar', '.cache/pack/tools/asm.jar', '.cache/pack/sources/main.zip', '.cache/pack/sources/core.zip'])
            self.assertEqual(pairs[-1][0]['hash'], 'c' * 64)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="virgos-fetch-test-")
        self.addCleanup(self.scratch.cleanup)
        self.target = Path(self.scratch.name) / "dependency.jar"
        self.payload = b"verified artifact"
        self.record = {"url": "https://example.test/dependency.jar", "filename": self.target.name,
                       "hash_algorithm": "sha256", "hash": hashlib.sha256(self.payload).hexdigest()}

    def response(self, data):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = data
        return response

    def test_incomplete_download_retries_then_verifies(self):
        with patch.object(fetcher.urllib.request, "urlopen", side_effect=[
            http.client.IncompleteRead(b"partial", 20), self.response(self.payload)
        ]) as request, patch.object(fetcher.time, "sleep"):
            fetcher.fetch(self.record, self.target)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(self.target.read_bytes(), self.payload)

    def test_bad_hash_never_replaces_existing_file(self):
        self.target.write_bytes(b"previous bytes")
        with patch.object(fetcher.urllib.request, "urlopen", return_value=self.response(b"bad bytes")), \
             patch.object(fetcher.time, "sleep"), self.assertRaises(ValueError):
            fetcher.fetch(self.record, self.target)
        self.assertEqual(self.target.read_bytes(), b"previous bytes")

    def test_verified_cache_does_not_download(self):
        self.target.write_bytes(self.payload)
        with patch.object(fetcher.urllib.request, "urlopen") as request:
            fetcher.fetch(self.record, self.target)
        request.assert_not_called()

    def test_runtime_algorithm_alias(self):
        record = dict(self.record)
        record["algorithm"] = record.pop("hash_algorithm").upper()
        with patch.object(fetcher.urllib.request, "urlopen", return_value=self.response(self.payload)):
            fetcher.fetch(record, self.target)
        self.assertEqual(self.target.read_bytes(), self.payload)


if __name__ == "__main__":
    unittest.main()
