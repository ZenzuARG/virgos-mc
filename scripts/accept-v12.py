"""Record candidate checks before any production mutation."""
from pathlib import Path
import json,hashlib,tomllib
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf-8-sig'))
p=read('.lab/reports/v12-preliminary.json');buyer=read('.lab/reports/v12-buyer.json');recipes=read('.lab/reports/recipe-sync-v1.json')
assert buyer['passed'] and all(c['passed'] for c in buyer['cases'])
assert recipes['passed'] and p['bountyDelivery']['passed'] and all(p[k] for k in ['npcGuides','menuIconsProtected','barterStockPersistedAcrossRestart','emptyStockRefusesPayment','marketBreakProtected','npcAfterRestart','spanishMarketUI'])
a=read('.lab/server/virgos-reports/mercado-v12-audit.json');assert a['checked']==9584 and all(not a[k] for k in ['missing','wrongBlocks','unsupported','routeProblems','blockedWalkChecks'])
old=list((R/'config/heracles/quests').glob('*.json'));assert len(old)==154
assert all(json.loads(f.read_text('utf-8'))==read('pack/server-overrides/config/heracles/quests/'+f.name) for f in old)
assert len(list((R/'pack/server-overrides/config/heracles/quests').glob('*.json')))==186
for name in ['installer-v3-unit.json','tlauncher-settings-v4.json']:assert read('.lab/reports/'+name)['passed']
for rel in ['virgos_world/serverconfig/openpartiesandclaims-server.toml','defaultconfigs/openpartiesandclaims-server.toml']:
 left=tomllib.loads((R/rel).read_text('utf-8'));right=tomllib.loads((R/'.lab/v12/overrides'/rel).read_text('utf-8'))
 def diff(a,b,path=''):
  result=[]
  for k in a.keys()|b.keys():
   if isinstance(a.get(k),dict) and isinstance(b.get(k),dict):result.extend(diff(a[k],b[k],path+k+'.'))
   elif a.get(k)!=b.get(k):result.append(path+k)
  return result
 changed=diff(left,right);assert all(k.split('.')[-1] in ['forcedBlockProtectionExceptionList','forcedEntityProtectionExceptionList','itemUseProtectionExceptionList'] for k in changed),changed
jar=R/'dev/virgos-core/build/libs/virgos_core-1.2.0.jar'
record={'passed':True,'version':'1.2.0','coreSha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'originalQuestsPreserved':154,'quests':186,'chapters':26,
 'preliminary':p,'buyer':buyer,'recipes':recipes,'marketAudit':a,'npcEvidence':['v12-npc-fixed-page1.png','v12-npc-fixed-page2.png','v12-npc-fixed-page3.png','v12-npc-after-restart.png'],
 'scope':'Real sequential offline Forge clients in isolated lab; current core built with check/build; construction visually inspected.',
 'limits':['No eight-player load or real microphone audio test.','Discord awaits user login.','A first post-boot lab handshake timed out; reconnect succeeded.','Ketting baseline dimension and optional mixin warnings remain.']}
(R/'.lab/reports/v12-acceptance.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
print('Candidate acceptance recorded; public QA still required.')
