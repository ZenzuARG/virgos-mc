"""Export the built spawn with WorldEdit; keep every operation local to the lab."""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
helper=runpy.run_path(str(ROOT/'scripts/qa-spawn.py'))
state,server,client,wait_for=[helper[k] for k in ('state','server','client','wait_for')]
if state().get('name')!='VirgosQA2':raise SystemExit('Requires the authenticated local QA player.')
folder=ROOT/'.lab/server/config/worldedit/schematics'
destination=ROOT/'pack/spawn'
regions=[('bastion-virgos-v4',[560,80,624],[784,165,848]),
         ('bastion-acceso-norte-v4',[664,55,556],[680,165,623]),
         ('bastion-acceso-sur-v4',[664,55,849],[680,165,916]),
         ('bastion-acceso-oeste-v4',[492,55,728],[559,165,744]),
         ('bastion-acceso-este-v4',[785,55,728],[852,165,744])]
if any((folder/(name+'.schem')).exists() for name,_,_ in regions):raise SystemExit('Export names already exist; preserve them and choose a new revision.')
destination.mkdir(parents=True,exist_ok=True)
client({'action':'close'})
server('tp VirgosQA2 672.5 115 752.5 180 0')
wait_for(lambda s:abs(s.get('x',0)-672.5)<.1 and abs(s.get('z',0)-752.5)<.1)
server('op VirgosQA2')
manifest={'name':'Bastión Virgos','seed':-4556043908712459124,'origin':[672,115,752],
          'minecraft':'1.20.1','worldedit':'7.2.15','files':[]}
try:
    time.sleep(1)
    client({'action':'command','value':'/sel cuboid'})
    for name,minimum,maximum in regions:
        for command in ['/pos1 '+','.join(map(str,minimum)), '/pos2 '+','.join(map(str,maximum)), '/copy', '/schem save '+name]:
            client({'action':'command','value':command})
        path=folder/(name+'.schem')
        deadline=time.monotonic()+60
        previous=-1; stable=0
        while time.monotonic()<deadline:
            if path.exists():
                size=path.stat().st_size
                stable=stable+1 if size==previous and size>0 else 0
                if stable>=5:break
                previous=size
            time.sleep(.5)
        else:raise RuntimeError('WorldEdit export did not complete: '+name)
        shutil.copy2(path,destination/path.name)
        manifest['files'].append({'file':path.name,'minimum':minimum,'maximum':maximum,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
        print('Exported',path.name,flush=True)
finally:
    client({'action':'command','value':'clearclipboard'})
    server('deop VirgosQA2')
