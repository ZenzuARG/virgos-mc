"""Walk the four gates with the localhost-only Forge QA driver."""
from pathlib import Path
import json
import time

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'client/standard/virgos-qa'
REPORT=ROOT/'.lab/reports/qa-spawn-gates.json'

def state():
    try:return json.loads((QA/'status.json').read_text('utf-8'))
    except (OSError,json.JSONDecodeError):return {}

def server(command):
    with (ROOT/'.lab/server/console-commands.txt').open('a',encoding='utf-8') as stream:stream.write(command+'\n')

def client(command):
    path=QA/'commands.jsonl'
    with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(command)+'\n')
    return len(path.read_text('utf-8').splitlines())

def wait_for(predicate, timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=state()
        if predicate(value):return value
        time.sleep(.2)
    raise RuntimeError('QA condition timed out: '+json.dumps(state()))

def main():
    marker=ROOT/'.lab/server/virgos_world/virgos-build-bastion-repair-v4-state.json'
    if not json.loads(marker.read_text('utf-8'))['complete']:raise SystemExit('Wait for construction to finish.')
    if state().get('name')!='VirgosQA2':raise SystemExit('This test requires VirgosQA2 in the lab.')
    client({'action':'close'})
    server('time set 6000');server('weather clear');server('gamemode survival VirgosQA2')
    cases=[('norte',672.5,674.5,180,lambda s:s['z']<656),
           ('sur',672.5,798.5,0,lambda s:s['z']>816),
           ('oeste',610.5,736.5,90,lambda s:s['x']<592),
           ('este',734.5,736.5,-90,lambda s:s['x']>752)]
    report=[]
    for name,x,z,yaw,passed in cases:
        server(f'tp VirgosQA2 {x} 115 {z} {yaw} 0')
        initial=wait_for(lambda s:abs(s.get('x',0)-x)<.1 and abs(s.get('z',0)-z)<.1 and abs(s.get('y',0)-115)<.1)
        line=client({'action':'hold','name':'key.forward','ticks':110})
        wait_for(lambda s:s.get('line',0)>=line)
        time.sleep(6)
        final=state()
        screenshot=client({'action':'screenshot'})
        result={'gate':name,'start':initial,'end':final,'passed':passed(final) and final['health']==20,'screenshot':f'virgos-qa-{screenshot}.png'}
        report.append(result);REPORT.write_text(json.dumps(report,indent=2),'utf-8')
        print(name, 'PASS' if result['passed'] else 'FAIL', flush=True)
        if not result['passed']:raise SystemExit('Gate traversal failed; inspect report.')
    print('All four gates crossed on foot without damage.',flush=True)

if __name__=='__main__':main()
