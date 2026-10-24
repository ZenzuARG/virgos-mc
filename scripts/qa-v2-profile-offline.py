"""Verify persisted profiles and separate quest progress with a second real identity."""
from qa_v2_helpers import *
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--connected',action='store_true');args=parser.parse_args()
if not args.connected:
    q.wait(lambda:'TitleScreen' in state().get('screen',''),240)
    q.wait(lambda:'Dedicated server took' in q.log(),300)
    action('connect');q.wait(lambda:state().get('name')=='VirgosQA3',100)
secret=json.loads((ROOT/'.cache/qa-account-3.json').read_text('utf-8'))['password']
action('close');action('command',value='register '+secret+' '+secret);time.sleep(3)
action('command',value='login '+secret);time.sleep(2)
action('scale',value=2);action('command',value='perfil virgosqa2');q.wait(lambda:'ProfileScreen' in state().get('screen',''),15)
photo('profile-offline-friend')
click('Mi perfil');photo('profile-separate-player')
click('Códice [J]');q.wait(lambda:'LibraryScreen' in state().get('screen',''),15)
photo('codex-final-list')
rows=[w for w in widgets() if w['visible'] and w['height']==40];assert rows
w=rows[0];action('click',x=w['x']+25,y=w['y']+20);time.sleep(1);photo('codex-final-details')
click('Objetivos');photo('codex-final-objectives')
report={'identity':'VirgosQA3','friend':'VirgosQA2','screenshots':['profile-offline-friend.png','profile-separate-player.png','codex-final-list.png','codex-final-details.png','codex-final-objectives.png'],'state':state()}
(ROOT/'.lab/v2/profile-offline-test.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print('Second identity queried persisted friend profile and opened its own separate profile/quests.',flush=True)
