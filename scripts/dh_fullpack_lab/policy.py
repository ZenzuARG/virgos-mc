"""Selection and validation shared by preparation and launch; no implicit launch."""
import hashlib
import json
import os
import re
import uuid
from pathlib import Path

SCHEMA = 1
AUTHORIZED_LAB = Path('D:/proyectos/mc-server-lab/dh-fullpack-20261024')
DH_PREFIX = 'DistantHorizons-3.3.3'
CONFIG_DIRS = {'aether', 'alexscaves_biome_generation', 'alexsmobs', 'ars_nouveau',
               'artifacts', 'bettercombat', 'betterdeserttemples', 'betterfortresses',
               'betterstrongholds', 'bountiful', 'cristellib', 'easy_npc', 'explorify',
               'heracles', 'irons_spellbooks_spell_config', 'jade', 'lightmanscurrency',
               'Obscuria', 'regions_unexplored', 'simplyswords', 'towns_and_towers',
               'defaultoptions', 'fancymenu'}
CONFIG_SUFFIXES = {'.toml', '.json', '.json5', '.properties', '.txt', '.html'}
VIRGOS_FILES = {'client-update.json', 'expeditions.json', 'progression.json', 'services.json'}
FORBIDDEN = re.compile(r'token|credential|secret|authkey|session|password|account|\.db$|\.sqlite', re.I)
REMOTE = re.compile(r'virgos-mc\.playit|playit\.(?:gg|plus)|discord(?:app)?\.com/api/webhooks', re.I)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def regular(path):
    path = Path(path)
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
           for p in [path, *path.parents]):
        raise ValueError('Links and junctions are not permitted: ' + str(path))
    if not path.is_file():
        raise ValueError('Missing regular file: ' + str(path))
    return path


def validate_destination(lab, sources):
    raw = Path(lab).absolute()
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in [raw, *raw.parents]):
        raise ValueError('Linked destination forbidden')
    lab = raw.resolve()
    if lab.exists():
        raise ValueError('Destination must not exist')
    for source in sources:
        source = Path(source).resolve()
        if lab == source or lab in source.parents or source in lab.parents:
            raise ValueError('Destination must be disjoint from every source')
    return lab


def files(root):
    root = Path(root)
    if not root.exists():
        return []
    result = []
    for parent, dirs, names in os.walk(root, followlinks=False):
        for entry in dirs + names:
            path = Path(parent) / entry
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise ValueError('Linked source forbidden: ' + str(path))
        result.extend(regular(Path(parent) / name) for name in names)
    return sorted(result)


def verified_artifacts(directory, client):
    directory = Path(directory)
    manifest = json.loads(regular(directory / 'compat-manifest.json').read_text('utf-8'))
    if manifest.get('schema') != SCHEMA:
        raise ValueError('Unsupported artifact manifest schema')
    originals = list((Path(client) / 'mods').glob(DH_PREFIX + '*.jar'))
    if len(originals) != 1 or sha(regular(originals[0])) != manifest.get('originalDhSha256'):
        raise ValueError('Original installed DH hash mismatch')
    result = []
    names = set()
    for entry in manifest.get('artifacts', []):
        name = entry.get('filename', '')
        if not re.fullmatch(r'[A-Za-z0-9_.+\-]+\.jar', name) or name in names:
            raise ValueError('Invalid or duplicate artifact filename')
        path = regular(directory / name)
        if sha(path) != entry.get('sha256'):
            raise ValueError('Artifact hash mismatch: ' + name)
        names.add(name)
        result.append(path)
    if not any(n.startswith(DH_PREFIX) for n in names) or not any(n.startswith('virgos_dh_compat-') for n in names):
        raise ValueError('Patched DH and compatibility addon are required')
    return result


def config_allowed(relative):
    parts = relative.parts
    if FORBIDDEN.search(str(relative)) or relative.suffix.lower() not in CONFIG_SUFFIXES:
        return False
    if len(parts) == 1:
        return not any(word in relative.name.lower() for word in
                       ['backup', 'voicechat', 'playit', 'discord', 'spark', 'chunky', 'distanthorizons'])
    return parts[0] in CONFIG_DIRS or (parts[0] == 'virgos' and relative.name in VIRGOS_FILES)


