"""Three real Forge clients exercise Umbral and new UX/persistence rules.
Damage and prerequisite awards are console-simulated, not a human difficulty test.
"""
from pathlib import Path
import importlib.util,json,time,uuid,hashlib,re,runpy,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.REPORT=ROOT/'.lab/reports/qa-v03.json';q.PROFILES[3]='qa-tertiary'
q.IDS[3]=str(uuid.UUID(bytes=hashlib.md5(b'OfflinePlayer:VirgosQA3').digest(),version=3))
read_nbt=runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt']

def position():
    for a,(x,z) in enumerate([(655.5,1050.5),(689.5,1050.5),(672.5,1033.5)],1):
        q.action(a,{'action':'close'});q.server(f'gamemode survival VirgosQA{a}')
        q.server(f'tp VirgosQA{a} {x} 79 {z} 180 30');q.server(f'item replace entity VirgosQA{a} hotbar.4 with minecraft:air')
        q.wait(lambda:abs(q.state(a).get('x',0)-x)<.1 and abs(q.state(a).get('z',0)-z)<.1,60)
        q.action(a,{'action':'key','name':'key.hotbar.5'})

def charge():
    for a in (1,2,3):q.send(a,{'action':'hold','name':'key.use','ticks':200})
    q.wait(lambda:'/COMBAT' in q.status(),30)

def mob_value(selector,key):
    offset=len(q.log());q.server(f'data get entity {selector} {key}')
    text=q.wait(lambda:q.log()[offset:] if 'entity data:' in q.log()[offset:] else None)
    return float(re.search(r'entity data: ([0-9.]+)',text)[1])

def quest_progress(a):
    marker='QA_SAVE_'+uuid.uuid4().hex
    q.server('save-all flush');q.server('say '+marker)
    q.wait(lambda:marker in q.log(),60)
    return read_nbt(q.LAB/'virgos_world/data/heracles_quest_progress.dat')['']['data'].get(q.IDS[a],{})

def finish_checks():
    progress=quest_progress(3).get('inicio_cama',{})
    q.record('red-bed-completes-any-color-quest',bool(progress.get('tasks',{}).get('objetivo',{}).get('complete')),progress=progress)
    q.action(3,{'action':'command','value':'virgos'});q.action(3,{'action':'command','value':'virgos pueblo'});q.action(3,{'action':'command','value':'virgos expedicion estado'})
    q.screenshot(3,'v03-help-and-community')
    q.server('forge tps');q.server('virgos audit');q.server('save-all flush')
    print('Three-client Umbral, durable contributions and red bed checked.',flush=True)

