"""Retained palettes must not hide later geometry or material updates."""
import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
try:
    spec = importlib.util.spec_from_file_location('dh_shared_checker', SCRIPTS / 'check-dh-fullpack-lab.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
finally:
    sys.path.pop(0)


class ServerUpdateTests(unittest.TestCase):
    def test_detects_data_only_and_mapping_only_updates_but_not_identical(self):
        previous = {'Data': 'old-data', 'Mapping': 'known-palette'}
        for current, changed in [
            ({'Data': 'new-data', 'Mapping': 'known-palette'}, True),
            ({'Data': 'old-data', 'Mapping': 'new-palette'}, True),
            (dict(previous), False),
            (None, False),
        ]:
            with self.subTest(current=current):
                proof = checker.Proof.__new__(checker.Proof)
                proof.row = lambda role: current
                self.assertEqual(proof.changed(previous), current if changed else None)


if __name__ == '__main__':
    unittest.main()
