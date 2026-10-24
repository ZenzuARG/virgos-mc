"""Actual Ars projectile across a claim boundary, with an unclaimed control."""
from pathlib import Path
import json
import runpy
import time
ROOT=Path(__file__).resolve().parents[1]
q=runpy.run_path(str(ROOT/'scripts/qa-expeditions.py'))
server,action,state,wait=(q[k] for k in ['server','action','state','wait'])
report={}

def present():
    offset=len(q['log']())
    server('execute if block 961 92 738 minecraft:oak_planks')
    text=wait(lambda:q['log']()[offset:] if 'Test ' in q['log']()[offset:] else None)
    return 'Test passed' in text

def fire():
    action(2,{'action':'hold','name':'key.use','ticks':1})
    time.sleep(3)
    return present()

def main():
    if state(2).get('name')!='VirgosQA2':raise RuntimeError('Requires QA2')
    if state(2).get('health',0)<=0:raise RuntimeError('Respawn QA2 first')
    server('forceload add 956 736 964 740')
    time.sleep(3)
    server('oclaims player unclaim as VirgosQA1 in minecraft:overworld 960 736 960 736 anyway')
    server('fill 956 90 736 964 90 740 minecraft:glass')
    server('setblock 961 92 738 minecraft:oak_planks')
    server('gamemode survival VirgosQA2')
    server('tp VirgosQA2 958.5 91 738.5 -90 2.3')
    book='{"ars_nouveau:caster":{current_slot:0,spell_count:1,spells:{spell0:{name:"Prueba local",recipe:{size:2,part0:"ars_nouveau:glyph_projectile",part1:"ars_nouveau:glyph_break"}}}}}'
    server('item replace entity VirgosQA2 hotbar.4 with ars_nouveau:archmage_spell_book'+book)
    wait(lambda:abs(state(2).get('x',0)-958.5)<.1)
    action(2,{'action':'close'});action(2,{'action':'key','name':'key.hotbar.5'})
    try:
        report['unclaimedControlBreaks']=not fire()
        if not report['unclaimedControlBreaks']:raise RuntimeError('Control spell did not break target')
        server('setblock 961 92 738 minecraft:oak_planks')
        server('oclaims player claim as VirgosQA1 in minecraft:overworld 960 736 960 736 anyway')
        time.sleep(2)
        report['foreignClaimStopsProjectile']=fire()
        if not report['foreignClaimStopsProjectile']:raise RuntimeError('Projectile bypassed private claim')
        # An ordinary piston outside the claim may not push an owned block.
        server('setblock 960 92 738 minecraft:stone')
        server('setblock 959 92 738 minecraft:piston[facing=east]')
        server('setblock 958 92 738 minecraft:redstone_block')
        time.sleep(2)
        offset=len(q['log']())
        server('execute if block 960 92 738 minecraft:stone')
        time.sleep(1)
        report['pistonBoundaryBlocked']='Test passed' in q['log']()[offset:]
        if not report['pistonBoundaryBlocked']:raise RuntimeError('Piston moved owned block')
        report['passed']=True
        print('PASS: unclaimed spell works, private claim blocks the same spell and boundary piston.',flush=True)
    finally:
        (ROOT/'.lab/reports/qa-claim-boundary.json').write_text(json.dumps(report,indent=2),'utf-8')
        server('oclaims player unclaim as VirgosQA1 in minecraft:overworld 960 736 960 736 anyway')
        for x in range(958,963):server(f'setblock {x} 92 738 minecraft:air')
        server('fill 956 90 736 964 90 740 minecraft:air replace minecraft:glass')
        server('item replace entity VirgosQA2 hotbar.4 with minecraft:air')
        server('tp VirgosQA2 672.5 115 752.5 180 0')
        server('forceload remove 956 736 964 740')

if __name__=='__main__':main()
