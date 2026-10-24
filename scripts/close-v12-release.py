"""Close 1.2 only after public checks, final construction and a verified restart."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
promotion=read('.lab/reports/v12-promotion.json')
assert not promotion['servicesConstructionPending'] and promotion['serviceTextUtf8Verified']
state=read('.runtime/active-run.json');assert not state.get('finished')
backup=read('.runtime/last-backup.json');assert backup['archive']!=promotion['backup']
assert datetime.fromisoformat(backup['completed'].replace('Z','+00:00')) > datetime.fromisoformat(read('.lab/reports/v12-service-text.json')['verifiedAt'])
assert datetime.fromisoformat(state['started'].replace('Z','+00:00')) > datetime.fromisoformat(backup['completed'].replace('Z','+00:00'))
assert sha(backup['archive'])==backup['sha256']
evidence=['v12-acceptance.json','public-v12.json','installer-v3-unit.json','tlauncher-settings-v4.json','v12-service-text.json']
for name in evidence:assert read('.lab/reports/'+name)['passed'],name
audit=read('virgos-reports/mercado-v12-audit.json')
assert audit['checked']==9584 and all(not audit[k] for k in ['unsupported','missing','wrongBlocks','blockedWalkChecks','routeProblems'])
assert read('virgos_world/virgos-build-mercado-v12-state.json')['complete']
assert not (R/'virgos_world/virgos-market.json').exists() or read('virgos_world/virgos-market.json')=={},'Public stalls must remain unreserved'
checks={}
for address in ['127.0.0.1','virgos-mc.playit.plus']:
 result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(R/'scripts/comprobar.ps1'),'-Address',address],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert result.returncode==0,result.stdout
 checks[address]=json.loads(result.stdout);assert checks[address]['result']=='OK'
props=(R/'server.properties').read_text();assert 'white-list=false' in props and 'online-mode=false' in props
release=read('dist/release.json');assert release['version']=='1.2.0' and release['required']==98
for item in release['files']:assert sha(R/'dist'/item['name'])==item['sha256']
record={'version':'1.2.0','passed':True,'completed':datetime.now(timezone.utc).isoformat(),'serverRunning':state,
 'checks':checks,'backupAfterPublication':backup,'promotion':promotion,'marketAudit':audit,'clientRelease':release,
 'evidence':evidence,'quests':186,'chapters':26,'discord':'Pending user login; DiscordSRV not installed or activated',
 'limits':['Voice UDP connection tested, not human microphone audio.','No eight-player load test or combat balance playtest.',
 'TLauncher settings tested with fixtures; native launcher not launched.','Existing baseline mod/loader warnings remain; targeted 1.2 errors corrected.']}
(R/'.lab/reports/v12-final.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
current=read('pack/current-release.json')
current.update(version='1.2.0',published=record['completed'],quests=186,chapters=26,installer=4,coreSha256=promotion['coreSha256'],
 marketBlueprintSha256=sha(R/'config/virgos/mercado-v12.blocks.json.gz'),verification='.lab/reports/v12-final.json')
(R/'pack/current-release.json').write_text(json.dumps(current,indent=2)+'\n','utf-8')
print('1.2 verified and published. Public server running; Discord integration pending login.')
