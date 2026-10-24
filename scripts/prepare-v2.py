"""Resolve Virgos 2 world renewal into an isolated candidate, without editing live locks."""
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures, importlib.util, json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.lab/v2'; OUT.mkdir(parents=True, exist_ok=True)
spec=importlib.util.spec_from_file_location('resolver',ROOT/'scripts/resolve-pack.py')
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
PINS={
 'integrated-villages':'hoQg6GXe','idas':'mgwwWo3b','integrated-stronghold':'HX8UIG5u',
 'integrated-api':'Pt3ikLE2','terralith':'WeYhEb5d','terralith-restoned':'9wwdRqkT',
 'when-dungeons-arise':'6hQpx5Tc','when-dungeons-arise-seven-seas':'AxIOkvEv',
 'bosses-of-mass-destruction-forge':'2Kw4xPhp','meet-your-fight':'f5pZH4Tl',
 'deep-aether':'IE1ZMRN3','aquamirae':'A6aIqoJZ','incendium':'uUqarp2H',
 'nullscape':'QsRKydVt','guard-villagers':'zCzBkn3R','obscure-api':'7sZmDObM'}
SERVER_ONLY={'terralith','terralith-restoned','incendium','nullscape'}
REPLACE={'towns-and-towers','yungs-better-strongholds'}
lock=json.loads((ROOT/'pack/mods.lock.json').read_text('utf-8-sig'))
removed=[a for a in lock['artifacts'] if a['project'] in REPLACE]
lock['artifacts']=[a for a in lock['artifacts'] if a['project'] not in REPLACE]
existing={a['project_id']:a for a in lock['artifacts'] if a.get('project_id')}
new={}; queue=[(r.request_json('version/'+pin),slug,True,SERVER_ONLY.__contains__(slug)) for slug,pin in PINS.items()]
while queue:
 v,slug,isroot,server_only=queue.pop(0)
 if v['project_id'] in existing:
  continue
 if v['project_id'] in new:
  if not server_only:new[v['project_id']]['sides']=['client','server']
  continue
 assert 'forge' in v['loaders'] and '1.20.1' in v['game_versions'],slug
 f=next((f for f in v['files'] if f['primary']),v['files'][0])
 assert f['filename'].endswith('.jar'),(slug,f['filename'])
 new[v['project_id']]={'project':slug,'project_id':v['project_id'],'version_id':v['id'],
  'version':v['version_number'],'filename':f['filename'],'url':f['url'],'hash_algorithm':'sha512',
  'hash':f['hashes']['sha512'],'size':f['size'],'sides':['server'] if server_only else ['client','server'],
  'mode':'standard','root':isroot,'source':f'https://modrinth.com/mod/{slug}/version/{v["id"]}'}
 for dep in v['dependencies']:
  if dep['dependency_type']!='required':continue
  pid=dep['project_id']
  if pid in existing:
   assert not dep.get('version_id') or existing[pid].get('version_id')==dep['version_id'],(slug,dep)
   if not server_only:existing[pid]['sides']=sorted(set(existing[pid]['sides'])|{'client','server'})
   continue
  dv=r.request_json('version/'+dep['version_id']) if dep.get('version_id') else r.project_version(pid)
  queue.append((dv,r.request_json('project/'+pid)['slug'],False,server_only))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 additions=list(pool.map(r.download,new.values()))
for a in additions:
 a['descriptor']=r.inspect_jar(r.DOWNLOADS/a['filename'])
 print(json.dumps({'project':a['project'],'version':a['version'],'filename':a['filename'],
  'mandatory':[d for d in a['descriptor']['dependencies'] if d.get('mandatory') and d['modId'] not in {'forge','minecraft'}]}),flush=True)
lock['artifacts']+=additions
ids={'minecraft','forge','java'}|{m['id'] for a in lock['artifacts'] for m in a.get('descriptor',{}).get('mods',[])}
missing=[{'file':a['filename'],**d} for a in lock['artifacts'] for d in a.get('descriptor',{}).get('dependencies',[]) if d.get('mandatory') and d['modId'] not in ids]
lock.update(status='v2-isolated-candidate-not-published',missing_declared_mod_ids=missing)
(OUT/'mods.lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf-8')
(OUT/'additions.json').write_text(json.dumps(additions,ensure_ascii=False,indent=2)+'\n','utf-8')
(OUT/'plan.json').write_text(json.dumps({'version':'2.0.0','created':datetime.now(timezone.utc).isoformat(),
 'authorized':{'mixedFantasyMedievalCreate':True,'newWorld':True,'resetInventoryAndProgress':True,'publishClientToDiscordAfterVerification':True},
 'preserve':['AuthMe identities','Playit endpoints','Discord bot credentials','previous full world archive'],
 'removed':[a['filename'] for a in removed],'additions':list(PINS),'missingDependencies':missing,
 'tasks':['resolve and validate dependencies','balance world generation, loot and boss progression',
 'generate fresh isolated world','build and audit integrated spawn','exercise client join, quests and world content',
 'package and verify v2 installer','archive old world and reset all progression','verify public connection and voice',
 'update Discord installer and instructions'],'status':'dependencies-resolved-pending-world-tests'},indent=2)+'\n','utf-8')
assert not missing,missing
print(json.dumps({'newJars':len(additions),'removed':len(removed),'candidateJars':len(lock['artifacts'])}),flush=True)
