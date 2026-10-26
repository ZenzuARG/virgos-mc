import hashlib
import io
import sys
import json
import copy
import tempfile
import unittest
import zipfile
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from create_addons_lab import artifacts as a
from dh_fullpack_lab import policy

SCRATCH = Path(tempfile.mkdtemp(prefix='virgos-addons-artifact-tests-'))
print('Addon artifact test scratch:', SCRATCH)


class DownloadTests(unittest.TestCase):
    def fixture(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as jar:
            jar.writestr('META-INF/mods.toml', '[[mods]]\nmodId="fixture"\nversion="1"\n')
        content = stream.getvalue()
        spec = {'id': 'version', 'project': 'project', 'version': '1', 'filename': 'fixture.jar'}
        file = {'primary': True, 'filename': 'fixture.jar', 'size': len(content),
                'url': 'https://cdn.modrinth.com/data/project/versions/version/fixture.jar',
                'hashes': {kind: hashlib.new(kind, content).hexdigest() for kind in ['sha1', 'sha512']}}
        metadata = {'id': 'version', 'project_id': 'project', 'version_number': '1',
                    'loaders': ['forge'], 'game_versions': ['1.20.1'], 'files': [file]}
        return spec, metadata, content

    def test_hash_mismatch_is_rejected(self):
        spec, metadata, content = self.fixture()
        metadata['files'][0]['hashes']['sha512'] = '0' * 128
        with self.assertRaises(ValueError):
            a.validate_download(metadata, spec, content)

    def test_identity_loader_filename_url_size_both_hashes_and_jar_are_checked(self):
        spec, good, content = self.fixture()
        self.assertEqual(a.validate_download(good, spec, content), content)
        bad_values = [('id', 'other'), ('project_id', 'other'), ('version_number', '2'),
                      ('loaders', ['fabric']), ('game_versions', ['1.21.1'])]
        for key, value in bad_values:
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): a.validate_download(bad, spec, content)
        for key, value in [('filename', '../fixture.jar'), ('url', 'https://evil.test/fixture.jar'),
                           ('url', good['files'][0]['url'] + '?token=x'), ('size', len(content) + 1),
                           ('hashes', {'sha512': good['files'][0]['hashes']['sha512']})]:
            bad = copy.deepcopy(good); bad['files'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): a.validate_download(bad, spec, content)
        bad = copy.deepcopy(good); bad['files'].append(copy.deepcopy(bad['files'][0]))
        with self.assertRaises(ValueError): a.validate_download(bad, spec, content)
        bad = copy.deepcopy(good); corrupt = b'not a jar'
        bad['files'][0].update(size=len(corrupt), hashes={k: hashlib.new(k, corrupt).hexdigest() for k in ['sha1', 'sha512']})
        with self.assertRaises(ValueError): a.validate_download(bad, spec, corrupt)

    def test_dependency_ranges_are_strict_and_optional_is_not_required(self):
        for version, required, expected in [('6.0.8', '[6.0.2,6.1.0)', True), ('6.1.0', '[6.0.2,6.1.0)', False),
                                             ('47.4.22', '[47,)', True), ('1.20.1', '[1.20.1]', True),
                                             ('1.20.1', '(1.20.1,1.21)', False), ('6.0.8', '[6.0.8.0]', True)]:
            self.assertEqual(a.satisfies(version, required), expected)
        for version, required in [('6.0.8-beta', '[6,)'), ('6.0.8', 'latest'), ('6.0.8', '[6,),[7,)')]:
            with self.assertRaises(ValueError): a.satisfies(version, required)
        descriptor = {'mods': [], 'dependencies': [{'modId': 'absent', 'mandatory': False}]}
        a.check_dependencies([descriptor], {})
        for installed in [{}, {'create': {'6.0.1'}}, {'create': {'6.0.8', '6.0.9'}}]:
            descriptor['dependencies'] = [{'modId': 'create', 'mandatory': True, 'versionRange': '[6.0.2,6.1.0)'}]
            with self.assertRaises(ValueError): a.check_dependencies([descriptor], installed)

    def test_existing_inspector_recurses_embedded_descriptors_without_import_side_effects(self):
        _, _, inner = self.fixture()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as jar:
            jar.writestr('META-INF/mods.toml', '[[mods]]\nmodId="outer"\nversion="1"\n')
            jar.writestr('META-INF/jarjar/metadata.json', json.dumps({'jars': [{'path': 'META-INF/jars/inner.jar'}]}))
            jar.writestr('META-INF/jars/inner.jar', inner)
        data = stream.getvalue(); a.check_crc(data)
        result = a.inspector()(a.MemoryJar('outer.jar', data))
        self.assertEqual([m['id'] for m in result['mods']], ['outer', 'fixture'])
        self.assertTrue(result['embedded'])

    def test_valid_upstream_hashes_do_not_bypass_jar_crc(self):
        spec, metadata, content = self.fixture()
        with zipfile.ZipFile(io.BytesIO(content)) as jar:
            item = jar.getinfo('META-INF/mods.toml')
            offset = item.header_offset + 30 + len(item.filename.encode()) + len(item.extra)
        corrupt = bytearray(content); corrupt[offset] ^= 1; corrupt = bytes(corrupt)
        metadata['files'][0]['hashes'] = {k: hashlib.new(k, corrupt).hexdigest() for k in ['sha1', 'sha512']}
        with self.assertRaises(ValueError): a.validate_download(metadata, spec, corrupt)


