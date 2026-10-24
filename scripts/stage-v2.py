"""Create a fresh localhost-only v2 world; never reuse player or production data."""
from pathlib import Path
import hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'.lab/v2/server'
assert not LAB.exists(), 'Candidate already exists; inspect it before changing it.'
LAB.mkdir(parents=True)
lock=json.loads((ROOT/'.lab/v2/mods.lock.json').read_text('utf-8'))
for directory in ['config','defaultconfigs','kubejs','resourcepacks','libraries','moonlight-global-datapacks']:
 if (ROOT/directory).exists():shutil.copytree(ROOT/directory,LAB/directory)
for name in ['ketting-server.jar','eula.txt','bukkit.yml','spigot.yml','commands.yml']:
 if (ROOT/name).is_file():shutil.copy2(ROOT/name,LAB/name)
world=LAB/'virgos_world';world.mkdir()
shutil.copytree(ROOT/'virgos_world/serverconfig',world/'serverconfig')
shutil.copy2(ROOT/'server.properties',LAB/'server.properties')
props=(LAB/'server.properties').read_text('utf-8')
settings={'server-ip':'127.0.0.1','server-port':'25575','level-name':'virgos_world',
 'level-seed':'-6042897318059711023','white-list':'false','enforce-whitelist':'false',
 'view-distance':'6','simulation-distance':'4','motd':'Virgos-MC 2.0 - laboratorio',
 'enable-rcon':'false','enable-query':'false','generate-structures':'true'}
for key,value in settings.items():
 props,n=re.subn(r'(?m)^'+re.escape(key)+r'=.*$',lambda m:key+'='+value,props)
 if not n:props+='\n'+key+'='+value+'\n'
(LAB/'server.properties').write_text(props,'utf-8')
mods=LAB/'mods';mods.mkdir()
for a in lock['artifacts']:
 if 'server' not in a['sides'] or a.get('mode')=='optional':continue
 src=ROOT/'.cache/pack/downloads'/a['filename']
 assert hashlib.new(a['hash_algorithm'],src.read_bytes()).hexdigest()==a['hash'],a['filename']
 shutil.copy2(src,mods/a['filename'])
custom=json.loads((ROOT/'pack/custom-artifacts.lock.json').read_text('utf-8-sig'))
for a in custom['artifacts']:
 if 'server' in a['sides']:shutil.copy2(ROOT/'mods'/a['filename'],mods/a['filename'])
plugins=LAB/'plugins';plugins.mkdir()
for f in (ROOT/'plugins').glob('*.jar'):
 if 'DiscordSRV' not in f.name:shutil.copy2(f,plugins/f.name)
for plugin in ['AuthMe','LuckPerms','CoreProtect','DecentHolograms']:
 src=ROOT/'plugins'/plugin
 if not src.exists():continue
 for p in src.rglob('*.yml'):
  target=plugins/plugin/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
voice=LAB/'config/voicechat/voicechat-server.properties'
text=voice.read_text('utf-8')
for key,value in {'port':'24465','bind_address':'127.0.0.1','voice_host':''}.items():
 text=re.sub(r'(?m)^'+key+r'=.*$',lambda m:key+'='+value,text)
voice.write_text(text,'utf-8')
maintenance=LAB/'config/virgos/maintenance.json';data=json.loads(maintenance.read_text());data['enabled']=False;maintenance.write_text(json.dumps(data,indent=2),'utf-8')
assert not list(mods.glob('*playit*')) and not list(plugins.rglob('.token'))
record={'directory':str(LAB),'worldSeed':settings['level-seed'],'freshWorld':True,
 'copiedAccounts':False,'copiedProgress':False,'publicTunnels':False,'serverModJars':len(list(mods.glob('*.jar')))}
(ROOT/'.lab/v2/staging.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
print(json.dumps(record))
