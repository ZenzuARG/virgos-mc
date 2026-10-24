"""Resolve the approved pack into a local, hash-verified download cache.

This script never touches the running server's mods or world. The generated
lock is a build input; Forge's own dependency validation is still required.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import time
import tomllib
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'pack'
DOWNLOADS = CACHE / 'downloads'
API = CACHE / 'api'
for folder in (DOWNLOADS, API):
    folder.mkdir(parents=True, exist_ok=True)

def request_json(path: str):
    key = hashlib.sha256(path.encode()).hexdigest()
    target = API / (key + '.json')
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    req = urllib.request.Request('https://api.modrinth.com/v2/' + path,
                                 headers={'User-Agent': 'VirgosMC-PackBuilder/1.0'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.load(response)
            target.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            return data
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + attempt * 2)

def project_version(project_id: str):
    query = urllib.parse.urlencode({'loaders': '["forge"]', 'game_versions': '["1.20.1"]'})
    versions = request_json(f'project/{project_id}/version?{query}')
    releases = [v for v in versions if v['version_type'] == 'release']
    if not versions:
        raise ValueError(f'No Forge 1.20.1 version for {project_id}')
    return (releases or versions)[0]

def download(record):
    name = record['filename']
    if Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError(f'Unsafe filename: {name}')
    target = DOWNLOADS / name
    algorithm, expected = record['hash_algorithm'], record.get('hash')
    if target.exists() and expected:
        if hashlib.new(algorithm, target.read_bytes()).hexdigest() == expected:
            return record
    request = urllib.request.Request(record['url'], headers={'User-Agent':'VirgosMC-PackBuilder/1.0'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content = response.read()
            actual = hashlib.new(algorithm, content).hexdigest()
            if expected and actual != expected:
                raise ValueError(f'Hash mismatch: {name}')
            if not zipfile.is_zipfile(io.BytesIO(content)):
                raise ValueError(f'Not a jar: {name}')
            temporary = target.with_name(target.name + '.partial')
            temporary.write_bytes(content)
            temporary.replace(target)
            record['hash'] = actual
            record['size'] = len(content)
            print(f'Downloaded {name}', flush=True)
            return record
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 2)

def inspect_jar(path: Path):
    found, dependencies, embedded = [], [], []
    def inspect_bytes(data, origin):
        with zipfile.ZipFile(io.BytesIO(data)) as jar:
            if 'META-INF/mods.toml' in jar.namelist():
                toml = tomllib.loads(jar.read('META-INF/mods.toml').decode('utf-8-sig'))
                manifest = jar.read('META-INF/MANIFEST.MF').decode('utf-8', errors='replace') if 'META-INF/MANIFEST.MF' in jar.namelist() else ''
                jar_version = next((line.split(': ',1)[1].strip() for line in manifest.splitlines() if line.startswith('Implementation-Version: ')), None)
                for mod in toml.get('mods', []):
                    version = mod.get('version', '')
                    if version == '${file.jarVersion}': version = jar_version or version
                    found.append({'id':mod['modId'], 'version':version, 'origin':origin})
                for owner, deps in toml.get('dependencies', {}).items():
                    for dep in deps:
                        dependencies.append({'owner':owner, **dep})
            if 'META-INF/jarjar/metadata.json' in jar.namelist():
                for entry in json.loads(jar.read('META-INF/jarjar/metadata.json')).get('jars', []):
                    internal = entry.get('path')
                    embedded.append(entry)
                    if internal in jar.namelist(): inspect_bytes(jar.read(internal), origin + '!' + internal)
    inspect_bytes(path.read_bytes(), path.name)
    return {'mods':found, 'dependencies':dependencies, 'embedded':embedded}

def main():
    selection = json.loads((ROOT/'docs'/'seleccion-mods.json').read_text(encoding='utf-8-sig'))
    projects = {}
    queue = []
    exclusions = json.loads((ROOT/'pack/exclusions.json').read_text('utf-8'))
    for item in selection['mods']:
        if item['slug'] in exclusions:
            continue
        if not item['modrinth_version_id']:
            continue
        version = request_json('version/' + item['modrinth_version_id'])
        sides = set()
        if 'Cliente' in item['destino']: sides.add('client')
        if 'servidor' in item['destino'].lower(): sides.add('server')
        mode = 'optional' if item['estado'] == 'opcional' else 'tool' if item['estado'] == 'herramienta' else 'standard'
        projects[version['project_id']] = {'version':version, 'sides':sides, 'mode':mode, 'root':True, 'slug':item['slug']}
        queue.append(version['project_id'])
    # Required dependencies missing from some project's Modrinth metadata are
    # recorded explicitly after checking their actual Forge descriptor.
    extra_file = ROOT/'pack'/'extra-dependencies.json'
    if extra_file.exists():
        for extra in json.loads(extra_file.read_text(encoding='utf-8')):
            v = request_json('version/'+extra['version_id']) if extra.get('version_id') else project_version(extra['project'])
            if v['project_id'] not in projects:
                projects[v['project_id']]={'version':v,'sides':set(extra['sides']),'mode':'standard','root':False,'slug':extra['project']}
                queue.append(v['project_id'])
    while queue:
        project_id = queue.pop(0)
        parent = projects[project_id]
        for dep in parent['version']['dependencies']:
            if dep['dependency_type'] != 'required': continue
            dependency_id = dep.get('project_id')
            if not dependency_id and dep.get('version_id'):
                dependency_id=request_json('version/'+dep['version_id'])['project_id']
            if not dependency_id:
                raise ValueError(f'Unresolved file-only dependency: {dep}')
            if dependency_id in projects:
                target=projects[dependency_id]
                previous=set(target['sides'])
                target['sides'].update(parent['sides'])
                if parent['mode']=='standard': target['mode']='standard'
                if target['sides'] != previous: queue.append(dependency_id)
                continue
            meta = request_json('project/'+dependency_id)
            v = request_json('version/'+dep['version_id']) if dep.get('version_id') else project_version(dependency_id)
            sides={s for s in parent['sides'] if meta.get(s+'_side') != 'unsupported'}
            projects[dependency_id]={'version':v,'sides':sides,'mode':parent['mode'],'root':False,'slug':meta['slug']}
            queue.append(dependency_id)
    records=[]
    for project_id, entry in projects.items():
        v=entry['version']
        file=next((f for f in v['files'] if f['primary']),v['files'][0])
        algorithm='sha512' if 'sha512' in file['hashes'] else 'sha1'
        records.append({'project':entry['slug'],'project_id':project_id,'version_id':v['id'],'version':v['version_number'],
            'filename':file['filename'],'url':file['url'],'hash_algorithm':algorithm,'hash':file['hashes'][algorithm],
            'size':file['size'],'sides':sorted(entry['sides']),'mode':entry['mode'],'root':entry['root'],
            'source':'https://modrinth.com/mod/'+entry['slug']+'/version/'+v['id']})
    manual_file=ROOT/'pack'/'manual-artifacts.json'
    if manual_file.exists(): records.extend(json.loads(manual_file.read_text(encoding='utf-8')))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records=list(pool.map(download, records))
    all_mod_ids={'minecraft','forge','java'}
    for record in records:
        record['descriptor']=inspect_jar(DOWNLOADS/record['filename'])
        all_mod_ids.update(m['id'] for m in record['descriptor']['mods'])
    missing=[]
    for record in records:
        for dep in record['descriptor']['dependencies']:
            if dep.get('mandatory') and dep['modId'] not in all_mod_ids:
                missing.append({'file':record['filename'], **dep})
    result={'minecraft':'1.20.1','forge':'47.4.22','status':'resolved_downloads_pending_runtime_validation',
            'artifacts':records,'missing_declared_mod_ids':missing}
    (ROOT/'pack').mkdir(exist_ok=True)
    (ROOT/'pack'/'mods.lock.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'artifacts':len(records),'missing':missing},ensure_ascii=False),flush=True)

if __name__=='__main__': main()
