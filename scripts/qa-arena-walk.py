"""Walk the arena approach in both directions with a normal survival client."""
from pathlib import Path
import json
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
h=runpy.run_path(str(ROOT/'scripts/qa-spawn.py'))
state,server,client,wait_for=(h[k] for k in ['state','server','client','wait_for'])
report=[]

def walk(label,z,y,yaw,passed):
    client({'action':'close'})
    server('gamemode survival VirgosQA2')
    server(f'tp VirgosQA2 672.5 {y} {z} {yaw} 8')
    initial=wait_for(lambda s:abs(s.get('z',0)-z)<.1 and abs(s.get('y',0)-y)<.1)
    samples=[]
    for ticks in [200,200,150]:
        line=client({'action':'hold','name':'key.forward','ticks':ticks})
        wait_for(lambda s:s.get('line',0)>=line)
        time.sleep(ticks/20+1)
        samples.append(state())
        print(label,round(samples[-1].get('z',0),2),samples[-1].get('health'),flush=True)
        if passed(samples[-1]):break
    result={'route':label,'initial':initial,'samples':samples,'passed':passed(samples[-1]) and all(s.get('health')==20 for s in samples)}
    report.append(result)
    (ROOT/'.lab/reports/qa-arena-walk.json').write_text(json.dumps(report,indent=2),'utf-8')
    if not result['passed']:raise RuntimeError('Arena road traversal failed')

if __name__=='__main__':
    if state().get('name')!='VirgosQA2':raise RuntimeError('Requires QA2')
    walk('descenso-al-anfiteatro',917.5,119,0,lambda s:s.get('z',0)>1020)
    walk('regreso-al-bastion',1020.5,79,180,lambda s:s.get('z',2000)<917)
    server('tp VirgosQA2 672.5 115 752.5 180 0')
    print('PASS: both road directions walked without jumping or damage.',flush=True)
