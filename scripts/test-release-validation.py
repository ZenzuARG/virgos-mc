"""Use an isolated fixture to verify startup refusals; set VIRGOS_SERVER_FIXTURE_ROOT to use an installed server's files."""
from pathlib import Path
import atexit,hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
FIXTURE_ROOT=Path(os.environ.get('VIRGOS_SERVER_FIXTURE_ROOT',ROOT))
fixture_dir=tempfile.TemporaryDirectory(prefix='validation-')
atexit.register(fixture_dir.cleanup)
target=Path(fixture_dir.name)
for rel in ['versions.lock.json','eula.txt','ketting-server.jar','pack/mods.lock.json','pack/custom-artifacts.lock.json','pack/luckperms.lock.json','pack/administration.lock.json']:
 out=target/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(FIXTURE_ROOT/rel,out)
server_lock=target/'pack/server-artifacts.lock.json'
fixture_server_lock=FIXTURE_ROOT/'pack/server-artifacts.lock.json'
if fixture_server_lock.exists():
 data=json.loads(fixture_server_lock.read_text('utf-8'))
 for item in data.get('artifacts',[]):
  component=FIXTURE_ROOT/'mods'/item['filename']
  hasher=hashlib.new(item['hash_algorithm'].lower())
  with component.open('rb') as stream:
   for block in iter(lambda:stream.read(1024*1024),b''):hasher.update(block)
  if component.stat().st_size!=item['size'] or hasher.hexdigest()!=item['hash'].lower():raise RuntimeError('Installed server fixture does not match its server-only artifact lock: '+item['filename'])
 shutil.copy2(fixture_server_lock,server_lock)
else:server_lock.write_text(json.dumps({'schema':1,'artifacts':[]}),'utf-8')
for folder in ['mods','plugins']:
 (target/folder).mkdir()
 for f in (FIXTURE_ROOT/folder).glob('*.jar'):shutil.copy2(f,target/folder/f.name)
base=json.loads((FIXTURE_ROOT/'versions.lock.json').read_text('utf-8'))
java=target/'.runtime'/base['java']['folder']/'bin/java.exe';java.parent.mkdir(parents=True);java.write_bytes(b'fixture, not executed')
cases=[]
def run(case,valid,fragment=''):
 result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/validar-entrega.ps1'),'-ServerPath',str(target)],capture_output=True,text=True)
 output=result.stdout+result.stderr
 ok=(result.returncode==0)==valid and fragment in output
 cases.append({'case':case,'passed':ok})
 if not ok:raise RuntimeError(case+': '+output)
run('complete release',True)
plugin=target/'plugins'/base['authMe']['file'];plugin.write_bytes(b'corrupt fixture')
run('corrupt plugin refused',False,'modificado o incompleto')
shutil.copy2(FIXTURE_ROOT/'plugins'/plugin.name,plugin)
qa=target/'mods/virgos_local_qa-0.1.0.jar';qa.write_bytes(b'QA fixture')
run('unlisted QA mod refused',False,'JAR no incluido')
qa.unlink()
custom=target/'pack/custom-artifacts.lock.json';data=json.loads(custom.read_text('utf-8'));data['artifacts'].append(data['artifacts'][0]);custom.write_text(json.dumps(data),'utf-8')
run('duplicate manifest entry refused',False,'duplicado')
shutil.copy2(FIXTURE_ROOT/'pack/custom-artifacts.lock.json',custom)
mods_lock=json.loads((target/'pack/mods.lock.json').read_text('utf-8'))
smallships=next(item for item in mods_lock['artifacts'] if item['filename']=='smallships-2.0.2-forge-1.20.1.jar')
smallships_file=target/'mods'/smallships['filename']
original=smallships_file.read_bytes()
patched=original+b' server-only validation fixture'
smallships_file.write_bytes(patched)
override_hash=hashlib.sha512(patched).hexdigest()
other_overrides=[item for item in json.loads(server_lock.read_text('utf-8')).get('artifacts',[]) if item['filename']!=smallships['filename']]
override={'schema':1,'artifacts':[{'filename':smallships['filename'],'base_hash_algorithm':smallships['hash_algorithm'],'base_hash':smallships['hash'],'base_size':smallships['size'],'hash_algorithm':'sha512','hash':override_hash,'size':len(patched),'reason':'Server-only fixture override'},*other_overrides]}
server_lock.write_text(json.dumps(override),'utf-8')
run('server-only artifact override accepted',True)
override['artifacts'][0]['base_hash']='0'*128
server_lock.write_text(json.dumps(override),'utf-8')
run('stale server override base refused',False,'referencia base')
override['artifacts'][0]['base_hash']=smallships['hash']
override['artifacts'].append(dict(override['artifacts'][0]))
server_lock.write_text(json.dumps(override),'utf-8')
run('duplicate server override refused',False,'duplicado')
report=ROOT/'.lab/reports/startup-validation-v03.json';report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps({'cases':cases,'fixture':'temporary fixture cleaned at exit'},indent=2),'utf-8')
print(json.dumps(cases))
