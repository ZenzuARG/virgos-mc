"""Publish the verified expansion; never copy world/player data from the lab."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,socket,zipfile
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=read('.runtime/active-run.json');assert state.get('finished') and not state.get('backupInProgress') and not state.get('backupError')
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',25565))!=0
accept=read('.lab/reports/v12-acceptance.json');assert accept['passed']
jar=R/'dev/virgos-core/build/libs/virgos_core-1.2.0.jar';assert sha(jar)==accept['coreSha256']
for name in ['installer-v3-unit.json','tlauncher-settings-v4.json']:assert read('.lab/reports/'+name)['passed']
backup=read('.runtime/last-backup.json');full=Path(backup['archive']);assert sha(full)==backup['sha256']
with zipfile.ZipFile(full) as z:
 manifest=json.loads(z.read('backup-manifest.json'));assert len(manifest['worldFolders'])==6
 assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
custom=read('pack/custom-artifacts.lock.json');entry=custom['artifacts'][0]
assert entry['filename']=='virgos_core-1.1.0.jar','Only the audited 1.1 baseline may be promoted'
old=R/'mods'/entry['filename'];assert sha(old)==entry['hash']
copies={}
for spec in read('.lab/v12/additions.json'):
 source=R/'.cache/pack/downloads'/spec['filename']
 assert hashlib.new(spec['hash_algorithm'],source.read_bytes()).hexdigest()==spec['hash']
 if 'server' in spec['sides']:copies[R/'mods'/source.name]=source
for spec in read('.lab/v12/administration.lock.json'):
 if spec['project']=='decentholograms':
  source=R/'.cache/pack/downloads'/spec['filename'];assert hashlib.new(spec['hash_algorithm'],source.read_bytes()).hexdigest()==spec['hash']
  copies[R/'plugins'/source.name]=source
for base,target,mirror in [(R/'.lab/v12/overrides',R,R/'pack/server-overrides'),(R/'.lab/v12/client-overrides',R/'pack/client-overrides',None)]:
 for source in base.rglob('*'):
  if not source.is_file():continue
  rel=source.relative_to(base)
  assert rel.parts[0] in ['config','kubejs','defaultconfigs','plugins','resourcepacks'] or (len(rel.parts)==3 and rel.parts[0].startswith('virgos_world') and rel.parts[1]=='serverconfig' and rel.name in ['smallships-server.toml','openpartiesandclaims-server.toml']),rel
  copies[target/rel]=source
  if mirror:copies[mirror/rel]=source
for source in (R/'pack/server-overrides/config/heracles').rglob('*'):
 if source.is_file():copies[R/'config/heracles'/source.relative_to(R/'pack/server-overrides/config/heracles')]=source
for path in (R/'config/heracles/quests').glob('*.json'):
 assert json.loads(path.read_text('utf-8'))==json.loads((R/'pack/server-overrides/config/heracles/quests'/path.name).read_text('utf-8')),path.name
assert len(list((R/'pack/server-overrides/config/heracles/quests').glob('*.json')))==186
copies[R/'mods'/jar.name]=jar
for name in ['mods.lock.json','administration.lock.json']:copies[R/'pack'/name]=R/'.lab/v12'/name
progress=R/'virgos_world/data/heracles_quest_progress.dat';before=sha(progress) if progress.exists() else None
stamp=datetime.now().strftime('%Y%m%d-%H%M%S');rollback=R/f'backups/v12-promotion-{stamp}.zip'
with zipfile.ZipFile(rollback,'w',zipfile.ZIP_DEFLATED) as z:
 for target in set(copies)|{old,R/'pack/custom-artifacts.lock.json',R/'pack/current-release.json'}:
  if target.is_file():z.write(target,target.relative_to(R).as_posix())
 z.writestr('new-files.json',json.dumps([p.relative_to(R).as_posix() for p in copies if not p.exists()],indent=2))
retired=R/'backups/retired-mods'/old.name;retired.parent.mkdir(parents=True,exist_ok=True)
if retired.exists():assert sha(retired)==sha(old)
else:shutil.copy2(old,retired)
for target,source in copies.items():
 assert target.resolve().is_relative_to(R.resolve());target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
old.unlink()
entry.update(filename=jar.name,local_source=jar.relative_to(R).as_posix(),hash=sha(jar))
(R/'pack/custom-artifacts.lock.json').write_text(json.dumps(custom,ensure_ascii=False,indent=2)+'\n','utf-8')
assert (sha(progress) if progress.exists() else None)==before
record={'version':'1.2.0','promoted':datetime.now(timezone.utc).isoformat(),'coreSha256':sha(jar),'backup':str(full),'rollback':str(rollback),
 'questProgressSha256Before':before,'questIdsPreserved':154,'worldDataCopiedFromLab':False,'servicesConstructionPending':True,
 'copiedFiles':[p.relative_to(R).as_posix() for p in copies]}
(R/'.lab/reports/v12-promotion.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
print('1.2 candidate promoted with world data preserved. Services construction and public QA remain.')
