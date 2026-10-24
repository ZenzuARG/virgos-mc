"""Locate new content and generate representative chunks in the isolated world.

Temporary force loads are removed in finally; no structures are placed manually.
"""
from pathlib import Path
import argparse,json,re,time
ROOT=Path(__file__).resolve().parents[1];LAB=ROOT/'.lab/v2/server';REPORT=ROOT/'.lab/v2/worldgen-tests.json'
assert 'server-port=25575' in (LAB/'server.properties').read_text('utf-8')
def log():return (LAB/'logs/latest.log').read_text('utf-8',errors='replace')
def send(command):
    with (LAB/'console-commands.txt').open('a',encoding='utf-8') as f:f.write(command+'\n')
def wait(predicate,seconds=240):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        result=predicate()
        if result:return result
        if json.loads((LAB/'process.json').read_text('utf-8')).get('finished'):raise RuntimeError('Server stopped during world generation test')
        time.sleep(.5)
    raise TimeoutError('Server generation response timed out')
wait(lambda:'Dedicated server took' in (LAB/'console.log').read_text('utf-8',errors='replace'),300)
tests=[('biome','alexscaves:'+b,'minecraft:overworld',False) for b in ['magnetic_caves','primordial_caves','toxic_caves','abyssal_chasm','forlorn_hollows','candy_cavity']]
tests += [('biome','terralith:alpine_highlands','minecraft:overworld',False),
 ('structure','integrated_villages:clockwork_village','minecraft:overworld',True),
 ('structure','#idas:common','minecraft:overworld',True),
 ('structure','integrated_stronghold:stronghold','minecraft:overworld',True),
 ('structure','dungeons_arise:foundry','minecraft:overworld',True),
 ('structure','dungeons_arise_seven_seas:pirate_junk','minecraft:overworld',True),
 ('structure','bosses_of_mass_destruction:lich_tower','minecraft:overworld',True),
 ('structure','aquamirae:ship','minecraft:overworld',True),
 ('structure','incendium:nether_reactor','minecraft:the_nether',True),
 ('biome','nullscape:shadowlands','minecraft:the_end',True),
 ('structure','deep_aether:brass_dungeon','aether:the_aether',True)]
parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--only');parser.add_argument('--origin',default='672 64 752');args=parser.parse_args()
results=json.loads(REPORT.read_text('utf-8'))['tests'] if args.resume and REPORT.exists() else []
results=[r for r in results if r.get('located') and (r['type']=='biome' or r.get('generated'))]
for kind,target,dimension,generate in tests:
    if args.only and args.only not in target:continue
    if any(r['id']==target for r in results):continue
    offset=len(log());command=f'execute in {dimension} positioned {args.origin} run locate {kind} {target}'
    send(command)
    response=wait(lambda:re.search(r'The nearest '+re.escape(target)+r'[^\n]*? is at \[(-?\d+), (?:~|-?\d+), (-?\d+)\][^\n]*',log()[offset:]) or re.search(r"\[net.minecraft.server.MinecraftServer/\]: ((?:Could not find|Couldn't find|Can't find|No structure|Unknown structure|Incorrect argument)[^\n]*)",log()[offset:]))
    result={'type':kind,'id':target,'dimension':dimension,'response':response.group(0),'located':response.lastindex==2}
    if result['located']:
        x,z=map(int,response.groups());result['x']=x;result['z']=z
        if generate:
            try:
                send(f'execute in {dimension} run forceload add {x-16} {z-16} {x+16} {z+16}')
                marker='V2_GENERATED_'+str(len(results));offset2=len(log())
                for attempt in range(30):
                    send(f'execute in {dimension} if loaded {x} 64 {z} run say {marker}')
                    time.sleep(3)
                    if marker in log()[offset2:]:break
                else:raise TimeoutError('Chunks not loaded: '+target)
                result['generated']=True
            finally:send(f'execute in {dimension} run forceload remove {x-16} {z-16} {x+16} {z+16}')
    results.append(result);REPORT.write_text(json.dumps({'scope':'Native locate + generated center and neighboring chunks; does not simulate boss combat','tests':results},ensure_ascii=False,indent=2),'utf-8')
    print(target,':',result['response'],flush=True)
send('save-all flush')
print('World generation probes complete.',flush=True)
