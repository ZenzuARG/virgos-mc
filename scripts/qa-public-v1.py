"""Public Forge/voice/auth smoke test using only the owned VirgosQA2 identity."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util,json,math,sqlite3,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
report={'version':'1.0.0','started':datetime.now(timezone.utc).isoformat(),'cases':[],
        'scope':'Real Forge client through public Minecraft domain and public voice UDP. No microphone listening or eight-player load test.'}
out=ROOT/'.lab/reports/public-v1.json'
def record(name,passed,**details):
    report['cases'].append({'case':name,'passed':bool(passed),**details})
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(name,'PASS' if passed else 'FAIL',flush=True)
    if not passed:raise RuntimeError(name)
def log():return (ROOT/'logs/latest.log').read_text('utf-8',errors='replace')
def server(command):
    with (ROOT/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write(command+'\n')
def state():return json.loads((ROOT/'.runtime/active-run.json').read_text('utf-8-sig'))
def status():
    offset=len(log());server('virgos status')
    result=q.wait(lambda:log()[offset:] if 'AuthMe=' in log()[offset:] else None)
    return next(line for line in result.splitlines() if 'AuthMe=' in line)
def registrations():
    with sqlite3.connect(f'file:{(ROOT/"plugins/AuthMe/authme.db").as_posix()}?mode=ro',uri=True) as db:
        return db.execute("SELECT COUNT(*) FROM authme WHERE LOWER(username)='virgosqa2'").fetchone()[0]
assert registrations()==0,'QA2 must be unregistered before this test'
assert (ROOT/'client/standard/virgos-qa/endpoint.txt').read_text().strip()=='virgos-mc.playit.plus'
credentials=json.loads((ROOT/'.cache/qa-account-2.json').read_text('utf-8'))
assert credentials['name']=='VirgosQA2'
q.wait(lambda:not state().get('finished') and 'Virgos: AuthMe bridge ready' in (ROOT/'.runtime/public-console.log').read_text('utf-8',errors='replace'),timeout=420)
record('core-services-ready',all(word in status() for word in ['AuthMe=true','progreso=true','arena=true','vozAuth=true','pueblo=true','respaldoAuto=true']))
q.action(2,{'action':'close'});q.action(2,{'action':'connect'})
q.wait(lambda:q.state(2).get('name')=='VirgosQA2',timeout=120)
time.sleep(2);before=q.state(2)
q.action(2,{'action':'hold','name':'key.forward','ticks':80});time.sleep(5);after=q.state(2)
record('pre-auth-movement-blocked',math.hypot(after['x']-before['x'],after['z']-before['z'])<.2,
       displacement=math.hypot(after['x']-before['x'],after['z']-before['z']))
offset=len(log());registration_start=time.monotonic()
q.action(2,{'action':'command','value':'register '+credentials['password']+' '+credentials['password']})
q.wait(lambda:'VirgosQA2 logged in' in log()[offset:],timeout=45)
record('public-offline-account-authenticated',registrations()==1,automaticLoginMs=round((time.monotonic()-registration_start)*1000))
q.wait(lambda:'vozConectados=1' in status(),timeout=45)
record('public-voice-connected',True,coreStatus=status())
pid=state()['pid'];offset=len(log());server('virgos checkpoint')
q.wait(lambda:'El respaldo completo espera' in log()[offset:])
record('checkpoint-refuses-connected-players',state()['pid']==pid and not (ROOT/'.runtime/checkpoint-request.json').exists())
completed=subprocess.run([sys.executable,str(ROOT/'scripts/qa-recipes.py'),'--public'],cwd=ROOT,capture_output=True,text=True)
record('public-recipe-sync',completed.returncode==0,report='recipe-sync-v1-public.json')
offset=len(log());server('forge tps');time.sleep(2)
report['tpsSample']=log()[offset:][-5000:]
server('authme unregister VirgosQA2')
q.wait(lambda:registrations()==0)
q.action(2,{'action':'disconnect'})
q.wait(lambda:'vozConectados=0' in status())
record('test-account-unregistered',True)
report['finished']=datetime.now(timezone.utc).isoformat();report['passed']=True
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Public v1 smoke test passed; QA2 disconnected and registration removed.',flush=True)