def copy_allowed(root, relative):
    """Apply identical sensitive-input exclusions before either overlay source wins."""
    if FORBIDDEN.search(str(relative)):
        return False
    if root == 'config':
        return config_allowed(relative)
    # Resource packs legitimately use ZIP; other gameplay roots retain their
    # existing binary formats (PNG, NBT, compressed build data, and so on).
    if relative.suffix.lower() in {'.db', '.sqlite', '.sqlite3'}:
        return False
    return root == 'resourcepacks' or relative.suffix.lower() != '.zip'


def inventory(server, client):
    """Explicit gameplay roots only. No public plugin directory or world recursion."""
    server, client = Path(server), Path(client)
    plan, omitted = [], []
    for side, source in [('server', server), ('client', client)]:
        for jar in sorted((source / 'mods').glob('*.jar')):
            regular(jar)
            if 'playit' in jar.name.lower() or jar.name.startswith('DistantHorizons-'):
                omitted.append({'side': side, 'file': jar.name, 'reason': 'infrastructure or native DH replacement'})
            else:
                plan.append((jar, Path(side) / 'mods' / jar.name))
        for root in ['config', 'defaultconfigs', 'kubejs']:
            for path in files(source / root):
                rel = path.relative_to(source / root)
                if not copy_allowed(root, rel):
                    continue
                plan.append((path, Path(side) / root / rel))
    keep = ('authme', 'luckperms', 'coreprotect', 'decentholograms')
    for jar in sorted((server / 'plugins').glob('*.jar')):
        regular(jar)
        if jar.name.lower().startswith(keep):
            plan.append((jar, Path('server/plugins') / jar.name))
        else:
            omitted.append({'side': 'server', 'file': jar.name, 'reason': 'external integration or DHSupport replacement'})
    return plan, omitted


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def identity(name):
    return str(uuid.UUID(bytes=hashlib.md5(('OfflinePlayer:' + name).encode()).digest(), version=3))


def write_safety(lab):
    lab = Path(lab)
    props = {'server-ip': '127.0.0.1', 'server-port': '25575', 'level-name': 'virgos_world',
             'online-mode': 'false', 'white-list': 'true', 'enforce-whitelist': 'true',
             'enable-rcon': 'false', 'enable-query': 'false', 'view-distance': '2',
             'simulation-distance': '2', 'max-players': '2', 'level-seed': '42',
             'motd': 'Isolated DH full-pack laboratory', 'enable-jmx-monitoring': 'false'}
    write(lab / 'server/server.properties', ''.join(f'{k}={v}\n' for k, v in props.items()))
    write(lab / 'server/eula.txt', 'eula=true\n')
    write(lab / 'server/whitelist.json', json.dumps([{'name': n, 'uuid': identity(n)} for n in ['VirgosQA1', 'VirgosQA2']]))
    write(lab / 'server/config/virgos/maintenance.json', json.dumps({
        'schema': 1, 'enabled': False, 'intervalMinutes': 120, 'idleMinutes': 10,
        'backupOnCleanStop': False, 'autoRestartOnUnexpectedExit': False}))
    write(lab / 'server/config/simplebackups-common.toml', 'enabled = false\n')
    write(lab / 'server/defaultconfigs/simplebackups-server.toml', 'enabled = false\n')
    write(lab / 'server/virgos_world/serverconfig/simplebackups-server.toml', 'enabled = false\n')
    write(lab / 'server/plugins/AuthMe/config.yml', '''DataSource:
    backend: SQLITE
    caching: false
    mySQLDatabase: authme-lab
settings:
    sessions:
        enabled: false
    restrictions:
        maxRegPerIp: 0
        loginTimeout: 120
        registerTimeout: 120
    useAsyncTasks: true
Hooks:
    bungeecord: false
    sendPlayerTo: ''
Protection:
    geoIpDatabase:
        enabled: false
BackupSystem:
    ActivateBackup: false
    OnServerStart: false
    OnServerStop: false
''')
    write(lab / 'server/plugins/bStats/config.yml', 'enabled: false\n')
    write(lab / 'server/plugins/LuckPerms/config.yml', 'storage-method: h2\nwatch-files: false\n')
    write(lab / 'server/plugins/CoreProtect/config.yml', 'use-mysql: false\ncheck-updates: false\n')
    write(lab / 'server/plugins/DecentHolograms/config.yml', 'update-checker: false\n')
    write(lab / 'server/config/voicechat/voicechat-server.properties',
          'bind_address=127.0.0.1\nport=24455\nvoice_host=127.0.0.1:24455\n')
    for side in ['server', 'client', 'client2']:
        write(lab / side / 'config/DistantHorizons.toml', '''[common.worldGenerator]
generatorPlan = "CHUNKS_ONLY"
chunkGeneratorMode = "PRE_EXISTING_ONLY"
generationMaxChunkRadius = 32
[common.multiThreading]
numberOfThreads = 2
threadRunTimeRatio = "0.5"
[server]
enableRealTimeUpdates = true
realTimeUpdateDistanceRadiusInChunks = 32
synchronizeOnLoad = true
syncOnLoadRateLimit = 4
maxSyncOnLoadRequestDistance = 512
generationRequestRateLimit = 4
maxGenerationRequestDistance = 512
[client.advanced.graphics.quality]
lodChunkRenderDistanceRadius = 32
''')
        if side != 'server':
            write(lab / side / 'virgos-qa/endpoint.txt', '127.0.0.1:25575')
            write(lab / side / 'virgos-qa/commands.jsonl', '')
            write(lab / side / 'virgos-qa/status.json', '{"screen":"prepared"}')
            write(lab / side / 'options.txt', 'renderDistance:2\nsimulationDistance:5\nmaxFps:30\nenableVsync:false\npauseOnLostFocus:false\nsoundCategory_master:0.0\n')
    write(lab / 'server/commands.txt', '')


