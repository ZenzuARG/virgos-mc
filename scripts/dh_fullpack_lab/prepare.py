"""Build an offline snapshot using explicit gameplay selections only."""
import json
import re
import shutil
from pathlib import Path
from . import policy as p


def allowed(item):
    result = not item.get('rules')
    for rule in item.get('rules', []):
        target = rule.get('os', {})
        if target.get('name', 'windows') != 'windows' or target.get('arch', 'amd64') not in {'amd64', 'x86_64'} or rule.get('features'):
            continue
        result = rule['action'] == 'allow'
    return result


def client_args(client, lab, role, skin_fixture=None):
    vanilla = json.loads(p.regular(client / 'versions/1.20.1/1.20.1.json').read_text('utf-8-sig'))
    forge = json.loads(p.regular(client / 'versions/1.20.1-forge-47.4.22/1.20.1-forge-47.4.22.json').read_text('utf-8-sig'))
    index_name = vanilla['assetIndex']['id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', index_name):
        raise ValueError('Invalid cached asset index name')
    index = json.loads(p.regular(client / 'assets/indexes' / (index_name + '.json')).read_text('utf-8'))
    for entry in index.get('objects', {}).values():
        digest = entry.get('hash', '')
        if not re.fullmatch(r'[0-9a-f]{40}', digest):
            raise ValueError('Invalid cached asset object hash')
        p.regular(client / 'assets/objects' / digest[:2] / digest)
    libraries = {}
    for lib in vanilla['libraries'] + forge['libraries']:
        if allowed(lib):
            parts = lib['name'].split(':')
            libraries[':'.join(parts[:2] + parts[3:])] = lib
    classpath = []
    for lib in libraries.values():
        artifact = lib.get('downloads', {}).get('artifact')
        if artifact:
            rel = Path(artifact['path'])
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Invalid cached library path')
            classpath.append(str(p.regular(client / 'libraries' / rel)))
    classpath.append(str(p.regular(client / 'versions/1.20.1/1.20.1.jar')))
    name = 'VirgosQA2' if role == 'client2' else 'VirgosQA1'
    if skin_fixture and role == skin_fixture['role']:
        name = skin_fixture['name']
    values = {'natives_directory': str(lab / role / 'natives'), 'launcher_name': 'VirgosIsolatedFullPackQA',
              'launcher_version': '1', 'classpath': ';'.join(classpath), 'classpath_separator': ';',
              'library_directory': str(client / 'libraries'), 'version_name': forge['id'],
              'version_type': 'release', 'auth_player_name': name, 'auth_uuid': p.identity(name),
              'auth_access_token': '0', 'auth_xuid': '', 'clientid': '', 'user_type': 'legacy',
              'game_directory': str(lab / role), 'assets_root': str(client / 'assets'),
              'assets_index_name': vanilla['assetIndex']['id'], 'user_properties': '{}'}
    def expand(items):
        result = []
        for item in items:
            if isinstance(item, dict):
                if not allowed(item):
                    continue
                item = item['value']
            for arg in item if isinstance(item, list) else [item]:
                for key, value in values.items():
                    arg = arg.replace('${' + key + '}', value)
                if arg.startswith('-DignoreList='):
                    arg += ',1.20.1.jar'
                if '${' in arg:
                    raise ValueError('Unresolved launch metadata placeholder')
                result.append(arg)
        return result
    return ['-Xms512M', '-Xmx8G', '-Duser.home=' + str(lab / role / 'home'),
            '-Dforge.disableVersionCheck=true'] + expand(vanilla['arguments']['jvm'] + forge['arguments']['jvm']) + [forge['mainClass']] + expand(vanilla['arguments']['game'] + forge['arguments']['game']) + ['--width', '640', '--height', '360']


