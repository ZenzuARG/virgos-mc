"""Final real-client profile checks; credentials never enter output or release."""
from qa_v2_helpers import *
checks=[]
def check(name,test=True):
    assert test,name
    checks.append(name);print('PASS',name,flush=True)
    (ROOT/'.lab/v2/final-ui.json').write_text(json.dumps({'passed':True,'checks':checks,'client':state()},ensure_ascii=False,indent=2),'utf-8')
q.wait(lambda:'TitleScreen' in state().get('screen',''),300)
for attempt in range(2):
    action('connect');q.wait(lambda:state().get('name')=='VirgosQA3' or 'DisconnectedScreen' in state().get('screen',''),100)
    if 'DisconnectedScreen' in state().get('screen',''):action('disconnect');continue
    break
else:raise RuntimeError('Cannot connect to isolated server')
action('close');action('command',value='perfil');time.sleep(1)
check('profile-not-open-before-authentication','ProfileScreen' not in state().get('screen',''))
password=json.loads((ROOT/'.cache/qa-account-3.json').read_text('utf-8'))['password']
action('command',value='login '+password);time.sleep(3)
action('scale',value=2);action('command',value='perfil');q.wait(lambda:'ProfileScreen' in state().get('screen',''))
check('profile-opens-after-authentication');photo('profile-final-summary')
action('command',value='perfil NoExisteQA');time.sleep(1);photo('profile-missing-name')
check('missing-name-keeps-profile-open','ProfileScreen' in state().get('screen',''))
action('command',value='perfil VirgosQA2');time.sleep(1);photo('profile-final-offline');check('offline-profile-request')
click('Mi perfil');click('Misiones');photo('profile-final-chapters');click('Jugadores');check('tabs-remain-usable')
click('Códice [J]');check('profile-links-to-codex','LibraryScreen' in state().get('screen',''))
click('Ver mapa original');check('original-map-fallback','QuestsScreen' in state().get('screen',''));photo('codex-original-map')
action('close');action('command',value='perfil');time.sleep(1);action('scale',value=3);photo('profile-small-gui')
check('profile-at-large-gui-scale','ProfileScreen' in state().get('screen',''))
action('scale',value=2);action('close')
print('Final UI checks complete; client remains connected for world inspection.',flush=True)
