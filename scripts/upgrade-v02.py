"""Selective upgrade after lab validation. Never copy lab worlds or player data."""
from pathlib import Path
import argparse,hashlib,json,shutil,socket,zipfile,re
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
run=json.loads((ROOT/'.runtime/active-run.json').read_text('utf-8'))
if not run.get('finished'):raise SystemExit('Stop the public server first.')
with socket.socket() as probe:
    if probe.connect_ex(('127.0.0.1',25565))==0:raise SystemExit('Public port is still active.')
backup=ROOT/'backups/full/virgos-20261018-002243-antes-v02.zip'
with zipfile.ZipFile(backup) as z:
    if z.testzip():raise SystemExit('Backup failed integrity check.')
source=ROOT/'pack/server-overrides'
copies={}
for folder in ['config/heracles/quests','kubejs/data/virgos/advancements']:
    for f in (source/folder).glob('*.json'):copies[f.relative_to(source).as_posix()]=f
for name in ['config/heracles/groups.txt','config/virgos/expeditions.json','config/voicechat/voicechat-server.properties','plugins/CoreProtect/config.yml']:
    copies[name]=source/name
candidates=json.loads((ROOT/'.cache/v02/candidates.json').read_text('utf-8'))
for entry in candidates:
    f=ROOT/'.cache/v02'/entry['filename']
    assert hashlib.new(entry['hash_algorithm'],f.read_bytes()).hexdigest()==entry['hash']
    copies[('plugins/' if entry['project']=='coreprotect' else 'mods/')+entry['filename']]=f
core=json.loads((ROOT/'pack/custom-artifacts.lock.json').read_text('utf-8'))['artifacts'][0]
f=ROOT/core['local_source'];assert hashlib.sha256(f.read_bytes()).hexdigest()==core['hash'];copies['mods/'+core['filename']]=f
for name in copies:
    target=(ROOT/name).resolve();assert target.is_relative_to(ROOT) and target.parts[len(ROOT.parts)] in ['mods','plugins','config','kubejs']
    assert 'virgos_local_qa' not in name
voice_css='\n/* Voice uses Companion native integration: tunnel name simple-voice-chat. */\n'
css=ROOT/'config/playit-companion/custom_tunnels.css'
content=css.read_text('utf-8')
content=re.sub(r'#(?:bluemap|minecraft-bedrock)\s*\{[^}]*enabled:\s*false;[^}]*\}', '', content)
if 'simple-voice-chat' not in content:content+=voice_css
report={'version':'0.2.0-rc1','applied':a.apply,'utc':datetime.now(timezone.utc).isoformat(),'backup':str(backup),'files':{n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in copies.items()},'voiceEndpoint':'practically-accountant.tun.ply.gg:2685','worldsCopied':False}
if a.apply:
    for name,f in copies.items():
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
    css.write_text(content,'utf-8')
    old=ROOT/'mods/virgos_core-0.1.0.jar';stash=ROOT/'backups/upgrade-v02/public-virgos_core-0.1.0.jar'
    if old.exists():
        if stash.exists():raise SystemExit('Previous integration stash already exists; inspect before retry.')
        shutil.move(str(old),str(stash))
    (ROOT/'pack/administration.lock.json').write_text(json.dumps([x for x in candidates if x['project']=='coreprotect'],indent=2)+'\n','utf-8')
    (ROOT/'pack/upgrade-v02.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
print(json.dumps({'applied':a.apply,'files':len(copies),'backupVerified':True,'worldsCopied':False},indent=2))
