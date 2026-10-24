"""Exercise one temporary private claim through the local Forge test client.

The platform/chest must already exist at the coordinates below. The positive
owner case uses exactly the same aim as the foreign-player case.
"""
from pathlib import Path
import json
import runpy
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(ROOT/'scripts/qa-spawn.py'))
state,server,client,wait_for=(helpers[k] for k in ['state','server','client','wait_for'])
REPORT=ROOT/'.lab/reports/qa-private-claims.json'
result={}

def action(value):
    line=client(value)
    wait_for(lambda s:s.get('line',0)>=line)
    time.sleep(.7)
    return state()

def capture(label):
    line=client({'action':'screenshot'})
    source=ROOT/f'client/standard/screenshots/virgos-qa-{line}.png'
    deadline=time.monotonic()+15
    while not source.exists() and time.monotonic()<deadline:time.sleep(.2)
    target=ROOT/f'.lab/reports/qa-claim-{label}.png'
    shutil.copy2(source,target)
    return str(target.relative_to(ROOT))

def save():REPORT.write_text(json.dumps(result,indent=2),'utf-8')

def main():
    wait_for(lambda s:s.get('name')=='VirgosQA2',timeout=120)
    action({'action':'close'})
    server('tp VirgosQA2 962.5 251 738.5 180 20')
    wait_for(lambda s:abs(s.get('x',0)-962.5)<.05 and abs(s.get('y',0)-251)<.05)
    action({'action':'key','name':'key.hotbar.5'})
    result['foreignUse']=action({'action':'use'})
    result['foreignScreenshot']=capture('foreign')
    if result['foreignUse']['screen']!='game':save();raise RuntimeError('Foreign chest opened')
    action({'action':'attack'})
    log=ROOT/'.lab/server/console.log'
    previous=len(log.read_text('utf-8',errors='replace'))
    marker='QA_PRIVATE_CHEST_INTACT_20261017'
    server('execute if block 962 251 736 minecraft:chest run say '+marker)
    time.sleep(2)
    result['foreignBreakDenied']=marker in log.read_text('utf-8',errors='replace')[previous:]
    if not result['foreignBreakDenied']:save();raise RuntimeError('Private chest disappeared')
    server('oclaims player unclaim as VirgosQA1 in minecraft:overworld 960 736 960 736 anyway')
    time.sleep(2)
    action({'action':'command','value':'oclaims claim'})
    result['claimScreenshot']=capture('owner-claimed')
    result['ownerUse']=action({'action':'use'})
    result['ownerScreenshot']=capture('owner-chest')
    if not result['ownerUse']['screen'].endswith('ContainerScreen'):save();raise RuntimeError('Owner chest did not open')
    action({'action':'close'})
    action({'action':'command','value':'oclaims unclaim'})
    result['passed']=True
    save()
    # Remove only the objects placed by this test, before unloading its chunk.
    server('setblock 962 251 736 minecraft:air')
    server('fill 960 250 736 964 250 740 minecraft:air replace minecraft:glass')
    server('tp VirgosQA2 672.5 115 752.5 180 0')
    server('gamemode survival VirgosQA2')
    print('PASS: private chest denied to visitor; same chest opens for its owner; temporary setup removed.')

if __name__=='__main__':main()
