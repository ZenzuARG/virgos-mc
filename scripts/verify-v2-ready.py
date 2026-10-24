"""Verify the clean snapshot and the final public restart before publication."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,subprocess,time,zipfile
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2'
def read(p):return json.loads(p.read_text('utf-8-sig'))
backup=R/'backups/full/virgos-20261019-002554-v2-ready.zip'
with zipfile.ZipFile(backup) as z:
    manifest=json.loads(z.read('backup-manifest.json'));assert len(manifest['worldFolders'])==6
    assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
    assert not any(len(parts:=Path(f['path']).parts)>2 and parts[0] in manifest['worldFolders'] and parts[1] in {'playerdata','stats','advancements'} for f in manifest['files'])
    assert not json.loads(z.read('virgos_world/virgos-profiles.json'))['players']
record={'archive':str(backup),'sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'completed':datetime.now(timezone.utc).isoformat(),'verifiedFiles':len(manifest['files']),'worldFolders':manifest['worldFolders']}
(V/'clean-backup.json').write_text(json.dumps(record,indent=2),'utf-8')
(R/'.runtime/last-backup.json').write_text(json.dumps(record,indent=2),'utf-8')
print('Clean v2 backup verified:',record['verifiedFiles'],'files',flush=True)
until=time.monotonic()+360
while time.monotonic()<until:
    state=read(R/'.runtime/active-run.json');log=(R/'.runtime/public-console.log').read_text('utf-8',errors='replace')
    if not state.get('finished') and 'Dedicated server took' in log:break
    time.sleep(2)
else:raise TimeoutError('Final public restart did not become ready')
status=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(R/'scripts/comprobar.ps1'),'-Address','virgos-mc.playit.plus'],capture_output=True,text=True,check=True)
ping=json.loads(status.stdout);assert ping['result']=='OK' and 'Virgos-MC 2.0' in ping['description']['text']
with (R/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write('virgos status\nvirgos audit auditoria-pueblo-v2\n')
time.sleep(5)
audit=read(R/'virgos-reports/auditoria-pueblo-v2-audit.json');assert not any(audit[k] for k in ['unsupported','missing','wrongBlocks','blockedWalkChecks','routeProblems'])
with sqlite3.connect(f'file:{(R/"plugins/AuthMe/authme.db").as_posix()}?mode=ro',uri=True) as db:
    assert db.execute("SELECT COUNT(*) FROM authme WHERE LOWER(username) IN ('virgosqa1','virgosqa2','virgosqa3')").fetchone()[0]==0
assert not list((R/'virgos_world/playerdata').glob('*.dat'))
assert not read(R/'virgos_world/virgos-profiles.json')['players']
for name in ['acceptance.json','public-test.json','user-client-upgrade.json','public-cleanup.json']:assert read(V/name)['passed']
assert not read(V/'production-audit.json')['failed']
report={'version':'2.0.0','readyForPlayers':True,'verified':datetime.now(timezone.utc).isoformat(),'publicStatus':ping,'serverPid':state['pid'],'backup':record,'clientMemoryMb':6144,'serverMemoryGb':8,'counts':read(V/'production-audit.json')['counts'],'publicTests':'public-test.json','release':read(R/'dist/release.json'),'discord':'pending','limits':['Human microphone listening not tested','Eight-player factory load not tested','New boss combat difficulty still needs group feedback']}
(V/'final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print('Public v2 ready; clean snapshot and reset verified.',flush=True)
