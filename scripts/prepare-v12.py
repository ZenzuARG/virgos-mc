"""Resolve only the approved expansion into an isolated candidate; preserve live locks."""
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures, importlib.util, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.lab/v12';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('resolver',ROOT/'scripts/resolve-pack.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
PINS={'bountiful':'EM7Su3PD','exposure':'Wk43p4gt','small-ships':'9KNCbtCC',
      'immersive-melodies':'9vAY9Ic1','every-compat':'1W3wIglQ',
      'create-alexs-caves-compat':'aqpInCWh','easy-npc':'iaFm8RmB',
      'lightmans-currency':'CmqiNDe3'}
def record(v,slug,root=True,plugin=False):
    f=next((f for f in v['files'] if f['primary']),v['files'][0]);kind='sha512' if 'sha512' in f['hashes'] else 'sha1'
    return dict(project=slug,project_id=v['project_id'],version_id=v['id'],version=v['version_number'],
        filename=f['filename'],url=f['url'],hash_algorithm=kind,hash=f['hashes'][kind],size=f['size'],
        sides=['server'] if plugin else ['client','server'],mode='required' if plugin else 'standard',root=root,
        source=f'https://modrinth.com/{"plugin" if plugin else "mod"}/{slug}/version/{v["id"]}')
lock=json.loads((ROOT/'pack/mods.lock.json').read_text('utf-8'))
existing={a['project_id']:a for a in lock['artifacts'] if a.get('project_id')}
new={};queue=[(r.request_json('version/'+pin),slug,True) for slug,pin in PINS.items()]
while queue:
    v,slug,root=queue.pop(0)
    if v['project_id'] in existing or v['project_id'] in new:continue
    if 'forge' not in v['loaders'] or '1.20.1' not in v['game_versions']:raise ValueError(slug)
    new[v['project_id']]=record(v,slug,root)
    for dep in v['dependencies']:
        if dep['dependency_type']!='required':continue
        pid=dep['project_id']
        if pid in existing:
            if dep.get('version_id') and existing[pid].get('version_id')!=dep['version_id']:
                raise ValueError(f'Existing version differs from exact dependency: {slug} {pid}')
            continue
        if pid in new:continue
        dv=r.request_json('version/'+dep['version_id']) if dep.get('version_id') else r.project_version(pid)
        queue.append((dv,r.request_json('project/'+pid)['slug'],False))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    additions=list(pool.map(r.download,new.values()))
for a in additions:
    a['descriptor']=r.inspect_jar(r.DOWNLOADS/a['filename'])
    print(a['filename'],json.dumps(a['descriptor']['dependencies']))
lock['artifacts']+=additions;lock['status']='v1.2-lab-candidate'
(OUT/'mods.lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf-8')
plugins=json.loads((ROOT/'pack/administration.lock.json').read_text('utf-8'))
p=record(r.request_json('version/fbE7wARc'),'decentholograms',plugin=True);r.download(p)
plugins.append(p);(OUT/'administration.lock.json').write_text(json.dumps(plugins,indent=2)+'\n','utf-8')
(OUT/'additions.json').write_text(json.dumps(additions,ensure_ascii=False,indent=2)+'\n','utf-8')
baseline=OUT/'baseline'
if not baseline.exists():
    baseline.mkdir()
    for name in ['pack/mods.lock.json','pack/administration.lock.json','pack/custom-artifacts.lock.json','pack/current-release.json','dist/release.json']:
        dest=baseline/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    archive=ROOT/'backups'/f'v12-before-sources-{datetime.now():%Y%m%d-%H%M%S}.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for directory in ['scripts','templates','pack','docs','dev/virgos-core/src']:
            for f in (ROOT/directory).rglob('*'):
                if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(ROOT))
        for f in (ROOT/'dev/virgos-core').glob('*'):
            if f.is_file():z.write(f,f.relative_to(ROOT))
print(f'Candidate: {len(additions)} new mod jars; DecentHolograms. Live locks untouched.')
