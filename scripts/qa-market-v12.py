"""Real client buyer on the isolated lab; fixtures belong only to QA identities."""
from pathlib import Path
import importlib,json,sys,time
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'));q=importlib.import_module('qa-expeditions')
out=R/'.lab/reports/v12-buyer.json';report={'passed':False,'cases':[]}
def record(name,passed,**detail):
 report['cases'].append({'case':name,'passed':bool(passed),**detail});out.write_text(json.dumps(report,indent=2),'utf-8')
 print(name,'PASS' if passed else 'FAIL',flush=True)
 assert passed,name
def click(x,y):q.action(2,{'action':'click','x':x,'y':y});time.sleep(.6)
def inventory():
 q.action(2,{'action':'slots'});return json.loads((R/'client/standard/virgos-qa/slots.json').read_text())
if '--joined' not in sys.argv:
 q.wait(lambda:'TitleScreen' in q.state(2).get('screen',''),timeout=420)
 q.wait(lambda:'Virgos: AuthMe bridge ready' in q.log(),timeout=420)
 q.action(2,{'action':'connect'})
q.wait(lambda:q.state(2).get('name')=='VirgosQA1',timeout=180)
q.action(2,{'action':'command','value':'virgos menu'});time.sleep(1)
record('menu-blocked-before-auth',q.state(2)['screen']=='game')
secret=json.loads((R/'.cache/qa-account.json').read_text())
q.action(2,{'action':'command','value':'login '+secret['password']})
q.wait(lambda:'VirgosQA1 logged in' in q.log(),timeout=45)
q.server('deop VirgosQA1');q.server('gamemode survival VirgosQA1');q.server('clear VirgosQA1');q.server('give VirgosQA1 minecraft:wheat 12')
q.server('tp VirgosQA1 604.5 115 782.5 180 20');time.sleep(2)
q.action(2,{'action':'command','value':'virgos mercado reservar 1'});time.sleep(1)
ledger=json.loads((R/'.lab/server/virgos_world/virgos-market.json').read_text())
record('other-owner-reservation-refused','13e2e728-2a7a-36a6-84ee-5c289cf4cc02' not in ledger)
q.action(2,{'action':'key','name':'key.hotbar.5'});q.action(2,{'action':'use'});time.sleep(1)
record('buyer-opens-trading-screen','TraderScreen' in q.state(2)['screen'])
click(433,71)
record('buyer-cannot-open-owner-storage','TraderStorageScreen' not in q.state(2)['screen'])
q.action(2,{'action':'close'});q.action(2,{'action':'use'});time.sleep(1)
q.screenshot(2,'v12-buyer-before');click(320,88)
q.wait(lambda:any('sophisticatedbackpacks:backpack' in x for x in q.state(2).get('inventory',[])))
slots=inventory();items=[v['item'] for v in slots['slots']]
record('buyer-receives-modded-nbt',any('virgos_qa:"keep"' in x and 'QA bolsa' in x for x in items),items=[x for x in items if 'backpack' in x])
record('payment-consumed',not any('minecraft:wheat' in x for x in q.state(2)['inventory']))
q.server('give VirgosQA1 minecraft:wheat 12');time.sleep(1);click(320,88)
record('second-buyer-purchase-refused-without-stock','minecraft:wheat x12' in q.state(2)['inventory'] and sum('backpack x1' in x for x in q.state(2)['inventory'])==1)
q.action(2,{'action':'close'});q.server('tp VirgosQA1 612.5 115 782.5 180 20');time.sleep(1)
q.action(2,{'action':'command','value':'virgos mercado reservar 2'});time.sleep(1)
ledger=json.loads((R/'.lab/server/virgos_world/virgos-market.json').read_text())
record('new-owner-reserves-free-stall',ledger.get(q.state(2)['uuid'])==2)
q.action(2,{'action':'use'});time.sleep(1);click(433,71);click(320,88);q.screenshot(2,'v12-default-barter')
q.action(2,{'action':'close'});q.action(2,{'action':'key','name':'key.heracles.open_quests'});time.sleep(1);q.screenshot(2,'v12-quests-expanded');q.action(2,{'action':'close'})
q.server('virgos audit mercado-v12');q.server('save-all flush')
report['passed']=True;out.write_text(json.dumps(report,indent=2),'utf-8')
print('Buyer tests complete. Inspect default barter screenshot separately.',flush=True)
