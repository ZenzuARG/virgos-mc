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

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();candidate=parser.add_mutually_exclusive_group();candidate.add_argument('--candidate-v12',action='store_true');candidate.add_argument('--candidate-v2',action='store_true');options=parser.parse_args()
current=json.loads((ROOT/'pack/current-release.json').read_text('utf-8'))
VERSION='2.0.0' if options.candidate_v2 else ('1.2.0' if options.candidate_v12 else current['version'])
INSTALLER=6 if options.candidate_v2 else (5 if options.candidate_v12 else current['installer'])
candidate_dir='.lab/v2' if options.candidate_v2 else ('.lab/v12' if options.candidate_v12 else None)
lock=json.loads((ROOT/(candidate_dir+'/mods.lock.json' if candidate_dir else 'pack/mods.lock.json')).read_text('utf-8'))
files=[];client=[];bundled={}
for item in lock['artifacts']:
    if 'client' not in item['sides'] or item['mode']=='tool':continue
    source=ROOT/'.cache/pack/downloads'/item['filename']
    content=source.read_bytes()
    if hashlib.new(item['hash_algorithm'],content).hexdigest()!=item['hash']:raise ValueError(item['filename'])
    hashes={kind:hashlib.new(kind,content).hexdigest() for kind in ['sha1','sha512']}
    files.append({'path':'mods/'+item['filename'],'hashes':hashes,'env':{'client':'optional' if item['mode']=='optional' else 'required','server':'unsupported'},'downloads':[item['url']],'fileSize':len(content)})
    client.append({'filename':item['filename'],'url':item['url'],'sha512':hashes['sha512'],'optional':item['mode']=='optional','project':item['project'],'source':item['source']})
custom=[]
if options.candidate_v2:
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
manifest={'version':VERSION,'installerVersion':INSTALLER,'minecraft':lock['minecraft'],'forge':lock['forge'],'files':client}
runtime=json.loads((ROOT/'pack/client-runtime.lock.json').read_text('utf-8'))
assert runtime['minecraftJson']['url'].startswith('https://piston-meta.mojang.com/')
for spec,folder in [(runtime['java'],ROOT/'.cache'),(runtime['forge'],ROOT/'.cache/pack')]:
    assert hashlib.sha256((folder/spec['file']).read_bytes()).hexdigest()==spec['hash']
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
with zipfile.ZipFile(output/f'Virgos-MC-{VERSION}.mrpack','w',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('modrinth.index.json',json.dumps(index,ensure_ascii=False,indent=2))
    for name,content in overrides.items():archive.writestr(name,content)
    for name,content in bundled.items():archive.writestr('overrides/mods/'+name,content)
zip_name=f'Virgos-MC-{VERSION}-instalar.zip'
with zipfile.ZipFile(output/zip_name,'w',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('asistente/cliente.lock.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    for name,content in bundled.items():archive.writestr('asistente/bundled/'+name,content)
    for name in ['instalar-cliente.ps1','instalar-cliente.bat','installer-common.ps1','tlauncher-settings.ps1','install-launcher.ps1','asistente.ps1']:
        content=(ROOT/'templates'/name).read_text('utf-8-sig')
        archive.writestr('asistente/'+name,content.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8-sig' if name.endswith('.ps1') else 'ascii'))
    archive.write(ROOT/'pack/client-runtime.lock.json','asistente/runtime.lock.json')
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
