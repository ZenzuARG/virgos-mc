"""Real Forge smoke test through the owned public domain; remove its QA account."""
from qa_v2_helpers import *
from datetime import datetime,timezone
import math,sqlite3
report={'version':'2.0.0','passed':False,'started':datetime.now(timezone.utc).isoformat(),'checks':[]};out=ROOT/'.lab/v2/public-test.json'
def record(name,**data):
    report['checks'].append({'name':name,**data});out.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print('PASS',name,flush=True)
def public(command):
    with (ROOT/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write(command+'\n')
def log():return (ROOT/'logs/latest.log').read_text('utf-8',errors='replace')
def status():
    offset=len(log());public('virgos status')
    result=q.wait(lambda:log()[offset:] if 'AuthMe=' in log()[offset:] else None)
    return next(line for line in result.splitlines() if 'AuthMe=' in line)
def registrations():
    with sqlite3.connect(f'file:{(ROOT/"plugins/AuthMe/authme.db").as_posix()}?mode=ro',uri=True) as db:
        return db.execute("SELECT COUNT(*) FROM authme WHERE LOWER(username)='virgosqa3'").fetchone()[0]
assert registrations()==0,'Do not overwrite an existing account'
assert (QA/'endpoint.txt').read_text().strip()=='virgos-mc.playit.plus'
q.wait(lambda:'TitleScreen' in state().get('screen',''),360)
ready=status();assert all(v in ready for v in ['AuthMe=true','progreso=true','arena=true','vozAuth=true','pueblo=true','respaldoAuto=true'])
record('production-services',status=ready)
password=json.loads((ROOT/'.cache/qa-account-3.json').read_text('utf-8'))['password']
try:
    for _ in range(2):
        action('connect');q.wait(lambda:state().get('name')=='VirgosQA3' or 'DisconnectedScreen' in state().get('screen',''),120)
        if 'DisconnectedScreen' not in state().get('screen',''):break
        action('disconnect')
    else:raise RuntimeError('Public connection failed')
    action('close');before=state();action('hold',name='key.forward',ticks=60);time.sleep(4);after=state()
    distance=math.hypot(after['x']-before['x'],after['z']-before['z']);assert distance<.2
    record('pre-authentication-movement-blocked',displacement=distance)
    action('command',value='perfil');time.sleep(.7);assert 'ProfileScreen' not in state().get('screen','')
    record('profile-requires-authentication')
    offset=len(log());action('command',value='register '+password+' '+password)
    q.wait(lambda:'VirgosQA3 logged in' in log()[offset:],45);assert registrations()==1
    record('public-domain-forge-authentication')
    q.wait(lambda:'vozConectados=1' in status(),60);record('public-voice-connected')
    action('scale',value=2);action('command',value='perfil');q.wait(lambda:'ProfileScreen' in state().get('screen',''))
    photo('public-profile');click('Misiones');photo('public-chapters');click('Códice [J]')
    assert 'LibraryScreen' in state().get('screen','');photo('public-codex');record('public-profile-and-codex')
    action('close');recipes=QA/'recipes-audit.json';old=recipes.stat().st_mtime if recipes.exists() else 0
    action('audit_recipes');q.wait(lambda:recipes.exists() and recipes.stat().st_mtime>old);time.sleep(.5)
    client=json.loads(recipes.read_text('utf-8'));server=json.loads((ROOT/'virgos-reports/registries.json').read_text('utf-8'))
    missing=set(server['recipes'])-set(client['recipes']);extra=set(client['recipes'])-set(server['recipes'])
    assert client['jeiSynced'] and not client['jeiFallback'] and not missing and not extra
    record('all-recipes-synced',recipes=len(client['recipes']))
    public('virgos audit auditoria-pueblo-v2');public('forge tps')
    action('disconnect');q.wait(lambda:'vozConectados=0' in status(),30)
    # logout writes the current world profile, without copying any lab progress.
    profiles=ROOT/'virgos_world/virgos-profiles.json'
    q.wait(lambda:profiles.exists() and '3b6e246d-95b1-37ba-83c4-359423490806' in json.loads(profiles.read_text('utf-8')).get('players',{}),75)
    profile=json.loads(profiles.read_text('utf-8'))['players']['3b6e246d-95b1-37ba-83c4-359423490806']
    assert profile['level']==0 and profile['quests']==0 and profile['questTotal']==244
    record('new-world-personal-progress-reset',level=profile['level'],quests=profile['quests'],total=profile['questTotal'])
    report['passed']=True
finally:
    if registrations():public('authme unregister VirgosQA3');q.wait(lambda:registrations()==0,30)
    if state().get('name')=='VirgosQA3':action('disconnect')
    report['accountRemoved']=registrations()==0;report['finished']=datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print('Public smoke test passed; QA account removed.',flush=True)
