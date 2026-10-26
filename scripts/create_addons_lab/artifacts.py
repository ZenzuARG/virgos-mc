"""Pinned laboratory inputs; never modifies approved pack pins or runtime directories."""
import ast
import functools
import hashlib
import io
import json
import re
import shutil
import tomllib
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from dh_fullpack_lab import policy

OUTPUT_ROOT = policy.ADDON_LAB_ROOT
VARIANTS = {'baseline': (), 'crafts': ('crafts',), 'bells': ('bells',), 'cei': ('cei',),
            'combined': ('crafts', 'bells', 'cei'), 'baseline-after': ()}
SPECS = {
    'crafts': {'id': '9LgyB6Yb', 'project': 'kU1G12Nn', 'version': 'forge-1.20.1-1.3.3',
               'filename': 'createaddition-1.20.1-1.3.3.jar', 'mod': 'createaddition'},
    'bells': {'id': 'kW8DoegV', 'project': 'gJ5afkVv', 'version': '0.4.5-1.20.x',
              'filename': 'bellsandwhistles-0.4.5-1.20.x-Create6.0+.jar', 'mod': 'bellsandwhistles'},
    'cei': {'id': 'caLmFTZ1', 'project': 'JWGBpFUP', 'version': '1.4.1',
            'filename': 'create_enchantment_industry-1.4.1-for-create-6.0.8.jar',
            'mod': 'create_enchantment_industry'},
}


def destination(root, child, sources=()):
    root = Path(root).absolute()
    if root != OUTPUT_ROOT.absolute():
        raise ValueError('Only the explicitly authorized addon output root is permitted')
    return policy.validate_destination(root / child, sources)


def metadata_file(metadata, spec):
    if any(metadata.get(k) != spec[v] for k, v in
           [('id', 'id'), ('project_id', 'project'), ('version_number', 'version')]):
        raise ValueError('Unexpected upstream project/version identity')
    if 'forge' not in metadata.get('loaders', []) or metadata.get('game_versions') != ['1.20.1']:
        raise ValueError('Forge 1.20.1 release required')
    primary = [file for file in metadata.get('files', []) if file.get('primary') is True]
    if len(primary) != 1:
        raise ValueError('Exactly one primary upstream file is required')
    file = primary[0]
    name = file.get('filename', '')
    if name != spec['filename'] or not re.fullmatch(r'[A-Za-z0-9_.+\-]+\.jar', name):
        raise ValueError('Unexpected or unsafe filename')
    url = urllib.parse.urlsplit(file.get('url', ''))
    expected = f"/data/{spec['project']}/versions/{spec['id']}/{name}"
    if (url.scheme != 'https' or url.netloc != 'cdn.modrinth.com' or url.query or url.fragment
            or urllib.parse.unquote(url.path) != expected):
        raise ValueError('Primary file must use its exact official CDN location')
    if type(file.get('size')) is not int or not 0 < file['size'] <= 20_000_000:
        raise ValueError('Unexpected artifact size')
    for algorithm, length in [('sha512', 128), ('sha1', 40)]:
        if not re.fullmatch('[0-9a-f]{' + str(length) + '}', file.get('hashes', {}).get(algorithm, '')):
            raise ValueError('Both upstream hashes are required')
    return file


def validate_download(metadata, spec, content):
    file = metadata_file(metadata, spec)
    if len(content) != file['size'] or any(hashlib.new(kind, content).hexdigest() != file['hashes'][kind]
                                          for kind in ['sha512', 'sha1']):
        raise ValueError('Artifact size/hash mismatch: ' + spec['filename'])
    check_crc(content)
    return content


def check_crc(content, depth=0):
    if depth > 5:
        raise ValueError('Unexpected nested JarJar depth')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as jar:
            if sum(item.file_size for item in jar.infolist()) > 100_000_000 or jar.testzip() is not None:
                raise ValueError('Invalid JAR CRC or expanded size')
            if 'META-INF/jarjar/metadata.json' in jar.namelist():
                for entry in json.loads(jar.read('META-INF/jarjar/metadata.json')).get('jars', []):
                    name = entry['path']
                    if name.startswith('/') or '..' in name.split('/') or '\\' in name:
                        raise ValueError('Unsafe embedded artifact path')
                    check_crc(jar.read(name), depth + 1)
    except (zipfile.BadZipFile, KeyError) as error:
        raise ValueError('Invalid JAR or embedded artifact') from error


@functools.lru_cache(maxsize=1)
def inspector():
    # Reuse the existing descriptor implementation without executing its cache-creating module body.
    source = Path(__file__).resolve().parents[1] / 'resolve-pack.py'
    node = next(n for n in ast.parse(source.read_text('utf-8')).body
                if isinstance(n, ast.FunctionDef) and n.name == 'inspect_jar')
    namespace = {'Path': Path, 'io': io, 'json': json, 'tomllib': tomllib, 'zipfile': zipfile}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['inspect_jar']


class MemoryJar:
    def __init__(self, name, data):
        self.name, self.data = name, data

    def read_bytes(self):
        return self.data


def numeric_version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)*', value):
        raise ValueError('Unsupported mandatory dependency version: ' + str(value))
    return tuple(int(part) for part in value.split('.'))


