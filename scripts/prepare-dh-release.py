"""Prepare verified DH release inputs locally; never publish or modify release locks."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = [Path('D:/proyectos/mc-server'), Path('C:/Users/zulia/AppData/Local/Virgos-MC/juego')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, kind='file'):
    path = Path(path).absolute()
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in [path, *path.parents]):
        raise ValueError('Linked release input/output refused: ' + str(path))
    if kind == 'file' and not path.is_file(): raise ValueError('Missing input: ' + str(path))
    if kind == 'directory' and not path.is_dir(): raise ValueError('Missing directory: ' + str(path))
    return path.resolve()


def filename(name):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.+ ()-]+', name) or name in {'.', '..'}:
        raise ValueError('Unsafe locked filename')
    return name


def verified(path, record):
    path = checked(path)
    algorithm = record.get('hash_algorithm', 'sha256')
    if algorithm not in {'sha256', 'sha512'} or hashlib.new(algorithm, path.read_bytes()).hexdigest() != record.get('hash', record.get('sha256')):
        raise ValueError('Locked input hash mismatch: ' + path.name)
    return path


def class_constants(data):
    """Read ConstantValue fields, not arbitrary strings occurring in a class pool."""
    offset = 0
    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        result = struct.unpack_from(fmt, data, offset); offset += size
        return result[0] if len(result) == 1 else result
    if read('>I') != 0xCAFEBABE: raise ValueError('Invalid ClientRelease class')
    read('>HH'); count = read('>H'); pool = [None] * count; i = 1
    while i < count:
        tag = read('>B')
        if tag == 1:
            length = read('>H'); pool[i] = data[offset:offset + length].decode('utf-8'); offset += length
        elif tag in {7, 8, 16, 19, 20}: pool[i] = read('>H')
        elif tag in {3, 4, 9, 10, 11, 12, 17, 18}: read('>I')
        elif tag in {5, 6}: read('>Q'); i += 1
        elif tag == 15: read('>BH')
        else: raise ValueError('Unsupported ClientRelease class constant')
        i += 1
    read('>HHH'); interfaces = read('>H'); offset += 2 * interfaces
    result = {}
    for _ in range(read('>H')):
        _, name, _, attributes = read('>HHHH')
        for _ in range(attributes):
            attribute, size = read('>HI')
            if pool[attribute] == 'ConstantValue' and size == 2:
                value = pool[read('>H')]; result[pool[name]] = pool[value]
            else: offset += size
    return result


def identity(jar):
    try:
        with zipfile.ZipFile(jar) as archive:
            return class_constants(archive.read('mc/virgos/update/ClientRelease.class'))
    except (KeyError, IndexError, struct.error, UnicodeError, zipfile.BadZipFile) as error:
        raise ValueError('Invalid embedded release identity: ' + str(jar)) from error


def one_jar(directory, prefix):
    jars = [p for p in directory.glob(prefix + '*.jar') if not p.name.endswith(('-sources.jar', '-javadoc.jar'))]
    if len(jars) != 1: raise ValueError('Expected exactly one built artifact: ' + prefix)
    return checked(jars[0])


def deterministic_sources(root, target):
    module = root / 'dev/dh-compat'
    files = [checked(module / name) for name in ['README.md', 'build.gradle', 'settings.gradle', 'gradle.properties', 'build-artifacts.py']]
    files += [checked(p) for p in (module / 'patcher').rglob('*.java')]
    files += [checked(p) for p in (module / 'src/main').rglob('*') if p.is_file()]
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(files):
            info = zipfile.ZipInfo('dev/dh-compat/' + source.relative_to(module).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.create_system = 3; info.external_attr = 0o100644 << 16; info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())


def source_extras(metadata, current):
    result = []
    names = set()
    records = current.get('sourceFiles', [])
    if not isinstance(records, list): raise ValueError('Corresponding sources must be a list')
    for record in records:
        if not isinstance(record, dict): raise ValueError('Invalid corresponding source record')
        name = filename(record['filename'])
        relative = record.get('local_source', '')
        if (name in names or not name.endswith(('.zip', '.txt')) or not isinstance(relative, str)
            or not relative or '\\' in relative or ':' in relative or Path(relative).is_absolute()
            or '..' in Path(relative).parts or 'virgos_local_qa' in name.lower() or 'trace' in name.lower()):
            raise ValueError('Unsafe/duplicate corresponding source')
        if not re.fullmatch(r'[a-f0-9]{64}', str(record.get('sha256', ''))): raise ValueError('Corresponding source requires SHA256')
        path = verified(metadata.parent / relative, record)
        if 'size' in record and (type(record['size']) is not int or record['size'] != path.stat().st_size):
            raise ValueError('Corresponding source size mismatch')
        if name.endswith('.zip'):
            with zipfile.ZipFile(path) as archive:
                if archive.testzip(): raise ValueError('Corresponding source CRC mismatch')
                entries = set()
                for entry in archive.infolist():
                    if (entry.filename in entries or '\\' in entry.filename or ':' in entry.filename
                        or entry.filename.startswith('/') or '..' in Path(entry.filename).parts
                        or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                        raise ValueError('Unsafe/duplicate corresponding source ZIP entry')
                    entries.add(entry.filename)
        names.add(name);result.append((dict(record, local_source='artifacts/' + name), path))
    return result


def tree_bundle(directory):
    spec = importlib.util.spec_from_file_location('tree_release_stage', ROOT / 'scripts/build-tree-release.py')
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    return helper.load_artifacts(directory, allow_platform_variant=True)


def prepare(metadata, cache_root, inputs_dir, java_home, offline=False, *, root=ROOT, runner=subprocess.run, tree_artifacts=None):
    root = checked(root, 'directory'); metadata = checked(metadata); cache = checked(cache_root, 'directory')
    output = checked(inputs_dir, 'output'); java_home = checked(java_home, 'directory')
    for protected in [root, cache, metadata.parent, java_home, *[p.resolve() for p in PUBLIC]]:
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError('Output overlaps a source/cache/public path')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Release inputs directory must be new or empty')
    current = json.loads(metadata.read_text('utf-8-sig'))
    version, release = current.get('version', ''), current.get('clientRelease', '')
    if (not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[A-Za-z0-9.-]+)?', version)
        or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', release)
        or not (release == version or release.startswith(version + '-'))
        or current.get('clientFingerprint') != 'virgos-client-' + release
        or type(current.get('installer')) is not int or current['installer'] < 1):
        raise ValueError('Invalid candidate release metadata')
    extras = source_extras(metadata, current)
    tree_platform_variant = False
    if tree_artifacts is not None:
        manifest = json.loads(checked(tree_artifacts / 'tree-release.json').read_text('utf-8'))
        tree_platform_variant = bool(manifest.get('platformVariantAllowed') and not manifest.get('byteIdenticalFrozen', True))
    tree = tree_bundle(tree_artifacts) if tree_artifacts is not None else []
    expected = {'RELEASE': release, 'FINGERPRINT': current['clientFingerprint']}
    source = checked(root / 'dev/virgos-core/src/shared/java/mc/virgos/update/ClientRelease.java').read_text('utf-8')
    source_values = dict(re.findall(r'public\s+static\s+final\s+String\s+(RELEASE|FINGERPRINT)\s*=\s*"([^"]+)"', source))
    if source_values != expected: raise ValueError('Source ClientRelease does not match metadata')
    libs = root / 'dev/virgos-core/build/libs'
    core, codex = one_jar(libs, 'virgos_core-'), one_jar(libs, 'virgos_codex-')
    for jar in [core, codex]:
        if identity(jar) != expected: raise ValueError('Embedded ClientRelease does not match metadata: ' + jar.name)
    upstream = json.loads(checked(root / 'pack/dh-upstream.lock.json').read_text('utf-8'))
    if upstream.get('schema') != 1 or len(upstream.get('source_archives', [])) != 2:
        raise ValueError('Invalid DH upstream/source lock')
    original = verified(cache / 'pack/downloads' / filename(upstream['filename']), upstream)
    asm = verified(cache / 'pack/tools' / filename(upstream['asm']['file']), upstream['asm'])
    source_inputs = [verified(cache / 'pack/sources' / filename(item['filename']), item) for item in upstream['source_archives']]
    with zipfile.ZipFile(original) as archive:
        licenses = {name: archive.read(name) for name in ['LICENSE.txt', 'LICENSE.LESSER.txt', 'LICENSE-LOGOS.txt']}
    administration = json.loads(checked(root / 'pack/administration.lock.json').read_text('utf-8'))
    administration = [item for item in administration if not item.get('filename', '').lower().startswith('distanthorizonssupport-')]
    if tree:
        plugin = next(record for record, _ in tree if record['kind'] == 'server-plugin')
        matches = [item for item in administration if item.get('project') == 'tree-feller']
        if (len(matches) != 1 or (matches[0].get('hash') != plugin['sha256'] and not tree_platform_variant)
            or matches[0].get('filename') != plugin['filename'] or matches[0].get('sides') != ['server']
            or matches[0].get('mode') != 'required'):
            raise ValueError('Tree server administration pin mismatch')

    # All identity, hash, source and output guards have passed before any child/output writes.
    wrapper = checked(root / ('dev/virgos-core/gradlew.bat' if os.name == 'nt' else 'dev/virgos-core/gradlew'))
    command = ([str(wrapper)] if os.name == 'nt' else ['bash', str(wrapper)]) + ['-p', str(root / 'dev/dh-compat'),
        'check', 'jar', '--no-daemon', '-PdhJar=' + str(original)]
    if offline: command.append('--offline')
    environment = dict(os.environ, JAVA_HOME=str(java_home))
    runner(command, cwd=root, env=environment, check=True)
    addon = one_jar(root / 'dev/dh-compat/build/libs', 'virgos_dh_compat-')
    scratch = Path(tempfile.mkdtemp(prefix='virgos-dh-release-build-'))
    patched = scratch / 'patched'
    runner([sys.executable, '-B', str(root / 'dev/dh-compat/build-artifacts.py'), '--original', str(original),
            '--addon', str(addon), '--asm', str(asm), '--output', str(patched), '--java-home', str(java_home)], cwd=root, env=environment, check=True)
    patch_manifest = json.loads(checked(patched / 'compat-manifest.json').read_text('utf-8'))
    patched_files = {item['filename']: verified(patched / filename(item['filename']), item) for item in patch_manifest['artifacts']}
    if set(patched_files) != {original.name, addon.name}: raise ValueError('Unexpected patch builder artifacts')
    staged = scratch / 'inputs'; artifacts = staged / 'artifacts'; artifacts.mkdir(parents=True)
    custom = []
    for jar, sides in [(core, ['server']), (codex, ['client']), (patched_files[original.name], ['client', 'server']), (patched_files[addon.name], ['client', 'server'])]:
        shutil.copyfile(jar, artifacts / jar.name)
        custom.append({'filename': jar.name, 'local_source': 'artifacts/' + jar.name, 'hash_algorithm': 'sha256',
                       'hash': sha(artifacts / jar.name), 'sides': sides, 'mode': 'required'})
    for path in source_inputs: shutil.copyfile(path, artifacts / path.name)
    for name, data in licenses.items(): (artifacts / ('DistantHorizons-' + name)).write_bytes(data)
    deterministic_sources(root, artifacts / 'Virgos-DH-modifications-source.zip')
    notice = ('Distant Horizons 3.3.3; LGPL-3.0-only. Upstream notices are retained.\n'
              'Virgos modifications: semantic same-detail palette comparison and version-pinned lifecycle ordering.\n'
              'Original SHA256: ' + sha(original) + '\n' +
              '\n'.join(item['filename'] + ' commit ' + str(item.get('commit', '')) for item in upstream['source_archives']) + '\n'
              'Rebuild using scripts/prepare-dh-release.py and dev/dh-compat/build-artifacts.py from this release source.\n')
    (artifacts / 'DH-SOURCES.txt').write_text(notice, encoding='utf-8', newline='\n')
    source_names = [p.name for p in source_inputs] + ['DistantHorizons-' + n for n in licenses] + ['Virgos-DH-modifications-source.zip', 'DH-SOURCES.txt']
    merged = {item['filename']: item for item, _ in extras}
    for record, path in extras:
        target = artifacts / record['filename']
        if target.exists() and sha(target) != sha(path): raise ValueError('Conflicting corresponding source')
        shutil.copyfile(path, target)
    for name in source_names:
        generated = {'filename': name, 'local_source': 'artifacts/' + name, 'sha256': sha(artifacts / name)}
        if name in merged and merged[name]['sha256'] != generated['sha256']:
            raise ValueError('Conflicting generated corresponding source')
        merged.setdefault(name, generated)
    for record, path in tree:
        name = record['filename']
        if (artifacts / name).exists():
            if record['kind'] == 'server-plugin' or sha(artifacts / name) != sha(path): raise ValueError('Duplicate Tree release artifact')
        else: shutil.copyfile(path, artifacts / name)
        if record['kind'] == 'server-plugin':
            matches = [item for item in administration if item.get('project') == 'tree-feller']
            if len(matches) != 1 or (matches[0].get('hash') != record['sha256'] and not tree_platform_variant) or matches[0].get('sides') != ['server']:
                raise ValueError('Tree server administration pin mismatch')
            if tree_platform_variant:
                matches[0]['hash'] = record['sha256']
            matches[0]['local_source'] = str(output / 'artifacts' / name)
        else:
            extra = {'filename': name, 'local_source': 'artifacts/' + name, 'sha256': record['sha256'], 'size': record['size']}
            if name in merged and merged[name]['sha256'] != extra['sha256']: raise ValueError('Conflicting Tree source')
            merged.setdefault(name, extra)
    current['sourceFiles'] = list(merged.values())
    for name, value in [('release.json', current), ('custom-artifacts.lock.json', {'schema': 1, 'artifacts': custom}),
                        ('administration.lock.json', administration), ('client-update.json', {'schema': 1, 'release': release,
                         'fingerprint': current['clientFingerprint'], 'installer': 'Virgos-MC-' + version + '-instalar.zip'})]:
        (staged / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    shutil.copytree(staged, output, dirs_exist_ok=True)
    return {'version': version, 'clientRelease': release, 'inputs': str(output), 'buildScratch': str(scratch)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ['metadata', 'cache-root', 'inputs-dir']: parser.add_argument('--' + flag, required=True, type=Path)
    parser.add_argument('--java-home', type=Path, default=os.environ.get('JAVA_HOME'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--tree-artifacts', type=Path, help='Verified external build-tree-release output; stage server-only plugin and complete GPL sources')
    arguments = parser.parse_args()
    if not arguments.java_home: parser.error('--java-home or JAVA_HOME is required')
    try: print(json.dumps(prepare(arguments.metadata, arguments.cache_root, arguments.inputs_dir, arguments.java_home, arguments.offline, tree_artifacts=arguments.tree_artifacts)))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, 'Preparation refused: ' + str(error) + '\n')
