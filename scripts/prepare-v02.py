"""Stage the v0.2 additive changes, never touch the running public world."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
candidates=json.loads((ROOT/'.cache/v02/candidates.json').read_text('utf-8'))
lock=json.loads((ROOT/'pack/mods.lock.json').read_text('utf-8'))
voice=next(x for x in candidates if x['project']=='simple-voice-chat')
if not any(x['project']==voice['project'] for x in lock['artifacts']):lock['artifacts'].append(voice)
(ROOT/'pack/mods.lock.json').write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n','utf-8')
for profile in ['standard','qa-secondary']:
    shutil.copy2(ROOT/'.cache/v02'/voice['filename'],ROOT/'client'/profile/'mods'/voice['filename'])
for base in [ROOT/'pack/server-overrides',ROOT/'.lab/server']:
    file=base/'config/virgos/expeditions.json'
    data=json.loads(file.read_text('utf-8'))
    data['balance']={name:dict(zip(['damagePerSecond','damageBurst','healingPerSecond'],values)) for name,values in [('resonancia',(20,10,4)),('forja',(30,18,6)),('umbral',(40,24,8))]}
    data['guardianHealth']=480
    file.write_text(json.dumps(data,indent=2)+'\n','utf-8')
    folder=base/'config/voicechat';folder.mkdir(exist_ok=True)
    lab=base.name=='server'
    (folder/'voicechat-server.properties').write_text(
        f'port={24455 if lab else 24454}\nbind_address=127.0.0.1\nvoice_host={"127.0.0.1:24455" if lab else "practically-accountant.tun.ply.gg:2685"}\n'
        'max_voice_distance=32.0\nwhisper_distance=8.0\nenable_groups=true\nforce_voice_chat=false\nallow_recording=false\nallow_pings=true\n','utf-8')
    plugin=base/'plugins/CoreProtect';plugin.mkdir(parents=True,exist_ok=True)
    (plugin/'config.yml').write_text('language: es\nuse-mysql: false\nuse-duckdb: false\nverbose: false\ncheck-updates: false\nerror-reporting: false\nplayer-commands: false\nplayer-messages: false\nrollback-items: false\nrollback-entities: false\n','utf-8')
folder=ROOT/'pack/client-overrides/config/voicechat';folder.mkdir(exist_ok=True)
(folder/'voicechat-client.properties').write_text('microphone_activation_type=PTT\nmuted=false\n','utf-8')
options=ROOT/'pack/client-overrides/config/defaultoptions/options.txt'
lines=[x for x in options.read_text('utf-8').splitlines() if 'key.voicechat_' not in x and not x.startswith(('key_key.push_to_talk:','key_key.voice_chat:'))]
lines+=['key_key.push_to_talk:key.keyboard.caps.lock','key_key.voice_chat:key.keyboard.o']
options.write_text('\n'.join(lines)+'\n','utf-8')
print('v0.2 staged; public server untouched. Voice pinned and QA clients updated.')
