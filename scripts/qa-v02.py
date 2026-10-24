"""Integration checks on two real Forge clients. Combat damage is console-simulated."""
from pathlib import Path
import importlib.util,json,time
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.REPORT=ROOT/'.lab/reports/qa-v02.json'

def ready():
    for a in (1,2):
        q.wait(lambda:q.state(a).get('name')==f'VirgosQA{a}',240)
        for rank in ['explorador','especialista','resonancia','forja']:q.server(f'advancement grant VirgosQA{a} only virgos:{rank}')
        q.action(a,{'action':'close'})
        q.server(f'effect give VirgosQA{a} minecraft:resistance 600 4 true')
        q.server(f'attribute VirgosQA{a} minecraft:generic.knockback_resistance base set 1')
    q.server('gamerule doMobSpawning false');q.server('time set 6000');q.server('weather clear')

def position(round=1,kind='resonancia'):
    spots=([(655.5,1050.5,180,30),(689.5,1050.5,180,30)] if kind!='resonancia' or round==1 else
           [(689.5,1050.5,180,30),(672.5,1033.5,180,30)] if round==2 else
           [(655.5,1050.5,180,30),(672.5,1033.5,180,30)])
    for a,(x,z,yaw,pitch) in zip((1,2),spots):
        q.server(f'gamemode survival VirgosQA{a}');q.server(f'tp VirgosQA{a} {x} 79 {z} {yaw} {pitch}')
        q.server(f'item replace entity VirgosQA{a} hotbar.4 with minecraft:air')
        q.wait(lambda:abs(q.state(a).get('x',0)-x)<.1 and abs(q.state(a).get('z',0)-z)<.1,60)
        q.action(a,{'action':'key','name':'key.hotbar.5'})

def expedition(kind):
    position(kind=kind)
    for a in (1,2):q.action(a,{'action':'command','value':f'virgos expedicion unirse {kind}'})
    q.action(1,{'action':'command','value':'virgos expedicion iniciar'})
    q.wait(lambda:'activeRun' in q.journal());run=q.journal()['activeRun']['id']
    selector='@e[nbt={ForgeData:{virgos_encounter:"'+run+'"}}]'
    for round in range(1,4):
        position(round,kind)
        if kind=='forja':
            before=q.status();q.record(f'forja-{round}-awaits-materials','/SEALS' in before)
            item,count=[('create:iron_sheet',8),('create:brass_sheet',4),('create:precision_mechanism',1)][round-1]
            q.server(f'give VirgosQA2 {item} {count}');time.sleep(1)
            q.action(2,{'action':'command','value':'virgos expedicion aportar'})
        q.charge();q.record(f'{kind}-{round}-seals',True)
        if kind=='forja':
            time.sleep(7);offset=len(q.log())
            q.server(f'execute as {selector} run damage @s 10000 minecraft:player_attack by VirgosQA2');time.sleep(1)
            q.record(f'forja-{round}-closed-without-cooling','/COMBAT' in q.status(),console=q.log()[offset:][-1000:])
        end=time.monotonic()+70
        ticks=0
        while time.monotonic()<end and '/COMBAT' in q.status():
            if kind=='forja' and ticks%5==0:q.send(1,{'action':'hold','name':'key.use','ticks':160})
            q.server(f'execute as {selector} run damage @s 10000 minecraft:player_attack by VirgosQA2')
            ticks+=1;time.sleep(.6)
        current=q.status()
        q.record(f'{kind}-{round}-bounded-damage-completion','/SEALS' in current if round<3 else 'expedición=libre' in current,status=current,damageCycles=ticks)
    q.record(kind+'-individual-result',q.journal()['lastResult']['result']=='complete',journal=q.journal())

def community():
    for a in (1,2):
        q.server(f'tp VirgosQA{a} 672.5 115 752.5');q.server(f'give VirgosQA{a} minecraft:wheat 96');time.sleep(1)
        for _ in range(3):q.action(a,{'action':'command','value':'virgos pueblo aportar cocina'});time.sleep(.8)
    file=q.LAB/'virgos_world/virgos-community.json';data=json.loads(file.read_text('utf-8'))
    q.record('community-consumes-and-caps-contributions',set(data['projects']['cocina'].values())=={64} and len(data['projects']['cocina'])==2 and not data['pending'],journal=data)

def main():
    ready();q.record('voice-guard-registered','vozAuth=true' in q.status())
    expedition('resonancia');expedition('forja')
    position(kind='umbral')
    for a in (1,2):q.action(a,{'action':'command','value':'virgos expedicion unirse umbral'})
    q.action(1,{'action':'command','value':'virgos expedicion iniciar'});time.sleep(1)
    q.record('umbral-refuses-two-players','activeRun' not in q.journal())
    for a in (1,2):q.action(a,{'action':'command','value':'virgos expedicion salir'})
    community();q.server('forge tps');q.server('save-all flush')
    q.screenshot(2,'v02-integration-client')
    print('v0.2 integration checks complete',flush=True)

if __name__=='__main__':main()
