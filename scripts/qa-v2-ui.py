"""Exercise the shipped v2 UI against the loopback lab with a dedicated QA identity."""
from pathlib import Path
import importlib.util,json,time,shutil,argparse
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.LAB=ROOT/'.lab/v2/server';q.PROFILES[2]='qa-v2';QA=ROOT/'client/qa-v2/virgos-qa';REPORT=ROOT/'.lab/v2/ui-test.json';checks=[]
def record(name):
    checks.append(name);REPORT.write_text(json.dumps({'checks':checks,'state':q.state(2)},ensure_ascii=False,indent=2),'utf-8');print('PASS:',name,flush=True)
def screen(part):return part in q.state(2).get('screen','')
def widgets():
    q.action(2,{'action':'inspect_screen'});return json.loads((QA/'screen.json').read_text('utf-8'))
def click(text):
    matches=[w for w in widgets() if w['text']==text and w['visible'] and w['active']]
    assert len(matches)==1,(text,matches)
    w=matches[0];q.action(2,{'action':'click','x':w['x']+w['width']/2,'y':w['y']+w['height']/2});time.sleep(1)
def photo(name):
    line=q.action(2,{'action':'screenshot'});source=ROOT/f'client/qa-v2/screenshots/virgos-qa-{line}.png';q.wait(source.exists);time.sleep(.4);shutil.copy2(source,ROOT/'.lab/v2'/f'{name}.png')
parser=argparse.ArgumentParser();parser.add_argument('--connected',action='store_true');args=parser.parse_args()
if not args.connected:
    q.wait(lambda:screen('TitleScreen'),240)
    password=json.loads((ROOT/'.cache/qa-account-2.json').read_text('utf-8'))['password']
    for attempt in range(2):
        q.action(2,{'action':'connect'})
        q.wait(lambda:q.state(2).get('name')=='VirgosQA2' or screen('DisconnectedScreen'),90)
        if screen('DisconnectedScreen'):
            q.action(2,{'action':'disconnect'});continue
        q.action(2,{'action':'close'})
        q.action(2,{'action':'command','value':'login '+password})
        time.sleep(3);break
    else:raise RuntimeError('Unable to join the local candidate')
q.action(2,{'action':'scale','value':2})
q.action(2,{'action':'command','value':'perfil'})
q.wait(lambda:screen('ProfileScreen'),15);record('authenticated-own-profile-opens');photo('profile-summary')
click('Misiones');photo('profile-chapters');record('profile-chapter-page')
click('Jugadores');photo('profile-players');record('profile-player-list')
click('Códice [J]');q.wait(lambda:screen('LibraryScreen'),15);record('profile-to-codex');photo('codex-list')
click('Para reclamar');photo('codex-rewards');record('codex-reward-filter')
click('Todas')
rows=[w for w in widgets() if w['visible'] and w['active'] and w['height']==40]
assert rows and rows[0]['text'];record('quest-titles-readable-and-narratable')
w=rows[0];q.action(2,{'action':'click','x':w['x']+30,'y':w['y']+20})
q.wait(lambda:'screens.quest.' in q.state(2).get('screen',''),15);record('quest-details-open');photo('codex-details')
print('UI baseline complete; player remains in local QA for visual review.',flush=True)
