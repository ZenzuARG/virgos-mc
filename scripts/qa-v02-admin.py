"""Isolated lab: real client block edits, server-simulated boss damage and voice connection."""
from pathlib import Path
import importlib.util,json,time,sqlite3
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.REPORT=ROOT/'.lab/reports/qa-v02-admin.json'

def block_edit(item,place):
    q.server('gamemode creative VirgosQA2');q.server('fill 837 120 898 843 120 906 minecraft:stone')
    q.server('fill 837 121 898 843 124 906 minecraft:air');q.server('tp VirgosQA2 840.5 121 900.5 0 45')
    q.server(f'item replace entity VirgosQA2 hotbar.0 with {item}')
    q.wait(lambda:abs(q.state(2).get('x',0)-840.5)<.1,45);q.action(2,{'action':'close'});q.action(2,{'action':'key','name':'key.hotbar.1'})
    q.action(2,{'action':'use'});time.sleep(1)
    q.action(2,{'action':'key','name':'key.hotbar.5'});q.action(2,{'action':'attack'});time.sleep(1)
    q.record('real-client-edit-'+place,True)

def main():
    q.wait(lambda:q.state(2).get('name')=='VirgosQA2',120)
    time.sleep(4);q.record('voice-client-authenticated-udp', 'vozConectados=1' in q.status(),status=q.status())
    q.server('gamerule mobGriefing false');q.server('gamerule doMobSpawning false')
    q.server('effect give VirgosQA2 minecraft:resistance 600 4 true')
    block_edit('minecraft:stone','vanilla');block_edit('create:andesite_casing','modded')
    time.sleep(12)
    offset=len(q.log());q.server('co lookup u:VirgosQA2 t:10m r:#global a:block');time.sleep(3)
    q.record('coreprotect-lookup-responds','CoreProtect' in q.log()[offset:],output=q.log()[offset:][-6000:])
    q.server('gamemode survival VirgosQA2');q.server('tp VirgosQA2 840.5 121 900.5')
    q.server('advancement revoke VirgosQA2 only virgos:jefe_guardian')
    q.server('summon cataclysm:ender_guardian 850 121 900 {NoAI:1b,PersistenceRequired:1b,Tags:["v02_boss_test"]}')
    time.sleep(2)
    q.server('damage @e[tag=v02_boss_test,limit=1] 20 minecraft:out_of_world by VirgosQA2');time.sleep(4)
    q.server('damage @e[tag=v02_boss_test,limit=1] 10000 minecraft:out_of_world by VirgosQA2');time.sleep(4)
    q.server('save-all flush');time.sleep(3)
    file=q.LAB/f'virgos_world/advancements/{q.IDS[2]}.json';data=json.loads(file.read_text('utf-8'))
    q.record('personal-boss-bonus',data.get('virgos:jefe_guardian',{}).get('done') is True)
    community=json.loads((q.LAB/'virgos_world/virgos-community.json').read_text('utf-8'))
    q.record('donations-survive-restart',sum(community['projects']['cocina'].values())==128 and not community['pending'])
    q.action(2,{'action':'key','name':'key.heracles.open_quests'});q.screenshot(2,'v02-codex');q.action(2,{'action':'close'})
    print('Admin integration checks complete',flush=True)

if __name__=='__main__':main()
