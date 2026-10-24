"""Generate the original Bastión Virgos build from a surveyed site.

The output is consumed once by /virgos build. Coordinates are absolute and
the surveyed world seed is recorded, so the build is reproducible.
"""
from pathlib import Path
import argparse
import gzip
import json
import math
import random

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--x', type=int, required=True)
parser.add_argument('--z', type=int, required=True)
parser.add_argument('--y', type=int, required=True, help='Courtyard ground level')
parser.add_argument('--survey', type=Path, default=ROOT / '.lab/server/virgos-reports/survey.json')
parser.add_argument('--repair-from', type=Path)
parser.add_argument('--repair-name', default='bastion-repair-v3')
args = parser.parse_args()
CX, CZ, Y = args.x, args.z, args.y
survey = json.loads(args.survey.read_text('utf-8'))
grid = {(p[0], p[1]): p[2] for p in survey['terrain']}
spacing = survey['step']
x0, z0 = min(x for x, z in grid), min(z for x, z in grid)
palette, lookup, blocks, fills, entities, routes = [], {}, {}, [], [], []
rng = random.Random(31012001)


def pal(block):
    block = block if ':' in block else 'minecraft:' + block
    if block not in lookup:
        lookup[block] = len(palette)
        palette.append(block)
    return lookup[block]


def put(x, y, z, block):
    blocks[(round(x) + CX, round(y) + Y, round(z) + CZ)] = pal(block)


def box(x1, y1, z1, x2, y2, z2, block):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(y1, y2 + 1):
                put(x, y, z, block)


def fill(x1, y1, z1, x2, y2, z2, block):
    fills.append([x1 + CX, y1 + Y, z1 + CZ, x2 + CX, y2 + Y, z2 + CZ, pal(block)])


def ground(x, z):
    ax, az = x + CX, z + CZ
    gx = x0 + math.floor((ax - x0) / spacing) * spacing
    gz = z0 + math.floor((az - z0) / spacing) * spacing
    tx, tz = (ax-gx)/spacing, (az-gz)/spacing
    try:
        return ((grid[gx, gz]*(1-tx)+grid[gx+spacing, gz]*tx)*(1-tz)
                +(grid[gx, gz+spacing]*(1-tx)+grid[gx+spacing, gz+spacing]*tx)*tz) - 1
    except KeyError:
        raise ValueError('Site and approach roads must be inside the survey')


def disk(x, y, z, radius, block, inner=-1):
    for dx in range(-radius, radius+1):
        for dz in range(-radius, radius+1):
            if inner*inner < dx*dx+dz*dz <= radius*radius or inner < 0 and dx*dx+dz*dz <= radius*radius:
                put(x+dx, y, z+dz, block)


def lamp(x, z, base=0, tall=4):
    box(x, base+1, z, x, base+tall-1, z, 'dark_oak_fence')
    put(x, base+tall, z, 'lantern[hanging=false]')
    put(x, base, z, 'chiseled_stone_bricks')


def sign(x, y, z, lines, rotation=0):
    put(x, y, z, f'spruce_sign[rotation={rotation},waterlogged=false]')
    messages = [json.dumps({'text': line, 'color': 'black'}, ensure_ascii=False) for line in lines]
    messages += [json.dumps({'text': ''})] * (4-len(messages))
    nbt = '{front_text:{messages:[' + ','.join(json.dumps(m, ensure_ascii=False) for m in messages) + '],color:"black",has_glowing_text:0b},is_waxed:1b}'
    entities.append({'x': x+CX, 'y': y+Y, 'z': z+CZ, 'nbt': nbt})


