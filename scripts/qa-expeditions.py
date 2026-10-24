"""Two real local Forge identities exercise expedition coordination.

Wave completion uses explicitly simulated server damage, not a difficulty test.
Player input, authentication, seals and individual awards run on actual clients.
"""
from pathlib import Path
import json
import re
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'.lab/server'
REPORT=ROOT/'.lab/reports/qa-expeditions.json'
PROFILES={1:'qa-secondary',2:'standard'}
IDS={1:'13e2e728-2a7a-36a6-84ee-5c289cf4cc02',2:'32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e'}
results=[]
SCOPE='Real clients and seals; console-simulated wave kills, not combat balance validation'

def state(account):
    try:return json.loads((ROOT/f'client/{PROFILES[account]}/virgos-qa/status.json').read_text('utf-8'))
    except (OSError,json.JSONDecodeError):return {}

def send(account,command):
    path=ROOT/f'client/{PROFILES[account]}/virgos-qa/commands.jsonl'
    with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(command)+'\n')
    return len(path.read_text('utf-8').splitlines())

def wait(predicate,timeout=30):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.25)
    raise RuntimeError('QA condition timed out')

def action(account,command):
    line=send(account,command)
    wait(lambda:state(account).get('line',0)>=line)
    return line

def server(command):
    with (LAB/'console-commands.txt').open('a',encoding='utf-8') as stream:stream.write(command+'\n')

def log():return (LAB/'console.log').read_text('utf-8',errors='replace')

def status():
    offset=len(log());server('virgos status')
    text=wait(lambda:log()[offset:] if 'AuthMe=' in log()[offset:] else None)
    return text.split('AuthMe=')[-1].splitlines()[0]

def journal():return json.loads((LAB/'virgos_world/virgos-expeditions-state.json').read_text('utf-8'))

def record(name,passed,**details):
    results.append({'case':name,'passed':passed,**details})
    REPORT.write_text(json.dumps({'scope':SCOPE,'cases':results},indent=2,ensure_ascii=False),'utf-8')
    print(name,'PASS' if passed else 'FAIL',flush=True)
    if not passed:raise RuntimeError(name)

def screenshot(account,name):
    line=action(account,{'action':'screenshot'})
    source=ROOT/f'client/{PROFILES[account]}/screenshots/virgos-qa-{line}.png'
    wait(lambda:source.exists())
    time.sleep(.3);shutil.copy2(source,ROOT/f'.lab/reports/{name}.png')

def position():
    for account,x in [(1,655.5),(2,689.5)]:
        action(account,{'action':'close'})
        server(f'gamemode survival VirgosQA{account}')
        server(f'tp VirgosQA{account} {x} 79 1050.5 180 30')
        server(f'effect give VirgosQA{account} minecraft:instant_health 1 4 true')
        server(f'effect give VirgosQA{account} minecraft:saturation 1 4 true')
        server(f'item replace entity VirgosQA{account} hotbar.4 with minecraft:air')
        wait(lambda:abs(state(account).get('x',0)-x)<.1 and abs(state(account).get('z',0)-1050.5)<.1)
        action(account,{'action':'key','name':'key.hotbar.5'})

def join_and_start():
    for account in (1,2):action(account,{'action':'command','value':'virgos expedicion unirse resonancia'})
    action(1,{'action':'command','value':'virgos expedicion iniciar'})
    wait(lambda:'activeRun' in journal())
    return journal()['activeRun']['id']

def charge():
    for account in (1,2):send(account,{'action':'hold','name':'key.use','ticks':200})
    end=time.monotonic()+20
    while time.monotonic()<end:
        current=status()
        if '/COMBAT' in current:return current
        if 'expedición=libre' in current:raise RuntimeError('Encounter ended before combat: '+str(journal()))
        time.sleep(1)
    screenshot(2,'qa-expedition-seals-failed')
    raise RuntimeError('Seals did not charge with two clients')

def main():
    for account in (1,2):
        if state(account).get('name')!=f'VirgosQA{account}':raise RuntimeError('Requires two authenticated QA clients')
        server(f'advancement grant VirgosQA{account} only virgos:explorador')
        server(f'advancement revoke VirgosQA{account} only virgos:resonancia')
    server('time set 6000');server('weather clear');position()
    run=join_and_start()
    record('two-distinct-players-start',set(journal()['activeRun']['participants'])==set(IDS.values()),run=run)
    for wave in range(1,4):
        position()
        current=charge();record(f'round-{wave}-seals',True,status=current)
        screenshot(2,f'qa-expedition-round-{wave}')
        selector='@e[nbt={ForgeData:{virgos_encounter:"'+run+'"}}]'
        offset=len(log())
        server(f'execute as {selector} run damage @s 10000 minecraft:player_attack by VirgosQA2')
        time.sleep(2)
        current=status()
        record(f'round-{wave}-simulated-kills',('/SEALS' in current if wave<3 else 'expedición=libre' in current),status=current,console=log()[offset:][-2500:])
    wait(lambda:journal()['lastResult'].get('result')=='complete')
    server('save-all flush');time.sleep(3)
    for account in (1,2):
        data=json.loads((LAB/f'virgos_world/advancements/{IDS[account]}.json').read_text('utf-8'))
        record(f'personal-recognition-{account}',data.get('virgos:resonancia',{}).get('done') is True)
    record('award-ledger-drained',not journal()['pendingAwards'],journal=journal())
    # The following attempt must not grant recognition when one participant logs out.
    for account in (1,2):server(f'advancement revoke VirgosQA{account} only virgos:resonancia')
    position();join_and_start()
    action(1,{'action':'command','value':'logout'})
    wait(lambda:'activeRun' not in journal(),timeout=25)
    record('logout-cancels-without-awards',journal()['lastResult'].get('result')!='complete' and not journal()['pendingAwards'],journal=journal())
    print('PASS: two-player seals, individual awards and logout cancellation. Combat was simulated.',flush=True)

if __name__=='__main__':main()
