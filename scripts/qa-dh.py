"""Drive only the owned DH lab/client, without displaying QA credentials."""
from pathlib import Path
import json,time,sqlite3,sys
ROOT=Path(__file__).resolve().parents[1];LAB=ROOT/'.lab/dh/server';QA=ROOT/'client/qa-dh/virgos-qa'
def state():
    try:return json.loads((QA/'status.json').read_text())
    except (OSError,ValueError):return {}
def wait(predicate,timeout=60):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.5)
    raise TimeoutError('QA condition timed out: '+str(state()))
def action(kind,**kwargs):
    with (QA/'commands.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'action':kind,**kwargs})+'\n')
    line=len((QA/'commands.jsonl').read_text().splitlines());wait(lambda:state().get('line',0)>=line)
    return line
def server(command):
    with (LAB/'console-commands.txt').open('a',encoding='utf-8') as f:f.write(command+'\n')
def log():return (LAB/'logs/latest.log').read_text('utf-8',errors='replace')
def connect():
    wait(lambda:'TitleScreen' in state().get('screen',''),360);wait(lambda:'Done (' in log(),360)
    action('connect');wait(lambda:state().get('name')=='VirgosQA3' or 'DisconnectedScreen' in state().get('screen',''),120)
    assert state().get('name')=='VirgosQA3',state()
    action('close');print('Connected without changing account permissions',flush=True)
def auth():
    password=json.loads((ROOT/'.cache/qa-account-3.json').read_text())['password']
    with sqlite3.connect(f'file:{(LAB/"plugins/AuthMe/authme.db").as_posix()}?mode=ro',uri=True) as db:
        registered=db.execute("SELECT COUNT(*) FROM authme WHERE LOWER(username)='virgosqa3'").fetchone()[0]
    offset=len(log());action('command',value=('login '+password if registered else 'register '+password+' '+password))
    wait(lambda:'VirgosQA3 logged in' in log()[offset:],40);print('Authenticated',flush=True)
if __name__=='__main__':
    task=sys.argv[1]
    if task=='connect':connect()
    elif task=='auth':auth()
    elif task=='server':server(' '.join(sys.argv[2:]))
    elif task=='state':print(json.dumps(state(),ensure_ascii=False))
    elif task=='photo':print(action('screenshot'))
    elif task=='audit':action('audit_dh');print((QA/'dh-audit.json').read_text())
    else:action(task)
