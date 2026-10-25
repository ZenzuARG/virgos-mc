"""Graphical Windows setup for official/TLauncher clients; mrpack as secondary export.

Only URLs, pinned hashes, setup scripts and explicit client overrides are shipped.
No accounts, credentials, QA driver, worlds, launcher or Minecraft binaries.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import struct
import argparse
import re

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
candidate=parser.add_mutually_exclusive_group()
candidate.add_argument('--candidate-v12',action='store_true')
candidate.add_argument('--candidate-v2',action='store_true')
for flag in ['release-metadata','custom-lock','mods-lock','output','downloads','runtime-cache']:
    parser.add_argument('--'+flag,type=Path,help='Explicit offline candidate input/output; see docs/client-release-candidates.md')
options=parser.parse_args()
explicit=any(getattr(options,name) is not None for name in ['release_metadata','custom_lock','mods_lock','output','downloads','runtime_cache'])
source_payloads={}


class ReproducibleZip:
    """Candidate-only stable entries, independent of host clock, mode and file mtime."""
    def __init__(self, path, *args):
        self.path = path
        self.entries = {}

    def __enter__(self): return self

    def writestr(self, name, data):
        if name in self.entries: raise ValueError('Duplicate archive entry: ' + name)
        self.entries[name] = data.encode('utf-8') if isinstance(data, str) else data

    def write(self, path, name): self.writestr(name, Path(path).read_bytes())

    def __exit__(self, kind, value, traceback):
        if kind is not None: return False
        with zipfile.ZipFile(self.path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(self.entries):
                entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                entry.create_system = 3; entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, self.entries[name])

def safe_path(path,kind='file'):
    path=path.absolute()
    if any(p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()) for p in [path,*path.parents]):
        raise ValueError('Candidate linked path forbidden: '+str(path))
    if kind=='file' and not path.is_file():raise ValueError('Candidate input missing: '+str(path))
    if kind=='directory' and not path.is_dir():raise ValueError('Candidate cache missing: '+str(path))
    return path.resolve()

def safe_filename(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.+ ()-]+',name) or name in {'.','..'}:
        raise ValueError('Candidate unsafe filename')
    return name

def candidate_artifacts(lock,path):
    import tomllib
    payloads={};roles=set();sources=[]
    for item in lock['artifacts']:
        if 'client' not in item['sides']:continue
        name=safe_filename(item['filename'])
        mod_version=r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?'
        if re.fullmatch(r'virgos_codex-'+mod_version+r'\.jar',name):role='virgos_codex'
        elif name=='DistantHorizons-3.3.3-1.20.1-fabric-forge.jar':role='distanthorizons'
        elif re.fullmatch(r'virgos_dh_compat-'+mod_version+r'\.jar',name):role='virgos_dh_compat'
        else:raise ValueError('Candidate artifact role/filename rejected: '+name)
        if role in roles or item.get('mode','required')!='required':raise ValueError('Candidate artifact duplicate/optional role: '+role)
        relative=Path(item['local_source'])
        if '..' in relative.parts:raise ValueError('Candidate artifact source traversal')
        source=safe_path(relative if relative.is_absolute() else path.parent/relative)
        content=source.read_bytes()
        if item.get('hash_algorithm') not in {'sha256','sha512'} or hashlib.new(item['hash_algorithm'],content).hexdigest()!=item.get('hash'):
            raise ValueError('Candidate artifact hash mismatch: '+name)
        with zipfile.ZipFile(source) as jar:
            paths=jar.namelist()
            def forbidden_entry(name):
                lower=name.lower()
                # These are shipped DH runtime diagnostics, not our QA driver or
                # unit tests. Preserve upstream bytes rather than stripping them.
                upstream_dh=(role=='distanthorizons' and (
                    name.startswith('assets/distanthorizons/shaders/test/') or
                    name in {'com/seibel/distanthorizons/common/render/blaze/test/',
                             'com/seibel/distanthorizons/common/render/openGl/test/',
                             'com/seibel/distanthorizons/common/render/blaze/test/BlazeDhTestTriangleRenderer.class',
                             'com/seibel/distanthorizons/common/render/openGl/test/GlTestTriangleRenderer.class',
                             'com/seibel/distanthorizons/common/render/openGl/test/GlTestTriangleRenderer_forge.class',
                             'com/seibel/distanthorizons/core/config/Config$Client$Advanced$Debugging$ExampleConfigScreen$CategoryTest.class'}))
                return ('/qa/' in lower or 'virgos_local_qa' in lower or name.endswith('ClientProbe.class')
                        or lower.startswith(('org/junit/','junit/')) or
                        (('/test/' in lower or '/tests/' in lower or re.search(r'(?:Test|Tests|TestCase)(?:\$[^/]*)?\.class$',name)) and not upstream_dh))
            if any(forbidden_entry(n) for n in paths):
                raise ValueError('Candidate artifact contains QA/tests: '+name)
            metadata=tomllib.loads(jar.read('META-INF/mods.toml').decode('utf-8-sig'))
            if [m.get('modId') for m in metadata.get('mods',[])]!=[role]:raise ValueError('Candidate artifact modId mismatch: '+name)
            if role=='distanthorizons' and metadata['mods'][0].get('version')!='3.3.3':raise ValueError('Candidate artifact DH version mismatch')
            if role=='virgos_codex' and 'mc/virgos/codex/ProfileScreen.class' not in paths:raise ValueError('Candidate artifact lacks profile UI')
        roles.add(role);sources.append(source);payloads[name]=content
    if roles!={'virgos_codex','distanthorizons','virgos_dh_compat'}:raise ValueError('Candidate artifacts require exactly Codex, DH and compatibility addon')
    return payloads,sources

if explicit:
    if options.candidate_v2 or options.candidate_v12:parser.error('Explicit candidate inputs cannot mix with legacy candidate flags')
    if not all(getattr(options,name) is not None for name in ['release_metadata','custom_lock','output','downloads','runtime_cache']):
        parser.error('Candidate requires --release-metadata --custom-lock --output --downloads --runtime-cache together')
    metadata_path=safe_path(options.release_metadata)
    custom_path=safe_path(options.custom_lock)
    mods_path=safe_path(options.mods_lock or ROOT/'pack/mods.lock.json')
    downloads=safe_path(options.downloads,'directory')
    runtime_cache=safe_path(options.runtime_cache,'directory')
    current=json.loads(metadata_path.read_text('utf-8-sig'))
    version=current.get('version')
    if not isinstance(version,str) or not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?',version):raise ValueError('Candidate version is unsafe')
    release=current.get('clientRelease','')
    if (not isinstance(release,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',release)
        or not (release==version or release.startswith(version+'-'))
        or current.get('clientFingerprint')!='virgos-client-'+release):raise ValueError('Candidate release identity mismatch')
    if type(current.get('installer')) is not int or current['installer']<1:raise ValueError('Candidate installer must be a positive integer')
    # Distribute pinned upstream sources and local modifications alongside patched binaries.
    for item in current.get('sourceFiles',[]):
        name=safe_filename(item['filename'])
        relative=Path(item['local_source'])
        if (name in source_payloads or not name.endswith(('.zip','.txt')) or
            relative.is_absolute() or '..' in relative.parts):
            raise ValueError('Candidate corresponding-source path rejected')
        source=safe_path(metadata_path.parent/relative)
        content=source.read_bytes()
        if hashlib.sha256(content).hexdigest()!=item.get('sha256'):
            raise ValueError('Candidate corresponding-source hash mismatch: '+name)
        source_payloads[name]=content
    custom_lock=json.loads(custom_path.read_text('utf-8-sig'))
    if custom_lock.get('schema')!=1:raise ValueError('Candidate custom lock schema must be 1')
    candidate_bundled,artifact_sources=candidate_artifacts(custom_lock,custom_path)
    output=safe_path(options.output,'output')
    protected=[ROOT.resolve(),Path('D:/proyectos/mc-server').resolve(),downloads,runtime_cache,
               metadata_path.parent,custom_path.parent,mods_path.parent,*[p.parent for p in artifact_sources]]
    if any(output==p or output in p.parents or p in output.parents for p in protected):raise ValueError('Candidate output overlaps a source/cache/public path')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):raise ValueError('Candidate output must be new or empty')
else:
    current=json.loads((ROOT/'pack/current-release.json').read_text('utf-8'))
VERSION=current['version'] if explicit else ('2.0.0' if options.candidate_v2 else ('1.2.0' if options.candidate_v12 else current['version']))
INSTALLER=current['installer'] if explicit else (6 if options.candidate_v2 else (5 if options.candidate_v12 else current['installer']))
candidate_dir='.lab/v2' if options.candidate_v2 else ('.lab/v12' if options.candidate_v12 else None)
lock=json.loads((mods_path if explicit else ROOT/(candidate_dir+'/mods.lock.json' if candidate_dir else 'pack/mods.lock.json')).read_text('utf-8'))
if explicit and (lock.get('minecraft')!='1.20.1' or lock.get('forge')!='47.4.22'):
    raise ValueError('Candidate mods lock must retain Minecraft 1.20.1 and Forge 47.4.22')
files=[];client=[];bundled={}
for item in lock['artifacts']:
    if 'client' not in item['sides'] or item['mode']=='tool':continue
    if explicit:
        safe_filename(item['filename'])
        if item['filename'] in candidate_bundled:continue
        if item['filename'].lower().startswith('distanthorizons'):raise ValueError('Candidate upstream DH conflicts with pinned replacement')
    source=safe_path(downloads/item['filename']) if explicit else ROOT/'.cache/pack/downloads'/item['filename']
    content=source.read_bytes()
    if hashlib.new(item['hash_algorithm'],content).hexdigest()!=item['hash']:raise ValueError(item['filename'])
    hashes={kind:hashlib.new(kind,content).hexdigest() for kind in ['sha1','sha512']}
    files.append({'path':'mods/'+item['filename'],'hashes':hashes,'env':{'client':'optional' if item['mode']=='optional' else 'required','server':'unsupported'},'downloads':[item['url']],'fileSize':len(content)})
    client.append({'filename':item['filename'],'url':item['url'],'sha512':hashes['sha512'],'optional':item['mode']=='optional','project':item['project'],'source':item['source']})
custom=[]
if explicit:
    bundled.update(candidate_bundled)
    for name,content in bundled.items():
        project=('virgos-codex' if name.startswith('virgos_codex-') else
                 'distant-horizons' if name.startswith('DistantHorizons-') else 'virgos-dh-compat')
        client.append({'filename':name,'sha512':hashlib.sha512(content).hexdigest(),'optional':False,'project':project,'source':'local-candidate','bundled':True})
elif options.candidate_v2:
    custom=[{'filename':'virgos_codex-2.0.0.jar','local_source':'dev/virgos-core/build/libs/virgos_codex-2.0.0.jar','sides':['client']}]
elif not options.candidate_v12:
    custom=json.loads((ROOT/'pack/custom-artifacts.lock.json').read_text('utf-8'))['artifacts']
for item in custom:
    if 'client' not in item['sides']:continue
    name=item['filename'];source=ROOT/item['local_source'];content=source.read_bytes()
    if 'hash' in item:assert hashlib.new(item['hash_algorithm'],content).hexdigest()==item['hash'],name
    assert name.startswith('virgos_codex-') and name.endswith('.jar'),name
    with zipfile.ZipFile(source) as jar:
        assert not any('/qa/' in path or path.endswith('ClientProbe.class') for path in jar.namelist())
        assert 'mc/virgos/codex/ProfileScreen.class' in jar.namelist()
    bundled[name]=content
    client.append({'filename':name,'sha512':hashlib.sha512(content).hexdigest(),'optional':False,'project':'virgos-codex','source':'Virgos-MC','bundled':True})
index={'formatVersion':1,'game':'minecraft','versionId':VERSION,'name':'Virgos-MC','summary':'Exploracion, magia e industria; cliente para el servidor Virgos-MC.','files':files,'dependencies':{'minecraft':lock['minecraft'],'forge':lock['forge']}}
manifest={'version':VERSION,'installerVersion':INSTALLER,'clientRelease':current.get('clientRelease',VERSION),'clientFingerprint':current.get('clientFingerprint',''),'minecraft':lock['minecraft'],'forge':lock['forge'],'files':client}
runtime=json.loads((ROOT/'pack/client-runtime.lock.json').read_text('utf-8'))
assert runtime['minecraftJson']['url'].startswith('https://piston-meta.mojang.com/')
for spec,folder in [(runtime['java'],runtime_cache if explicit else ROOT/'.cache'),(runtime['forge'],runtime_cache/'pack' if explicit else ROOT/'.cache/pack')]:
    if explicit:safe_filename(spec['file']);safe_path(folder/spec['file'])
    assert hashlib.sha256((folder/spec['file']).read_bytes()).hexdigest()==spec['hash']
template_names=['instalar-cliente.ps1','instalar-cliente.bat','installer-common.ps1','client-keybindings.ps1','tlauncher-settings.ps1','install-launcher.ps1','asistente.ps1']
dh_helper=ROOT/'templates/dh-client-settings.ps1'
dh_seed=ROOT/'pack/client-overrides/config/DistantHorizons.toml'
if dh_helper.is_file()!=dh_seed.is_file():raise ValueError('DH helper and seed must be supplied together')
if dh_helper.is_file():template_names.append('dh-client-settings.ps1')
elif explicit:raise ValueError('Candidate requires the paired DH helper and seed')
if not explicit:
    output=ROOT/('dist/v2-preview' if options.candidate_v2 else ('dist/v12-preview' if options.candidate_v12 else 'dist'));output.mkdir(exist_ok=True)
allow={'config','resourcepacks'}
overrides={}
for file in (ROOT/'pack/client-overrides').rglob('*'):
    if not file.is_file():continue
    relative=file.relative_to(ROOT/'pack/client-overrides')
    if relative.parts[0] not in allow:raise ValueError('Unexpected override: '+str(relative))
    overrides['overrides/'+relative.as_posix()]=file.read_bytes()
if candidate_dir:
    for file in (ROOT/candidate_dir/'client-overrides').rglob('*'):
        if file.is_file():
            relative=file.relative_to(ROOT/candidate_dir/'client-overrides');assert relative.parts[0] in allow
            overrides['overrides/'+relative.as_posix()]=file.read_bytes()
def nbt_string(value):
    data=value.encode('utf-8')
    return struct.pack('>H',len(data))+data
overrides['overrides/servers.dat']=(b'\x0a\x00\x00\x09'+nbt_string('servers')+b'\x0a'+struct.pack('>i',1)
    +b'\x08'+nbt_string('name')+nbt_string('Virgos-MC')
    +b'\x08'+nbt_string('ip')+nbt_string('virgos-mc.playit.plus')+b'\x00\x00')
initial_options=(ROOT/'pack/client-overrides/config/defaultoptions/options.txt').read_text('utf-8')
initial_options=initial_options.replace('resourcePacks:[]','resourcePacks:["vanilla","file/Virgos-MC-UI.zip"]')
overrides['overrides/options.txt']=initial_options.encode('utf-8')
if explicit:
    # Validate static package inputs before creating any candidate output.
    for relative in ['pack/client-runtime.lock.json','pack/keybindings.json','pack/shaderpack.lock.json','docs/manual-jugadores.md',
                     *['templates/'+name for name in template_names+['EMPEZAR.bat','LEEME.txt']]]:
        safe_path(ROOT/relative)
    output.mkdir(parents=True,exist_ok=True)
archive_type = ReproducibleZip if explicit else zipfile.ZipFile
with archive_type(output/f'Virgos-MC-{VERSION}.mrpack','w',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('modrinth.index.json',json.dumps(index,ensure_ascii=False,indent=2))
    for name,content in overrides.items():archive.writestr(name,content)
    for name,content in bundled.items():archive.writestr('overrides/mods/'+name,content)
    for name,content in source_payloads.items():archive.writestr('sources/'+name,content)
zip_name=f'Virgos-MC-{VERSION}-instalar.zip'
with archive_type(output/zip_name,'w',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('asistente/cliente.lock.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    for name,content in bundled.items():archive.writestr('asistente/bundled/'+name,content)
    for name,content in source_payloads.items():archive.writestr('sources/'+name,content)
    for name in template_names:
        content=(ROOT/'templates'/name).read_text('utf-8-sig')
        archive.writestr('asistente/'+name,content.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8-sig' if name.endswith('.ps1') else 'ascii'))
    archive.write(ROOT/'pack/client-runtime.lock.json','asistente/runtime.lock.json')
    archive.write(ROOT/'pack/keybindings.json','asistente/keybindings.json')
    archive.write(ROOT/'pack/shaderpack.lock.json','asistente/shaderpack.lock.json')
    for name in ['EMPEZAR.bat','LEEME.txt']:
        archive.writestr(name,(ROOT/'templates'/name).read_text('utf-8').replace('\r\n','\n').replace('\n','\r\n'))
    archive.writestr('COMO-JUGAR.txt',(ROOT/'docs/manual-jugadores.md').read_text('utf-8').encode('utf-8-sig'))
    for name,content in overrides.items():archive.writestr('asistente/'+name,content)
report={'version':VERSION,'installerVersion':INSTALLER,'required':sum(not x['optional'] for x in client),'optional':sum(x['optional'] for x in client),'upstreamBytes':sum(x['fileSize'] for x in files),'overrideFiles':len(overrides),'files':[]}
for file in [output/zip_name,output/f'Virgos-MC-{VERSION}.mrpack']:
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        assert not any('virgos_local_qa' in n or 'playit' in n.lower() or '/saves/' in n for n in archive.namelist())
    report['files'].append({'name':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(output/'release.json').write_text(json.dumps(report,indent=2),'utf-8')
print(json.dumps(report,indent=2))
