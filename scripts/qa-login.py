"""Reconnect the local test identity and authenticate as soon as Forge joins."""
from pathlib import Path
import argparse
import json
import time
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--account',choices=['1','2','3'],default='2')
parser.add_argument('--connect',action='store_true')
parser.add_argument('--instance',choices=['standard','secondary','tertiary'],default='standard')
parser.add_argument('--public',action='store_true')
parser.add_argument('--register',action='store_true')
parser.add_argument('--delay',type=int,default=0,help='Seconds to observe an unauthenticated player, at most 40')
args=parser.parse_args()
folder=ROOT/('client/standard/virgos-qa' if args.instance=='standard' else 'client/qa-'+args.instance+'/virgos-qa')
credentials=json.loads((ROOT/('.cache/qa-account.json' if args.account=='1' else '.cache/qa-account-'+args.account+'.json')).read_text('utf-8'))
def send(action):
    with (folder/'commands.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(action)+'\n')
if args.connect:
    deadline=time.monotonic()+480
    while time.monotonic()<deadline:
        try:ready=json.loads((folder/'status.json').read_text('utf-8'))
        except (OSError,json.JSONDecodeError):ready={}
        if ready.get('screen','').endswith('TitleScreen'):break
        time.sleep(.5)
    else:raise SystemExit('QA client did not reach the title screen')
    deadline=time.monotonic()+420
    while time.monotonic()<deadline:
        log_path=ROOT/('logs/latest.log' if args.public else '.lab/server/console.log')
        log=log_path.read_text('utf-8',errors='replace')
        current_run=True
        if args.public:
            run=json.loads((ROOT/'.runtime/active-run.json').read_text('utf-8'))
            current_run=not run.get('finished') and log_path.stat().st_mtime>=datetime.fromisoformat(run['started'].replace('Z','+00:00')).timestamp()
        if current_run and 'Virgos: AuthMe bridge ready' in log:
            time.sleep(2)
            break
        time.sleep(.5)
    else:raise SystemExit('Lab did not become ready')
    send({'action':'close'});send({'action':'connect'})
deadline=time.monotonic()+90
while time.monotonic()<deadline:
    try:state=json.loads((folder/'status.json').read_text('utf-8'))
    except (OSError,json.JSONDecodeError):time.sleep(.2);continue
    if state.get('name')==credentials['name']:
        if not 0<=args.delay<=40:raise SystemExit('Delay must be between 0 and 40 seconds')
        samples=[]
        for _ in range(args.delay):
            try:samples.append(json.loads((folder/'status.json').read_text('utf-8')))
            except (OSError,json.JSONDecodeError):pass
            time.sleep(1)
        if samples:
            (ROOT/'.lab/reports/qa-unauthenticated-position.json').write_text(json.dumps(samples,indent=2),'utf-8')
        value=('register '+credentials['password']+' '+credentials['password']) if args.register else 'login '+credentials['password']
        send({'action':'command','value':value})
        print('Local QA login queued for',credentials['name']);break
    time.sleep(.2)
else:raise SystemExit('QA client did not join in time')
