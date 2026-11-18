"""Pin separate server release and compatible client packaging identities."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseSelectionTest(unittest.TestCase):
    def test_server_hotfix_selects_explicit_client_packaging_metadata(self):
        workflow = (ROOT / '.github/workflows/release.yml').read_text()
        source = textwrap.dedent(workflow.split("python -B - <<'PY'", 1)[1].split('\n          PY', 1)[0])
        with tempfile.TemporaryDirectory(prefix='virgos-release-selection-') as temporary:
            root = Path(temporary)
            candidate = root / 'pack/candidates/3.0.7'
            candidate.mkdir(parents=True)
            (candidate.parent / 'current.json').write_text(json.dumps({'version': '3.0.7'}))
            for separate in (False, True):
                metadata = {'version': '3.0.7', 'clientRelease': '3.0.6', 'installer': 26}
                expected = 'pack/candidates/3.0.7/release.json'
                if separate:
                    expected = 'pack/candidates/3.0.7/client-release.json'
                    metadata['clientPackagingMetadata'] = expected
                    (root / expected).write_text(json.dumps({'version': '3.0.6', 'clientRelease': '3.0.6', 'installer': 26}))
                (candidate / 'release.json').write_text(json.dumps(metadata))
                output = root / 'env'
                output.write_text('')
                result = subprocess.run([sys.executable, '-c', source], cwd=root, capture_output=True, text=True,
                                        env={**os.environ, 'GITHUB_ENV': str(output), 'REQUESTED_TAG': 'v3.0.7',
                                             'REF_TYPE': 'branch', 'REF_NAME': 'main'})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.read_text(), 'CANDIDATE_METADATA=' + expected + '\n')