def main():
    for a in (1,2,3):
        q.wait(lambda:q.state(a).get('name')==f'VirgosQA{a}',240)
        for rank in ['explorador','especialista','resonancia','forja']:q.server(f'advancement grant VirgosQA{a} only virgos:{rank}')
        q.server(f'advancement revoke VirgosQA{a} only virgos:umbral')
        q.server(f'effect give VirgosQA{a} minecraft:resistance 1200 4 true')
        q.server(f'attribute VirgosQA{a} minecraft:generic.knockback_resistance base set 1')
    q.server('gamerule mobGriefing false');q.server('gamerule doMobSpawning false');q.server('time set 6000')
    q.record('core-services-ready',all(s in q.status() for s in ['arena=true','pueblo=true','vozAuth=true']))
    position()
    for a in (1,2):q.action(a,{'action':'command','value':'virgos expedicion unirse umbral'})
    q.action(1,{'action':'command','value':'virgos expedicion iniciar'});time.sleep(1)
    q.record('umbral-minimum-three','activeRun' not in q.journal())
    q.action(3,{'action':'command','value':'virgos expedicion unirse umbral'});q.action(1,{'action':'command','value':'virgos expedicion iniciar'})
    q.wait(lambda:'activeRun' in q.journal());run=q.journal()['activeRun']['id']
    q.record('three-real-identities',set(q.journal()['activeRun']['participants'])==set(q.IDS.values()))
    selector='@e[nbt={ForgeData:{virgos_encounter:"'+run+'"}},limit=1]'
    for phase in range(1,4):
        position();charge();initial=mob_value(selector,'Health')
        q.record(f'guardian-phase-{phase}-initial-health',abs(initial-[480,320,160][phase-1])<.1,health=initial)
        if phase==1:
            q.server('tp VirgosQA3 720.5 79 1033.5');time.sleep(2)
            frozen=mob_value(selector,'NoAI');before=mob_value(selector,'Health')
            q.server(f'damage {selector} 10000 minecraft:player_attack by VirgosQA2');time.sleep(.5)
            after=mob_value(selector,'Health')
            q.record('missing-member-pauses-damage',frozen==1 and before==after,health=after)
            q.server('tp VirgosQA3 672.5 79 1033.5 180 30');time.sleep(1)
        end=time.monotonic()+45;cycles=0
        while time.monotonic()<end and '/COMBAT' in q.status():
            q.server(f'damage {selector} 10000 minecraft:player_attack by VirgosQA2');cycles+=1;time.sleep(.7)
        expected='/SEALS' if phase<3 else 'expedición=libre'
        q.record(f'guardian-phase-{phase}-bounded-completion',expected in q.status(),damageCycles=cycles)
        if phase<3:
            floor=mob_value(selector,'Health')
            q.server(f'damage {selector} 10000 minecraft:player_attack by VirgosQA2');time.sleep(.5)
            q.record(f'guardian-phase-{phase}-barrier',floor==mob_value(selector,'Health') and abs(floor-[320,160][phase-1])<.1)
    q.server('save-all flush');time.sleep(3)
    for a in (1,2,3):
        data=json.loads((q.LAB/f'virgos_world/advancements/{q.IDS[a]}.json').read_text('utf-8'))
        q.record(f'umbral-personal-award-{a}',data.get('virgos:umbral',{}).get('done') is True)
    q.record('umbral-award-journal-drained',not q.journal()['pendingAwards'])
    # A second run may not award after a participant leaves or logs out.
    position()
    for a in (1,2,3):
        q.server(f'advancement revoke VirgosQA{a} only virgos:umbral')
        q.action(a,{'action':'command','value':'virgos expedicion unirse umbral'})
    q.action(1,{'action':'command','value':'virgos expedicion iniciar'});q.wait(lambda:'activeRun' in q.journal())
    q.action(3,{'action':'command','value':'logout'})
    q.wait(lambda:'activeRun' not in q.journal(),30)
    q.record('logout-cancels-three-player-run',q.journal()['lastResult']['result']!='complete' and not q.journal()['pendingAwards'])
    credentials=json.loads((ROOT/'.cache/qa-account-3.json').read_text('utf-8'))
    q.action(3,{'action':'command','value':'login '+credentials['password']});time.sleep(3)
    for a in (1,2,3):q.server(f'tp VirgosQA{a} 672.5 115 752.5')
    q.server('give VirgosQA3 minecraft:wheat 96');time.sleep(1)
    for _ in range(3):q.action(3,{'action':'command','value':'virgos pueblo aportar cocina'});time.sleep(.8)
    community=json.loads((q.LAB/'virgos_world/virgos-community.json').read_text('utf-8'))
    saved=read_nbt(q.LAB/f'virgos_world/playerdata/{q.IDS[3]}.dat')['']
    q.record('donation-durable-receipt-and-cap',community['projects']['cocina'].get(q.IDS[3])==64 and not community['pending'] and bool(saved.get('ForgeData',{}).get('virgos_donation_receipt')))
    q.server('save-all flush');time.sleep(2)
    for a in (1,2,3):
        data=json.loads((q.LAB/f'virgos_world/advancements/{q.IDS[a]}.json').read_text('utf-8'))
        q.record(f'community-award-{a}',data.get('virgos:pueblo_cocina',{}).get('done') is True)
    before=quest_progress(3)
    q.record('bed-quest-initially-incomplete',not before.get('inicio_cama',{}).get('complete'))
    quests={f.stem:json.loads(f.read_text('utf-8')) for f in (q.LAB/'config/heracles/quests').glob('*.json')}
    visited=set()
    def complete_dependencies(key):
        for dep in quests[key]['dependencies']:
            complete_dependencies(dep)
            if dep not in visited:q.server(f'heracles complete {dep} VirgosQA3');visited.add(dep)
    complete_dependencies('inicio_cama');time.sleep(2)
    q.server('give VirgosQA3 minecraft:red_bed 1');time.sleep(3)
    finish_checks()

if __name__=='__main__':
    if '--finish-after-flush' in sys.argv:
        # Preserve the attempt that read before save-all had drained its queue.
        shutil.copy2(q.REPORT,q.REPORT.with_name('qa-v03-before-save-fence.json'))
        q.results=[r for r in json.loads(q.REPORT.read_text('utf-8'))['cases'] if r['case']!='red-bed-completes-any-color-quest']
        finish_checks()
    else:main()