def satisfies(version, required):
    value = numeric_version(version)
    def compare(other):
        endpoint = numeric_version(other)
        width = max(len(value), len(endpoint))
        return (value + (0,) * (width - len(value)), endpoint + (0,) * (width - len(endpoint)))
    if not isinstance(required, str):
        raise ValueError('Missing mandatory dependency range')
    match = re.fullmatch(r'([\[(])\s*([^,\]\)]*)\s*,\s*([^,\]\)]*)\s*([\])])', required)
    if match:
        lower, upper = match[2].strip(), match[3].strip()
        if lower:
            left, right = compare(lower)
            if left < right or (left == right and match[1] == '('): return False
        if upper:
            left, right = compare(upper)
            if left > right or (left == right and match[4] == ')'): return False
        return True
    exact = re.fullmatch(r'\[([^,\[\]]+)\]', required)
    if exact:
        left, right = compare(exact[1].strip())
        return left == right
    raise ValueError('Unsupported mandatory dependency range: ' + required)


def inventory(lock):
    result = {'minecraft': {lock['minecraft']}, 'forge': {lock['forge']}}
    for artifact in lock['artifacts']:
        for mod in artifact.get('descriptor', {}).get('mods', []):
            result.setdefault(mod['id'], set()).add(mod['version'])
    return result


def check_dependencies(descriptors, installed):
    combined = {key: set(value) for key, value in installed.items()}
    for descriptor in descriptors:
        for mod in descriptor['mods']:
            versions = combined.setdefault(mod['id'], set())
            if versions and mod['version'] not in versions:
                raise ValueError('Conflicting addon mod identity: ' + mod['id'])
            versions.add(mod['version'])
    for descriptor in descriptors:
        for dep in descriptor['dependencies']:
            if dep.get('mandatory') is not True:
                continue
            versions = combined.get(dep['modId'], set())
            if len(versions) != 1 or not satisfies(next(iter(versions)), dep.get('versionRange')):
                raise ValueError('Unmet or ambiguous mandatory dependency: ' + json.dumps(dep))


def request(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'VirgosMC-CreateAddonsLab/1.0'})
    with urllib.request.urlopen(req, timeout=60) as response:
        if urllib.parse.urlsplit(response.url).netloc != urllib.parse.urlsplit(url).netloc:
            raise ValueError('Cross-host redirect forbidden')
        data = response.read(20_000_001)
    if len(data) > 20_000_000:
        raise ValueError('Response exceeds laboratory size bound')
    return data if binary else json.loads(data)


def fetch(root, base_lock, transport=request):
    target = destination(root, 'upstream', [base_lock])
    lock_path = policy.regular(base_lock)
    lock = json.loads(lock_path.read_text('utf-8-sig'))
    installed = inventory(lock)
    projects = {item['project_id'] for item in lock['artifacts'] if 'project_id' in item}
    projects.update(spec['project'] for spec in SPECS.values())
    records, payloads = {}, {}
    for name, spec in SPECS.items():
        metadata = transport('https://api.modrinth.com/v2/version/' + spec['id'])
        file = metadata_file(metadata, spec)
        for dep in metadata.get('dependencies', []):
            if dep.get('dependency_type') == 'required':
                known_versions = {item.get('version_id') for item in lock['artifacts']} | {s['id'] for s in SPECS.values()}
                if dep.get('project_id') not in projects or (dep.get('version_id') and dep['version_id'] not in known_versions):
                    raise ValueError('Unpinned required upstream project: ' + json.dumps(dep))
        data = validate_download(metadata, spec, transport(file['url'], binary=True))
        descriptor = inspector()(MemoryJar(spec['filename'], data))
        if spec['mod'] not in {mod['id'] for mod in descriptor['mods']}:
            raise ValueError('Expected addon mod missing from descriptor')
        records[name] = {'metadata': metadata, 'descriptor': descriptor,
                         'filename': spec['filename'], 'sha256': hashlib.sha256(data).hexdigest()}
        payloads[spec['filename']] = data
    for record in records.values():
        check_dependencies([record['descriptor']], installed)
    check_dependencies([record['descriptor'] for record in records.values()], installed)
    # Reject every bad input before creating any output. A completion record is written last.
    target.mkdir(parents=True)
    for filename, data in payloads.items():
        (target / filename).write_bytes(data)
    report = {'schema': 1, 'baseLockSha256': policy.sha(lock_path), 'addons': records,
              'baseInventory': {key: sorted(value) for key, value in installed.items()},
              'runtimeProof': 'pending'}
    (target / 'upstream.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def variants(root, base_artifacts, client):
    upstream = Path(root) / 'upstream'
    target = destination(root, 'variant-artifacts', [base_artifacts, client, upstream])
    base = policy.verified_artifacts(base_artifacts, client)
    base_manifest = json.loads(policy.regular(Path(base_artifacts) / 'compat-manifest.json').read_text('utf-8'))
    report = json.loads(policy.regular(upstream / 'upstream.json').read_text('utf-8'))
    if report.get('schema') != 1 or set(report['addons']) != set(SPECS):
        raise ValueError('Unexpected upstream report')
    for name, spec in SPECS.items():
        row = report['addons'][name]
        data = policy.regular(upstream / spec['filename']).read_bytes()
        validate_download(row['metadata'], spec, data)
        if row['filename'] != spec['filename'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Upstream report hash mismatch')
    base_names = {entry['filename'] for entry in base_manifest['artifacts']}
    if base_names.intersection(spec['filename'] for spec in SPECS.values()):
        raise ValueError('Addon already present in baseline artifacts')
    for name, selected in VARIANTS.items():
        directory = target / name
        directory.mkdir(parents=True)
        manifest = json.loads(json.dumps(base_manifest))
        for source in base:
            shutil.copy2(source, directory / source.name)
        for addon in selected:
            row = report['addons'][addon]
            shutil.copy2(upstream / row['filename'], directory / row['filename'])
            manifest['artifacts'].append({'filename': row['filename'], 'sha256': row['sha256']})
        (directory / 'compat-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return {name: str(target / name) for name in VARIANTS}
