"""Offline synthetic release preparation; no Gradle/JVM/network is launched."""
import hashlib
import importlib.util
import json
import os
import re
import struct
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('prepare_dh_release', Path(__file__).parents[1] / 'scripts/prepare-dh-release.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def identity_class(release, fingerprint):
    strings = ['RELEASE', 'FINGERPRINT', 'ConstantValue', release, fingerprint]
    pool = b''.join(b'\x01' + struct.pack('>H', len(s)) + s.encode() for s in strings)
    pool += b'\x08\x00\x04\x08\x00\x05'
    header = b'\xca\xfe\xba\xbe\x00\x00\x00\x3d' + struct.pack('>H', 8) + pool
    fields = b''.join(struct.pack('>HHHHHIH', 0x19, n, 1, 1, 3, 2, value) for n, value in [(1, 6), (2, 7)])
    return header + struct.pack('>HHHHH', 0x21, 0, 0, 0, 2) + fields


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='virgos-prepare-dh-test-'))
        print('SCRATCH=' + str(self.base))
        self.root = self.base / 'source'; self.cache = self.base / 'cache'; self.output = self.base / 'inputs'
        self.calls = []
        self.metadata = self.root / 'pack/candidates/2.1.0/release.json'
        self.write(self.metadata, {'version': '2.1.0', 'installer': 12, 'clientRelease': '2.1.0-r12', 'clientFingerprint': 'virgos-client-2.1.0-r12'})
        self.jar(self.cache / 'pack/downloads/DistantHorizons-3.3.3-1.20.1-fabric-forge.jar', {
            'LICENSE.txt': b'license', 'LICENSE.LESSER.txt': b'lesser', 'LICENSE-LOGOS.txt': b'logos',
            'com/seibel/distanthorizons/core/dataObjects/fullData/sources/FullDataSourceV2.class': b'original'})
        asm = self.put(self.cache / 'pack/tools/asm.jar', b'asm')
        sources = [self.put(self.cache / ('pack/sources/' + n), b'pinned source ' + n.encode()) for n in ['main.zip', 'core.zip']]
        original = self.cache / 'pack/downloads/DistantHorizons-3.3.3-1.20.1-fabric-forge.jar'
        self.write(self.root / 'pack/dh-upstream.lock.json', {'schema': 1, 'filename': original.name, 'hash_algorithm': 'sha256', 'hash': M.sha(original),
            'source_commit': 'pinned-main', 'asm': {'file': asm.name, 'hash_algorithm': 'sha256', 'hash': M.sha(asm)},
            'source_archives': [{'filename': p.name, 'sha256': M.sha(p), 'commit': 'pinned-' + p.stem} for p in sources]})
        self.write(self.root / 'pack/administration.lock.json', [{'filename': 'AuthMe.jar'}, {'filename': 'DistantHorizonsSupport-0.14.0.jar'}])
        self.put(self.root / 'dev/virgos-core/src/shared/java/mc/virgos/update/ClientRelease.java', b'public static final String RELEASE = "2.1.0-r12"; public static final String FINGERPRINT = "virgos-client-2.1.0-r12";')
        for role in ['core', 'codex']:
            self.jar(self.root / f'dev/virgos-core/build/libs/virgos_{role}-2.0.0.jar', {'mc/virgos/update/ClientRelease.class': identity_class('2.1.0-r12', 'virgos-client-2.1.0-r12')})
        for name in ['README.md', 'build.gradle', 'settings.gradle', 'gradle.properties', 'build-artifacts.py', 'patcher/PatchDh.java', 'src/main/java/Test.java', 'src/main/resources/mods.toml', 'qa/Private.java', 'src/test/java/Test.java']:
            self.put(self.root / 'dev/dh-compat' / name, b'synthetic source')
        self.put(self.root / 'dev/virgos-core/gradlew', b'wrapper')
        self.put(self.root / 'dev/virgos-core/gradlew.bat', b'wrapper')
        self.java = self.base / 'jdk'; self.java.mkdir()

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data); return path

    def write(self, path, data):
        return self.put(path, json.dumps(data).encode())

    def jar(self, path, entries):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w') as z:
            for n, b in entries.items(): z.writestr(n, b)

    def runner(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if 'check' in command:
            self.jar(self.root / 'dev/dh-compat/build/libs/virgos_dh_compat-0.1.0.jar', {'addon': b'compiled'})
        else:
            output = Path(command[command.index('--output') + 1]); output.mkdir()
            addon = Path(command[command.index('--addon') + 1])
            original = Path(command[command.index('--original') + 1])
            self.put(output / original.name, original.read_bytes()); self.put(output / addon.name, addon.read_bytes())
            self.write(output / 'compat-manifest.json', {'artifacts': [{'filename': p.name, 'sha256': M.sha(p)} for p in output.glob('*.jar')]})

    def prepare(self, **kwargs):
        return M.prepare(self.metadata, self.cache, self.output, self.java, offline=True, root=self.root, runner=self.runner, **kwargs)

    def test_prepares_all_roles_sources_without_published_mutation(self):
        before = {p: p.read_bytes() for p in (self.root / 'pack').rglob('*') if p.is_file()}
        result = self.prepare()
        print('BUILD_SCRATCH=' + result['buildScratch'])
        lock = json.loads((self.output / 'custom-artifacts.lock.json').read_text())
        self.assertEqual(len(lock['artifacts']), 4)
        self.assertEqual(result['clientRelease'], '2.1.0-r12')
        self.assertTrue(all(not Path(a['local_source']).is_absolute() for a in lock['artifacts']))
        admin = json.loads((self.output / 'administration.lock.json').read_text())
        self.assertEqual(admin, [{'filename': 'AuthMe.jar'}])
        metadata = json.loads((self.output / 'release.json').read_text())
        self.assertEqual(len(metadata['sourceFiles']), 7)
        with zipfile.ZipFile(self.output / 'artifacts/Virgos-DH-modifications-source.zip') as z:
            self.assertTrue(any(n.endswith('PatchDh.java') for n in z.namelist()))
            self.assertFalse(any('/qa/' in n or '/test/' in n for n in z.namelist()))
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertIn('--offline', self.calls[0][0])

    def test_existing_corresponding_sources_preserved_and_verified_before_children(self):
        extra = self.put(self.metadata.parent / 'sources/Existing-GPL.txt', b'full existing license')
        current = json.loads(self.metadata.read_text())
        current['sourceFiles'] = [{'filename': extra.name, 'local_source': 'sources/' + extra.name,
                                   'sha256': M.sha(extra), 'size': extra.stat().st_size}]
        self.write(self.metadata, current)
        self.prepare()
        staged = json.loads((self.output / 'release.json').read_text())
        self.assertEqual(len(staged['sourceFiles']), 8)
        self.assertEqual((self.output / 'artifacts' / extra.name).read_bytes(), extra.read_bytes())

    def test_existing_source_rejection_has_no_output_or_children(self):
        for item in [
            {'filename': 'source.zip', 'local_source': '../outside.zip', 'sha256': '0' * 64},
            {'filename': 'source.zip', 'local_source': 'missing.zip', 'sha256': '0' * 64},
            {'filename': 'virgos_local_qa.zip', 'local_source': 'missing.zip', 'sha256': '0' * 64},
        ]:
            current = json.loads(self.metadata.read_text());current['sourceFiles'] = [item]
            self.write(self.metadata, current)
            with self.assertRaises((ValueError, OSError)): self.prepare()
            self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_tree_stages_gpl_and_server_plugin_without_client_role(self):
        import test_tree_release_build as tree_tests
        fixture = tree_tests.TreeReleaseTests('test_mock_build_and_strict_artifact_roles_hash_size_paths')
        fixture.setUp()
        with patch.dict(tree_tests.M.EXPECTED, fixture.expected, clear=True):
            fixture.build()
            self.write(self.root / 'pack/administration.lock.json', [{'filename': 'AuthMe.jar'},
                {'project': 'tree-feller', 'filename': tree_tests.M.JAR, 'hash': fixture.expected[tree_tests.M.JAR],
                 'hash_algorithm': 'sha256', 'sides': ['server'], 'mode': 'required'}])
            with patch.object(M, 'tree_bundle', side_effect=tree_tests.M.load_artifacts):
                self.prepare(tree_artifacts=fixture.output)
        release = json.loads((self.output / 'release.json').read_text())
        self.assertEqual(len(release['sourceFiles']), 9)
        self.assertTrue((self.output / 'artifacts' / tree_tests.M.SOURCE).is_file())
        custom = json.loads((self.output / 'custom-artifacts.lock.json').read_text())['artifacts']
        self.assertEqual(sum('client' in item['sides'] for item in custom), 3)
        self.assertFalse(any('TreeFeller' in item['filename'] or 'SkinsRestorer' in item['filename'] for item in custom))
        admin = json.loads((self.output / 'administration.lock.json').read_text())
        tree = next(item for item in admin if item.get('project') == 'tree-feller')
        self.assertEqual(tree['local_source'], str(self.output / 'artifacts' / tree_tests.M.JAR))

    def test_bad_tree_manifest_rejects_before_children(self):
        directory = self.base / 'tree';directory.mkdir()
        self.write(directory / 'tree-release.json', {'schema': 1, 'artifacts': []})
        with self.assertRaises(ValueError): self.prepare(tree_artifacts=directory)
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_duplicate_existing_sources_reject_before_children(self):
        extra = self.put(self.metadata.parent / 'license.txt', b'license')
        record = {'filename': extra.name, 'local_source': extra.name, 'sha256': M.sha(extra)}
        current = json.loads(self.metadata.read_text());current['sourceFiles'] = [record, record]
        self.write(self.metadata, current)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_existing_source_hash_size_rejection_has_no_children(self):
        extra = self.put(self.metadata.parent / 'license.txt', b'complete existing license')
        for change in [{'sha256': '0' * 64}, {'size': 1}]:
            item = {'filename': extra.name, 'local_source': extra.name, 'sha256': M.sha(extra), 'size': extra.stat().st_size}
            item.update(change)
            current = json.loads(self.metadata.read_text());current['sourceFiles'] = [item]
            self.write(self.metadata, current)
            with self.assertRaises(ValueError):self.prepare()
            self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_source_archive_traversal_rejected_before_children(self):
        extra = self.metadata.parent / 'source.zip'
        self.jar(extra, {'../escaped.txt': b'not safe'})
        current = json.loads(self.metadata.read_text())
        current['sourceFiles'] = [{'filename': extra.name, 'local_source': extra.name, 'sha256': M.sha(extra)}]
        self.write(self.metadata, current)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_bad_dependencies_reject_without_output_or_children(self):
        for relative in ['pack/tools/asm.jar', 'pack/sources/main.zip', 'pack/downloads/DistantHorizons-3.3.3-1.20.1-fabric-forge.jar']:
            path = self.cache / relative; old = path.read_bytes(); path.write_bytes(b'wrong')
            with self.assertRaises(ValueError): self.prepare()
            self.assertFalse(self.output.exists()); self.assertFalse(self.calls)
            path.write_bytes(old)

    def test_embedded_or_source_identity_reject_before_children(self):
        path = self.root / 'dev/virgos-core/build/libs/virgos_codex-2.0.0.jar'
        self.jar(path, {'mc/virgos/update/ClientRelease.class': identity_class('2.0.0-r11', 'virgos-client-2.0.0-r11')})
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists()); self.assertFalse(self.calls)
        self.jar(path, {'mc/virgos/update/ClientRelease.class': identity_class('2.1.0-r12', 'virgos-client-2.1.0-r12')})
        self.put(self.root / 'dev/virgos-core/src/shared/java/mc/virgos/update/ClientRelease.java', b'public static final String RELEASE = "old";')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists()); self.assertFalse(self.calls)

    def test_output_overlap_rejected_before_children(self):
        self.output = self.cache / 'inputs'
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists()); self.assertFalse(self.calls)

    def test_nonempty_output_preserved_and_no_children(self):
        sentinel = self.put(self.output / 'sentinel', b'unchanged')
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(sentinel.read_bytes(), b'unchanged'); self.assertFalse(self.calls)

    def test_workflow_pointer_and_tag_check_before_build(self):
        source = (Path(__file__).parents[1] / '.github/workflows/release.yml').read_text('utf-8-sig')
        snippet = re.search(r"          python -B - <<'PY'\n(.*?)          PY", source, re.S).group(1)
        snippet = '\n'.join(line[10:] for line in snippet.splitlines())
        self.write(self.root / 'pack/candidates/current.json', {'version': '2.1.0'})
        environment = self.base / 'github-env'
        before = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ, {'GITHUB_ENV': str(environment), 'REF_TYPE': 'branch', 'REF_NAME': 'main', 'REQUESTED_TAG': ''}):
                exec(compile(snippet, '<workflow-selection>', 'exec'), {})
                self.assertIn('pack/candidates/2.1.0/release.json', environment.read_text())
                previous = environment.read_bytes()
                with patch.dict(os.environ, {'REQUESTED_TAG': 'v2.0.0'}), self.assertRaises(SystemExit):
                    exec(compile(snippet, '<workflow-selection>', 'exec'), {})
                self.assertEqual(environment.read_bytes(), previous)
        finally:
            os.chdir(before)
        self.assertIn("if: startsWith(github.ref, 'refs/tags/') || inputs.release_tag != ''", source)
        self.assertIn('GH_TOKEN: ${{ github.token }}', source)


if __name__ == '__main__': unittest.main()
