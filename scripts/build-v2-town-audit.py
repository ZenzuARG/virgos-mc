"""Audit the final composition, including the market's deliberate replacements."""
from pathlib import Path
import gzip,json,hashlib
ROOT=Path(__file__).resolve().parents[1];V2=ROOT/'.lab/v2';palette=[];blocks={};routes=[];checks=[]
for name in ['pueblo-v2','mercado-v2','arena-virgos-v3']:
    data=json.loads(gzip.decompress((V2/'server/config/virgos'/f'{name}.blocks.json.gz').read_bytes()))
    for x,y,z,index in data['blocks']:
        state=data['palette'][index]
        if state not in palette:palette.append(state)
        blocks[x,y,z]=palette.index(state)
    routes+=data.get('routes',[]);checks+=data.get('walkChecks',[])
out={'schema':2,'auditOnly':True,'name':'Pueblo v2 completo: plaza, mercado y anfiteatro','palette':palette,'blocks':[[*p,i] for p,i in blocks.items()],'routes':routes,'walkChecks':checks,'fills':[],'blockEntities':[]}
blob=gzip.compress(json.dumps(out,ensure_ascii=False).encode('utf-8'),mtime=0)
for folder in [V2/'server/config/virgos',V2/'server-overrides/config/virgos']:(folder/'auditoria-pueblo-v2.blocks.json.gz').write_bytes(blob)
print('Final town audit:',len(blocks),'blocks,',len(routes),'routes; sha256',hashlib.sha256(blob).hexdigest())
