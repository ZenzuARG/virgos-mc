"""Archive only temporary QA data after a clean, backed-up public smoke test."""
from pathlib import Path
from datetime import datetime,timezone
import json,runpy,shutil,sqlite3,hashlib
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2'
state=json.loads((R/'.runtime/active-run.json').read_text('utf-8-sig'))
assert state['exitCode']==0 and state.get('finished') and not state.get('backupInProgress')
test=json.loads((V/'public-test.json').read_text('utf-8'));assert test['passed'] and test['accountRemoved']
qa={'13e2e728-2a7a-36a6-84ee-5c289cf4cc02','32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e','3b6e246d-95b1-37ba-83c4-359423490806'}
archive=V/'public-qa-data';assert not archive.exists();archive.mkdir()
removed=[]
def preserve(file,move=True):
    assert file.resolve().is_relative_to(R.resolve()) and not file.is_symlink()
    target=archive/file.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    (shutil.move if move else shutil.copy2)(str(file),str(target));removed.append(file.relative_to(R).as_posix())
read=runpy.run_path(str(R/'scripts/inspect-nbt.py'))['read_nbt']
for world in R.glob('virgos_world*'):
    if not world.is_dir():continue
    for file in list(world.rglob('*')):
        if file.is_file() and any(identity in file.name for identity in qa):preserve(file)
for name in ['heracles_quest_progress.dat','heracles_pinned_quests.dat']:
    file=R/'virgos_world/data'/name
    if file.exists():
        assert set(read(file)['']['data'])<=qa,'Unexpected real player progress; do not erase'
        preserve(file)
profiles=R/'virgos_world/virgos-profiles.json'
if profiles.exists():
    data=json.loads(profiles.read_text('utf-8'));preserve(profiles,False)
    data['players']={k:v for k,v in data['players'].items() if k not in qa};profiles.write_text(json.dumps(data,indent=2),'utf-8')
cache=R/'usercache.json';data=json.loads(cache.read_text('utf-8-sig'));preserve(cache,False)
cache.write_text(json.dumps([p for p in data if p.get('uuid') not in qa],indent=2),'utf-8')
with sqlite3.connect(f'file:{(R/"plugins/AuthMe/authme.db").as_posix()}?mode=ro',uri=True) as db:
    assert db.execute("SELECT COUNT(*) FROM authme WHERE LOWER(username) IN ('virgosqa1','virgosqa2','virgosqa3')").fetchone()[0]==0
assert all(not p.get('name','').lower().startswith('virgosqa') for p in json.loads((R/'ops.json').read_text('utf-8-sig')))
report={'passed':True,'completed':datetime.now(timezone.utc).isoformat(),'archived':removed,'backupBeforeCleanup':json.loads((R/'.runtime/last-backup.json').read_text('utf-8-sig'))['archive']}
(V/'public-cleanup.json').write_text(json.dumps(report,indent=2),'utf-8');print('QA cleanup complete:',len(removed),'files archived or filtered')
