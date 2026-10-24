"""Cast real Iron scrolls with the localhost Forge client, without OP."""
from pathlib import Path
import json
import re
import runpy
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
h=runpy.run_path(str(ROOT/'scripts/qa-spawn.py'))
state,server,client,wait_for=(h[k] for k in ['state','server','client','wait_for'])
REPORT=ROOT/'.lab/reports/qa-magic-progression.json'
log=ROOT/'.lab/server/console.log'
report=[]

def action(command):
    line=client(command);wait_for(lambda s:s.get('line',0)>=line);time.sleep(.5)

def status():
    old=len(log.read_text('utf-8',errors='replace'))
    server('virgos status')
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        text=log.read_text('utf-8',errors='replace')[old:]
        m=re.search(r'Iron=(\d+) permitidos/(\d+) bloqueados; Ars=(\d+) permitidos/(\d+) bloqueados',text)
        if m:return dict(zip(['ironAllowed','ironBlocked','arsAllowed','arsBlocked'],map(int,m.groups())))
        time.sleep(.2)
    raise RuntimeError('No live progression status')

def scroll(level):
    nbt='{\"irons_spellbooks:spell_container\":{maxSpells:1,spellWheel:0b,mustEquip:0b,data:[{id:"irons_spellbooks:firebolt",index:0,level:'+str(level)+'}]}}'
    server('item replace entity VirgosQA2 hotbar.4 with irons_spellbooks:scroll'+nbt)
    time.sleep(1)

def attempt(name,expect,hold_ticks=60):
    before=status()
    action({'action':'hold','name':'key.use','ticks':hold_ticks})
    time.sleep(4)
    after=status()
    screenshot=client({'action':'screenshot'})
    source=ROOT/f'client/standard/screenshots/virgos-qa-{screenshot}.png'
    deadline=time.monotonic()+10
    while not source.exists() and time.monotonic()<deadline:time.sleep(.2)
    shutil.copy2(source,ROOT/f'.lab/reports/qa-magic-{name}.png')
    result={'case':name,'before':before,'after':after,'client':state()}
    result['passed']=after[expect]>before[expect]
    report.append(result);REPORT.write_text(json.dumps(report,indent=2),'utf-8')
    print(name,'PASS' if result['passed'] else 'FAIL',flush=True)
    if not result['passed']:raise RuntimeError('Inspect the spell screenshot and counters')

def main():
    if state().get('name')!='VirgosQA2':raise RuntimeError('Requires the QA2 client')
    action({'action':'close'})
    server('tp VirgosQA2 962.5 83 738.5 180 -35')
    server('gamemode survival VirgosQA2')
    for id in ['explorador','especialista','maestro','resonancia','forja','umbral']:
        server('advancement revoke VirgosQA2 only virgos:'+id)
    time.sleep(2)
    action({'action':'key','name':'key.hotbar.5'})
    scroll(1);attempt('iron-basic','ironAllowed')
    scroll(10);attempt('iron-gifted-locked','ironBlocked')
    for id in ['explorador','especialista','maestro','resonancia','forja','umbral']:
        server('advancement grant VirgosQA2 only virgos:'+id)
    time.sleep(1)
    attempt('iron-recognized','ironAllowed')
    for id in ['explorador','especialista','maestro','resonancia','forja','umbral']:
        server('advancement revoke VirgosQA2 only virgos:'+id)
    server('item replace entity VirgosQA2 hotbar.4 with minecraft:air')
    server('tp VirgosQA2 672.5 115 752.5 180 0')
    print('PASS: real scroll casts respect personal progression; QA grants/items removed.')

if __name__=='__main__':main()
