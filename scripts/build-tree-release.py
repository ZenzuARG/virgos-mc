"""Build pinned server-only TreeFeller and complete GPL sources in external directories.

Default mode fetches anonymous official inputs. --offline never contacts a network.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('tree_release_helpers', ROOT / 'scripts/prepare-dh-release.py')
H = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(H)
VERSION = '1.33.0-virgos.3'
FORK_SHA256 = '9388b4ac0649e47b33620912841882ee24b796a6cc4efe3231327843895bb46e'
JAR = 'TreeFeller-' + VERSION + '.jar'
SOURCE = 'TreeFeller-' + VERSION + '-sources.zip'
LICENSE = 'TreeFeller-GPL-3.0.txt'
EXPECTED = {
    JAR: '8a88c0ba36b806ba2459e00f125b3a7951068cb85b5ac31b398df118c03ac61f',
    SOURCE: '1cd1f907a40fb15c4c95e9e73e915b3fda96d97ce49ab86b7ded1f3a1a309264',
    LICENSE: '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986',
}
KINDS = {JAR: 'server-plugin', SOURCE: 'corresponding-source', LICENSE: 'license'}
KETTING_URL = ('https://reposilite.c0d3m4513r.com/Ketting-Server-Releases/org/kettingpowered/server/forge/'
               '1.20.1-47.4.22-0.6.1/forge-1.20.1-47.4.22-0.6.1-universal.jar')


def fork_bytes(module, path):
    data = path.read_bytes().replace(b'\r\n', b'\n')
    if b'\r' in data: raise ValueError('Unexpected frozen source line ending')
    return data if path.relative_to(module).as_posix() == 'LICENSE' else data.replace(b'\n', b'\r\n')


def source_fingerprint(module):
    digest = hashlib.sha256()
    files = [p for p in module.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    for path in sorted(files, key=lambda p: p.relative_to(module).as_posix()):
        digest.update(path.relative_to(module).as_posix().encode())
        digest.update(b'\0');digest.update(fork_bytes(module, path));digest.update(b'\0')
    return digest.hexdigest()


def load_pin(root):
    module = H.checked(root / 'dev/tree-feller', 'directory')
    for path in module.rglob('*'):
        if '__pycache__' not in path.parts:
            H.checked(path, 'directory' if path.is_dir() else 'file')
    if source_fingerprint(module) != FORK_SHA256: raise ValueError('Frozen Tree source fingerprint mismatch')
    pin = json.loads(H.checked(module / 'UPSTREAM.json').read_text())
    if pin['modified_version'] != VERSION or pin['license'] != 'GPL-3.0':
        raise ValueError('Unsupported Tree release identity/license')
    H.verified(module / 'LICENSE', {'sha256': EXPECTED[LICENSE]})
    for name, digest in pin['resources'].items():
        path = H.checked(module / 'resources' / H.filename(name))
        if hashlib.sha256(fork_bytes(module, path)).hexdigest() != digest: raise ValueError('Frozen catalog resource hash mismatch')
    return module, pin


def providers(pin):
    extras = pin['compile_inputs']['additional_jars']
    result = [
        ('TreeFeller-1.33.0.jar', pin['jar']['url'], pin['jar']['sha256']),
        ('TreeFeller-upstream-source.zip', pin['source']['url'], pin['source']['sha256']),
        ('forge-1.20.1-47.4.22-0.6.1-universal.jar', KETTING_URL, pin['compile_inputs']['ketting_universal_sha256']),
        ('CoreProtect-CE-24.1.jar', pin['coreprotect_compile_provider']['url'], pin['compile_inputs']['coreprotect_sha256']),
    ]
    for name in ['bungeecord-chat-1.20-R0.1.jar', 'guava-31.1-jre.jar']:
        path = ('net/md-5/bungeecord-chat/1.20-R0.1/' if name.startswith('bungeecord') else 'com/google/guava/guava/31.1-jre/')
        result.append((name, 'https://repo.maven.apache.org/maven2/' + path + name, extras[name]))
    return result


def anonymous_download(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        raise ValueError('Anonymous HTTPS provider required')
    # No netrc, GitHub session, auth header, or environment proxy credentials.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers={'User-Agent': 'VirgosMC-TreeRelease/1.0'})
    with opener.open(request, timeout=180) as response:
        return response.read()


def validate_archives(paths, module, pin):
    for path in paths:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip(): raise ValueError('Provider CRC mismatch')
            for entry in archive.infolist():
                parts = Path(entry.filename).parts
                if ('\\' in entry.filename or ':' in entry.filename or entry.filename.startswith('/')
                    or '..' in parts or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                    raise ValueError('Unsafe provider ZIP entry')
    with zipfile.ZipFile(paths[1]) as archive:
        names = [name for name in archive.namelist() if not name.endswith('/')]
        roots = {name.split('/')[0] for name in names}
        if len(roots) != 1: raise ValueError('Expected one upstream source root')
        prefix = roots.pop() + '/'
        if archive.read(prefix + 'LICENSE') != (module / 'LICENSE').read_bytes():
            raise ValueError('Incomplete or changed GPL license')
        for patchfile in sorted((module / 'patches').glob('*.json')):
            patch = json.loads(patchfile.read_text())
            body = archive.read(prefix + patch['path'])
            if hashlib.sha256(body).hexdigest() != patch['source_sha256']:
                raise ValueError('Unexpected upstream patch source')
            text = body.decode('utf-8').replace('\r\n', '\n')
            for replacement in patch['replacements']:
                if text.count(replacement['before']) != 1: raise ValueError('Patch source context changed')
                text = text.replace(replacement['before'], replacement['after'], 1)
    with zipfile.ZipFile(paths[3]) as archive:
        for name, digest in pin['coreprotect_compile_provider']['referenced_classes_sha256'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError('CoreProtect compile API class mismatch')


def load_artifacts(directory):
    directory = H.checked(directory, 'directory')
    manifest = json.loads(H.checked(directory / 'tree-release.json').read_text())
    if not isinstance(manifest, dict) or manifest.get('schema') != 1: raise ValueError('Unknown Tree release manifest')
    records = manifest.get('artifacts', [])
    if (not isinstance(records, list) or len(records) != 3 or any(not isinstance(r, dict) or not isinstance(r.get('filename'), str) for r in records)
        or {r.get('filename') for r in records} != set(EXPECTED)):
        raise ValueError('Incomplete/duplicate Tree release artifacts')
    result = []
    for record in records:
        name = H.filename(record['filename'])
        if (record.get('local_source') != name or record.get('kind') != KINDS[name]
            or record.get('sides') != ['server'] or record.get('sha256') != EXPECTED[name]
            or type(record.get('size')) is not int or record['size'] < 1):
            raise ValueError('Tree artifact role/path/hash declaration rejected')
        path = H.verified(directory / name, record)
        if path.stat().st_size != record['size']: raise ValueError('Tree artifact size mismatch')
        result.append((record, path))
    with zipfile.ZipFile(directory / JAR) as archive:
        if archive.testzip(): raise ValueError('Tree JAR CRC mismatch')
        if ('version: ' + VERSION) not in archive.read('plugin.yml').decode():
            raise ValueError('Tree plugin identity mismatch')
        if any('mc/virgos/qa/' in n or 'virgos_local_qa' in n or 'virgos_qa.mixins' in n for n in archive.namelist()):
            raise ValueError('QA artifact forbidden')
    with zipfile.ZipFile(directory / SOURCE) as archive:
        if archive.testzip(): raise ValueError('Tree source CRC mismatch')
        for name in ['upstream/LICENSE', 'virgos-fork/LICENSE']:
            if archive.read(name) != (directory / LICENSE).read_bytes(): raise ValueError('Incomplete GPL source license')
        for name in ['virgos-fork/build.py', 'pinned-inputs/source.zip', 'pinned-inputs/TreeFeller-1.33.0.jar']:
            if not archive.read(name): raise ValueError('Incomplete corresponding source')
    return result


def build(cache_root, output, java_home, offline=False, *, root=ROOT, runner=subprocess.run,
          downloader=anonymous_download, plan=False):
    root = H.checked(root, 'directory');module, pin = load_pin(root)
    cache = H.checked(cache_root, 'output');output = H.checked(output, 'output')
    java_home = H.checked(java_home, 'directory')
    for candidate in [cache, output]:
        for protected in [root, java_home, *[p.resolve() for p in H.PUBLIC]]:
            if candidate == protected or candidate in protected.parents or protected in candidate.parents:
                raise ValueError('Tree output/cache overlaps source/JDK/public')
    source_root = H.checked(output.with_name(output.name + '-source'), 'output')
    if source_root.exists() or source_root == cache or source_root in cache.parents or cache in source_root.parents:
        raise ValueError('External canonical source directory must be NEW and separate from cache')
    if output.exists() or output == cache or output in cache.parents or cache in output.parents:
        raise ValueError('Tree output must be NEW and separate from cache')
    for tool in ['java', 'javac']:
        H.checked(java_home / 'bin' / (tool + ('.exe' if os.name == 'nt' else '')))
    paths = []
    for name, url, digest in providers(pin):
        target = H.checked(cache / H.filename(name), 'output')
        if not target.exists():
            if offline or plan: raise ValueError('Missing offline Tree provider: ' + name)
            data = downloader(url)
            if hashlib.sha256(data).hexdigest() != digest: raise ValueError('Downloaded Tree provider hash mismatch: ' + name)
            cache.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(data)
        paths.append(H.verified(target, {'sha256': digest}))
    validate_archives(paths, module, pin)
    build_module = source_root / 'dev/tree-feller'
    command = [sys.executable, '-B', str(build_module / 'build.py'), '--upstream-jar', str(paths[0]),
               '--source-zip', str(paths[1]), '--bukkit-api', str(paths[2]), '--coreprotect-api', str(paths[3]),
               '--classpath', str(paths[4]), '--classpath', str(paths[5]), '--jdk', str(java_home), '--output', str(output), '--tests']
    if plan: return {'command': command, 'offline': offline, 'output': str(output)}
    for path in module.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            target = build_module / path.relative_to(module)
            target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(fork_bytes(module, path))
    if source_fingerprint(build_module) != FORK_SHA256: raise ValueError('External frozen source copy mismatch')
    runner(command, cwd=source_root, check=True)
    shutil.copyfile(module / 'LICENSE', output / LICENSE)
    records = [{'filename': name, 'local_source': name, 'kind': KINDS[name], 'sides': ['server'],
                'sha256': H.sha(output / name), 'size': (output / name).stat().st_size} for name in EXPECTED]
    for record in records:
        if record['sha256'] != EXPECTED[record['filename']]: raise ValueError('Tree build differs from frozen release pin')
    (output / 'tree-release.json').write_text(json.dumps({'schema': 1, 'artifacts': records}, indent=2) + '\n')
    load_artifacts(output)
    return {'artifacts': str(output), 'version': VERSION, 'nativeAcceptance': 'UNPROVEN: controlled public trial'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['cache-root', 'output', 'java-home']: parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--offline', action='store_true', help='Use verified cache only; never contact network')
    parser.add_argument('--plan', action='store_true', help='Verify cached inputs and print the build command without JVM/output writes')
    args = parser.parse_args()
    try: print(json.dumps(build(args.cache_root, args.output, args.java_home, args.offline, plan=args.plan)))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        parser.exit(1, 'Tree release refused: ' + str(error) + '\n')
