"""Cook and collect one rice portion at the public inn, with no OP."""
from pathlib import Path
import json
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(ROOT/'scripts/qa-spawn.py'))
state,server,client,wait_for=[helpers[key] for key in ('state','server','client','wait_for')]
if state().get('name')!='VirgosQA2':raise SystemExit('This test requires VirgosQA2.')
if (state().get('width'),state().get('height'))!=(640,360):raise SystemExit('Inspect the GUI before using this recorded layout.')
client({'action':'close'});client({'action':'key','name':'key.hotbar.4'})
server('gamemode survival VirgosQA2');server('tp VirgosQA2 618.5 115 787.5 0 0')
wait_for(lambda s:abs(s.get('x',0)-618.5)<.1 and abs(s.get('z',0)-787.5)<.1)
client({'action':'use'})
wait_for(lambda s:s.get('screen','').endswith('CookingPotScreen'))
server('give VirgosQA2 farmersdelight:rice 1');server('give VirgosQA2 minecraft:bowl 1')
initial=wait_for(lambda s:'farmersdelight:rice x1' in s.get('inventory',[]) and 'minecraft:bowl x1' in s.get('inventory',[]))
if initial['inventory'][:5]!=['alexsmobs:animal_dictionary x1','ars_nouveau:worn_notebook x1','minecraft:bread x8','farmersdelight:rice x1','minecraft:bowl x1']:
    raise SystemExit('Inventory changed; inspect slots before continuing.')
for x,y in [(302,246),(270,122),(320,246),(332,160)]:client({'action':'click','x':x,'y':y})
time.sleep(9)
client({'action':'screenshot'})
client({'action':'click','x':364,'y':160})
client({'action':'click','x':338,'y':246})
result=wait_for(lambda s:'farmersdelight:cooked_rice x1' in s.get('inventory',[]))
(ROOT/'.lab/reports/qa-public-cooked-recipe.json').write_text(json.dumps(result,indent=2),'utf-8')
client({'action':'close'})
print('PASS: public pot cooked and delivered one rice portion to the non-OP player.')
