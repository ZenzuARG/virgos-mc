"""Selective 1.0 -> 1.1 promotion after a clean stop and verified full backup.

Worlds and player progress are never copied from the lab. The reviewed spawn
blueprint is applied separately, with public admissions closed during construction.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,socket,zipfile
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=read('.runtime/active-run.json')
assert state.get('finished') and not state.get('backupInProgress') and not state.get('backupError')
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',25565))!=0
for f in ['quests-v11-static.json','quest-v11-runtime.json','installer-v4-unit.json','tlauncher-settings-v4.json']:
    assert read('.lab/reports/'+f)['passed'],f
assert all(v['passed'] for v in read('.lab/reports/pueblo-v11-walk.json'))
audit=read('.lab/server/virgos-reports/pueblo-v11-final-audit.json')
for k in ['unsupported','missing','blockedWalkChecks','wrongBlocks','routeProblems']:assert not audit[k],k
backup=read('.runtime/last-backup.json');archive=Path(backup['archive'])
assert sha(archive)==backup['sha256']
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('backup-manifest.json'))
    assert len(manifest['worldFolders'])==6
    assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
custom=read('pack/custom-artifacts.lock.json');entry=custom['artifacts'][0]
assert entry['filename']=='virgos_core-1.0.0.jar','This migration only accepts the previous audited core'
old=ROOT/'mods'/entry['filename'];assert sha(old)==entry['hash']
jar=ROOT/'dev/virgos-core/build/libs/virgos_core-1.1.0.jar';assert jar.is_file()
oldQuests=ROOT/'config/heracles/quests';newQuests=ROOT/'pack/server-overrides/config/heracles/quests'
assert {p.name for p in oldQuests.glob('*.json')}<={p.name for p in newQuests.glob('*.json')}
progress=ROOT/'virgos_world/data/heracles_quest_progress.dat';beforeProgress=sha(progress) if progress.exists() else None
stamp=datetime.now().strftime('%Y%m%d-%H%M%S');rollback=ROOT/f'backups/v11-promotion-{stamp}.zip'
with zipfile.ZipFile(rollback,'w',zipfile.ZIP_DEFLATED) as z:
    for path in [old,ROOT/'pack/custom-artifacts.lock.json',ROOT/'server.properties']+list((ROOT/'config/heracles').rglob('*')):
        if path.is_file():z.write(path,path.relative_to(ROOT).as_posix())
retired=ROOT/'backups/retired-mods'/old.name;retired.parent.mkdir(parents=True,exist_ok=True)
if retired.exists():assert sha(retired)==sha(old)
else:shutil.copy2(old,retired)
old.unlink();shutil.copy2(jar,ROOT/'mods'/jar.name)
shutil.copytree(ROOT/'pack/server-overrides/config/heracles',ROOT/'config/heracles',dirs_exist_ok=True)
blueprint='config/virgos/pueblo-v11-final.blocks.json.gz'
shutil.copy2(ROOT/'pack/server-overrides'/blueprint,ROOT/blueprint)
entry.update(filename=jar.name,local_source=jar.relative_to(ROOT).as_posix(),hash=sha(jar))
(ROOT/'pack/custom-artifacts.lock.json').write_text(json.dumps(custom,ensure_ascii=False,indent=2)+'\n','utf-8')
# Temporary construction guard. Completion explicitly runs `whitelist off`.
properties=ROOT/'server.properties';s=properties.read_text('utf-8');assert 'white-list=false' in s
properties.write_text(s.replace('white-list=false','white-list=true'),'utf-8')
assert (sha(progress) if progress.exists() else None)==beforeProgress
record={'version':'1.1.0','promoted':datetime.now(timezone.utc).isoformat(),'coreSha256':sha(jar),
        'backup':str(archive),'rollback':str(rollback),'questProgressSha256Before':beforeProgress,
        'questIdsPreserved':True,'worldDataCopiedFromLab':False,'blueprint':blueprint,'blueprintSha256':sha(ROOT/blueprint),
        'maintenanceWhitelist':True,'constructionPending':True}
(ROOT/'.lab/reports/v11-promotion.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
print(json.dumps(record))
