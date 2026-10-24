"""Prepare stopped lab/client and isolate the restored production snapshot."""
from pathlib import Path
import json,shutil,re,ctypes
ROOT=Path(__file__).resolve().parents[1]
def stopped(path):
 state=json.loads(path.read_text('utf-8-sig'))
 if state.get('finished'):return
 handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,state['pid'])
 if handle:ctypes.windll.kernel32.CloseHandle(handle);raise SystemExit('Still running: '+str(path))
stopped(ROOT/'.lab/server/process.json');stopped(ROOT/'client/standard/virgos-qa/process.json')
shutil.copy2(ROOT/'dev/virgos-core/build/libs/virgos_core-0.3.0.jar',ROOT/'.lab/server/mods/virgos_core-0.3.0.jar')
shutil.copy2(ROOT/'dev/virgos-core/build/libs/virgos_local_qa-0.1.0.jar',ROOT/'client/standard/mods/virgos_local_qa-0.1.0.jar')
for target in [ROOT/'.lab/server/config/modernfix-mixins.properties',ROOT/'client/standard/config/modernfix-mixins.properties']:
 shutil.copy2(ROOT/'pack/client-overrides/config/modernfix-mixins.properties',target)
restored=ROOT/'.lab/restore-check/auditoria-v03'
assert (restored/'restore-verification.json').is_file()
for jar in (restored/'mods').glob('*playit*.jar'):
 stash=restored/'disabled-tunnel';stash.mkdir(exist_ok=True)
 shutil.move(str(jar),str(stash/jar.name))
props=restored/'server.properties';text=props.read_text('utf-8')
for key,value in {'server-ip':'127.0.0.1','server-port':'25576','enable-rcon':'false','enable-query':'false'}.items():text=re.sub(r'^'+key+r'=.*$',key+'='+value,text,flags=re.M)
props.write_text(text,'utf-8')
voice=restored/'config/voicechat/voicechat-server.properties';text=voice.read_text('utf-8');text=re.sub(r'^port=.*$','port=24456',text,flags=re.M);text=re.sub(r'^voice_host=.*$','voice_host=127.0.0.1:24456',text,flags=re.M);voice.write_text(text,'utf-8')
policy=restored/'config/virgos/maintenance.json';data=json.loads(policy.read_text('utf-8'));data['enabled']=False;data['backupOnCleanStop']=False;policy.write_text(json.dumps(data,indent=2),'utf-8')
print('Lab/client candidate ready; restored snapshot has no public tunnel and distinct local ports.')
