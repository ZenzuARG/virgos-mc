"""Adapt the author's downloaded Cynera town to the existing protected spawn.

Only produces a reviewed blueprint; never edits a running world. All portals,
invisible light/barrier blocks, inventories and original sign commands are omitted.
"""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, math, runpy

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--name',default='pueblo-v11-final');parser.add_argument('--candidate-v2',action='store_true');args=parser.parse_args()
if args.candidate_v2 and args.name=='pueblo-v11-final':args.name='pueblo-v2'
assert __import__('re').fullmatch('[a-z0-9_-]{1,64}',args.name)
source=ROOT/'.cache/v11/cynera-spawn.schem'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='321631f3512dd688e2214a813db42864977f7fe957394aff471cea7a08d2dcac'
n=next(iter(runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt'](source).values()))
assert n['Version']==2 and n['DataVersion']<=3465 and not n['Entities']
w,h,l=n['Width'],n['Height'],n['Length']; raw=[]; value=shift=0
for b in n['BlockData']:
    b&=255;value|=(b&127)<<shift
    if b&128:shift+=7
    else:raw.append(value);value=shift=0
assert len(raw)==w*h*l
original={v:k for k,v in n['Palette'].items()}
X,Y,Z=605,(79 if args.candidate_v2 else 114),685
palette=[];indexes={};blocks={};fills=[];entities=[];routes=[]
def pal(state):
    if ':' not in state:state='minecraft:'+state
    if state not in indexes:indexes[state]=len(palette);palette.append(state)
    return indexes[state]
def put(x,y,z,state):blocks[X+x,Y+y,Z+z]=pal(state)
def box(x1,y1,z1,x2,y2,z2,state):
    for x in range(x1,x2+1):
        for z in range(z1,z2+1):
            for y in range(y1,y2+1):put(x,y,z,state)
def sign(x,y,z,lines,rotation=0):
    put(x,y,z,f'spruce_sign[rotation={rotation},waterlogged=false]')
    messages=[json.dumps({'text':s,'color':'dark_green'},ensure_ascii=False) for s in lines]
    # Quotes encoded as JSON strings form valid SNBT string values.
    nbt='{front_text:{messages:['+','.join(json.dumps(s,ensure_ascii=False) for s in messages)+'],color:"black",has_glowing_text:0b},is_waxed:1b}'
    entities.append({'x':X+x,'y':Y+y,'z':Z+z,'nbt':nbt})

# Restore the surveyed terrace, including its slopes. A flat air-clearing box would
# cut the higher natural terrain and leave visible cliffs and half trees.
survey=json.loads((ROOT/('.lab/v2/terrain-second.json' if args.candidate_v2 else '.lab/reports/survey-bastion.json')).read_text('utf-8'))
if args.candidate_v2:
    assert survey['seed']==-4556043908712459124 and survey['centerX']==672 and survey['centerZ']==736 and survey['radius']==224
grid={(p[0],p[1]):p[2]-1 for p in survey['terrain']}
def natural(ax,az):
    step=survey['step'];gx=math.floor(ax/step)*step;gz=math.floor(az/step)*step;tx=(ax-gx)/step;tz=(az-gz)/step
    return (grid[gx,gz]*(1-tx)+grid[gx+step,gz]*tx)*(1-tz)+(grid[gx,gz+step]*(1-tx)+grid[gx+step,gz+step]*tx)*tz
terrace={}
for ax in range(560,785):
    for az in range(624,849):
        distance=max(abs(ax-672),abs(az-736));t=max(0,min(1,(distance-81)/31));t=t*t*(3-2*t)
        top=round(Y*(1-t)+natural(ax,az)*t)
        low=min(Y-5,top-5,round(natural(ax,az))-3)
        fills.append([ax,low,az,ax,top-3,az,pal('stone')])
        fills.append([ax,top-2,az,ax,top-1,az,pal('dirt')])
        fills.append([ax,top+1,az,ax,210,az,pal('air')])
        blocks[ax,top,az]=pal('grass_block');terrace[ax,az]=top
with gzip.open(ROOT/'pack/server-overrides/config/virgos/bastion.blocks.json.gz','rt',encoding='utf-8') as f:previous=json.load(f)
if args.candidate_v2:previous={'routes':[],'blocks':[],'palette':[]}
for r in previous['routes'][:4]:
    for px,py,pz in r['points']:
        ax,ay,az=int(px),int(py)-1,int(pz)
        if max(abs(ax-672),abs(az-736))<80:continue
        horizontal=az==736
        for delta in range(-6,7):
            tx,tz=(ax,az+delta) if horizontal else (ax+delta,az)
            if (tx,tz) in terrace:blocks.pop((tx,terrace[tx,tz],tz),None)
            fills.append([tx,ay-3,tz,tx,ay-1,tz,pal('stone')])
            fills.append([tx,ay+1,tz,tx,210,tz,pal('air')])
for ax,ay,az,pid in previous['blocks']:
    if (abs(ax-672)>=80 and abs(az-736)<=8) or (abs(az-736)>=80 and abs(ax-672)<=8):
        blocks[ax,ay,az]=pal(previous['palette'][pid])
for r in previous['routes'][:4]:
    points=[p for p in r['points'] if max(abs(p[0]-.5-672),abs(p[2]-.5-736))>=80]
    routes.append({'name':r['name'],'points':points})
removed=collections.Counter()
for index,pid in enumerate(raw):
    state=original[pid];name=state.split('[')[0]
    if name=='minecraft:air':continue
    if name in {'minecraft:barrier','minecraft:light','minecraft:end_portal','minecraft:end_portal_frame','minecraft:nether_portal','minecraft:command_block','minecraft:chain_command_block','minecraft:repeating_command_block','minecraft:structure_block','minecraft:jigsaw','minecraft:lava','minecraft:fire','minecraft:ladder'}:
        removed[name]+=1;continue
    x=index%w;z=(index//w)%l;y=index//(w*l)
    # Remove the old low palisade outside the usable village, replaced by our walls.
    if (x-70)**2+(z-51)**2>48**2 and y<5 and any(s in name for s in ['fence','trapdoor','oak_wood']):continue
    if name=='minecraft:lectern':state=state.replace('has_book=true','has_book=false')
    if 'leaves[' in state:state=state.replace('persistent=false','persistent=true')
    put(x,y+1,z,state)

# Low stone walls with four generous arches; the plaza remains visible from the roads.
for x in range(12,129):
    for z in (-6,108):
        box(x,1,z,x,4,z,'stone_bricks')
        put(x,5,z,'stone_brick_slab[type=bottom]' if x%3 else 'stone_bricks')
for z in range(-5,108):
    for x in (12,128):
        box(x,1,z,x,4,z,'stone_bricks')
        put(x,5,z,'stone_brick_slab[type=bottom]' if z%3 else 'stone_bricks')
for x,z in [(12,-6),(128,-6),(12,108),(128,108)]:
    box(x-2,0,z-2,x+2,6,z+2,'stone_bricks')
    box(x-1,1,z-1,x+1,5,z+1,'air')
    box(x-3,7,z-3,x+3,7,z+3,'dark_prismarine_slab[type=bottom]')
    box(x-2,8,z-2,x+2,8,z+2,'dark_prismarine_slab[type=bottom]')
    put(x,8,z,'dark_prismarine')
    put(x,9,z,'lantern')

def path(name,points,width=5):
    route=[]
    for a,b in zip(points,points[1:]):
        assert a[0]==b[0] or a[1]==b[1]
        count=abs(a[0]-b[0])+abs(a[1]-b[1])
        for i in range(count+1):
            x=a[0]+(b[0]-a[0])*i//max(count,1);z=a[1]+(b[1]-a[1])*i//max(count,1)
            r=width//2
            box(x-r,0,z-r,x+r,0,z+r,'cobblestone')
            box(x-r,1,z-r,x+r,3,z+r,'air')
            for dx in range(-r,r+1):
                for dz in range(-r,r+1):
                    if abs(dx)<r and abs(dz)<r:put(x+dx,0,z+dz,'gravel')
            route.append([X+x+.5,Y+1,Z+z+.5])
    routes.append({'name':name,'points':route})

# Paths go around the original homes, with short links into the existing four roads.
path('oeste',[(60,52),(12,52),(-13,52),(-13,51)])
path('norte',[(60,52),(77,52),(77,-29),(67,-29)])
path('este',[(80,52),(93,52),(93,72),(128,72),(147,72),(147,51)])
path('sur',[(60,52),(65,52),(65,80),(55,80),(55,131),(67,131)])
for name,points in [('plaza',[(65,52),(65,67),(67,67)]),('cocina',[(55,80),(43,80)]),('taller',[(77,40),(85,40)])]:path(name,points,3)

def arch(x,z,axis):
    for a in range(-5,6):
        for y in range(1,9):
            state='air' if abs(a)<=3 and y<=6 else ('spruce_log[axis=y]' if abs(a)>=4 and y<7 else 'stone_bricks')
            for depth in (-1,0,1):put(x+(a if axis=='x' else depth),y,z+(depth if axis=='x' else a),state)
    for a in (-4,4):put(x+(a if axis=='x' else 0),9,z+(0 if axis=='x' else a),'lantern')
arch(12,52,'z');arch(77,-6,'x');arch(128,72,'z');arch(55,108,'x')

# Spawn remains at the familiar location; an open teaching square surrounds it.
box(64,0,61,73,0,73,'stone_bricks')
box(64,1,61,73,3,73,'air')
for x,z in [(64,61),(73,61),(64,73),(73,73)]:
    box(x,1,z,x,3,z,'spruce_fence');put(x,4,z,'lantern')
sign(65,1,69,['VIRGOS-MC','J: misiones','/virgos guia','Bienvenidos'])
sign(69,1,69,['Pueblo de Cynera','itzvmbie y equipo','Adaptado a Virgos','Salida a pie'])
# Shared stations are clearly labelled, kept outside the walking line.
for x,state in [(42,'crafting_table'),(43,'farmersdelight:cooking_pot'),(44,'barrel[facing=up]')]:put(x,1,83,state)
put(43,0,83,'campfire[lit=true]');sign(46,1,83,['COCINA','J: capitulo 18','Espacio comun','No dejes valores'])
for x,state in [(83,'crafting_table'),(84,'stonecutter[facing=south]'),(85,'anvil[facing=east]')]:put(x,1,42,state)
sign(87,1,42,['TALLER','J: capitulo 13','Create + Ponder','Maquinas en tu base'])
sign(13,1,57,['SALIDA OESTE','Mundo libre','Fuera del spawn','/virgos guia bases'])
sign(59,1,109,['SALIDA SUR','Camino a la arena','672 / 78 / 1048','/virgos expedicion'])

if args.candidate_v2:
    # Rebuild the four approaches from the new terrain, without transplanting
    # the previous world's ground heights or old roadside blocks.
    for name,dx,dz,facing in [('oeste',-1,0,'west'),('este',1,0,'east'),('norte',0,-1,'north'),('sur',0,1,'south')]:
        length=180 if name=='sur' else 208
        end=78 if name=='sur' else round(natural(672+dx*length,736+dz*length))
        route=[];last=Y
        for distance in range(80,length+1):
            ax,az=672+dx*distance,736+dz*distance
            t=(distance-80)/(length-80);top=round(Y+(end-Y)*(t*t*(3-2*t)))
            assert abs(top-last)<=1
            for side in range(-4,5):
                tx,tz=ax+dz*side,az+dx*side
                nat=round(natural(tx,tz));low=min(nat-3,top-4)
                fills.append([tx,low,tz,tx,top-1,tz,pal('stone')])
                fills.append([tx,top+1,tz,tx,max(210,nat+16),tz,pal('air')])
                state='stone_bricks' if abs(side)>=3 else 'gravel'
                if top>last:state=f'stone_brick_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]'
                blocks[tx,top,tz]=pal(state)
                if (tx,tz) in terrace and terrace[tx,tz]!=top:blocks.pop((tx,terrace[tx,tz],tz),None)
                if distance>=96 and abs(side)==4 and top-nat>4:blocks[tx,top+1,tz]=pal('stone_brick_wall')
            if distance>=96 and distance%24==0:
                for side in [-4,4]:
                    tx,tz=ax+dz*side,az+dx*side
                    for y in range(top+1,top+4):blocks[tx,y,tz]=pal('spruce_fence')
                    blocks[tx,top+4,tz]=pal('lantern')
            route.append([ax+.5,top+1,az+.5]);last=top
        routes.append({'name':'v2-'+name,'points':route})
    sign(83,1,45,['TALLER CREATE','J: Create','W sobre objetos','para ver Ponder'])
    sign(46,1,85,['COCINA COMUN','J: Cocina','Comida para viajar','No dejes valores'])

# Preserve the market's two wooden support posts beside the northern path.
for sx,sz in [(79,42),(79,46)]:
    for sy in (0,1):put(sx,sy+1,sz,'stripped_dark_oak_wood[axis=y]')

# Paths can remove a plant's supporting ground or one half. Omit the whole plant.
for position,index in list(blocks.items()):
    state=palette[index];name=state.split('[')[0];x,y,z=position
    if args.candidate_v2 and name=='minecraft:vine' and abs(x-678)<3 and abs(z-739)<3:
        blocks[position]=pal('air')
    if name in {'minecraft:tall_grass','minecraft:large_fern'}:
        upper='half=upper' in state;other=blocks.get((x,y+(-1 if upper else 1),z),pal('air'))
        if palette[other].split('[')[0]!=name:blocks[position]=pal('air')
    if name in {'minecraft:grass','minecraft:fern','minecraft:tall_grass','minecraft:large_fern'} and 'half=upper' not in state:
        below=palette[blocks.get((x,y-1,z),pal('grass_block') if y-1==Y else pal('air'))].split('[')[0]
        if below not in {'minecraft:grass_block','minecraft:dirt','minecraft:coarse_dirt','minecraft:podzol','minecraft:moss_block'}:
            blocks[position]=pal('air')
            if name in {'minecraft:tall_grass','minecraft:large_fern'}:blocks[x,y+1,z]=pal('air')

data={'schema':2,'name':'Pueblo Virgos · adaptación de Cynera','seed':survey['seed'],
      'origin':[X,Y,Z],'spawn':[672,Y+1,752],'palette':palette,'fills':fills,
      'blocks':[[*p,i] for p,i in sorted(blocks.items(),key=lambda e:(e[0][1],e[0][2],e[0][0]))],
      'blockEntities':entities,'walkChecks':[[672,Y+1,752]],'routes':routes}
for rel in (['.lab/v2/server-overrides/config/virgos','.lab/v2/server/config/virgos'] if args.candidate_v2 else ['pack/server-overrides/config/virgos','.lab/server/config/virgos']):
    folder=ROOT/rel;folder.mkdir(parents=True,exist_ok=True)
    with gzip.open(folder/(args.name+'.blocks.json.gz'),'wt',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,separators=(',',':'))
report={'source':'https://www.planetminecraft.com/project/medieval-spawn-town-1-17-1-18/',
        'author':'itzvmbie; SaraGrey, CoolMMN, FireVoges, Vmbie, Z3phrin, Cynera Staff',
        'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceSize':[w,h,l],
        'removed':dict(removed),'blocks':len(blocks),'spawn':data['spawn'],'routes':len(routes),
        'blueprint':args.name,'status':'LAB_ONLY_PENDING_WALK_AND_VISUAL_QA'}
(ROOT/('.lab/v2/pueblo.json' if args.candidate_v2 else 'pack/pueblo-v11.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(report,ensure_ascii=True))
