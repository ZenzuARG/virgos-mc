"""Read saved probe chunks; no changes to the running world."""
from pathlib import Path
import collections,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2';read=runpy.run_path(str(R/'scripts/inspect-nbt.py'))['read_nbt']
class Bytes:
    def __init__(self,value):self.value=value
    def read_bytes(self):return self.value
tests=json.loads((V/'worldgen-tests.json').read_text('utf-8'))['tests'];out=[]
for test in tests:
    if not test.get('generated') or test['dimension']!='minecraft:overworld':continue
    cx,cz=test['x']//16,test['z']//16;blocks=collections.Counter();chests=[];structures=set()
    for x in range(cx-1,cx+2):
        for z in range(cz-1,cz+2):
            file=V/f'server/virgos_world/region/r.{x//32}.{z//32}.mca'
            if not file.exists():continue
            b=file.read_bytes();i=4*((x%32)+(z%32)*32);offset=int.from_bytes(b[i:i+3],'big')*4096
            if not offset:continue
            length=int.from_bytes(b[offset:offset+4],'big');compression=b[offset+4];assert compression==2,compression
            n=read(Bytes(zlib.decompress(b[offset+5:offset+4+length])))['']
            structures.update(n.get('structures',{}).get('starts',{}))
            for section in n.get('sections',[]):
                for entry in section.get('block_states',{}).get('palette',[]):blocks[entry['Name'].split(':')[0]]+=1
            for e in n.get('block_entities',[]):
                if 'lootr' in e.get('id','') or e.get('LootTable'):
                    chests.append({k:e[k] for k in ['id','x','y','z','LootTable'] if k in e})
    out.append({'id':test['id'],'paletteReferencesByMod':dict(blocks),'lootContainers':chests,'structureStarts':sorted(structures)})
(V/'generated-content.json').write_text(json.dumps(out,indent=2),'utf-8')
print(json.dumps([{'id':r['id'],'createPaletteEntries':r['paletteReferencesByMod'].get('create',0),'lootContainers':len(r['lootContainers']),'lootr':sum('lootr' in c['id'] for c in r['lootContainers'])} for r in out],indent=2))
