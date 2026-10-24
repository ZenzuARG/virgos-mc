"""Record release completion only after its full backup and managed restart."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text('utf-8-sig'))
def wait(test,seconds=480):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            value=test()
            if value:return value
        except (OSError,json.JSONDecodeError):pass
        time.sleep(2)
    raise RuntimeError('Final restart did not become ready; inspect the server log.')
promotion=read('.lab/reports/v11-promotion.json')
assert not promotion['constructionPending'] and not promotion['maintenanceWhitelist']
wait(lambda:not read('.runtime/active-run.json').get('finished') and
     read('.runtime/last-backup.json')['archive']!=promotion['backup'] and
     'Virgos: AuthMe bridge ready' in (ROOT/'.runtime/public-console.log').read_text('utf-8',errors='replace'))
checks={}
for address in ['127.0.0.1','virgos-mc.playit.plus']:
    completed=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/comprobar.ps1'),'-Address',address],cwd=ROOT,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert completed.returncode==0,completed.stdout
    checks[address]=json.loads(completed.stdout);assert checks[address]['result']=='OK'
assert 'white-list=false' in (ROOT/'server.properties').read_text('utf-8')
assert 'online-mode=false' in (ROOT/'server.properties').read_text('utf-8')
checks['whitelistOffAfterRestart']=True
backup=read('.runtime/last-backup.json');assert Path(backup['archive']).is_file()
assert hashlib.sha256(Path(backup['archive']).read_bytes()).hexdigest()==backup['sha256']
evidence=['public-v11.json','quests-v11-static.json','quest-v11-runtime.json','v11-progress-preserved.json',
          'installer-v4-unit.json','tlauncher-settings-v4.json','installer-v4-integration.json']
for name in evidence:assert read('.lab/reports/'+name)['passed'],name
assert all(c['passed'] for c in read('.lab/reports/public-v11.json')['cases'])
assert all(c['passed'] for c in read('.lab/reports/pueblo-v11-walk.json'))
audit=read('virgos-reports/pueblo-v11-final-audit.json')
assert all(not audit[k] for k in ['unsupported','missing','blockedWalkChecks','routeProblems'])
assert all('expected=minecraft:air actual=Block{minecraft:vine}' in v for v in audit['wrongBlocks'])
record={'version':'1.1.0','passed':True,'completed':datetime.now(timezone.utc).isoformat(),
        'serverRunning':read('.runtime/active-run.json'),'checks':checks,'backupAfterPublication':backup,
        'promotion':promotion,'questCount':154,'newQuests':71,'chapters':20,'spawnAudit':audit,
        'clientRelease':read('dist/release.json'),'evidence':evidence,
        'limits':['TLauncher preferences and installer tested; native TLauncher UI not installed or launched.',
                  'Voice connection verified; no human microphone listening test.',
                  'No eight-player factory load test or new combat-difficulty tuning.']}
(ROOT/'.lab/reports/v11-final.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
(ROOT/'pack/current-release.json').write_text(json.dumps({'version':'1.1.0','published':record['completed'],
    'minecraft':'1.20.1','forge':'47.4.22','ketting':'0.6.1','quests':154,'chapters':20,
    'installer':4,'coreSha256':promotion['coreSha256'],'spawnBlueprintSha256':promotion['blueprintSha256'],
    'verification':'.lab/reports/v11-final.json'},indent=2)+'\n','utf-8')
p=ROOT/'pack/pueblo-v11.json';v=json.loads(p.read_text('utf-8'));v['status']='PUBLISHED_VERIFIED';v['verification']='.lab/reports/v11-final.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Virgos-MC 1.1 closed: public server running, no whitelist, full backup verified.',flush=True)
