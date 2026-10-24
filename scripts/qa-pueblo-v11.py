from pathlib import Path
import json,runpy,time
ROOT=Path(__file__).resolve().parents[1]
q=runpy.run_path(str(ROOT/'scripts/qa-expeditions.py'))
assert q['state'](2).get('name')=='VirgosQA2'
q['action'](2,{'action':'close'});q['server']('gamemode survival VirgosQA2')
cases=[('oeste',629.5,737.5,90,'x',607.5),('norte',682.5,691.5,180,'z',669.5),
       ('este',721.5,757.5,-90,'x',743.5),('sur',660.5,781.5,0,'z',803.5)]
results=[]
for name,x,z,yaw,axis,end in cases:
    q['server'](f'tp VirgosQA2 {x} 115 {z} {yaw} 0')
    q['wait'](lambda:abs(q['state'](2).get('x',0)-x)<.1 and abs(q['state'](2).get('z',0)-z)<.1)
    q['action'](2,{'action':'hold','name':'key.forward','ticks':110});time.sleep(6)
    s=q['state'](2);passed=abs(s[axis]-end)<3 and s['health']==20 and abs(s['y']-115)<.1
    results.append({'gate':name,'passed':passed,'end':{k:s[k] for k in ['x','y','z','health']}})
    (ROOT/'.lab/reports/pueblo-v11-walk.json').write_text(json.dumps(results,indent=2),'utf-8')
    q['screenshot'](2,'pueblo-v11-gate-'+name)
    print(name,'PASS' if passed else 'FAIL',flush=True)
    assert passed,name
q['server']('virgos audit pueblo-v11-final')