def tower(x, z, radius=6, height=19, copper=False):
    for y in range(1,height+radius+5): disk(x,y,z,radius-1,'air')
    for y in range(1, height+1):
        outer = radius + (1 if y in (1, height-3, height) else 0)
        disk(x, y, z, outer, 'stone_bricks' if y % 5 else 'polished_andesite', radius-2)
    disk(x,0,z,radius-1,'spruce_planks')
    disk(x,height-2,z,radius-1,'spruce_planks')
    stair_radius=3 if radius>=7 else 2
    box(x-stair_radius+1,1,z-stair_radius+1,x+stair_radius-1,height-3,z+stair_radius-1,'polished_andesite')
    ring=[]
    for dx in range(-stair_radius,stair_radius):ring.append((dx,-stair_radius))
    for dz in range(-stair_radius,stair_radius):ring.append((stair_radius,dz))
    for dx in range(stair_radius,-stair_radius,-1):ring.append((dx,stair_radius))
    for dz in range(stair_radius,-stair_radius,-1):ring.append((-stair_radius,dz))
    steps=[]
    for n in range(2*(height-2)):
        dx,dz=ring[n%len(ring)];sy=1+n//2
        box(x+dx,sy+1,z+dz,x+dx,sy+3,z+dz,'air')
        steps.append((x+dx,sy,z+dz,'spruce_slab[type='+('bottom' if n%2==0 else 'top')+']'))
    for sx,sy,sz,state in steps:put(sx,sy,sz,state)
    routes.append({'name':f'Torre {x},{z}', 'points':[[CX+sx+.5,Y+sy+(.5 if 'bottom' in state else 1),CZ+sz+.5] for sx,sy,sz,state in steps]})
    for level in (5, 12):
        for dx, dz in [(radius, 0), (-radius, 0), (0, radius), (0, -radius)]:
            box(x+dx, level, z+dz, x+dx, level+2, z+dz, 'cyan_stained_glass')
            ix=dx-(1 if dx>0 else -1 if dx<0 else 0)
            iz=dz-(1 if dz>0 else -1 if dz<0 else 0)
            box(x+ix,level,z+iz,x+ix,level+2,z+iz,'air')
    # The courtyard-facing passage also cuts through the adjoining curtain wall.
    if abs(x)>abs(z):
        direction=-1 if x>0 else 1
        for distance in range(radius-1,radius+4):box(x+direction*distance,1,z-1,x+direction*distance,3,z+1,'air')
    else:
        direction=-1 if z>0 else 1
        for distance in range(radius-1,radius+4):box(x-1,1,z+direction*distance,x+1,3,z+direction*distance,'air')
    for y in range(1, radius+4):
        r = max(0, radius+2-y)
        disk(x, height+y, z, r, 'waxed_weathered_cut_copper' if copper else 'deepslate_tiles')
    put(x, height+radius+4, z, 'lightning_rod')
    # Four lanterns make the silhouette visible at night.
    for dx, dz in [(radius+1, 0), (-radius-1, 0), (0, radius+1), (0, -radius-1)]:
        put(x+dx, height-2, z+dz, 'lantern')


