"""Generate the v1.2 audit reference from the approved town and market designs.

Does not modify Minecraft blocks or copy observed world data into expectations.
The market's deliberate clearances and floor replace overlapping v1.1 blocks.
"""
from pathlib import Path
import gzip,json,hashlib
r=Path(__file__).resolve().parents[1]
parents=['pueblo-v11-final','mercado-v12']
palette=[];positions={};walk=[];routes=[];sources=[]
for name in parents:
    p=r/f'config/virgos/{name}.blocks.json.gz'
    raw=p.read_bytes();d=json.loads(gzip.decompress(raw))
    sources.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'blocks':len(d['blocks'])})
    for x,y,z,index in d['blocks']:
        state=d['palette'][index]
        if state not in palette:palette.append(state)
        positions[(x,y,z)]=palette.index(state)
    walk.extend(d.get('walkChecks',[]));routes.extend(d.get('routes',[]))
out={'schema':2,'name':'Referencia de auditoria: pueblo y mercado 1.2','palette':palette,
     'blocks':[[*point,index] for point,index in sorted(positions.items())],
     'walkChecks':walk,'routes':routes,'sources':sources}
raw=gzip.compress(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode(),mtime=0)
for folder in ['config/virgos','pack/server-overrides/config/virgos']:
    (r/folder/'auditoria-pueblo-v12.blocks.json.gz').write_bytes(raw)
print(json.dumps({'blocks':len(positions),'sources':sources,'worldModified':False}))
