"""Build only the accepted additive market in the stopped-and-backed-up production world."""
from pathlib import Path
import json,time,uuid
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf-8-sig'))
def wait(test,seconds=420):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if test():return
  time.sleep(1)
 raise RuntimeError('Timed out; inspect public-console.log')
def log():return (R/'.runtime/public-console.log').read_text('utf-8',errors='replace')
def command(value):
 with (R/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write(value+'\n')
p=read('.lab/reports/v12-promotion.json');assert p['servicesConstructionPending']
wait(lambda:'Virgos: AuthMe bridge ready' in log() and 'Voice chat server started' in log())
command('virgos build mercado-v12')
state=R/'virgos_world/virgos-build-mercado-v12-state.json'
wait(lambda:state.exists() and read(state)['complete'])
assert read(state)['index']==9584
command('virgos servicios instalar')
time.sleep(2)
for key in ['guia','mercado','encargos','cronista']:
 identifier=uuid.uuid5(uuid.NAMESPACE_URL,'virgos-mc/services/'+key)
 command(f'execute if entity {identifier} run say V12_NPC_OK_{key}')
wait(lambda:all('V12_NPC_OK_'+k in log() for k in ['guia','mercado','encargos','cronista']),30)
command('virgos audit mercado-v12')
audit=R/'virgos-reports/mercado-v12-audit.json';wait(lambda:audit.exists(),30)
a=read(audit);assert a['checked']==9584 and all(not a[k] for k in ['missing','wrongBlocks','unsupported','blockedWalkChecks','routeProblems']),a
assert not (R/'virgos_world/virgos-market.json').exists()
command('save-all flush');time.sleep(3)
p['servicesConstructionPending']=False;p['marketBlueprintSha256']=read(state)['blueprintSha256'];p['npcCount']=4
(R/'.lab/reports/v12-promotion.json').write_text(json.dumps(p,indent=2)+'\n','utf-8')
print('Public market built and audited; four NPCs present, all eight stalls unreserved.',flush=True)
