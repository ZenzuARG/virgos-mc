"""Read-only, repeatable release audit. Never exports accounts or tunnel credentials."""
from pathlib import Path
import argparse,hashlib,json,zipfile,tomllib,collections,re
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',default='.lab/reports/audit-baseline.json');a=p.parse_args()
def read(path):return json.loads((ROOT/path).read_text('utf-8-sig'))
def digest(path,algorithm='sha256'):return hashlib.new(algorithm,Path(path).read_bytes()).hexdigest()
checks=[]
def check(key,ok,detail):checks.append({'id':key,'passed':bool(ok),'detail':detail})
base=read('versions.lock.json');mods=read('pack/mods.lock.json')['artifacts']+read('pack/custom-artifacts.lock.json')['artifacts']
expected={m['filename']:m for m in mods if 'server' in m['sides'] and m.get('mode')!='optional'}
expected[base['playitCompanion']['file']]={'hash':base['playitCompanion']['hash'],'hash_algorithm':base['playitCompanion']['algorithm']}
actual={f.name:f for f in (ROOT/'mods').glob('*.jar')}
check('server_mod_inventory',set(actual)==set(expected),{'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected))})
bad=[name for name,m in expected.items() if name not in actual or digest(actual[name],m['hash_algorithm'])!=m['hash']]
check('server_mod_hashes',not bad,bad)
ids=collections.defaultdict(list)
for name,path in actual.items():
 with zipfile.ZipFile(path) as z:
  if 'META-INF/mods.toml' in z.namelist():
   metadata=tomllib.loads(z.read('META-INF/mods.toml').decode('utf-8-sig'))
   for m in metadata.get('mods',[]):ids[m['modId']].append(name)
duplicates={k:v for k,v in ids.items() if len(v)>1}
check('duplicate_mod_ids',not duplicates,duplicates)
plugins={base['authMe']['file']:(base['authMe']['algorithm'],base['authMe']['hash'])}
lp=read('pack/luckperms.lock.json');plugins[lp['filename']]=('sha512',lp['sha512'])
for m in read('pack/administration.lock.json'):plugins[m['filename']]=(m['hash_algorithm'],m['hash'])
plugin_files={p.name:p for p in (ROOT/'plugins').glob('*.jar')}
check('plugin_inventory',set(plugin_files)==set(plugins),{'expected':sorted(plugins),'actual':sorted(plugin_files)})
check('plugin_hashes',all(n in plugin_files and digest(plugin_files[n],alg)==h for n,(alg,h) in plugins.items()),sorted(plugins))
properties=dict(line.split('=',1) for line in (ROOT/'server.properties').read_text('utf-8-sig').splitlines() if '=' in line and not line.startswith('#'))
expected_properties={'online-mode':'false','white-list':'false','enforce-secure-profile':'false','pvp':'false','enable-rcon':'false','enable-command-block':'false','max-players':'10','view-distance':'8','simulation-distance':'6'}
property_drift={key:{'expected':value,'actual':properties.get(key)} for key,value in expected_properties.items() if properties.get(key)!=value}
check('server_access_and_load_policy',not property_drift,property_drift)
auth=(ROOT/'plugins/AuthMe/config.yml').read_text('utf-8-sig')
auth_values={'caching':'false','allowMovement':'false','ForceSingleSession':'true','kickOnWrongPassword':'true','maxRegPerIp':'0','maxLoginPerIp':'0','loginTimeout':'120'}
auth_drift={key:value for key,value in auth_values.items() if not re.search(r'^\s+'+re.escape(key)+r':\s*'+value+r'\s*$',auth,re.M)}
auth_no_comments='\n'.join(line for line in auth.splitlines() if not line.lstrip().startswith('#'))
sessions_disabled=bool(re.search(r'^\s+sessions:\s*\n\s+enabled:\s*false\s*$',auth_no_comments,re.M))
check('offline_auth_policy',not auth_drift and sessions_disabled,{'mismatches':auth_drift,'automaticIpSessionsDisabled':sessions_disabled})
check('no_qa_administrators',all(not str(entry.get('name','')).lower().startswith('virgosqa') for entry in read('ops.json')),None)
policy=read('pack/balance-policy.json');drift=[]
for rel,values in policy.items():
 path=ROOT/('virgos_world/'+rel if rel.startswith('serverconfig/') else rel)
 doc=(json.loads if path.suffix=='.json' else tomllib.loads)(path.read_text('utf-8-sig'))
 for key,want in values.items():
  try:
   actual_value=doc
   for part in key.split('.'):actual_value=actual_value[part]
  except KeyError:actual_value='<missing>'
  if actual_value!=want:drift.append({'file':rel,'key':key,'expected':want,'actual':actual_value})
check('effective_balance_policy',not drift,drift)
recipe_paths=['config/modernfix-mixins.properties','pack/server-overrides/config/modernfix-mixins.properties','pack/client-overrides/config/modernfix-mixins.properties']
check('recipe_sync_configuration',all((ROOT/f).exists() and re.search(r'^mixin\.perf\.smart_ingredient_sync=false\s*$',(ROOT/f).read_text('utf-8'),re.M) for f in recipe_paths),recipe_paths)
quests={f.stem:json.loads(f.read_text('utf-8')) for f in (ROOT/'config/heracles/quests').glob('*.json')}
unknown=[];cycles=[];state={}
def visit(key,chain):
 if state.get(key)==1:cycles.append(chain+[key]);return
 if state.get(key)==2:return
 state[key]=1
 for dep in quests[key].get('dependencies',[]):
  if dep not in quests:unknown.append((key,dep))
  else:visit(dep,chain+[key])
 state[key]=2
for key in quests:visit(key,[])
check('quest_graph',not unknown and not cycles,{'quests':len(quests),'unknown':unknown,'cycles':cycles})
check('personal_nonrepeatable_quests',all(q['settings'].get('individual_progress') and not q['settings'].get('repeatable') for q in quests.values()),len(quests))
registry=read('virgos-reports/registries.json');items=set(registry['items']);tags=set(registry.get('itemTags',[]));invalid=[]
for key,q in quests.items():
 for task in q.get('tasks',{}).values():
  if task.get('type')=='heracles:item' and isinstance(task.get('item'),str):
   value=task['item'];valid=value[1:] in tags if value.startswith('#') else value in items
   if not valid:invalid.append((key,value))
 for reward in q.get('rewards',{}).values():
  if reward.get('type')=='heracles:item' and reward.get('item',{}).get('id') not in items:invalid.append((key,reward.get('item')))
check('quest_item_registry',not invalid,invalid)
templates=ROOT/'pack/server-overrides';differences=[];override_drift=[]
for path in templates.rglob('*'):
 if not path.is_file() or not path.suffix in {'.json','.js','.txt','.properties','.toml','.yml'}:continue
 rel=path.relative_to(templates);live=ROOT/rel
 if not live.exists():override_drift.append({'file':rel.as_posix(),'reason':'missing'});continue
 if path.read_bytes()==live.read_bytes():continue
 differences.append(rel.as_posix())
 # These libraries rewrite comments and append their defaults at startup.
 # Compare every configured value while allowing those generated additions.
 if path.suffix=='.properties' or rel.as_posix()=='plugins/CoreProtect/config.yml':
  separator='=' if path.suffix=='.properties' else ':'
  def values(file):
   return {line.split(separator,1)[0].strip():line.split(separator,1)[1].strip() for line in file.read_text('utf-8-sig').splitlines() if separator in line and not line.lstrip().startswith('#')}
  want=values(path);current=values(live)
  mismatches=[key for key,value in want.items() if current.get(key)!=value]
  if mismatches:override_drift.append({'file':rel.as_posix(),'keys':mismatches})
 elif path.suffix in {'.json','.toml'}:
  # Mods normalize whitespace/comments at startup. Still compare every value,
  # including added/removed keys, rather than accepting any changed file.
  parse=json.loads if path.suffix=='.json' else tomllib.loads
  if parse(path.read_text('utf-8-sig'))!=parse(live.read_text('utf-8-sig')):
   override_drift.append({'file':rel.as_posix(),'reason':'configured values differ'})
 else:override_drift.append({'file':rel.as_posix(),'reason':'content differs'})
check('configured_server_overrides',not override_drift,override_drift)
worlds=sorted(p.name for p in ROOT.glob('virgos_world*') if p.is_dir())
automatic=sorted((ROOT/'simplebackups').glob('*.zip'),key=lambda p:p.stat().st_mtime)
auto_coverage=[]
if automatic:
 with zipfile.ZipFile(automatic[-1]) as z:auto_coverage=sorted({name.split('/')[0] for name in z.namelist()})
complete_record=ROOT/'.runtime/last-backup.json';full_coverage=[];full_verified=False;full_archive=None
if complete_record.exists():
 record=read('.runtime/last-backup.json');full_archive=Path(record['archive'])
 if full_archive.is_file() and digest(full_archive)==record['sha256']:
  with zipfile.ZipFile(full_archive) as z:
   manifest=json.loads(z.read('backup-manifest.json'));full_coverage=manifest['worldFolders']
   full_verified=all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
check('automatic_world_backup_coverage',full_verified and set(worlds)<=set(full_coverage),{'worlds':worlds,'fullArchive':str(full_archive),'verified':full_verified,'completeWorlds':full_coverage,'simpleBackupsPartialRoots':auto_coverage})
check('production_has_no_qa_mod',not any('virgos_local_qa' in name for name in actual),None)
report={'scope':'Installed release, effective policy, dependency identities, quest graph, backup coverage. Runtime and human checks are separate.','checks':checks,'templateDifferences':differences,'counts':{'serverJars':len(actual),'modIds':len(ids),'plugins':len(plugin_files),'quests':len(quests),'worldFolders':len(worlds)},'components':sorted(actual),'failed':[c['id'] for c in checks if not c['passed']]}
dest=ROOT/a.output;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'report':a.output,'counts':report['counts'],'failed':report['failed'],'templateDifferences':differences},ensure_ascii=False))
raise SystemExit(1 if report['failed'] else 0)
