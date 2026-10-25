"""Build an offline synthetic distribution outside the worktree and inspect it."""
import hashlib
import json
import os
import time
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ClientReleaseContentsTest(unittest.TestCase):
    def test_distribution_contains_controls_policy_and_managed_allocation(self):
        with tempfile.TemporaryDirectory(prefix="virgos-release-contents-") as directory:
            fixture = Path(directory)
            for folder in ["scripts", "pack", "templates", "docs", ".cache/pack/downloads"]:
                (fixture / folder).mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "scripts/build-client-release.py", fixture / "scripts")
            for source in (ROOT / "templates").iterdir():
                if source.is_file():
                    shutil.copy2(source, fixture / "templates")
            shutil.copytree(ROOT / "pack/client-overrides", fixture / "pack/client-overrides")
            for name in ["keybindings.json", "shaderpack.lock.json"]:
                shutil.copy2(ROOT / "pack" / name, fixture / "pack" / name)
            shutil.copy2(ROOT / "docs/manual-jugadores.md", fixture / "docs")

            def write_json(name, value):
                (fixture / name).write_text(json.dumps(value), encoding="utf-8")

            payload = b"synthetic fixture, not a Minecraft mod"
            (fixture / ".cache/pack/downloads/fixture.jar").write_bytes(payload)
            write_json("pack/mods.lock.json", {
                "minecraft": "1.20.1", "forge": "47.4.22", "artifacts": [{
                    "filename": "fixture.jar", "sides": ["client"], "mode": "required",
                    "hash_algorithm": "sha512", "hash": hashlib.sha512(payload).hexdigest(),
                    "url": "https://cdn.modrinth.com/fixture.jar", "project": "fixture", "source": "fixture",
                }],
            })
            write_json("pack/current-release.json", {"version": "2.0.0", "installer": 6})
            write_json("pack/custom-artifacts.lock.json", {"artifacts": []})
            digest = hashlib.sha256(payload).hexdigest()
            (fixture / ".cache/java.zip").write_bytes(payload)
            (fixture / ".cache/pack/forge.jar").write_bytes(payload)
            write_json("pack/client-runtime.lock.json", {
                "minecraftJson": {"url": "https://piston-meta.mojang.com/fixture.json"},
                "java": {"file": "java.zip", "hash": digest},
                "forge": {"file": "forge.jar", "hash": digest},
            })
            result = subprocess.run([sys.executable, "-B", str(fixture / "scripts/build-client-release.py")],
                                    cwd=fixture, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(fixture / "dist/Virgos-MC-2.0.0-instalar.zip") as archive:
                self.assertIn("asistente/client-keybindings.ps1", archive.namelist())
                policy = json.loads(archive.read("asistente/keybindings.json"))
                self.assertEqual(policy, json.loads((ROOT / "pack/keybindings.json").read_text("utf-8")))
                common = archive.read("asistente/installer-common.ps1").decode("utf-8-sig")
                self.assertIn("function Get-VirgosClientMemoryMb { return 8192 }", common)
                options = archive.read("asistente/overrides/options.txt").decode("utf-8")
                self.assertIn("key_key.virgos_codex.open:key.keyboard.j", options)
                self.assertIn("key_iris.keybind.reload:key.keyboard.f8", options)
                self.assertFalse(any("virgos_local_qa" in name or "/saves/" in name for name in archive.namelist()))
            # Legacy CLI retains its payloads and its original file-mtime behavior.
            legacy = fixture / 'dist/Virgos-MC-2.0.0-instalar.zip'
            with zipfile.ZipFile(legacy) as archive:
                payloads = {name: archive.read(name) for name in archive.namelist()}
            os.utime(fixture / 'pack/keybindings.json', (946684800, 946684800))
            repeated = subprocess.run([sys.executable, '-B', str(fixture / 'scripts/build-client-release.py')],
                                      cwd=fixture, capture_output=True, text=True, timeout=30)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            with zipfile.ZipFile(legacy) as archive:
                self.assertEqual(payloads, {name: archive.read(name) for name in archive.namelist()})
                self.assertEqual(archive.getinfo('asistente/keybindings.json').date_time[0], time.localtime(946684800).tm_year)


class CandidateReleaseTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='virgos-release-candidate-'))
        print('SCRATCH=' + str(self.root))
        self.source = self.root / 'source'
        for directory in ['scripts', 'pack', 'templates', 'docs', '.cache/pack/downloads']:
            (self.source / directory).mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/build-client-release.py', self.source / 'scripts')
        shutil.copytree(ROOT / 'templates', self.source / 'templates', dirs_exist_ok=True)
        shutil.copytree(ROOT / 'pack/client-overrides', self.source / 'pack/client-overrides')
        for name in ['keybindings.json', 'shaderpack.lock.json']:
            shutil.copy2(ROOT / 'pack' / name, self.source / 'pack' / name)
        shutil.copy2(ROOT / 'docs/manual-jugadores.md', self.source / 'docs')
        self.downloads = self.root / 'downloads'; self.downloads.mkdir()
        self.runtime = self.root / 'runtime'; (self.runtime / 'pack').mkdir(parents=True)
        self.inputs = self.root / 'candidate'; self.inputs.mkdir()
        self.output = self.root / 'output'
        payload = b'fixture upstream content'
        (self.downloads / 'fixture.jar').write_bytes(payload)
        (self.source / '.cache/pack/downloads/fixture.jar').write_bytes(payload)
        self.mods = {'minecraft': '1.20.1', 'forge': '47.4.22', 'artifacts': [{
            'filename': 'fixture.jar', 'sides': ['client'], 'mode': 'required',
            'hash_algorithm': 'sha512', 'hash': hashlib.sha512(payload).hexdigest(),
            'url': 'https://cdn.modrinth.com/fixture.jar', 'project': 'fixture', 'source': 'fixture'}]}
        self.write(self.source / 'pack/mods.lock.json', self.mods)
        self.write(self.source / 'pack/current-release.json', {'version': '2.0.0', 'installer': 11})
        self.write(self.source / 'pack/custom-artifacts.lock.json', {'artifacts': []})
        digest = hashlib.sha256(payload).hexdigest()
        for cache in [self.runtime, self.source / '.cache']:
            (cache / 'java.zip').write_bytes(payload)
            (cache / 'pack/forge.jar').write_bytes(payload)
        self.write(self.source / 'pack/client-runtime.lock.json', {
            'minecraftJson': {'url': 'https://piston-meta.mojang.com/fixture.json'},
            'java': {'file': 'java.zip', 'hash': digest}, 'forge': {'file': 'forge.jar', 'hash': digest}})
        self.metadata = {'version': '2.1.0', 'installer': 12,
                         'clientRelease': '2.1.0-r1', 'clientFingerprint': 'virgos-client-2.1.0-r1'}
        self.write(self.inputs / 'release.json', self.metadata)
        self.custom = {'schema': 1, 'artifacts': []}
        for name, modid in [('virgos_codex-2.1.0.jar', 'virgos_codex'),
                            ('DistantHorizons-3.3.3-1.20.1-fabric-forge.jar', 'distanthorizons'),
                            ('virgos_dh_compat-0.1.0.jar', 'virgos_dh_compat')]:
            jar = self.inputs / name
            with zipfile.ZipFile(jar, 'w') as archive:
                archive.writestr('META-INF/mods.toml', f'modLoader="javafml"\n[[mods]]\nmodId="{modid}"\nversion="3.3.3"\n')
                archive.writestr('LICENSE.txt', 'fixture original license notice')
                if modid == 'virgos_codex':
                    archive.writestr('mc/virgos/codex/ProfileScreen.class', b'fixture')
                if modid == 'distanthorizons':
                    archive.writestr('assets/distanthorizons/shaders/test/gl/frag.frag', b'original runtime shader')
                    archive.writestr('com/seibel/distanthorizons/common/render/openGl/test/GlTestTriangleRenderer.class', b'original runtime diagnostic')
            self.custom['artifacts'].append({'filename': name, 'local_source': name,
                'sides': ['client'], 'mode': 'required', 'hash_algorithm': 'sha256',
                'hash': hashlib.sha256(jar.read_bytes()).hexdigest()})
        self.write(self.inputs / 'custom.json', self.custom)

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def command(self, extra=()):
        return [sys.executable, '-B', str(self.source / 'scripts/build-client-release.py'),
                '--release-metadata', str(self.inputs / 'release.json'), '--custom-lock', str(self.inputs / 'custom.json'),
                '--output', str(self.output), '--downloads', str(self.downloads), '--runtime-cache', str(self.runtime), *extra]

    def invoke(self, command=None):
        return subprocess.run(command or self.command(), cwd=self.source, capture_output=True, text=True, timeout=30)

    def test_candidate_bundles_required_roles_and_preserves_inputs(self):
        before = {p: p.read_bytes() for base in [self.source / 'pack', self.source / '.cache', self.downloads, self.runtime, self.inputs]
                  for p in base.rglob('*') if p.is_file()}
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.output / 'Virgos-MC-2.1.0-instalar.zip') as archive:
            manifest = json.loads(archive.read('asistente/cliente.lock.json'))
            self.assertEqual(manifest['clientRelease'], '2.1.0-r1')
            self.assertEqual(manifest['clientFingerprint'], 'virgos-client-2.1.0-r1')
            self.assertIn('asistente/dh-client-settings.ps1', archive.namelist())
            self.assertIn('enableAutoUpdater = false', archive.read('asistente/overrides/config/DistantHorizons.toml').decode())
            custom = [x for x in manifest['files'] if x.get('bundled')]
            self.assertEqual(len(custom), 3)
            for item in custom:
                self.assertFalse(item['optional'])
                self.assertNotIn('url', item)
                original = (self.inputs / item['filename']).read_bytes()
                self.assertEqual(archive.read('asistente/bundled/' + item['filename']), original)
        with zipfile.ZipFile(self.output / 'Virgos-MC-2.1.0.mrpack') as archive:
            for item in self.custom['artifacts']:
                self.assertEqual(archive.read('overrides/mods/' + item['filename']),
                                 (self.inputs / item['filename']).read_bytes())
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse((self.source / 'dist').exists())

    def test_explicit_archives_reproduce_bytes_in_separate_outputs(self):
        first = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        other = self.root / 'second-output'
        os.utime(self.source / 'pack/keybindings.json', (946684800, 946684800))
        second = self.invoke(self.command(['--output', str(other)]))
        self.assertEqual(second.returncode, 0, second.stderr)
        for name in ['Virgos-MC-2.1.0-instalar.zip', 'Virgos-MC-2.1.0.mrpack']:
            self.assertEqual((self.output / name).read_bytes(), (other / name).read_bytes())
            with zipfile.ZipFile(other / name) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                self.assertTrue(all(i.date_time == (2026, 1, 1, 0, 0, 0) and i.create_system == 3
                                    and i.external_attr >> 16 == 0o100644 for i in archive.infolist()))

    def test_rejects_hash_and_metadata_without_output(self):
        self.custom['artifacts'][0]['hash'] = '0' * 64
        self.write(self.inputs / 'custom.json', self.custom)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('hash', result.stderr.lower())
        self.assertFalse(self.output.exists())

    def test_candidate_includes_verified_corresponding_sources(self):
        source = self.inputs / 'changes.txt'
        source.write_bytes(b'fixture source and modification notice')
        self.metadata['sourceFiles'] = [{'filename': source.name, 'local_source': source.name,
                                        'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]
        self.write(self.inputs / 'release.json', self.metadata)
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ['Virgos-MC-2.1.0-instalar.zip', 'Virgos-MC-2.1.0.mrpack']:
            with zipfile.ZipFile(self.output / name) as archive:
                self.assertEqual(archive.read('sources/changes.txt'), source.read_bytes())

    def test_source_hash_rejection_leaves_candidate_unwritten(self):
        (self.inputs / 'changes.txt').write_bytes(b'original')
        self.metadata['sourceFiles'] = [{'filename': 'changes.txt', 'local_source': 'changes.txt', 'sha256': '0' * 64}]
        self.write(self.inputs / 'release.json', self.metadata)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.metadata['version'] = '../escape'
        self.write(self.inputs / 'release.json', self.metadata)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('version', result.stderr.lower())
        self.assertFalse(self.output.exists())

    def test_rejects_partial_mixed_and_overlapping_paths(self):
        commands = [self.command() + ['--candidate-v2'],
                    [sys.executable, '-B', str(self.source / 'scripts/build-client-release.py'),
                     '--release-metadata', str(self.inputs / 'release.json')],
                    self.command() + ['--output', str(self.downloads)]]
        for command in commands:
            result = self.invoke(command)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.output.exists())

    def test_rejects_wrong_modid_and_qa_even_with_matching_hash(self):
        item = self.custom['artifacts'][0]
        jar = self.inputs / item['filename']
        for modid, extra in [('virgos_codex', 'mc/virgos/qa/ClientProbe.class'),
                             ('virgos_codex', 'mc/virgos/codex/ProfileScreenTest.class'),
                             ('virgos_local_qa', 'mc/virgos/qa/ClientProbe.class'),
                             ('unrelated_mod', 'example/Main.class')]:
            with zipfile.ZipFile(jar, 'w') as archive:
                archive.writestr('META-INF/mods.toml', f'[[mods]]\nmodId="{modid}"\n')
                archive.writestr(extra, b'fixture')
                if modid == 'virgos_codex':
                    archive.writestr('mc/virgos/codex/ProfileScreen.class', b'fixture UI')
            item['hash'] = hashlib.sha256(jar.read_bytes()).hexdigest()
            self.write(self.inputs / 'custom.json', self.custom)
            result = self.invoke()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('artifact', result.stderr.lower())
            self.assertFalse(self.output.exists())

    def test_optional_mods_input_replaces_upstream_dh_and_ignores_server_core(self):
        self.mods['artifacts'].append({**self.mods['artifacts'][0],
            'filename': 'DistantHorizons-3.3.3-1.20.1-fabric-forge.jar',
            'url': 'https://cdn.modrinth.com/original-dh.jar'})
        self.write(self.inputs / 'mods.json', self.mods)
        self.custom['artifacts'].append({'filename': 'virgos_core-2.0.0.jar', 'sides': ['server'],
                                        'local_source': 'not-a-client-input.jar'})
        self.write(self.inputs / 'custom.json', self.custom)
        result = self.invoke(self.command(['--mods-lock', str(self.inputs / 'mods.json')]))
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.output / 'Virgos-MC-2.1.0-instalar.zip') as archive:
            manifest = json.loads(archive.read('asistente/cliente.lock.json'))
            dh = [item for item in manifest['files'] if item['filename'].startswith('DistantHorizons')]
            self.assertEqual(len(dh), 1)
            self.assertTrue(dh[0]['bundled'])
            self.assertFalse(any('virgos_core' in name for name in archive.namelist()))

    def test_rejects_unexpected_roles_traversal_and_duplicates(self):
        original = json.loads(json.dumps(self.custom))
        for field, value in [('filename', '../escape.jar'), ('filename', 'unexpected.jar'),
                             ('local_source', '../escape.jar'), ('mode', 'optional')]:
            self.custom = json.loads(json.dumps(original))
            self.custom['artifacts'][0][field] = value
            self.write(self.inputs / 'custom.json', self.custom)
            result = self.invoke()
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.output.exists())
        original['artifacts'].append(original['artifacts'][0])
        self.write(self.inputs / 'custom.json', original)
        self.assertNotEqual(self.invoke().returncode, 0)
        self.assertFalse(self.output.exists())

    def test_rejects_incomplete_dh_seed_helper_pair_before_output(self):
        (self.source / 'templates/dh-client-settings.ps1').rename(self.source / 'templates/dh-client-settings.held')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('helper', result.stderr.lower())
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
