"""Use an isolated fixture to verify startup refusals, never corrupt live files."""
from pathlib import Path
import json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
target=Path(tempfile.mkdtemp(prefix='validation-',dir=ROOT/'.lab'))
for rel in ['versions.lock.json','eula.txt','ketting-server.jar','pack/mods.lock.json','pack/custom-artifacts.lock.json','pack/luckperms.lock.json','pack/administration.lock.json']:
 out=target/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,out)
for folder in ['mods','plugins']:
 (target/folder).mkdir()
 for f in (ROOT/folder).glob('*.jar'):shutil.copy2(f,target/folder/f.name)
base=json.loads((ROOT/'versions.lock.json').read_text('utf-8'))
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
shutil.copy2(ROOT/'plugins'/plugin.name,plugin)
qa=target/'mods/virgos_local_qa-0.1.0.jar';qa.write_bytes(b'QA fixture')
run('unlisted QA mod refused',False,'JAR no incluido')
qa.unlink()
custom=target/'pack/custom-artifacts.lock.json';data=json.loads(custom.read_text('utf-8'));data['artifacts'].append(data['artifacts'][0]);custom.write_text(json.dumps(data),'utf-8')
run('duplicate manifest entry refused',False,'duplicado')
(ROOT/'.lab/reports/startup-validation-v03.json').write_text(json.dumps({'cases':cases,'fixture':str(target)},indent=2),'utf-8')
print(json.dumps(cases))
