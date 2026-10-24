"""Promote the stopped v2 candidate with a full reset and a recoverable v1 archive.

No account, permission, Playit or Discord files are imported from the laboratory.
Run without --apply first. Acceptance records must match the actual built jars.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ctypes,hashlib,json,re,runpy,shutil,socket,zipfile
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2';L=V/'server'
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def within(p):
    assert p.resolve().is_relative_to(R.resolve()),p
    assert not p.is_symlink(),p
    return p
def stopped(state,port):
    data=read(state);assert data.get('finished') and not data.get('backupInProgress'),state
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0,port
stopped(R/'.runtime/active-run.json',25565);stopped(L/'process.json',25575)
assert read(L/'process.json')['exitCode']==0
accept=read(V/'acceptance.json');assert accept['passed']
core=R/'dev/virgos-core/build/libs/virgos_core-2.0.0.jar';codex=core.with_name('virgos_codex-2.0.0.jar')
assert sha(core)==accept['coreSha256']==sha(L/'mods'/core.name)
assert sha(codex)==accept['codexSha256']
backup=read(R/'.runtime/last-backup.json');archive=within(Path(backup['archive']));assert sha(archive)==backup['sha256']
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('backup-manifest.json'));assert len(manifest['worldFolders'])==6
    assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
assert read(R/'pack/current-release.json')['version']=='1.2.0','Promotion is only from the backed-up v1.2'
audit=read(L/'virgos-reports/auditoria-pueblo-v2-audit.json')
assert all(not audit[k] for k in ['unsupported','missing','wrongBlocks','blockedWalkChecks','routeProblems'])
worlds=sorted(w for w in L.glob('virgos_world*') if w.is_dir());assert len(worlds)==6
qa={'13e2e728-2a7a-36a6-84ee-5c289cf4cc02','32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e','3b6e246d-95b1-37ba-83c4-359423490806'}
assert all(f.stem in qa for f in (L/'virgos_world/playerdata').glob('*.dat'))
nbt=runpy.run_path(str(R/'scripts/inspect-nbt.py'))['read_nbt']
for name in ['heracles_quest_progress.dat','heracles_pinned_quests.dat']:
    f=L/'virgos_world/data'/name
    if f.exists():assert set(nbt(f)['']['data'])<=qa
assert not (L/'virgos_world/virgos-market.json').exists() or not read(L/'virgos_world/virgos-market.json')
omitted=[];copies={}
reset={'session.lock','heracles_quest_progress.dat','heracles_pinned_quests.dat','lightmanscurrency_bank_data.dat','lightmanscurrency_notification_data.dat','perks.dat','virgos-profiles.json','virgos-profiles.json.tmp','virgos-expeditions-state.json','virgos-community.json'}
for world in worlds:
    for f in world.rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(world)
        skip=f.name in reset or rel.parts[0] in {'playerdata','stats','advancements','deaths'} or any(q in rel.as_posix() for q in qa)
        if skip:omitted.append(f.relative_to(L).as_posix())
        else:copies[R/world.name/rel]=f
# Generated mod defaults have been tested, but voice/tunnel/maintenance keep their
# production settings. Only the curated plugin override is admitted below.
for f in (L/'config').rglob('*'):
    if not f.is_file():continue
    rel=f.relative_to(L)
    if any(v in rel.as_posix().lower() for v in ['playit','voicechat','maintenance.json']):continue
    copies[R/rel]=f
for folder in ['kubejs','defaultconfigs']:
    for f in (L/folder).rglob('*'):
        if f.is_file():
            assert not any(token in f.name.lower() for token in ['zz_qa','debug','test_']),f
            copies[R/f.relative_to(L)]=f
for f in (V/'server-overrides').rglob('*'):
    if f.is_file():
        rel=f.relative_to(V/'server-overrides');assert rel.parts[0] in {'config','kubejs','defaultconfigs','plugins'}
        copies[R/rel]=f;copies[R/'pack/server-overrides'/rel]=f
for f in (V/'client-overrides').rglob('*'):
    if f.is_file():copies[R/'pack/client-overrides'/f.relative_to(V/'client-overrides')]=f
lock=read(V/'mods.lock.json')
expected=set()
for item in lock['artifacts']:
    if 'server' not in item['sides'] or item['mode']=='optional':continue
    source=R/'.cache/pack/downloads'/item['filename'];assert hashlib.new(item['hash_algorithm'],source.read_bytes()).hexdigest()==item['hash']
    assert source.read_bytes()==(L/'mods'/source.name).read_bytes()
    copies[R/'mods'/source.name]=source;expected.add(source.name)
copies[R/'mods'/core.name]=core;expected.add(core.name)
expected.add(read(R/'versions.lock.json')['playitCompanion']['file'])
retire=[f for f in (R/'mods').glob('*.jar') if f.name not in expected]
admin=read(R/'pack/administration.lock.json');cp=next(a for a in admin if a['project']=='coreprotect')
patched=V/'CoreProtect-CE-24.1-virgos.1.jar';assert sha(patched)==sha(L/'plugins'/patched.name)
retire.append(R/'plugins'/cp['filename'])
cp['upstream']={k:cp[k] for k in ['filename','url','hash','hash_algorithm']}
cp.update(filename=patched.name,version='24.1-virgos.1',local_source=patched.relative_to(R).as_posix(),hash_algorithm='sha256',hash=sha(patched));cp.pop('url',None)
copies[R/'plugins'/patched.name]=patched
copies[R/'pack/mods.lock.json']=V/'mods.lock.json';copies[R/'pack/quests-index.json']=V/'quests-index.json'
custom={'schema':1,'artifacts':[{'filename':f.name,'local_source':f.relative_to(R).as_posix(),'hash_algorithm':'sha256','hash':sha(f),'sides':[side],'mode':'required','name':name} for f,side,name in [(core,'server','Integración Virgos-MC'),(codex,'client','Códice y perfiles Virgos-MC')]]}
report={'version':'2.0.0','applied':args.apply,'backup':str(archive),'files':len(copies),'worlds':[w.name for w in worlds],'omittedQA':omitted,'retired':[p.relative_to(R).as_posix() for p in retire],'credentialPolicy':'Production accounts, permissions, Discord and Playit preserved'}
for target,source in copies.items():within(target);within(source)
if args.apply:
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');old=within(R/'backups'/f'v1-before-v2-{stamp}');old.mkdir()
    # Preserve every overwritten non-world file; original worlds are moved intact.
    with zipfile.ZipFile(old/'configuration.zip','w',zipfile.ZIP_DEFLATED) as z:
        for target in set(copies)|set(retire)|{R/'pack/current-release.json',R/'pack/custom-artifacts.lock.json',R/'pack/administration.lock.json',R/'server.properties',R/'spigot.yml',R/'plugins/DiscordSRV/config.yml'}:
            if target.is_file() and target.relative_to(R).parts[0] not in [w.name for w in worlds]:z.write(target,target.relative_to(R).as_posix())
    for world in worlds:
        source=within(R/world.name);dest=within(old/world.name);assert source.is_dir() and not dest.exists()
        shutil.move(str(source),str(dest))
    for target in retire:
        if target.exists():
            dest=within(old/target.relative_to(R));dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(target),str(dest))
    for target,source in copies.items():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for name,data in [('custom-artifacts.lock.json',custom),('administration.lock.json',admin)]:
        (R/'pack'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    # Preserve existing access, public ports, secrets and load policy.
    props=(R/'server.properties').read_text('utf-8')
    props=re.sub(r'(?m)^level-seed=.*$','level-seed=-4556043908712459124',props)
    props=re.sub(r'(?m)^motd=.*$','motd=Virgos-MC 2.0 | Aventuras, magia y Create',props)
    (R/'server.properties').write_text(props,'utf-8')
    # Allow initial complex chunk generation; retain a finite watchdog.
    spigot=(R/'spigot.yml').read_text('utf-8').replace('timeout-time: 60','timeout-time: 180').replace('restart-on-crash: true','restart-on-crash: false')
    (R/'spigot.yml').write_text(spigot,'utf-8')
    discord=R/'plugins/DiscordSRV/config.yml'
    response=re.search(r'(?m)^DiscordCannedResponses:.*$',(R/'templates/discordsrv/config.yml').read_text('utf-8-sig')).group(0)
    text,count=re.subn(r'(?m)^DiscordCannedResponses:.*$',lambda m:response,discord.read_text('utf-8-sig'))
    assert count==1
    discord.write_text(text,'utf-8')
    current=read(R/'pack/current-release.json');current.update(version='2.0.0',quests=244,chapters=10,installer=6,coreSha256=sha(core),published=None,verification='.lab/v2/final.json',spawnBlueprintSha256=sha(R/'config/virgos/pueblo-v2.blocks.json.gz'),marketBlueprintSha256=sha(R/'config/virgos/mercado-v2.blocks.json.gz'),townAuditBlueprintSha256=sha(R/'config/virgos/auditoria-pueblo-v2.blocks.json.gz'))
    (R/'pack/current-release.json').write_text(json.dumps(current,indent=2)+'\n','utf-8')
    report['rollback']=str(old);report['promoted']=datetime.now(timezone.utc).isoformat()
(V/'promotion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='omittedQA'},ensure_ascii=False))
