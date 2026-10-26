"""Pure Python release boundaries; the builder and anonymous downloads are mocked."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('tree_release_build', ROOT / 'scripts/build-tree-release.py')
M = importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class TreeReleaseTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='virgos-tree-release-test-'))
        print('SCRATCH=' + str(self.base))
        self.root = self.base / 'source';self.module = self.root / 'dev/tree-feller'
        self.module.mkdir(parents=True);self.cache = self.base / 'cache';self.cache.mkdir()
        self.output = self.base / 'output';self.jdk = self.base / 'jdk'
        for name in ['java', 'javac']:
            path = self.jdk / 'bin' / (name + ('.exe' if os.name == 'nt' else ''))
            path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(b'fixture; never executed')
        for name in ['UPSTREAM.json', 'LICENSE', 'build.py']:
            shutil.copyfile(ROOT / 'dev/tree-feller' / name, self.module / name)
        shutil.copytree(ROOT / 'dev/tree-feller/resources', self.module / 'resources')
        (self.module / 'patches').mkdir()
        self.pin = json.loads((self.module / 'UPSTREAM.json').read_text())
        self.license = (self.module / 'LICENSE').read_bytes()
        names = [r[0] for r in M.providers(self.pin)]
        for index, name in enumerate(names):
            entries = {'fixture': b'provider'}
            if index == 1: entries = {'source/LICENSE': self.license}
            if index == 3: entries = {'net/coreprotect/CoreProtect.class': b'public-api'}
            self.zip(self.cache / name, entries)
        digests = [M.H.sha(self.cache / name) for name in names]
        self.pin['jar']['sha256'], self.pin['source']['sha256'] = digests[:2]
        self.pin['compile_inputs']['ketting_universal_sha256'] = digests[2]
        self.pin['compile_inputs']['coreprotect_sha256'] = digests[3]
        self.pin['compile_inputs']['additional_jars'] = dict(zip(names[4:], digests[4:]))
        self.pin['coreprotect_compile_provider']['referenced_classes_sha256'] = {
            'net/coreprotect/CoreProtect.class': hashlib.sha256(b'public-api').hexdigest()}
        (self.module / 'UPSTREAM.json').write_text(json.dumps(self.pin))
        self.fake = self.base / 'built';self.fake.mkdir()
        self.zip(self.fake / M.JAR, {'plugin.yml': ('name: TreeFeller\nversion: ' + M.VERSION).encode()})
        self.zip(self.fake / M.SOURCE, {'upstream/LICENSE': self.license,'virgos-fork/LICENSE': self.license,
            'virgos-fork/build.py': b'full fixture builder','pinned-inputs/source.zip': (self.cache / names[1]).read_bytes(),
            'pinned-inputs/TreeFeller-1.33.0.jar': (self.cache / names[0]).read_bytes()})
        (self.fake / M.LICENSE).write_bytes(self.license)
        self.expected = {n: M.H.sha(self.fake / n) for n in M.EXPECTED}
        self.calls = []

    def zip(self, path, entries):
        with zipfile.ZipFile(path, 'w') as archive:
            for name, content in entries.items():archive.writestr(name, content)

    def runner(self, command, **kwargs):
        self.calls.append(command);self.output.mkdir()
        for name in [M.JAR, M.SOURCE]:shutil.copyfile(self.fake / name, self.output / name)

    def build(self, **kwargs):
        with patch.object(M, 'FORK_SHA256', M.source_fingerprint(self.module)):
            return M.build(self.cache, self.output, self.jdk, offline=True, root=self.root,
                           runner=self.runner, downloader=lambda url: self.fail('Offline network call'), **kwargs)

    def test_offline_plan_has_exact_inputs_no_jvm_or_output(self):
        result = self.build(plan=True)
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)
        command = result['command']
        self.assertEqual(command.count('--classpath'), 2)
        self.assertEqual(command[-1], '--tests')
        self.assertEqual(Path(command[command.index('--coreprotect-api') + 1]).name, 'CoreProtect-CE-24.1.jar')
        self.assertNotIn('virgos.1.jar', ' '.join(command))

    def test_missing_wrong_and_unsafe_inputs_reject_before_output(self):
        path = self.cache / M.providers(self.pin)[0][0]
        original = path.read_bytes();path.write_bytes(b'wrong')
        with self.assertRaises(ValueError):self.build()
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)
        path.write_bytes(original)
        self.cache = self.base / 'missing-cache'
        with self.assertRaises(ValueError):self.build()
        self.assertFalse(self.cache.exists());self.assertFalse(self.output.exists())
        self.cache = self.base / 'cache';self.output = self.root / 'unsafe-output'
        with self.assertRaises(ValueError):self.build()
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_mock_build_and_strict_artifact_roles_hash_size_paths(self):
        with patch.dict(M.EXPECTED, self.expected, clear=True):
            self.build();self.assertEqual(len(self.calls), 1)
            records = M.load_artifacts(self.output);self.assertEqual(len(records), 3)
            manifest = json.loads((self.output / 'tree-release.json').read_text())
            for field, value in [('sides', ['client']), ('local_source', '../escape.jar'), ('sha256', '0' * 64), ('size', 1)]:
                wrong = copy.deepcopy(manifest);wrong['artifacts'][0][field] = value
                (self.output / 'tree-release.json').write_text(json.dumps(wrong))
                before = {p.name: M.H.sha(p) for p in self.output.iterdir()}
                with self.assertRaises(ValueError):M.load_artifacts(self.output)
                self.assertEqual(before, {p.name: M.H.sha(p) for p in self.output.iterdir()})
            (self.output / 'tree-release.json').write_text(json.dumps(manifest))

    def test_changed_frozen_source_and_links_fail_before_children(self):
        with self.assertRaises(ValueError):
            M.build(self.cache, self.output, self.jdk, offline=True, root=self.root, runner=self.runner)
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)
        link = self.base / 'cache-link'
        try: link.symlink_to(self.cache, target_is_directory=True)
        except OSError:self.skipTest('Symlink privilege unavailable')
        self.cache = link
        with self.assertRaises(ValueError):self.build()
        self.assertFalse(self.output.exists());self.assertFalse(self.calls)

    def test_linux_style_checkout_retains_exact_frozen_fingerprint(self):
        checkout = self.base / 'lf-checkout'
        module = checkout / 'dev/tree-feller'
        shutil.copytree(ROOT / 'dev/tree-feller', module, ignore=shutil.ignore_patterns('__pycache__'))
        for path in module.rglob('*'):
            if path.is_file():path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
        M.load_pin(checkout)
        self.assertEqual(M.source_fingerprint(module), M.FORK_SHA256)
        path = module / 'src/main/java/mc/virgos/forestry/Forestry.java'
        path.write_bytes(path.read_bytes() + b'// changed\n')
        with self.assertRaises(ValueError):M.load_pin(checkout)

    def test_current_runtime_pin_and_release_boundaries(self):
        self.assertEqual(M.source_fingerprint(ROOT / 'dev/tree-feller'), M.FORK_SHA256)
        admin = json.loads((ROOT / 'pack/administration.lock.json').read_text())
        self.assertFalse(any('DistantHorizonsSupport' in i['filename'] for i in admin))
        core = next(i for i in admin if i['project'] == 'coreprotect')
        self.assertEqual(core['hash'], '1e0d93e1cc719cffb243b3b37a3e1c3ed2d9a37e65e31ab9b2d6b00ed740e8b7')
        for project in ['skinsrestorer', 'tree-feller']:
            self.assertEqual(next(i for i in admin if i['project'] == project)['sides'], ['server'])
        source = (ROOT / 'pack/server-overrides/plugins/SkinsRestorer/config.yml').read_text()
        for name in ['forceDefaultPermissions', 'alwaysApplyPremium', 'disableOnJoinSkins']:
            self.assertIn(name + ': false', source)
        for name in ['disableSkinCommand', 'disableSkullCommand', 'disableGUICommand']:
            self.assertIn(name + ': true', source)
        self.assertIn("mineskinAPIKey: ''", source)
        self.assertNotIn('Notch', source)
        self.assertTrue((ROOT / 'pack/server-overrides/plugins/SkinsRestorer/noautoupdate.txt').is_file())


if __name__ == '__main__':unittest.main()