def validate_run(lab, role):
    if any(x.is_symlink() or (hasattr(x, 'is_junction') and x.is_junction()) for x in [Path(lab), *Path(lab).parents]):
        raise ValueError('Linked lab root forbidden')
    lab = Path(lab).resolve()
    # The JVM can write outside the immutable manifest: new world data, generated
    # config, caches, saves and logs. Inspect the complete lab tree before launch,
    # rejecting links before os.walk can descend through a junction.
    files(lab)
    manifest = json.loads(regular(lab / 'lab-manifest.json').read_text('utf-8'))
    if manifest.get('schema') != SCHEMA or manifest.get('lab') != str(lab):
        raise ValueError('Lab identity mismatch')
    if role not in {'server', 'client', 'client2'}:
        raise ValueError('Invalid role')
    props = dict(line.split('=', 1) for line in regular(lab / 'server/server.properties').read_text().splitlines() if '=' in line)
    expected = {'server-ip': '127.0.0.1', 'server-port': '25575', 'enable-rcon': 'false',
                'enable-query': 'false', 'white-list': 'true', 'level-name': 'virgos_world'}
    if any(props.get(k) != v for k, v in expected.items()):
        raise ValueError('Unsafe server properties')
    maintenance = json.loads(regular(lab / 'server/config/virgos/maintenance.json').read_text())
    if maintenance.get('enabled') is not False or maintenance.get('backupOnCleanStop') is not False:
        raise ValueError('Maintenance and clean-stop backups must remain disabled')
    voice = dict(line.split('=', 1) for line in regular(lab / 'server/config/voicechat/voicechat-server.properties').read_text().splitlines() if '=' in line and not line.startswith('#'))
    if voice.get('bind_address') != '127.0.0.1' or voice.get('port') != '24455':
        raise ValueError('Voice chat must remain isolated on loopback UDP 24455')
    backup = regular(lab / 'server/config/simplebackups-common.toml').read_text()
    if not re.search(r'^enabled\s*=\s*false\s*$', backup, re.M):
        raise ValueError('Scheduled backups must remain disabled')
    for side in ['server', 'client', 'client2']:
        if any('playit' in p.name.lower() for p in (lab / side / 'mods').glob('*.jar')):
            raise ValueError('Tunnel mod forbidden')
    if any('discord' in p.name.lower() or 'distanthorizonssupport' in p.name.lower()
           for p in (lab / 'server/plugins').glob('*.jar')):
        raise ValueError('External plugin forbidden')
    if role != 'server' and regular(lab / role / 'virgos-qa/endpoint.txt').read_text().strip() != '127.0.0.1:25575':
        raise ValueError('Unsafe QA endpoint')
    for item in manifest.get('files', []):
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid manifest path')
        if sha(regular(lab / relative)) != item['sha256']:
            raise ValueError('Prepared input changed: ' + str(relative))
    return manifest
