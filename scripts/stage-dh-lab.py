"""Create an isolated DH test from a stopped production server and personal client."""
from pathlib import Path
import json, shutil, re
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'.lab/dh/server'
CLIENT=ROOT/'client/qa-dh'
PERSONAL=Path.home()/'AppData/Local/Virgos-MC/juego'
run=json.loads((ROOT/'.runtime/active-run.json').read_text('utf-8-sig'))
assert run.get('finished') and not run.get('backupError'), 'Production must be stopped; staging only reads it'
assert not LAB.exists() and not CLIENT.exists(), 'Never overwrite an existing lab'
LAB.mkdir(parents=True);CLIENT.mkdir()
for name in ['libraries','mods','config','defaultconfigs','kubejs','moonlight-global-datapacks','easy_npc','modernfix','plugins']:
    def ignore(folder, names):
        return [n for n in names if (n.lower().startswith('playit') or n.lower().startswith('discordsrv'))]
    if (ROOT/name).exists(): shutil.copytree(ROOT/name,LAB/name,ignore=ignore)
for world in ROOT.glob('virgos_world*'):
    if world.is_dir():shutil.copytree(world,LAB/world.name)
for name in ['ketting-server.jar','server.properties','bukkit.yml','spigot.yml','ketting.yml','commands.yml','permissions.yml','eula.txt']:
    shutil.copy2(ROOT/name,LAB/name)
props=(LAB/'server.properties').read_text()
for key,value in {'server-ip':'127.0.0.1','server-port':'25575','enable-rcon':'false','enable-query':'false','motd':'Virgos-MC DH laboratorio local','view-distance':'8','simulation-distance':'6'}.items():
    props=re.sub(r'(?m)^'+re.escape(key)+r'=.*$',key+'='+value,props)
(LAB/'server.properties').write_text(props)
voice=LAB/'config/voicechat/voicechat-server.properties'
text=voice.read_text();text=re.sub(r'(?m)^port=.*','port=24465',text);text=re.sub(r'(?m)^voice_host=.*','voice_host=127.0.0.1:24465',text)
voice.write_text(text)
maintenance=LAB/'config/virgos/maintenance.json'
if maintenance.exists():
    data=json.loads(maintenance.read_text('utf-8-sig'));data['enabled']=False;maintenance.write_text(json.dumps(data,indent=2))
dh=json.loads((ROOT/'.lab/dh/release.json').read_text('utf-8-sig'))['files'][0]['filename']
shutil.copy2(ROOT/'.cache/pack/downloads'/dh,LAB/'mods'/dh)
for name in ['mods','config','resourcepacks','shaderpacks']:
    if (PERSONAL/name).exists():shutil.copytree(PERSONAL/name,CLIENT/name)
shutil.copy2(PERSONAL/'options.txt',CLIENT/'options.txt')
opts=(CLIENT/'options.txt').read_text()
for key,value in {'fullscreen':'false','maxFps':'60','pauseOnLostFocus':'false'}.items():opts=re.sub(r'(?m)^'+key+':.*$',key+':'+value,opts)
(CLIENT/'options.txt').write_text(opts)
shutil.copy2(ROOT/'client/qa-v2/mods/virgos_local_qa-0.1.0.jar',CLIENT/'mods/virgos_local_qa-0.1.0.jar')
runner=(ROOT/'scripts/run-v2-lab.cjs').read_text().replace(".lab/v2/server",".lab/dh/server").replace("'-Xmx8G'","'-Xmx5G'").replace('Local v2 laboratory','Local DH laboratory')
(ROOT/'scripts/run-dh-lab.cjs').write_text(runner)
print(json.dumps({'server':str(LAB),'client':str(CLIENT),'clientDH':False,'serverDH':dh}))
