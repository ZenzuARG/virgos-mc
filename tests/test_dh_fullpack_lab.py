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
        self.assertNotIn('skinFixture', result)
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

    def skin_manifest(self):
        self.ready_fixture()
        plugin = self.artifacts / 'SkinsRestorer-15.12.6.jar'
        self.put(plugin, b'pinned fixture plugin')
        data = json.loads((self.artifacts / 'compat-manifest.json').read_text())
        data['serverPlugins'] = [{'filename': plugin.name, 'sha256': policy.sha(plugin)}]
        (self.artifacts / 'compat-manifest.json').write_text(json.dumps(data))
        return plugin, data

    def test_server_plugin_is_pinned_only_in_server_plugin_directory(self):
        plugin, data = self.skin_manifest()
        with mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
            result = prepare(self.server, self.client, self.pack, self.artifacts,
                             self.lab, self.java, self.java)
        self.assertEqual((self.lab / 'server/plugins' / plugin.name).read_bytes(), plugin.read_bytes())
        for role in ['server', 'client', 'client2']:
            self.assertFalse((self.lab / role / 'mods' / plugin.name).exists())
        for role in ['client', 'client2']:
            self.assertFalse((self.lab / role / 'plugins' / plugin.name).exists())
        pinned = [row for row in result['files'] if row['path'] == 'server/plugins/' + plugin.name]
        self.assertEqual(pinned, [{'path': 'server/plugins/' + plugin.name, 'sha256': policy.sha(plugin)}])
        policy.validate_run(self.lab, 'server')
        (self.lab / 'server/plugins' / plugin.name).write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            policy.validate_run(self.lab, 'server')

    def test_forestry_destination_and_pinned_plugin_boundary(self):
        forestry = policy.ADDON_LAB_ROOT / 'forestry'
        self.assertTrue(policy.authorized_lab(forestry))
        self.assertFalse(policy.authorized_lab(forestry / 'child'))
        self.assertFalse(policy.authorized_lab(policy.ADDON_LAB_ROOT / 'forestry-other'))
        with self.assertRaises(ValueError):
            policy.skin_fixture_identity(forestry, [])
        self.assertEqual(policy.SERVER_PLUGIN_PINS.get('TreeFeller-1.33.0-virgos.3.jar'),
                         '8a88c0ba36b806ba2459e00f125b3a7951068cb85b5ac31b398df118c03ac61f')

    def test_capture_input_lab_is_exact_and_has_no_skin_identity(self):
        for name in ['forestry-input', 'forestry-input-v2']:
            with self.subTest(name=name):
                capture = policy.ADDON_LAB_ROOT / name
                self.assertTrue(policy.authorized_lab(capture))
                self.assertFalse(policy.authorized_lab(capture / 'child'))
                self.assertFalse(policy.authorized_lab(policy.ADDON_LAB_ROOT / (name + '-other')))
                with self.assertRaises(ValueError):
                    policy.skin_fixture_identity(capture, [])
        self.assertEqual(policy.ADDON_VARIANTS,
                         ('baseline', 'crafts', 'bells', 'cei', 'combined', 'baseline-after'))

    def test_forestry_plugin_is_server_only_and_immutable(self):
        self.ready_fixture()
        plugin = self.artifacts / 'TreeFeller-1.33.0-virgos.3.jar'
        self.put(plugin, b'guarded forestry fixture')
        data = json.loads((self.artifacts / 'compat-manifest.json').read_text())
        data['serverPlugins'] = [{'filename': plugin.name, 'sha256': policy.sha(plugin)}]
        (self.artifacts / 'compat-manifest.json').write_text(json.dumps(data))
        # Only fixture bytes differ; real preparation enforces the published candidate pin.
        with mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
            prepare(self.server, self.client, self.pack, self.artifacts,
                    self.lab, self.java, self.java)
        self.assertEqual((self.lab / 'server/plugins' / plugin.name).read_bytes(), plugin.read_bytes())
        for role in ['server', 'client', 'client2']:
            self.assertFalse((self.lab / role / 'mods' / plugin.name).exists())
        for role in ['client', 'client2']:
            self.assertFalse((self.lab / role / 'plugins' / plugin.name).exists())
        policy.validate_run(self.lab, 'server')
        (self.lab / 'server/plugins' / plugin.name).write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            policy.validate_run(self.lab, 'server')

    def test_server_plugin_invalid_inputs_reject_before_destination_creation(self):
        plugin, valid = self.skin_manifest()
        variants = [None, {}, [{'filename': '../SkinsRestorer.jar', 'sha256': '0' * 64}],
                    [{'filename': 'unknown.jar', 'sha256': '0' * 64}],
                    [{'filename': plugin.name, 'sha256': '0' * 64}],
                    valid['serverPlugins'] * 2]
        for entries in variants:
            with self.subTest(entries=entries):
                data = dict(valid, serverPlugins=entries)
                (self.artifacts / 'compat-manifest.json').write_text(json.dumps(data))
                with mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
                    with self.assertRaises(ValueError):
                        prepare(self.server, self.client, self.pack, self.artifacts,
                                self.lab, self.java, self.java)
                self.assertFalse(self.lab.exists())

    def test_server_plugin_cannot_also_be_a_client_mod(self):
        plugin, data = self.skin_manifest()
        data['artifacts'].append(data['serverPlugins'][0])
        (self.artifacts / 'compat-manifest.json').write_text(json.dumps(data))
        with mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
            with self.assertRaises(ValueError):
                prepare(self.server, self.client, self.pack, self.artifacts,
                        self.lab, self.java, self.java)
        self.assertFalse(self.lab.exists())

    def test_skin_destination_is_exact_and_does_not_expand_addon_matrix(self):
        self.assertTrue(policy.authorized_lab(policy.ADDON_LAB_ROOT / 'skins'))
        self.assertFalse(policy.authorized_lab(policy.ADDON_LAB_ROOT / 'skins/child'))
        self.assertFalse(policy.authorized_lab(policy.ADDON_LAB_ROOT / 'unknown-plugin'))
        self.assertEqual(policy.ADDON_VARIANTS,
                         ('baseline', 'crafts', 'bells', 'cei', 'combined', 'baseline-after'))

    def test_diagnostic_destination_is_exact_without_expanding_skin_identity(self):
        diagnostic = policy.ADDON_LAB_ROOT / 'dh-diagnostic'
        self.assertTrue(policy.authorized_lab(diagnostic))
        self.assertFalse(policy.authorized_lab(diagnostic / 'child'))
        self.assertFalse(policy.authorized_lab(policy.ADDON_LAB_ROOT / 'dh-unapproved'))
        with self.assertRaises(ValueError):
            policy.skin_fixture_identity(diagnostic, [])
        self.assertEqual(policy.ADDON_VARIANTS,
                         ('baseline', 'crafts', 'bells', 'cei', 'combined', 'baseline-after'))

    def test_skin_fixture_requires_exact_lab_and_verified_plugin(self):
        plugin, _ = self.skin_manifest()
        with mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
            with self.assertRaises(ValueError):
                prepare(self.server, self.client, self.pack, self.artifacts,
                        self.lab, self.java, self.java, skin_fixture=True)
        self.assertFalse(self.lab.exists())
        data = json.loads((self.artifacts / 'compat-manifest.json').read_text())
        data.pop('serverPlugins')
        (self.artifacts / 'compat-manifest.json').write_text(json.dumps(data))
        with mock.patch.object(policy, 'ADDON_LAB_ROOT', self.root):
            with self.assertRaises(ValueError):
                prepare(self.server, self.client, self.pack, self.artifacts,
                        self.root / 'skins', self.java, self.java, skin_fixture=True)
        self.assertFalse((self.root / 'skins').exists())

    def test_skin_fixture_changes_only_explicit_client2_identity_and_whitelist(self):
        plugin, _ = self.skin_manifest()
        path = self.client / 'versions/1.20.1/1.20.1.json'
        metadata = json.loads(path.read_text())
        metadata['arguments']['game'] = ['--username', '${auth_player_name}', '--uuid', '${auth_uuid}',
                                         '--accessToken', '${auth_access_token}']
        path.write_text(json.dumps(metadata))
        self.lab = self.root / 'skins'
        reference = self.root / 'reference'
        policy.write_safety(reference)
        with mock.patch.object(policy, 'ADDON_LAB_ROOT', self.root), \
                mock.patch.dict(policy.SERVER_PLUGIN_PINS, {plugin.name: policy.sha(plugin)}):
            manifest = prepare(self.server, self.client, self.pack, self.artifacts,
                               self.lab, self.java, self.java, skin_fixture=True)
            self.assertEqual(manifest['skinFixture'], {'name': 'Notch', 'role': 'client2',
                'uuid': policy.identity('Notch'), 'ownershipVerified': False})
            for role, name in [('client', 'VirgosQA1'), ('client2', 'Notch')]:
                args = json.loads((self.lab / (role + '-args.json')).read_text())
                self.assertEqual(args[args.index('--username') + 1], name)
                self.assertEqual(args[args.index('--uuid') + 1], policy.identity(name))
                self.assertEqual(args[args.index('--accessToken') + 1], '0')
                policy.validate_run(self.lab, role)
            self.assertEqual([row['name'] for row in json.loads((self.lab / 'server/whitelist.json').read_text())],
                             ['VirgosQA1', 'Notch'])
            self.assertEqual((reference / 'server/plugins/AuthMe/config.yml').read_bytes(),
                             (self.lab / 'server/plugins/AuthMe/config.yml').read_bytes())
            self.assertEqual((reference / 'server/server.properties').read_bytes(),
                             (self.lab / 'server/server.properties').read_bytes())
            self.assertFalse((self.lab / 'server/ops.json').exists())
            default_lab = self.root / 'defaults'
            defaults = prepare(self.server, self.client, self.pack, self.artifacts,
                               default_lab, self.java, self.java)
            self.assertNotIn('skinFixture', defaults)
            default_args = json.loads((default_lab / 'client2-args.json').read_text())
            self.assertEqual(default_args[default_args.index('--username') + 1], 'VirgosQA2')
            self.assertEqual(default_args[default_args.index('--uuid') + 1], policy.identity('VirgosQA2'))
            manifest['skinFixture']['ownershipVerified'] = True
            (self.lab / 'lab-manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): policy.validate_run(self.lab, 'client2')

    def test_skin_readiness_and_profile_protocol_are_explicit(self):
        path = Path(__file__).resolve().parents[1] / 'scripts/run-dh-fullpack-lab.py'
        spec = importlib.util.spec_from_file_location('skin_runner_test', path)
        runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
        state = {'screen': 'game', 'name': 'Notch', 'uuid': policy.identity('Notch')}
        self.assertEqual(runner.client_state(state), 'pending')
        fixture = {'name': 'Notch', 'role': 'client2', 'uuid': policy.identity('Notch'), 'ownershipVerified': False}
        self.assertEqual(runner.client_state(state, fixture, 'client2'), 'ready')
        self.assertEqual(runner.client_state(state, fixture, 'client'), 'pending')
        self.assertEqual(runner.client_state(dict(state, uuid='online-account-id'), fixture, 'client2'), 'pending')
        source = (Path(__file__).resolve().parents[1] / 'dev/dh-compat/qa/mc/virgos/qa/ClientProbe.java').read_text()
        self.assertIn('case "audit_skin"', source)
        self.assertIn('getProperties().get("textures")', source)
        self.assertIn('getSkinTextureLocation()', source)
        self.assertIn('!"textures".equals(property.getName())', source)
        snapshot = source.split('private void auditSkin(')[1].split('public static final class PublicSkinTextures')[0]
        for forbidden in ['getUser(', 'getSession(', 'accessToken', 'getProperties().entries(', 'sendCommand(']:
            self.assertNotIn(forbidden, snapshot)

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




class PublicSkinPayloadTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('VIRGOS_QA_JAR') and os.environ.get('VIRGOS_QA_CLASSPATH_FILE'),
                         'Packaged QA artifact and runtime classpath are required for the Java boundary probe')
    def test_public_skin_payload_schema_against_packaged_qa(self):
        root = Path(tempfile.mkdtemp(prefix='virgos-public-skin-payload-'))
        print('Public skin payload scratch:', root)
        jar = Path(os.environ['VIRGOS_QA_JAR'])
        classpath_file = Path(os.environ['VIRGOS_QA_CLASSPATH_FILE'])
        self.assertTrue(jar.is_file()); self.assertTrue(classpath_file.is_file())
        suffix = '.exe' if os.name == 'nt' else ''
        jdk = Path(os.environ['JAVA_HOME']) / 'bin'
        classpath = (str(jar) + os.pathsep + classpath_file.read_text()).replace('\\', '/')
        source = root / 'PublicSkinTexturesTest.java'
        source.write_text(r"""import com.google.gson.*;
import mc.virgos.qa.ClientProbe.PublicSkinTextures;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
public final class PublicSkinTexturesTest {
    private static String encode(String json) { return Base64.getEncoder().encodeToString(json.getBytes(StandardCharsets.UTF_8)); }
    private static void check(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    private static void reject(String json, String signature) {
        try { PublicSkinTextures.read(encode(json), signature); }
        catch (IllegalArgumentException error) {
            check(error.getMessage().equals("Invalid public skin texture payload") && error.getCause() == null,
                "Rejected input diagnostics must not reveal contents");
            return;
        }
        throw new AssertionError("Invalid texture input accepted");
    }
    public static void main(String[] args) {
        String legacy = "{\"timestamp\":123,\"profileId\":\"00000000000000000000000000000000\",\"profileName\":\"Notch\",\"signatureRequired\":true,\"textures\":{\"SKIN\":{\"url\":\"http://textures.minecraft.net/texture/" + "a".repeat(64) + "\"}}}";
        var unsigned = PublicSkinTextures.read(encode(legacy), null);
        check(unsigned.get("signature").isJsonNull(), "Unsigned public properties remain observable");
        check(unsigned.get("value").getAsString().equals(encode(legacy)), "Original public property must be preserved");
        var modern = JsonParser.parseString(legacy).getAsJsonObject();
        var skin = modern.getAsJsonObject("textures").getAsJsonObject("SKIN");
        skin.addProperty("url", skin.get("url").getAsString().replace("http:", "https:"));
        var metadata = new JsonObject(); metadata.addProperty("model", "slim"); skin.add("metadata", metadata);
        var cape = new JsonObject(); cape.addProperty("url", "http://textures.minecraft.net/texture/" + "b".repeat(64));
        modern.getAsJsonObject("textures").add("CAPE", cape);
        var signed = PublicSkinTextures.read(encode(modern.toString()), "AQID");
        check(signed.get("signature").getAsString().equals("AQID"), "Public signature is observed, not verified");
        check(signed.getAsJsonObject("decoded").equals(modern), "Standard SKIN slim metadata and CAPE are preserved");
        reject(legacy.replace("\"profileName\":\"Notch\"", "\"profileName\":\"DO_NOT_LOG\",\"profileName\":\"Notch\""), null);
        var unknown = modern.deepCopy(); unknown.addProperty("accessToken", "DO_NOT_LOG"); reject(unknown.toString(), null);
        reject(legacy.replace("http://textures.minecraft.net", "https://evil.example"), null);
        reject(legacy.replace("http://textures.minecraft.net", "http://textures.minecraft.net@evil.example"), null);
        reject(legacy.replace("a".repeat(64), "a".repeat(64) + "?secret=DO_NOT_LOG"), null);
        reject(modern.toString().replace("\"slim\"", "\"DO_NOT_LOG\""), null);
        reject(legacy.replace("\"Notch\"", "\"Notch DO_NOT_LOG\""), null);
        reject(legacy, "a".repeat(8193));
        reject(legacy, "invalid signature");
        try { PublicSkinTextures.read("a".repeat(16385), null); throw new AssertionError("Oversize accepted"); }
        catch (IllegalArgumentException expected) { check(expected.getCause() == null, "No payload in cause"); }
        try { PublicSkinTextures.read("not base64!", null); throw new AssertionError("Malformed Base64 accepted"); }
        catch (IllegalArgumentException expected) { check(expected.getMessage().equals("Invalid public skin texture payload"), "Generic failure"); }
        System.out.println("PASS: legacy HTTP, HTTPS, SKIN slim, CAPE, unsigned/signed observation; duplicate/unknown/private/host/size rejection");
    }
}
""", encoding='utf-8')
        classes = root / 'classes'; classes.mkdir()
        compile_args = '-cp\n"' + classpath + '"\n-d\n"' + classes.as_posix() + '"\n"' + source.as_posix() + '"\n'
        run_args = '-cp\n"' + classes.as_posix() + os.pathsep + classpath + '"\nPublicSkinTexturesTest\n'
        for tool, args in [('javac', compile_args), ('java', run_args)]:
            argument_file = root / (tool + '.args')
            argument_file.write_text(args, encoding='utf-8')
            result = subprocess.run([str(jdk / (tool + suffix)), '@' + str(argument_file)],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if tool == 'java':
                self.assertIn('PASS: legacy HTTP, HTTPS, SKIN slim, CAPE', result.stdout)


if __name__ == '__main__':
    unittest.main()
