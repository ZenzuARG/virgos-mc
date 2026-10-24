"""An original physical amphitheatre reached by the Bastion's south road.

Consumes the local surveyed heights; no regeneration runs automatically.
"""
from pathlib import Path
import gzip
import json
import math
import argparse

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--candidate-v2',action='store_true');options=parser.parse_args()
survey=json.loads((ROOT/('.lab/v2/terrain-arena.json' if options.candidate_v2 else '.lab/reports/survey-arena.json')).read_text('utf-8'))
if (survey['centerX'],survey['centerZ'],survey['radius'],survey['step'])!=(672,1040,64,8):
    raise SystemExit('Requires the 672,1040 radius64 step8 survey.')
# The approach starts north of this survey. The earlier Bastion survey covers it.
older=json.loads((ROOT/('.lab/v2/terrain-second.json' if options.candidate_v2 else '.lab/reports/survey-bastion.json')).read_text('utf-8'))
survey_points=survey['terrain']+older['terrain']
CX,CZ,Y=672,1048,78
VERSION='arena-virgos-v3'
palette=[];lookup={};blocks={};fills=[];entities=[]

def pal(name):
    if ':' not in name:name='minecraft:'+name
    if name not in lookup:lookup[name]=len(palette);palette.append(name)
    return lookup[name]

def block(x,y,z,name):blocks[(x,y,z)]=pal(name)
def fill(x1,y1,z1,x2,y2,z2,name):
    if x1>x2 or y1>y2 or z1>z2:raise ValueError('Invalid arena fill')
    fills.append([x1,y1,z1,x2,y2,z2,pal(name)])

def ground(x,z):
    # Nearest survey point is sufficient for buried supports; walking surfaces
    # have an explicit profile independent of interpolation noise.
    nearest=min(survey_points,key=lambda p:(p[0]-x)**2+(p[1]-z)**2)
    if (nearest[0]-x)**2+(nearest[1]-z)**2>128:raise ValueError('Road outside surveys')
    return nearest[2]-1

for x in range(CX-32,CX+33):
    for z in range(CZ-32,CZ+33):
        r=math.hypot(x-CX,z-CZ)
        if r>31:continue
        g=ground(x,z)
        if g<Y:fill(x,g-3,z,x,Y-1,z,'stone')
        fill(x,Y+1,z,x,319,z,'air')
        floor='polished_deepslate' if r<18 else 'stone_bricks'
        if 18<=r<19 or 27<=r<28:floor='chiseled_stone_bricks'
        if r<6:floor='smooth_quartz' if (x+z)%2 else 'calcite'
        block(x,Y,z,floor)
        if 28<=r<=31 and not (abs(x-CX)<=4 and z<CZ):
            # Low circular seating/wall follows the terrain rather than a solid cube.
            top=Y+1+int(r-28)
            for y in range(Y+1,top+1):block(x,y,z,'stone_bricks')
            block(x,top,z,'mossy_stone_bricks' if (x+z)%7==0 else 'stone_bricks')

# A descending stair road joins the already-built south road at Z=916.
road=[]
for z in range(917,CZ-30):
    t=(z-916)/(CZ-31-916)
    height=78 if options.candidate_v2 else 118-round(40*t)
    previous=78 if options.candidate_v2 else 118-round(40*((z-1-916)/(CZ-31-916)))
    rising=height<previous
    surface='stone_bricks' if rising else 'gravel'
    for x in range(CX-4,CX+5):
        g=ground(x,z)
        # Surface surveys can miss small ravines/caves between sample points.
        # A continuous three-block subgrade keeps every gravel lane supported.
        fill(x,min(g-3,height-3),z,x,height-1,z,'stone')
        fill(x,height+1,z,x,319,z,'air')
        block(x,height,z,surface if abs(x-CX)<=2 else 'stone_bricks')
        if rising and abs(x-CX)<=2:
            block(x,height+1,z,'stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
    road.append([CX+.5,height+(2 if rising else 1),z+.5])
    if z%12==0:
        for x in [CX-4,CX+4]:
            block(x,height+1,z,'stone_brick_wall')
            block(x,height+2,z,'lantern[hanging=false,waterlogged=false]')

# Entrance arch, copper accents and the three clearly separated mechanisms.
entrance=CZ-30
for x in [CX-5,CX+5]:
    for z in range(entrance-1,entrance+2):
        for y in range(Y+1,Y+8):block(x,y,z,'stone_bricks')
for x in range(CX-5,CX+6):
    for z in range(entrance-1,entrance+2):
        block(x,Y+8,z,'chiseled_stone_bricks')
        block(x,Y+9,z,'waxed_oxidized_cut_copper_slab[type=bottom,waterlogged=false]')
for i,(x,z) in enumerate([(655,1048),(689,1048),(672,1031)]):
    for dx in range(-2,3):
        for dz in range(-2,3):block(x+dx,Y,z+dz,'amethyst_block' if abs(dx)+abs(dz)<3 else 'polished_deepslate')
    block(x,Y+1,z,'lodestone')
    for dx in [-2,2]:
        block(x+dx,Y+1,z,'stone_brick_wall')
        block(x+dx,Y+2,z,'lantern[hanging=false,waterlogged=false]')
    # Keep the sign out of the ray between an approaching player and the seal.
    signx,signz=x+1,z+2
    block(signx,Y+1,signz,'oak_sign[rotation=0,waterlogged=false]')
    messages=[f'SELLO {i+1}','Mano vacía','Mantené clic','con tu grupo']
    entities.append({'x':signx,'y':Y+1,'z':signz,'nbt':'{front_text:{messages:['+','.join(json.dumps(json.dumps({'text':m},ensure_ascii=False),ensure_ascii=False) for m in messages)+']},is_waxed:1b}'})

for dx,dz in [(-22,-15),(22,-15),(-22,15),(22,15)]:
    for y in range(Y+1,Y+6):block(CX+dx,y,CZ+dz,'polished_deepslate')
    block(CX+dx,Y+6,CZ+dz,'sea_lantern')
    block(CX+dx,Y+7,CZ+dz,'waxed_oxidized_cut_copper_slab[type=bottom,waterlogged=false]')

data={'name':'Anfiteatro de los Tres Sellos','seed':survey['seed'],'center':[CX,Y,CZ],
      'palette':palette,'blocks':[[*pos,value] for pos,value in sorted(blocks.items())],
      'fills':fills,'blockEntities':entities,
      'routes':[{'name':'Camino sur al anfiteatro','points':road}],
      'description':'Tres sellos físicos; llegada a pie desde la puerta sur del Bastión.'}
blob=gzip.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8'),mtime=0)
for base in (['.lab/v2/server-overrides/config/virgos','.lab/v2/server/config/virgos'] if options.candidate_v2 else ['pack/server-overrides/config/virgos','.lab/server/config/virgos']):
    folder=ROOT/base;folder.mkdir(parents=True,exist_ok=True)
    (folder/(VERSION+'.blocks.json.gz')).write_bytes(blob)
(ROOT/('.lab/v2/arena-build.json' if options.candidate_v2 else 'pack/arena-build.json')).write_text(json.dumps({'name':data['name'],'center':data['center'],'blocks':len(blocks),'fillVolume':sum((f[3]-f[0]+1)*(f[4]-f[1]+1)*(f[5]-f[2]+1) for f in fills),'enabled':False},indent=2),'utf-8')
print('Arena blueprint generated:',len(blocks),'blocks,',len(fills),'fills. Build and protection validation still required.')
