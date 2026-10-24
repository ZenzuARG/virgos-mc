"""Apply only the reviewed spawn blueprint, audit it, then reopen admissions."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    try:return json.loads((ROOT/path).read_text('utf-8-sig'))
    except (OSError,json.JSONDecodeError):return {}
def wait(test,seconds):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        result=test()
        if result:return result
        time.sleep(1)
    raise RuntimeError('Condition timed out; keep maintenance admissions closed and inspect the log.')
def log():return (ROOT/'.runtime/public-console.log').read_text('utf-8',errors='replace')
def command(value):
    with (ROOT/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write(value+'\n')
record=read('.lab/reports/v11-promotion.json')
assert record['version']=='1.1.0' and record['constructionPending']
assert hashlib.sha256((ROOT/record['blueprint']).read_bytes()).hexdigest()==record['blueprintSha256']
wait(lambda:not read('.runtime/active-run.json').get('finished') and 'Virgos: AuthMe bridge ready' in log(),420)
assert 'white-list=true' in (ROOT/'server.properties').read_text('utf-8')
offset=len(log());command('list')
wait(lambda:'There are 0 of a max of 10 players online:' in log()[offset:],20)
command('virgos build pueblo-v11-final');print('Production construction started; admissions closed.',flush=True)
marker='virgos_world/virgos-build-pueblo-v11-final-state.json'
wait(lambda:read(marker).get('complete'),900)
assert read(marker)['blueprintSha256']==record['blueprintSha256']
auditPath=ROOT/'virgos-reports/pueblo-v11-final-audit.json'
started=time.time();command('virgos audit pueblo-v11-final')
wait(lambda:auditPath.exists() and auditPath.stat().st_mtime>=started,60)
audit=read('virgos-reports/pueblo-v11-final-audit.json')
for key in ['unsupported','missing','blockedWalkChecks','routeProblems']:assert not audit[key],(key,audit[key])
assert all('expected=minecraft:air actual=Block{minecraft:vine}' in v for v in audit['wrongBlocks']),audit['wrongBlocks']
offset=len(log());command('whitelist off')
wait(lambda:any('Whitelist' in line and 'off' in line for line in log()[offset:].splitlines()),20)
# Ketting changes the runtime allowlist but does not persist this command here.
properties=ROOT/'server.properties';text=properties.read_text('utf-8')
properties.write_text(text.replace('white-list=true','white-list=false'),'utf-8')
command('save-all flush')
record.update(maintenanceWhitelist=False,constructionPending=False,constructionFinished=datetime.now(timezone.utc).isoformat(),
              auditedBlocks=audit['checked'],growingVines=len(audit['wrongBlocks']))
(ROOT/'.lab/reports/v11-promotion.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
print('Production town audited; admissions reopened without whitelist.',flush=True)
