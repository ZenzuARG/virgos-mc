"""Launch a fixed, clearly identified local QA account. Not a public launcher."""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import argparse
import ctypes
from datetime import datetime, timezone
from prepare_qa_helpers import allowed

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'client/standard'
parser = argparse.ArgumentParser()
parser.add_argument('--account', choices=['VirgosQA1', 'VirgosQA2','VirgosQA3'], default='VirgosQA1')
parser.add_argument('--instance', choices=['standard','secondary','tertiary','v2','dh'], default='standard')
parser.add_argument('--memory-mb',type=int,choices=[4096,5120,6144],default=6144)
parser.add_argument('--server', choices=['lab','public','local-public'], default='lab')
options=parser.parse_args()
name = options.account
CLIENT=BASE if options.instance=='standard' else ROOT/('client/qa-'+options.instance)
if not (CLIENT/'mods/virgos_local_qa-0.1.0.jar').is_file():raise SystemExit('Prepare this QA instance before launching it.')
record=CLIENT/'virgos-qa/process.json'
if record.exists():
    previous=json.loads(record.read_text('utf-8'))
    if previous.get('pid') and not previous.get('finished'):
        handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,previous['pid'])
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise SystemExit('This QA instance is already running.')
digest = hashlib.md5(('OfflinePlayer:' + name).encode()).digest()
identity = str(uuid.UUID(bytes=digest, version=3))
vanilla = json.loads((BASE / 'versions/1.20.1/1.20.1.json').read_text('utf-8'))
forge = json.loads((BASE / 'versions/1.20.1-forge-47.4.22/1.20.1-forge-47.4.22.json').read_text('utf-8'))
libraries = {}
for lib in vanilla['libraries'] + forge['libraries']:
    if not allowed(lib): continue
    parts = lib['name'].split(':')
    key = ':'.join(parts[:2] + parts[3:])
    libraries[key] = lib
classpath = []
for lib in libraries.values():
    artifact = lib.get('downloads', {}).get('artifact')
    if artifact:
        target = BASE / 'libraries' / artifact['path']
        if not target.exists(): raise FileNotFoundError(target)
        classpath.append(str(target))
classpath.append(str(BASE / 'versions/1.20.1/1.20.1.jar'))
values = {'natives_directory': str(BASE / 'natives'), 'launcher_name': 'VirgosLocalQA',
          'launcher_version': '1', 'classpath': ';'.join(classpath), 'classpath_separator': ';',
          'library_directory': str(BASE / 'libraries'), 'version_name': forge['id'],
          'version_type': 'release', 'auth_player_name': name, 'auth_uuid': identity,
          'auth_access_token': '0', 'auth_xuid': '', 'clientid': '', 'user_type': 'legacy',
          'game_directory': str(CLIENT), 'assets_root': str(BASE / 'assets'),
          'assets_index_name': vanilla['assetIndex']['id'], 'user_properties': '{}'}


def expand(arguments):
    result = []
    for arg in arguments:
        if isinstance(arg, dict):
            if not allowed(arg): continue
            arg = arg['value']
        for value in arg if isinstance(arg, list) else [arg]:
            for key, replacement in values.items(): value = value.replace('${' + key + '}', replacement)
            if value.startswith('-DignoreList='): value += ',1.20.1.jar'
            if '${' in value: raise ValueError('Unresolved launcher argument: ' + value)
            result.append(value)
    return result


args = [str(ROOT / '.runtime/jdk-17.0.20.1+1-jre/bin/java.exe'), '-Xms1G', f'-Xmx{options.memory_mb}M']
args += expand(vanilla['arguments']['jvm'] + forge['arguments']['jvm'])
args += [forge['mainClass']]
args += expand(vanilla['arguments']['game'] + forge['arguments']['game'])
args += ['--width', '1280', '--height', '720']
qa = CLIENT / 'virgos-qa'
qa.mkdir(exist_ok=True)
(qa/'endpoint.txt').write_text({'lab':'127.0.0.1:25575','public':'virgos-mc.playit.plus','local-public':'127.0.0.1:25565'}[options.server],'utf-8')
(qa / 'commands.jsonl').write_text('', 'utf-8')
(qa / 'status.json').write_text(json.dumps({'screen': 'starting'}), 'utf-8')
with (CLIENT / 'qa-client.log').open('w', encoding='utf-8') as log:
    process = subprocess.Popen(args, cwd=CLIENT, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    (qa / 'process.json').write_text(json.dumps({'pid': process.pid, 'name': name, 'memoryMb': options.memory_mb, 'started': datetime.now(timezone.utc).isoformat()}), 'utf-8')
    print('Local QA client PID', process.pid, flush=True)
    code = process.wait()
    (qa/'process.json').write_text(json.dumps({'pid':process.pid,'name':name,'finished':datetime.now(timezone.utc).isoformat(),'exitCode':code}),'utf-8')
    print('Local QA client exited', code, flush=True)
