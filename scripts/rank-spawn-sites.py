"""Rank inland sites with a 192-block footprint from the real generator survey."""
from pathlib import Path
import json
import math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'.lab/server/virgos-reports/survey.json').read_text('utf-8'))
grid={(p[0],p[1]):(p[2]-1,p[3]) for p in data['terrain']}
step=data['step']
xs=sorted({p[0] for p in grid}); zs=sorted({p[1] for p in grid})
wet=('ocean','river','swamp','beach','marsh','fen','bog')
candidates=[]
for x in xs:
    for z in zs:
        if min(x-xs[0],xs[-1]-x,z-zs[0],zs[-1]-z)<224: continue
        points=[grid[x+dx,z+dz] for dx in range(-96,97,step) for dz in range(-96,97,step)]
        if any(h<65 or any(w in biome for w in wet) for h,biome in points): continue
        heights=[p[0] for p in points]
        average=sum(heights)/len(heights)
        deviation=math.sqrt(sum((h-average)**2 for h in heights)/len(heights))
        spread=max(heights)-min(heights)
        if spread>24 or average>120: continue
        openness=sum(any(b in biome for b in ('plains','prairie','grassland','meadow','shrubland')) for h,biome in points)/len(points)
        score=deviation*3+spread*.4+(1-openness)*5+math.hypot(x,z)/10000
        candidates.append({'x':x,'z':z,'y':round(average),'range':spread,'stddev':round(deviation,2),'open':round(openness,2),'score':round(score,2),'biome':grid[x,z][1]})
selected=[]
for candidate in sorted(candidates,key=lambda c:c['score']):
    if all(math.hypot(candidate['x']-s['x'],candidate['z']-s['z'])>300 for s in selected): selected.append(candidate)
    if len(selected)==20:break
folder=ROOT/'.lab/reports';folder.mkdir(exist_ok=True,parents=True)
(folder/'spawn-sites.json').write_text(json.dumps(selected,indent=2),'utf-8')
im=Image.new('RGB',(len(xs)*6,len(zs)*6)); draw=ImageDraw.Draw(im)
for (x,z),(height,biome) in grid.items():
    color=(35,80,135) if height<64 or any(w in biome for w in wet) else (min(220,70+height),min(210,95+height//2),min(180,40+height//2))
    px=(x-xs[0])//step*6;pz=(z-zs[0])//step*6
    draw.rectangle((px,pz,px+5,pz+5),fill=color)
for i,candidate in enumerate(selected):
    x=(candidate['x']-xs[0])//step*6+3;z=(candidate['z']-zs[0])//step*6+3
    draw.rectangle((x-18,z-18,x+18,z+18),outline='white',width=2)
    draw.text((x+20,z-6),str(i+1),fill='white',stroke_width=1,stroke_fill='black')
im.save(folder/'spawn-sites.png')
print(json.dumps(selected[:8],indent=2))
