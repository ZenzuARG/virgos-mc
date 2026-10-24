"""Write a lab-only block patch between blueprints with identical terrain fills."""
from pathlib import Path
import argparse,gzip,json
p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parents[1];target=args.output.resolve()
assert target.is_relative_to(root/'.lab/server/config/virgos')
with gzip.open(args.before,'rt',encoding='utf-8') as f:a=json.load(f)
with gzip.open(args.after,'rt',encoding='utf-8') as f:b=json.load(f)
def fills(d):return [(*v[:6],d['palette'][v[6]]) for v in d['fills']]
assert fills(a)==fills(b),'Terrain changes need a full build'
old={tuple(v[:3]):a['palette'][v[3]] for v in a['blocks']};new={tuple(v[:3]):b['palette'][v[3]] for v in b['blocks']}
patch=dict(b);patch['fills']=[]
patch['blocks']=[[*p,b['palette'].index(new.get(p,'minecraft:air'))] for p in old.keys()|new.keys() if old.get(p,'minecraft:air')!=new.get(p,'minecraft:air')]
patch['blocks'].sort(key=lambda b:(b[1],b[2],b[0]))
with gzip.open(target,'wt',encoding='utf-8') as f:json.dump(patch,f)
print('Lab patch:',len(patch['blocks']),'blocks')
