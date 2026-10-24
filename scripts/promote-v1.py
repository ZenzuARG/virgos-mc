"""One-time, selective 0.2 -> 1.0 promotion. Never copies or replaces world data."""
from pathlib import Path
from datetime import datetime, timezone
import ctypes, hashlib, json, shutil, socket, zipfile
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=read('.runtime/active-run.json')
assert state.get('finished') and not state.get('backupInProgress'),'Stop production and finish its backup first'
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',25565))!=0,'Production port occupied'
reports=['startup-validation-v03.json','qa-v03.json','qa-lootr-v03.json','installer-v3-unit.json',
         'restore-runtime-verification.json','recipe-sync-v1.json','v1-class-equivalence.json','installer-v1-repair.json']
for name in reports:
    report=read('.lab/reports/'+name)
    assert report.get('passed',True) and all(c['passed'] for c in report.get('cases',[])),name
backup=read('.runtime/last-backup.json');archive=Path(backup['archive'])
assert archive.is_file() and sha(archive)==backup['sha256'],'Full backup hash mismatch'
worlds={p.name for p in ROOT.glob('virgos_world*') if p.is_dir()}
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('backup-manifest.json'))
    assert worlds<=set(manifest['worldFolders'])
    assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
custom=read('pack/custom-artifacts.lock.json');entry=custom['artifacts'][0]
assert entry['filename']=='virgos_core-0.2.0.jar','This promotion is only for the audited 0.2 release'
jar=ROOT/'dev/virgos-core/build/libs/virgos_core-1.0.0.jar'
assert sha(jar)==read('.lab/reports/v1-class-equivalence.json')['releaseSha256']
old=ROOT/'mods'/entry['filename'];assert sha(old)==entry['hash']
template=ROOT/'pack/server-overrides'
quests=template/'config/heracles/quests'
assert {f.name for f in quests.glob('*.json')}=={f.name for f in (ROOT/'config/heracles/quests').glob('*.json')},'Quest IDs changed'
changes=[p for p in (template/'config/heracles').rglob('*') if p.is_file()]
changes += [template/'config/virgos/maintenance.json',template/'config/modernfix-mixins.properties']
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
rollback=ROOT/f'backups/v1-promotion-{stamp}.zip'
with zipfile.ZipFile(rollback,'w',zipfile.ZIP_DEFLATED) as z:
    for path in [old,ROOT/'pack/custom-artifacts.lock.json']+[ROOT/p.relative_to(template) for p in changes]:
        if path.exists():z.write(path,path.relative_to(ROOT).as_posix())
reserve=ROOT/'backups/retired-mods'/old.name;reserve.parent.mkdir(parents=True,exist_ok=True)
if reserve.exists():assert sha(reserve)==sha(old)
else:shutil.copy2(old,reserve)
old.unlink()
shutil.copy2(jar,ROOT/'mods'/jar.name)
for source in changes:
    dest=ROOT/source.relative_to(template);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
entry.update(filename=jar.name,local_source=jar.relative_to(ROOT).as_posix(),hash=sha(jar))
lock=ROOT/'pack/custom-artifacts.lock.json';tmp=lock.with_suffix('.json.tmp')
tmp.write_text(json.dumps(custom,ensure_ascii=False,indent=2)+'\n','utf-8');tmp.replace(lock)
report={'version':'1.0.0','promoted':datetime.now(timezone.utc).isoformat(),'passed':True,
        'coreSha256':sha(jar),'backup':str(archive),'rollback':str(rollback),
        'files':[str(p.relative_to(template)).replace('\\','/') for p in changes],
        'worldDataReplaced':False,'questIdsPreserved':True,'preflightReports':reports}
(ROOT/'.lab/reports/v1-promotion.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
print(json.dumps({'version':'1.0.0','configurationFiles':len(changes),'rollback':str(rollback),'worldDataReplaced':False}))
