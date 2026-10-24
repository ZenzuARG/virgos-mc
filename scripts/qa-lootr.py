"""Inspect one physical Lootr chest using two authenticated, isolated clients."""
from pathlib import Path
import importlib.util,json,time,runpy,uuid,sys,struct
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.REPORT=ROOT/'.lab/reports/qa-lootr-v03.json'
q.SCOPE='Two authenticated Forge clients open one physical Lootr chest; taking loot preserves the other inventory.'
read_nbt=runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt']

def save():
    marker='QA_LOOTR_'+uuid.uuid4().hex;q.server('save-all flush');q.server('say '+marker);q.wait(lambda:marker in q.log(),90)

def open_chest(a):
    other=3-a;q.action(other,{'action':'close'});q.server(f'tp VirgosQA{other} 902.5 121 904.5')
    q.wait(lambda:abs(q.state(other).get('x',0)-902.5)<.1,60)
    q.action(a,{'action':'close'});q.server(f'gamemode survival VirgosQA{a}')
    q.server(f'tp VirgosQA{a} 900.5 121 900.5 0 30');q.server(f'item replace entity VirgosQA{a} hotbar.4 with minecraft:air')
    q.wait(lambda:abs(q.state(a).get('x',0)-900.5)<.1,60)
    q.action(a,{'action':'key','name':'key.hotbar.5'});q.action(a,{'action':'use'})
    q.wait(lambda:q.state(a).get('screen','').endswith('ContainerScreen') and q.state(a).get('screenTitle')=='Cofre',30)

def main():
    q.server('forceload add 900 900');time.sleep(4)
    q.server('fill 898 120 898 903 120 905 minecraft:stone');q.server('fill 898 121 898 903 124 905 minecraft:air')
    q.server('setblock 900 121 902 lootr:lootr_chest[facing=north]{LootTable:"minecraft:chests/simple_dungeon"}')
    for a in (1,2):
        open_chest(a);q.screenshot(a,f'v03-lootr-player-{a}');q.action(a,{'action':'close'})
        q.server(f'tp VirgosQA{a} 902.5 121 904.5')
    save()
    paths=[p for p in (q.LAB/'virgos_world').rglob('*') if p.is_file() and 'lootr' in p.as_posix().lower()]
    records={p.relative_to(q.LAB).as_posix():read_nbt(p) for p in paths if p.suffix in ['.dat','.nbt']}
    (ROOT/'.lab/reports/lootr-data-v03.json').write_text(json.dumps(records,indent=2),'utf-8')
    print('Both clients opened the same physical chest; inspect individual persisted inventories:',list(records),flush=True)
    q.server('forceload remove 900 900')

def consume():
    data=json.loads((ROOT/'.lab/reports/lootr-data-v03.json').read_text('utf-8'))
    current=[(name,entry['']['data']) for name,entry in data.items() if len(entry['']['data'].get('inventories',[]))==2]
    assert len(current)==1
    name,before=current[0]
    def inventories(record):return {str(uuid.UUID(bytes=struct.pack('>4i',*i['uuid']))):i['chest']['Items'] for i in record['inventories']}
    old=inventories(before)
    taken=next(i for i in old[q.IDS[1]] if i['Slot']==0)
    def inventory_amount():return sum(int(i.rsplit(' x',1)[1]) for i in q.state(1).get('inventory',[]) if i.rsplit(' x',1)[0]==taken['id'])
    amount_before=inventory_amount()
    q.record('one-physical-chest-two-personal-inventories',set(old)=={q.IDS[1],q.IDS[2]} and all(old.values()),container=name)
    open_chest(1)
    q.action(1,{'action':'click','x':248,'y':124});q.action(1,{'action':'click','x':392,'y':247});q.action(1,{'action':'close'})
    save();after=inventories(read_nbt(q.LAB/name)['']['data'])
    q.record('taking-player-one-loot-preserves-player-two',after[q.IDS[2]]==old[q.IDS[2]] and len(after[q.IDS[1]])==len(old[q.IDS[1]])-1 and not any(i['Slot']==0 for i in after[q.IDS[1]]))
    q.record('loot-reached-own-inventory',inventory_amount()==amount_before+taken['Count'])

if __name__=='__main__':
    if '--consume' in sys.argv:consume()
    else:main()