class StageTests(DownloadTests):
    serial = 0

    def setUp(self):
        StageTests.serial += 1
        self.home = SCRATCH / str(StageTests.serial); self.home.mkdir()
        self.output = self.home / 'output'
        self.lock = self.home / 'mods.lock.json'
        self.lock.write_text(json.dumps({'minecraft': '1.20.1', 'forge': '47.4.22', 'artifacts': []}))
        self.spec, self.metadata, self.content = self.fixture()
        self.spec['mod'] = 'fixture'
        self.requests = []

    def transport(self, url, binary=False):
        self.requests.append(url)
        return self.content if binary else copy.deepcopy(self.metadata)

    def fetch(self):
        with mock.patch.object(a, 'OUTPUT_ROOT', self.output), mock.patch.object(a, 'SPECS', {'fixture': self.spec}):
            return a.fetch(self.output, self.lock, self.transport)

    def test_rejected_hash_leaves_no_output_and_optional_projects_are_not_fetched(self):
        self.metadata['files'][0]['hashes']['sha1'] = '0' * 40
        with self.assertRaises(ValueError): self.fetch()
        self.assertFalse(self.output.exists())
        self.metadata['files'][0]['hashes']['sha1'] = hashlib.sha1(self.content).hexdigest()
        self.metadata['dependencies'] = [{'dependency_type': 'optional', 'project_id': 'optional'}]
        self.requests.clear()
        report = self.fetch()
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(report['addons']['fixture']['sha256'], hashlib.sha256(self.content).hexdigest())
        self.assertEqual((self.output / 'upstream/fixture.jar').read_bytes(), self.content)
        with self.assertRaises(ValueError): self.fetch()  # No replacement of completed evidence.

    def test_paths_and_unknown_required_projects_refuse_before_writes(self):
        with self.assertRaises(ValueError): a.fetch(self.home / 'not-authorized', self.lock, self.transport)
        self.assertEqual(self.requests, [])
        self.metadata['dependencies'] = [{'dependency_type': 'required', 'project_id': 'unselected'}]
        with self.assertRaises(ValueError): self.fetch()
        self.assertFalse(self.output.exists())

    def test_link_guard_and_missing_required_mod_leave_no_output(self):
        with mock.patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaises(ValueError): self.fetch()
        self.assertFalse(self.output.exists())
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as jar:
            jar.writestr('META-INF/mods.toml', '[[mods]]\nmodId="fixture"\nversion="1"\n'
                '[[dependencies.fixture]]\nmodId="missing"\nmandatory=true\nversionRange="[1,)"\n')
        self.content = stream.getvalue()
        self.metadata['files'][0].update(size=len(self.content), hashes={
            k: hashlib.new(k, self.content).hexdigest() for k in ['sha1', 'sha512']})
        with self.assertRaises(ValueError): self.fetch()
        self.assertFalse(self.output.exists())

    def test_variants_preserve_baseline_and_reject_tampering(self):
        self.fetch()
        base = self.home / 'base'; base.mkdir()
        client = self.home / 'client'; (client / 'mods').mkdir(parents=True)
        (client / 'mods/DistantHorizons-3.3.3.jar').write_bytes(b'original')
        files = []
        for filename in ['DistantHorizons-3.3.3.jar', 'virgos_dh_compat-0.1.0.jar', 'virgos_local_qa-2.0.0.jar']:
            (base / filename).write_bytes(b'base')
            files.append({'filename': filename, 'sha256': hashlib.sha256(b'base').hexdigest()})
        (base / 'compat-manifest.json').write_text(json.dumps({'schema': 1,
            'originalDhSha256': hashlib.sha256(b'original').hexdigest(), 'artifacts': files}))
        with mock.patch.object(a, 'OUTPUT_ROOT', self.output), mock.patch.object(a, 'SPECS', {'fixture': self.spec}), \
                mock.patch.object(a, 'VARIANTS', {'baseline': (), 'combined': ('fixture',)}):
            path = self.output / 'upstream/fixture.jar'; path.write_bytes(b'tampered')
            with self.assertRaises(ValueError): a.variants(self.output, base, client)
            self.assertFalse((self.output / 'variant-artifacts').exists())
            path.write_bytes(self.content)
            result = a.variants(self.output, base, client)
            self.assertEqual({p.name for p in Path(result['baseline']).glob('*.jar')}, {r['filename'] for r in files})
            self.assertTrue((Path(result['combined']) / 'fixture.jar').is_file())
            for value in result.values(): policy.verified_artifacts(value, client)


class AuthorizationTests(unittest.TestCase):
    def test_old_and_only_exact_new_variants_are_authorized(self):
        self.assertTrue(policy.authorized_lab(policy.AUTHORIZED_LAB))
        for name in a.VARIANTS: self.assertTrue(policy.authorized_lab(policy.ADDON_LAB_ROOT / name))
        for path in [policy.ADDON_LAB_ROOT, policy.ADDON_LAB_ROOT / 'unknown',
                     policy.ADDON_LAB_ROOT / 'combined/child', Path('D:/proyectos/mc-server')]:
            self.assertFalse(policy.authorized_lab(path))


if __name__ == '__main__':
    unittest.main()
