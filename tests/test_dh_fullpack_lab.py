import json
import hashlib
import sys
import tempfile
import os
import subprocess
import unittest
import importlib.util
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dh_fullpack_lab import policy
from dh_fullpack_lab.prepare import prepare


class LabPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server = self.root / 'public'
        self.client = self.root / 'installed'
        self.artifacts = self.root / 'artifacts'
        for p in [self.server, self.client, self.artifacts]:
            p.mkdir()
        self.lab = self.root / 'lab'
        self.put(self.client / 'mods/DistantHorizons-3.3.3.jar', b'original')
        self.put(self.artifacts / 'DistantHorizons-3.3.3.jar', b'patched')
        self.put(self.artifacts / 'virgos_dh_compat-0.1.0.jar', b'addon')
        self.manifest()

    def put(self, path, content=b'test'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def manifest(self):
        entries = [{'filename': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in self.artifacts.glob('*.jar')]
        (self.artifacts / 'compat-manifest.json').write_text(json.dumps({
            'schema': 1, 'originalDhSha256': hashlib.sha256(b'original').hexdigest(),
            'artifacts': entries}))

    def test_reject_related_destinations_without_writes(self):
        for target in [self.server, self.server / 'child', self.root]:
            with self.assertRaises(ValueError):
                policy.validate_destination(target, [self.server, self.client, self.artifacts])
        self.assertFalse(self.lab.exists())

    def test_artifacts_reject_traversal_missing_and_hash(self):
        valid = json.loads((self.artifacts / 'compat-manifest.json').read_text())
        for change in [{'filename': '../evil.jar'}, {'filename': 'missing.jar'}, {'sha256': '0' * 64}]:
            bad = json.loads(json.dumps(valid))
            bad['artifacts'][0].update(change)
            (self.artifacts / 'compat-manifest.json').write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                policy.verified_artifacts(self.artifacts, self.client)
        self.assertFalse(self.lab.exists())

    def test_plan_excludes_world_credentials_and_infrastructure(self):
        for name in ['game.jar', 'playit_companion.jar']:
            self.put(self.server / 'mods' / name)
        for name in ['AuthMe.jar', 'LuckPerms.jar', 'CoreProtect.jar', 'DecentHolograms.jar',
                     'DiscordSRV.jar', 'DistantHorizonsSupport.jar']:
            self.put(self.server / 'plugins' / name)
        self.put(self.server / 'world/level.dat')
        self.put(self.server / 'plugins/AuthMe/authme.db')
        self.put(self.server / 'plugins/DiscordSRV/.token')
        plan, omitted = policy.inventory(self.server, self.client)
        names = [dst.as_posix() for _, dst in plan]
        self.assertIn('server/mods/game.jar', names)
        self.assertIn('server/plugins/AuthMe.jar', names)
        self.assertFalse(any('Discord' in p or 'playit' in p or 'Support' in p for p in names))
        self.assertFalse(any('level.dat' in p or '.db' in p or '.token' in p for p in names))
        self.assertEqual(len(omitted), 4)

    def test_config_is_loopback_and_fake(self):
        policy.write_safety(self.lab)
        props = (self.lab / 'server/server.properties').read_text()
        for value in ['server-ip=127.0.0.1', 'server-port=25575', 'enable-rcon=false',
                      'enable-query=false', 'level-name=virgos_world', 'white-list=true']:
            self.assertIn(value, props)
        maintenance = json.loads((self.lab / 'server/config/virgos/maintenance.json').read_text())
        self.assertFalse(maintenance['enabled'])
        self.assertFalse(maintenance['backupOnCleanStop'])
        self.assertEqual([a['name'] for a in json.loads((self.lab / 'server/whitelist.json').read_text())],
                         ['VirgosQA1', 'VirgosQA2'])

    def test_runner_refuses_tampered_endpoint(self):
        policy.write_safety(self.lab)
        (self.lab / 'lab-manifest.json').write_text(json.dumps({'schema': 1, 'lab': str(self.lab.resolve())}))
        (self.lab / 'server/server.properties').write_text('server-ip=0.0.0.0\nserver-port=25575\n')
        with self.assertRaises(ValueError):
            policy.validate_run(self.lab, 'server')
        self.assertFalse((self.lab / 'server/process.json').exists())

    def test_runner_rejection_never_spawns_or_creates_state(self):
        path = Path(__file__).resolve().parents[1] / 'scripts/run-dh-fullpack-lab.py'
        spec = importlib.util.spec_from_file_location('lab_runner_test', path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with mock.patch.object(runner.subprocess, 'Popen') as spawn:
            with self.assertRaises(ValueError):
                runner.run(self.lab, 'server')
            spawn.assert_not_called()
        self.assertFalse(self.lab.exists())

    def test_symlink_source_rejected(self):
        self.put(self.server / 'mods/a.jar')
        try:
            (self.server / 'mods/link.jar').symlink_to(self.server / 'mods/a.jar')
        except OSError:
            self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(ValueError):
            policy.inventory(self.server, self.client)

    def ready_fixture(self):
        self.pack = self.root / 'snapshot'
        self.pack.mkdir()
        self.java = self.root / 'java.exe'
        self.put(self.java)
        self.put(self.server / 'ketting-server.jar')
        self.put(self.server / 'libraries/cache.jar')
        self.put(self.server / 'versions.lock.json', json.dumps({'minecraft': '1.20.1',
                 'forge': '47.4.22', 'ketting': '0.6.1'}).encode())
        for n in ['AuthMe', 'LuckPerms', 'CoreProtect', 'DecentHolograms']:
            self.put(self.server / ('plugins/' + n + '.jar'))
        self.put(self.server / 'mods/virgos_core-2.0.0.jar')
        self.put(self.client / 'mods/virgos_codex-2.0.0.jar')
        for version in ['1.20.1', '1.20.1-forge-47.4.22']:
            data = {'id': version, 'libraries': [], 'arguments': {'jvm': [], 'game': []},
                    'mainClass': 'test.Main', 'assetIndex': {'id': '5'}}
            self.put(self.client / f'versions/{version}/{version}.json', json.dumps(data).encode())
        self.put(self.client / 'versions/1.20.1/1.20.1.jar')
        self.put(self.client / 'assets/indexes/5.json', b'{"objects":{}}')
        self.put(self.client / 'versions/1.20.1-forge-47.4.22/natives/a.dll')

    def test_preparation_small_fixture_preserves_runtime_overlay(self):
        self.ready_fixture()
        self.put(self.pack / 'pack/server-overrides/kubejs/server_scripts/rule.js', b'canonical')
        self.put(self.server / 'kubejs/server_scripts/rule.js', b'runtime')
        self.put(self.server / 'plugins/AuthMe/authme.db', b'NEVER COPY')
        result = prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        self.assertEqual((self.lab / 'server/kubejs/server_scripts/rule.js').read_bytes(), b'runtime')
        self.assertEqual(len(result['overrides']), 1)
        self.assertFalse((self.lab / 'server/plugins/AuthMe/authme.db').exists())
        self.assertEqual((self.lab / 'client/mods/DistantHorizons-3.3.3.jar').read_bytes(), b'patched')
        self.assertEqual((self.lab / 'client2/mods/DistantHorizons-3.3.3.jar').read_bytes(), b'patched')
        policy.validate_run(self.lab, 'server')
        (self.lab / 'server/plugins/AuthMe/config.yml').write_text('DataSource:\n    backend: SQLITE\n# Expanded defaults\n')
        policy.validate_run(self.lab, 'server')
        self.assertFalse((self.lab / 'server/process.json').exists())

    def test_ephemeral_jna_native_is_not_copied_or_pinned(self):
        self.ready_fixture()
        self.put(self.client / 'versions/1.20.1-forge-47.4.22/natives/jna12345.dll', b'EPHEMERAL')
        self.put(self.client / 'versions/1.20.1-forge-47.4.22/natives/jna12345.dll.x', b'EPHEMERAL')
        result = prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        self.assertFalse((self.lab / 'client/natives/jna12345.dll').exists())
        self.assertFalse((self.lab / 'client/natives/jna12345.dll.x').exists())
        self.assertFalse(any('jna12345.dll' in item['path'] for item in result['files']))
        self.put(self.lab / 'client/natives/jna999.dll', b'generated')
        policy.validate_run(self.lab, 'server')
        (self.lab / 'client/natives/jna999.dll').unlink()
        policy.validate_run(self.lab, 'server')
        (self.lab / 'client/natives/a.dll').write_bytes(b'TAMPERED')
        with self.assertRaises(ValueError): policy.validate_run(self.lab, 'server')

    def test_missing_launch_dependency_creates_nothing(self):
        self.ready_fixture()
        (self.client / 'versions/1.20.1/1.20.1.jar').unlink()
        with self.assertRaises(ValueError):
            prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        self.assertFalse(self.lab.exists())

    def mock_client_run(self, role, screen, before_spawn=None):
        path = Path(__file__).resolve().parents[1] / 'scripts/run-dh-fullpack-lab.py'
        spec = importlib.util.spec_from_file_location('lifecycle_runner_test', path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        queue = self.lab / role / 'virgos-qa/commands.jsonl'
        status = self.lab / role / 'virgos-qa/status.json'
        clock = [0]
        child = mock.Mock(pid=7654321, returncode=None)
        def poll():
            if '"action":"quit"' in queue.read_text():
                child.returncode = 0
            return child.returncode
        child.poll.side_effect = poll
        def spawn(*args, **kwargs):
            if before_spawn:
                before_spawn()
            status.write_text(json.dumps({'screen': screen}))
            return child
        with mock.patch.object(runner.subprocess, 'Popen', side_effect=spawn), \
             mock.patch.object(runner.time, 'monotonic', side_effect=lambda: clock[0]), \
             mock.patch.object(runner.time, 'sleep', side_effect=lambda _: clock.__setitem__(0, clock[0] + 1)):
            result = runner.run(self.lab, role, lifetime=2, boot_timeout=1)
        return result, json.loads((self.lab / role / 'process.json').read_text())

    def test_client_restart_discards_old_commands_and_marks_audits_pending(self):
        self.ready_fixture()
        prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        for role in ['client', 'client2']:
            with self.subTest(role=role):
                qa = self.lab / role / 'virgos-qa'
                old = '{"action":"quit"}\n'
                (qa / 'commands.jsonl').write_text(old)
                (qa / 'dh-audit.json').write_text('{"ready":true}')
                (qa / 'loading-audit.json').write_text('{"success":true}')
                def before_spawn():
                    self.assertEqual((qa / 'commands.jsonl').read_text(), '')
                    for name in ['dh-audit.json', 'loading-audit.json']:
                        self.assertTrue(json.loads((qa / name).read_text())['pending'])
                self.mock_client_run(role, 'net.minecraft.client.gui.screens.TitleScreen', before_spawn)
                # A subsequent restart must also discard the timeout's prior quit.
                self.mock_client_run(role, 'net.minecraft.client.gui.screens.TitleScreen', before_spawn)

    def test_loading_error_screen_is_failure_not_ready(self):
        self.ready_fixture()
        prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        result, state = self.mock_client_run('client', 'net.minecraftforge.client.loading.LoadingErrorScreen')
        self.assertEqual(result, 1)
        self.assertFalse(state['ready'])
        self.assertEqual(state['reason'], 'client loading error')
        self.assertTrue((self.lab / 'client/virgos-qa/runner-failure.json').exists())

    def test_canonical_and_runtime_share_sensitive_input_exclusions(self):
        self.ready_fixture()
        for source in [self.server, self.pack / 'pack/server-overrides']:
            self.put(source / 'defaultconfigs/accounts.sqlite', b'ACCOUNT SENTINEL')
            self.put(source / 'kubejs/config/session-token.json', b'TOKEN SENTINEL')
            self.put(source / 'kubejs/assets/example/textures/block/test.png', b'PNG DATA')
            self.put(source / 'defaultconfigs/gameplay.toml', b'enabled = true')
        prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        self.assertFalse((self.lab / 'server/defaultconfigs/accounts.sqlite').exists())
        self.assertFalse((self.lab / 'server/kubejs/config/session-token.json').exists())
        self.assertEqual((self.lab / 'server/kubejs/assets/example/textures/block/test.png').read_bytes(), b'PNG DATA')
        self.assertEqual((self.lab / 'server/defaultconfigs/gameplay.toml').read_bytes(), b'enabled = true')

    @unittest.skipUnless(os.name == 'nt' and hasattr(os.path, 'isjunction'), 'Requires Windows junction support')
    def test_runner_rejects_ntfs_junctions_in_writable_footprint(self):
        self.ready_fixture()
        prepare(self.server, self.client, self.pack, self.artifacts, self.lab, self.java, self.java)
        outside = self.root / 'fake-public-world'
        outside.mkdir()
        sentinel = outside / 'level.dat'
        sentinel.write_bytes(b'EXTERNAL WORLD MUST NOT CHANGE')
        before = policy.sha(sentinel)
        for relative in ['server/virgos_world', 'server/config', 'server/mods',
                         'client/saves', 'client2/config']:
            with self.subTest(path=relative):
                target = self.lab / relative
                held = target.with_name(target.name + '-held-fixture')
                existed = target.exists()
                if existed:
                    target.rename(held)
                result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(target), str(outside)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(os.path.isjunction(target))
                try:
                    with self.assertRaises(ValueError):
                        policy.validate_run(self.lab, 'server')
                    self.assertEqual(policy.sha(sentinel), before)
                    self.assertFalse((self.lab / 'server/process.json').exists())
                finally:
                    # Remove only the verified fixture junction, never its target.
                    if os.path.isjunction(target):
                        os.rmdir(target)
                    if existed:
                        held.rename(target)


if __name__ == '__main__':
    unittest.main()
