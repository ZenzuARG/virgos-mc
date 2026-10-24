"""Promote the stopped, verified lab without replacing production credentials.

First deployment only: the new world name must not exist at the destination.
Original world folders remain on disk and in the predeployment backup.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import runpy
import shutil
import socket
import zipfile

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'.lab/server'
QA={'13e2e728-2a7a-36a6-84ee-5c289cf4cc02','32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e'}
parser=argparse.ArgumentParser()
parser.add_argument('--backup',type=Path,required=True)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()

def stopped(base,port):
    for file in [base/'process.json',base/'.runtime/active-run.json']:
        if not file.exists():continue
        state=json.loads(file.read_text('utf-8-sig'))
        if state.get('pid') and not state.get('finished'):
            handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,state['pid'])
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle);raise RuntimeError('Server still running: '+str(base))
    with socket.socket() as probe:
        probe.settimeout(.5)
        if probe.connect_ex(('127.0.0.1',port))==0:raise RuntimeError('Port still open: '+str(port))

stopped(ROOT,25565);stopped(LAB,25575)
backup=args.backup.resolve();backup.relative_to((ROOT/'backups/full').resolve())
with zipfile.ZipFile(backup) as archive:
    if archive.testzip() is not None:raise RuntimeError('Invalid predeployment backup')

reports=['qa-spawn-gates.json','qa-private-claims.json','qa-claim-boundary.json','qa-arena-walk.json','qa-expeditions.json','qa-arena-pve.json','qa-arena-melee.json','qa-corpse-recovery.json','qa-world-cleanup.json','client-installer-verification.json','restore-runtime-verification.json']
for name in reports:
    data=json.loads((ROOT/'.lab/reports'/name).read_text('utf-8'))
    cases=data if isinstance(data,list) else data.get('cases',[data])
    if not all(case.get('passed') is True for case in cases):raise RuntimeError('Validation not passed: '+name)
for name in ['bastion','arena-virgos-v3']:
    data=json.loads((LAB/f'virgos-reports/{name}-audit.json').read_text('utf-8'))
    if any(data[key] for key in ['unsupported','missing','wrongBlocks','blockedWalkChecks','routeProblems']):raise RuntimeError('Construction audit failed: '+name)
worlds=sorted(p for p in LAB.iterdir() if p.is_dir() and (p.name=='virgos_world' or p.name.startswith('virgos_world_')))
if len(worlds)!=6:raise RuntimeError('Expected six world folders')
for world in worlds:
    if (ROOT/world.name).exists():raise RuntimeError('Destination world already exists: '+world.name)
read_nbt=runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt']
for name in ['heracles_quest_progress.dat','heracles_pinned_quests.dat']:
    data=read_nbt(LAB/'virgos_world/data'/name)['']['data']
    if set(data)-QA:raise RuntimeError('Non-QA quest progress must be preserved explicitly')
for file in (LAB/'virgos_world/playerdata').glob('*.dat'):
    if file.stem not in QA:raise RuntimeError('Non-QA player exists; review before deployment')
for identity in QA:
    data=read_nbt(LAB/f'virgos_world/data/openpartiesandclaims/player-claims/{identity}.nbt')['']
    if data['dimensions']:raise RuntimeError('A QA claim remains')

lock=json.loads((ROOT/'pack/mods.lock.json').read_text('utf-8'))
custom=json.loads((ROOT/'pack/custom-artifacts.lock.json').read_text('utf-8'))
copies=[]
for item in lock['artifacts']+custom['artifacts']:
    if 'server' not in item['sides'] or item['mode']=='optional':continue
    source=ROOT/item['local_source'] if 'local_source' in item else ROOT/'.cache/pack/downloads'/item['filename']
    digest=hashlib.new(item['hash_algorithm'],source.read_bytes()).hexdigest()
    if digest!=item['hash'] or digest!=hashlib.new(item['hash_algorithm'],(LAB/'mods'/item['filename']).read_bytes()).hexdigest():raise RuntimeError('Unvalidated server mod: '+item['filename'])
    copies.append((source,ROOT/'mods'/item['filename']))
lp=json.loads((ROOT/'pack/luckperms.lock.json').read_text('utf-8'))
source=LAB/'plugins'/lp['filename']
if hashlib.sha512(source.read_bytes()).hexdigest()!=lp['sha512']:raise RuntimeError('LuckPerms mismatch')
copies.append((source,ROOT/'plugins'/source.name))
# Preserve generated defaults used during the live tests, including mods whose
# settings did not need a balance override. No tunnel or account files live here.
for file in (LAB/'config').rglob('*'):
    if not file.is_file() or file.suffix not in {'.toml','.properties','.json','.json5'}:continue
    relative=file.relative_to(LAB/'config')
    if 'playit' in relative.as_posix().lower() or file.name.startswith('amendments-'):continue
    copies.append((file,ROOT/'config'/relative))
for folder in ['config','defaultconfigs','kubejs']:
    for file in (ROOT/'pack/server-overrides'/folder).rglob('*'):
        if file.is_file():copies.append((file,ROOT/file.relative_to(ROOT/'pack/server-overrides')))
# Preserve AuthMe's production database while applying the tested settings/messages.
for name in ['config.yml','messages/messages_es.yml']:
    file=LAB/'plugins/AuthMe'/name
    if file.exists():copies.append((file,ROOT/'plugins/AuthMe'/name))

omitted=[];world_copies=[]
for world in worlds:
    for file in world.rglob('*'):
        if not file.is_file():continue
        relative=file.relative_to(world)
        if file.is_symlink():raise RuntimeError('Symlink in world')
        omit=(file.name=='session.lock' or any(identity in relative.as_posix() for identity in QA)
              or relative.as_posix() in ['data/heracles_quest_progress.dat','data/heracles_pinned_quests.dat','virgos-expeditions-state.json']
              or relative.parts[0]=='deaths')
        if omit:omitted.append((Path(world.name)/relative).as_posix())
        else:world_copies.append((file,ROOT/world.name/relative))
if any('virgos_local_qa' in target.name for _,target in copies):raise RuntimeError('QA included in release')
summary={'version':'0.1.0-rc1','applied':args.apply,'backup':backup.name,'worlds':[w.name for w in worlds],'filesToCopy':len(copies)+len(world_copies),'omittedQA':omitted,'credentialPolicy':'Existing Playit files and AuthMe database are preserved.','validationReports':reports}
if args.apply:
    for source,destination in copies+world_copies:
        destination.resolve().relative_to(ROOT.resolve())
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
    properties=(LAB/'server.properties').read_text('utf-8')
    properties=properties.replace('server-ip=127.0.0.1','server-ip=').replace('server-port=25575','server-port=25565')
    properties=properties.replace('motd=Virgos-MC | Laboratorio local','motd=Virgos-MC | Exploracion, magia y Create | 1.20.1')
    properties=properties.replace('level-seed=\n','level-seed=-4556043908712459124\n')
    (ROOT/'server.properties').write_text(properties,'utf-8')
    (ROOT/'pack/deployed-release.json').write_text(json.dumps(summary,indent=2),'utf-8')
print(json.dumps(summary,indent=2))