def house(x1, z1, x2, z2, floors=1, copper=False):
    height = floors*6+1
    box(x1-1, 0, z1-1, x2+1, 0, z2+1, 'stone_bricks')
    box(x1, 1, z1, x2, height, z2, 'air')
    for y in range(1, height+1):
        material = 'stone_bricks' if y < 3 else 'calcite'
        box(x1, y, z1, x2, y, z1, material)
        box(x1, y, z2, x2, y, z2, material)
        box(x1, y, z1, x1, y, z2, material)
        box(x2, y, z1, x2, y, z2, material)
    for x in range(x1, x2+1, 5):
        for z in (z1, z2): box(x, 1, z, x, height, z, 'stripped_spruce_log[axis=y]')
    for z in range(z1, z2+1, 5):
        for x in (x1, x2): box(x, 1, z, x, height, z, 'stripped_spruce_log[axis=y]')
    for floor in range(floors):
        base = floor*6
        box(x1+1, base, z1+1, x2-1, base, z2-1, 'spruce_planks')
        for x in range(x1+2, x2-1, 5):
            for z in (z1, z2):
                box(x, base+3, z, x+1, base+4, z, 'light_blue_stained_glass_pane')
                put(x, base+2, z, 'spruce_trapdoor[half=top,open=false]')
        box(x1, base+6, z1, x2, base+6, z1, 'spruce_log[axis=x]')
        box(x1, base+6, z2, x2, base+6, z2, 'spruce_log[axis=x]')
    mid = (x1+x2)//2
    for z in (z1, z2):
        box(mid-1, 1, z, mid+1, 3, z, 'air')
        box(mid-2, 1, z, mid-2, 4, z, 'dark_oak_log[axis=y]')
        box(mid+2, 1, z, mid+2, 4, z, 'dark_oak_log[axis=y]')
        box(mid-2, 4, z, mid+2, 4, z, 'dark_oak_log[axis=x]')
    # Stepped gable with a generous overhang and contrasting ridge.
    for dz in range(-2, (z2-z1)//2+2):
        y = height+max(0, dz+1)
        north, south = z1+dz, z2-dz
        if north > south: break
        roof = 'waxed_weathered_cut_copper' if copper else 'deepslate_tiles'
        stairs='waxed_weathered_cut_copper_stairs' if copper else 'deepslate_tile_stairs'
        if north==south:box(x1-2,y,north,x2+2,y,north,roof)
        else:
            box(x1-2, y, north, x2+2, y, north, stairs+'[facing=south]')
            box(x1-2, y, south, x2+2, y, south, stairs+'[facing=north]')
        for x in (x1, x2): box(x, height, north, x, y-1, north, 'spruce_planks')
    for x in range(x1+3, x2-1, 7):
        box(x,height,z1+1,x,height,z2-1,'spruce_log[axis=z]')
        for z in range(z1+3, z2-1, 6): put(x, height-1, z, 'lantern[hanging=true]')
        if floors>1:
            for z in range(z1+3,z2-1,6):put(x,5,z,'lantern[hanging=true]')
    if floors > 1:
        for i in range(6):
            box(x2-4, i+1, z1+3+i, x2-2, i+1, z1+3+i, 'spruce_stairs[facing=south]')
            box(x2-4, i+2, z1+3+i, x2-2, min(height-1,i+4), z1+3+i, 'air')
        routes.append({'name':f'Escalera {x1},{z1}','points':[[CX+x2-2.5,Y+i+2,CZ+z1+3+i+.5] for i in range(6)]})


# A 160-block courtyard fades into the surveyed terrain over 32 blocks.
for x in range(-112, 113):
    for z in range(-112, 113):
        distance = max(abs(x), abs(z))
        natural = ground(x, z)
        blend = max(0, min(1, (distance-81)/31))
        blend = blend*blend*(3-2*blend)
        top = round(Y*(1-blend)+natural*blend)-Y
        if distance > 109 and rng.random() < 0.35: continue
        fill(x, min(top-5, round(natural-Y)-3), z, x, top-3, z, 'stone')
        fill(x, top-2, z, x, top-1, z, 'dirt')
        fill(x, top+1, z, x, 319-Y, z, 'air')
        put(x, top, z, 'grass_block')

# Four walking approaches, and the main crossing through the city.
for axis in (0, 1):
    road_levels={}
    for direction in (-1,1):
        previous=0
        points=[]
        for distance in range(12,181):
            p=direction*distance
            x,z=(p,0) if axis==0 else (0,p)
            t=min(1,max(0,(distance-82)/70))
            wanted=round(Y*(1-t)+ground(x,z)*t)-Y
            previous=max(previous-1,min(previous+1,wanted))
            road_levels[p]=previous
            points.append([CX+x+.5,Y+previous+1,CZ+z+.5])
        routes.append({'name':f'Acceso {axis},{direction}','points':points})
    for p in range(-180, 181):
        t = min(1, max(0, (abs(p)-82)/70))
        for w in range(-6, 7):
            x, z = (p, w) if axis == 0 else (w, p)
            top = road_levels.get(p,0)
            # The road's cut replaces the terrace surface at this column.
            distance=max(abs(x),abs(z))
            if distance<=112:
                blend=max(0,min(1,(distance-81)/31));blend=blend*blend*(3-2*blend)
                terrace=round(Y*(1-blend)+ground(x,z)*blend)
                blocks.pop((x+CX,terrace,z+CZ),None)
            fill(x, top-3, z, x, top-1, z, 'stone')
            fill(x, top+1, z, x, 319-Y if abs(p)>86 else top+10, z, 'air')
            put(x, top, z, 'polished_andesite' if abs(w)==6 else rng.choice(['stone_bricks','stone_bricks','andesite','gravel']))
        if abs(p)>86 and p%18==0:
            for w in (-8, 8):
                x,z=(p,w) if axis==0 else (w,p)
                lamp(x,z,round(Y*(1-t)+ground(x,z)*t)-Y)

# Curtain walls with safe walkways and merlons; central openings remain unobstructed.
for axis in (0, 1):
    for edge in (-76, 76):
        for p in range(-76, 77):
            if abs(p) < 11: continue
            for width in range(-1, 2):
                x,z=(p,edge+width) if axis==0 else (edge+width,p)
                box(x,1,z,x,8,z,'stone_bricks')
                put(x,9,z,'polished_andesite')
                if p%4<2 and abs(width)==1: box(x,10,z,x,11,z,'stone_bricks')
            if p%12==0:
                x,z=(p,edge) if axis==0 else (edge,p)
                lamp(x,z,9)
for x in (-76,76):
    for z in (-76,76): tower(x,z,7,19)

# The four monumental gatehouses use curved openings rather than square cutouts.
for axis in (0,1):
    for edge in (-76,76):
        for p in range(-11,12):
            lower=12+round(6*math.sqrt(max(0,1-(p/10)**2))) if abs(p)<=9 else 1
            for width in range(-2,3):
                x,z=(p,edge+width) if axis==0 else (edge+width,p)
                box(x,lower,z,x,22,z,'stone_bricks')
                put(x,lower,z,'chiseled_stone_bricks')
                put(x,23,z,'waxed_weathered_cut_copper')
        for side in (-17,17):
            x,z=(side,edge) if axis==0 else (edge,side)
            tower(x,z,5,23,True)

# Fountain and copper astrolabe, surrounded by a patterned plaza.
disk(0,0,0,23,'smooth_stone')
for r in (22,18,12): disk(0,0,0,r,'polished_andesite',r-1)
disk(0,1,0,8,'stone_bricks')
disk(0,2,0,8,'stone_bricks',6)
disk(0,3,0,8,'stone_brick_slab[type=bottom]',7)
disk(0,2,0,6,'water[level=0]')
disk(0,2,0,2,'chiseled_stone_bricks')
box(-1,3,-1,1,7,1,'polished_andesite')
for angle in range(360):
    a=math.radians(angle)
    put(4*math.cos(a),11+4*math.sin(a),0,'waxed_exposed_cut_copper')
    put(0,11+4*math.sin(a),4*math.cos(a),'waxed_weathered_cut_copper')
    put(4*math.cos(a),11,4*math.sin(a),'waxed_cut_copper')
put(0,11,0,'sea_lantern')
for x,z in [(-18,-18),(18,-18),(-18,18),(18,18)]: lamp(x,z,0,5)
for cx,z1,z2 in [(-44,-34,-6),(44,-33,-6),(-45,6,29),(43,6,24)]:
    for x in range(cx-3,cx+4):
        for z in range(z1,z2+1): put(x,0,z,'stone_bricks' if abs(x-cx)==3 else 'gravel')
    for z in range(z1+3,z2,8):
        for x in (cx-5,cx+5):
            put(x,1,z,'spruce_fence')
            put(x,2,z,'lantern')

# Archive, workshop, and inn are furnished, usable buildings.
house(-62,-59,-27,-35,2)
house(27,-60,62,-34,1,True)
house(-62,30,-28,56,2)
tower(-56,-54,6,34,True)
for x in range(-48,-29):
    for y in (1,2,3,7,8,9): put(x,y,-57,'bookshelf')
for x in (-45,-37):
    box(x,1,-46,x+3,1,-44,'spruce_slab[type=top]')
    put(x,2,-45,'lantern')
    put(x+1,1,-42,'lectern[facing=south]')
for x in range(31,59,5):
    put(x,1,-58,'crafting_table')
    put(x+1,1,-58,'stonecutter[facing=south]')
    put(x+2,1,-58,'anvil[facing=north]')
put(47,1,-43,'create:depot')
put(47,3,-43,'create:mechanical_press[facing=west]')
for x in range(48,53): put(x,3,-43,'create:shaft[axis=x]')
put(53,3,-43,'create:water_wheel[facing=east]')
box(32,0,-27,63,0,-24,'stone_bricks')
for x in range(33,63): put(x,1,-25,'create:track[shape=xo]')
for x in (34,44,54,62): lamp(x,-28)
sign(45,1,-33,['Taller de ingeniería','Maqueta sin potencia','Armá tu propia red','Ponder: mantené W'])
for x in (-57,-49,-41,-33):
    box(x,1,38,x+2,1,40,'spruce_slab[type=top]')
    put(x+1,2,39,'lantern')
    put(x,1,37,'spruce_stairs[facing=south]')
    put(x,1,41,'spruce_stairs[facing=north]')
for x in range(-58,-31,3):
    put(x,1,54,'smoker[facing=north]')
    put(x+1,1,54,'barrel[facing=up]')
for x in (-54,-48):
    put(x,1,54,'farmersdelight:stove[facing=north,lit=true]')
    put(x,2,54,'farmersdelight:cooking_pot')
for x in (-56,-47,-38):
    put(x,7,49,'white_bed[facing=north,part=foot]')
    put(x,7,48,'white_bed[facing=north,part=head]')
    put(x+1,7,49,'barrel')

# Garden, greenhouse pergola, pond and practice targets.
disk(42,0,44,13,'moss_block')
disk(43,0,45,7,'water[level=0]')
disk(43,-1,45,7,'clay')
for x,z in [(26,30),(60,30),(26,61),(60,61)]:
    box(x,1,z,x,6,z,'stripped_spruce_log')
    for dx in range(-3,4):
        for dz in range(-3,4):
            if abs(dx)+abs(dz)<6: put(x+dx,7,z+dz,'azalea_leaves[persistent=true]')
for x in (29,57):
    for z in (30,37):box(x,1,z,x,5,z,'stripped_spruce_log')
for z in (30,37):box(28,6,z,58,6,z,'spruce_log[axis=x]')
for x in range(28,59,3):box(x,7,29,x,7,38,'spruce_slab[type=bottom]')
for x in (32,41,50):
    box(x,1,31,x+3,1,31,'handcrafted:spruce_bench')
    put(x+1,5,30,'lantern[hanging=true]')
for x in (32,43,54):
    put(x,1,63,'hay_block')
    put(x,2,63,'target')
for x in range(23,65):
    put(x,0,25,'mossy_stone_bricks')
    if x%4==0: lamp(x,25,0,3)

# Market stalls and low hedges connect buildings to the central streets.
for x,z,color in [(-18,34,'red'),(-18,49,'orange'),(18,-35,'cyan'),(18,-50,'green')]:
    box(x-3,0,z-3,x+3,0,z+3,'spruce_planks')
    for dx in (-3,3):
        for dz in (-3,3): box(x+dx,1,z+dz,x+dx,4,z+dz,'spruce_fence')
    for dx in range(-4,5):
        box(x+dx,5,z-4,x+dx,5,z+4,('white' if dx%2 else color)+'_wool')
    box(x-2,1,z,x+2,1,z,'barrel[facing=up]')
    put(x,4,z,'lantern[hanging=true]')
for p in range(-60,61,12):
    if abs(p)<24: continue
    for w in (-10,10): lamp(p,w); lamp(w,p)
for x,z in [(-17,-19),(17,-19),(-17,20),(17,20),(-66,-18),(66,18)]:
    disk(x,0,z,3,'mossy_stone_bricks')
    disk(x,1,z,3,'stone_brick_slab',2)
    disk(x,1,z,2,'grass_block')
    box(x,2,z,x,6,z,'oak_log')
    for y,r in [(5,3),(6,3),(7,2),(8,1)]: disk(x,y,z,r,'oak_leaves[persistent=true]')
    for dx,dz in [(-1,-1),(1,1),(-1,1),(1,-1)]: put(x+dx,2,z+dz,'allium')
for x,z,lines in [(-10,12,['Virgos-MC','Bastión Virgos','J · Códice','Buen viaje']),(-25,-30,['Archivo','Misiones: J','Mapa: M','Claims: P']),(26,-29,['Taller comunal','Create e ingeniería','Compartí el espacio',''] ),(-26,27,['Posada del Camino','Comida y descanso','Mochila: B','']),(25,22,['Jardín de prácticas','Probá tu equipo','Respetá a los demás',''])]:
    sign(x,1,z,lines)

checks=[]
for axis in (0,1):
    for p in range(-85,86):
        if abs(p)<12:continue
        x,z=(p,0) if axis==0 else (0,p)
        checks.append([CX+x,Y+1,CZ+z])
for x,z in [(-44,-35),(-44,-34),(-44,-59),(44,-34),(44,-60),(-45,30),(-45,56)]:checks.append([CX+x,Y+1,CZ+z])
data={'schema':2,'name':'Bastión Virgos','seed':survey['seed'],'origin':[CX,Y,CZ],
      'palette':palette,'fills':fills,'blocks':[[*position,index] for position,index in blocks.items()],
      'blockEntities':entities,'spawn':[CX,Y+1,CZ+16],'walkChecks':checks,'routes':routes}
for base in ['pack/server-overrides/config/virgos','.lab/server/config/virgos']:
    folder=ROOT/base
    folder.mkdir(parents=True,exist_ok=True)
    with gzip.open(folder/'bastion.blocks.json.gz','wt',encoding='utf-8') as stream:
        json.dump(data,stream,ensure_ascii=False,separators=(',',':'))
    if args.repair_from:
        with gzip.open(args.repair_from,'rt',encoding='utf-8') as stream:old=json.load(stream)
        cleared=[[b[0],b[1],b[2],pal('air')] for b in old['blocks'] if tuple(b[:3]) not in blocks]
        # Reapply terrain before the structure, including the top of trees that
        # the old limited-height excavation left hanging above the roads.
        repair=dict(data)
        # Clear obsolete blocks BEFORE refilling terrain. Clearing afterwards
        # could punch holes in the new road foundation and let gravel fall.
        repair['fills']=[[b[0],b[1],b[2],b[0],b[1],b[2],b[3]] for b in cleared]+data['fills']
        repair['blocks']=data['blocks']
        if not __import__('re').fullmatch(r'[a-z0-9_-]{1,64}',args.repair_name):raise ValueError('Invalid repair name')
        with gzip.open(folder/(args.repair_name+'.blocks.json.gz'),'wt',encoding='utf-8') as stream:
            json.dump(repair,stream,ensure_ascii=False,separators=(',',':'))
report={k:data[k] for k in ['name','seed','origin','spawn']}
report.update({'palette':len(palette),'fills':len(fills),'blocks':len(blocks),'blockEntities':len(entities),
               'fillVolume':sum((f[3]-f[0]+1)*(f[4]-f[1]+1)*(f[5]-f[2]+1) for f in fills)})
(ROOT/'pack/bastion-build.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),'utf-8')
print(json.dumps(report,ensure_ascii=False))
