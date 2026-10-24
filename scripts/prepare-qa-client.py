"""Prepare official 1.20.1 client assets for the isolated local QA instance.

This is a test harness, not the distributed launcher. Friends use their own
launcher/profile and the release's mods/config files. Forge installer runs first.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'client/standard'


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'VirgosMC-QA/1.0'}), timeout=60) as response:
        return json.load(response)


def fetch(spec, target):
    target = Path(target)
    if target.exists() and (not spec.get('sha1') or hashlib.sha1(target.read_bytes()).hexdigest() == spec['sha1']):
        return
    with urllib.request.urlopen(urllib.request.Request(spec['url'], headers={'User-Agent': 'VirgosMC-QA/1.0'}), timeout=120) as response:
        content = response.read()
    if spec.get('sha1') and hashlib.sha1(content).hexdigest() != spec['sha1']:
        raise ValueError('Download hash mismatch: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def allowed(item):
    if not item.get('rules'):
        return True
    result = False
    for rule in item['rules']:
        os = rule.get('os', {})
        if os.get('name', 'windows') != 'windows': continue
        if os.get('arch', 'amd64') not in ['amd64', 'x86_64']: continue
        if 'version' in os and not re.search(os['version'], '10.0'): continue
        if rule.get('features'): continue
        result = rule['action'] == 'allow'
    return result


def main():
    manifest = fetch_json('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
    entry = next(v for v in manifest['versions'] if v['id'] == '1.20.1')
    vanilla = fetch_json(entry['url'])
    target = CLIENT / 'versions/1.20.1'
    target.mkdir(parents=True, exist_ok=True)
    (target / '1.20.1.json').write_text(json.dumps(vanilla, indent=2), 'utf-8')
    fetch(vanilla['downloads']['client'], target / '1.20.1.jar')
    jobs = []
    for lib in vanilla['libraries']:
        if not allowed(lib): continue
        artifact = lib.get('downloads', {}).get('artifact')
        if artifact: jobs.append((artifact, CLIENT / 'libraries' / artifact['path']))
        native = lib.get('natives', {}).get('windows')
        if native:
            artifact = lib['downloads']['classifiers'][native.replace('${arch}', '64')]
            jobs.append((artifact, CLIENT / 'libraries' / artifact['path']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda job: fetch(*job), jobs))
    print(f'{len(jobs)} vanilla libraries verified.', flush=True)
    natives = CLIENT / 'natives'
    natives.mkdir(exist_ok=True)
    for _, file in jobs:
        if 'natives-windows' in file.name:
            with zipfile.ZipFile(file) as archive:
                for name in archive.namelist():
                    if name.lower().endswith('.dll'):
                        (natives / Path(name).name).write_bytes(archive.read(name))
    index_spec = vanilla['assetIndex']
    index_file = CLIENT / 'assets/indexes' / (index_spec['id'] + '.json')
    fetch(index_spec, index_file)
    index = json.loads(index_file.read_text('utf-8'))
    jobs = []
    for value in index['objects'].values():
        hash = value['hash']
        jobs.append(({'url': f'https://resources.download.minecraft.net/{hash[:2]}/{hash}', 'sha1': hash}, CLIENT / 'assets/objects' / hash[:2] / hash))
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for count, _ in enumerate(pool.map(lambda job: fetch(*job), jobs), 1):
            if count % 500 == 0: print(f'Assets {count}/{len(jobs)} verified.', flush=True)
    options = CLIENT / 'options.txt'
    if not options.exists():
        options.write_text('lang:es_ar\nrenderDistance:8\nsimulationDistance:6\nmaxFps:60\nenableVsync:false\nguiScale:2\nautoJump:false\nonboardAccessibility:false\n', 'utf-8')
    print('Official client assets ready.', flush=True)


if __name__ == '__main__': main()