def prepare(server, client, pack, artifacts, lab, java_server, java_client, skin_fixture=False):
    server, client, pack, artifacts = [Path(x).resolve() for x in [server, client, pack, artifacts]]
    lab = p.validate_destination(lab, [server, client, pack, artifacts])
    java_server, java_client = p.regular(java_server), p.regular(java_client)
    versions = json.loads(p.regular(server / 'versions.lock.json').read_text('utf-8-sig'))
    for key in ['minecraft', 'forge', 'ketting']:
        if not isinstance(versions.get(key), str):
            raise ValueError('Missing locked server version: ' + key)
    verified = p.verified_artifacts(artifacts, client)
    server_plugins = p.verified_server_plugins(artifacts)
    fixture = p.skin_fixture_identity(lab, server_plugins) if skin_fixture else None
    plan, omitted = p.inventory(server, client)
    plugin_names = [source.name.lower() for source, target in plan if target.parts[:2] == ('server', 'plugins')]
    if any(not any(name.startswith(prefix) for name in plugin_names)
           for prefix in ['authme', 'luckperms', 'coreprotect', 'decentholograms']):
        raise ValueError('All four gameplay plugins are required')
    # Canonical defaults first; explicitly selected runtime files take precedence.
    canonical = []
    for side in ['server', 'client']:
        root = pack / 'pack' / (side + '-overrides')
        for source in p.files(root):
            rel = source.relative_to(root)
            if rel.parts[0] in {'config', 'defaultconfigs', 'kubejs', 'resourcepacks'}:
                if not p.copy_allowed(rel.parts[0], Path(*rel.parts[1:])):
                    continue
                canonical.append((source, Path(side) / rel))
            elif (side == 'server' and rel.parts[:2] == ('virgos_world', 'serverconfig')
                  and source.suffix == '.toml' and p.copy_allowed('defaultconfigs', Path(*rel.parts[2:]))):
                canonical.append((source, Path('server') / rel))
    selected = {}
    conflicts = []
    for source, target in canonical + plan:
        if target in selected and p.sha(selected[target]) != p.sha(source):
            conflicts.append({'path': target.as_posix(), 'canonicalSha256': p.sha(selected[target]),
                              'runtimeSha256': p.sha(source), 'winner': 'selected installed runtime'})
        selected[target] = source
    selected[Path('server/ketting-server.jar')] = p.regular(server / 'ketting-server.jar')
    for source in p.files(server / 'libraries'):
        selected[Path('server/libraries') / source.relative_to(server / 'libraries')] = source
    natives = client / 'versions/1.20.1-forge-47.4.22/natives'
    native_files = [file for file in p.files(natives) if not re.fullmatch(r"jna[0-9]+\.dll(?:\.x)?", file.name, re.I)]
    if not native_files:
        raise ValueError('Missing cached client natives')
    for source in native_files:
        selected[Path('client/natives') / source.relative_to(natives)] = source
    for artifact in verified:
        for side in (['client'] if artifact.name.startswith('virgos_local_qa-') else ['server', 'client']):
            selected[Path(side) / 'mods' / artifact.name] = artifact
    for artifact in server_plugins:
        selected[Path('server/plugins') / artifact.name] = artifact
    # Fail before creating the destination, including on missing dependencies.
    args = {role: client_args(client, lab, role, fixture) for role in ['client', 'client2']}
    for target, source in selected.items():
        p.regular(source)
        if target.suffix.lower() in p.CONFIG_SUFFIXES | {'.js'}:
            if p.REMOTE.search(source.read_text('utf-8-sig', errors='replace')):
                raise ValueError('Production endpoint in selected input: ' + str(target))
    lab.mkdir(parents=True)
    for target, source in selected.items():
        dest = lab / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    # Independent writable game directories; libraries/assets remain read-only inputs.
    shutil.copytree(lab / 'client', lab / 'client2')
    p.write_safety(lab, fixture)
    server_args = ['-Xms1G', '-Xmx4G', '-Duser.home=' + str(lab / 'server/home'),
                   '-Dforge.disableVersionCheck=true', '-jar', 'ketting-server.jar',
                   '-minecraftVersion', versions['minecraft'], '-forgeVersion', versions['forge'],
                   '-kettingVersion', versions['ketting'], '-daul', '-dau', '-noui', 'nogui']
    for role in ['server', 'client', 'client2']:
        p.write(lab / (role + '-args.json'), json.dumps(server_args if role == 'server' else args[role], indent=2))
    immutable = []
    for side in ['server', 'client', 'client2']:
        for root in ['mods', 'plugins', 'natives', 'libraries']:
            for file in p.files(lab / side / root):
                if root == 'plugins' and (file.parent != lab / side / root or file.suffix != '.jar'):
                    continue  # Plugins legitimately expand their fresh configuration on boot.
                immutable.append({'path': file.relative_to(lab).as_posix(), 'sha256': p.sha(file)})
    for file in [lab / 'server/ketting-server.jar', *lab.glob('*-args.json')]:
        immutable.append({'path': file.relative_to(lab).as_posix(), 'sha256': p.sha(file)})
    manifest = {'schema': 1, 'lab': str(lab), 'sources': {'server': str(server), 'client': str(client)},
                'java': {'server': str(java_server), 'client': str(java_client), 'client2': str(java_client)},
                'files': immutable, 'overrides': conflicts, 'precedence': 'canonical < selected runtime < lab safety',
                'omitted': omitted, 'externalInfrastructure': ['Playit', 'DiscordSRV'],
                'substitution': 'DHSupport 0.14.0 replaced by native DH 3.3.3 plus compatibility artifact',
                'copiedBytes': sum(f.stat().st_size for f in p.files(lab)),
                'selectedInputs': [{'target': target.as_posix(), 'sha256': p.sha(source)}
                                   for target, source in selected.items()],
                'sharedReadOnly': [str(client / 'libraries'), str(client / 'assets')]}
    if fixture is not None:
        manifest['skinFixture'] = fixture
    p.write(lab / 'lab-manifest.json', json.dumps(manifest, indent=2))
    p.write(lab / 'status.json', '{"phase":"prepared","runtimeProof":"pending","publicWrites":false}')
    return manifest
