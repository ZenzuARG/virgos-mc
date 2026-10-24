"""Apply the first visual review corrections in the disposable lab world.

The same changes are also in build-bastion.py. This patch does not regenerate
the terrain or overwrite inventories. It uses normal server console commands.
"""
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cx,y,cz=672,114,736
commands=[f'fill {cx-16} {y+1} {cz-16} {cx+16} {y+2} {cz+16} air replace minecraft:water']
def row(x,y,z1,z2,block):
    if z1<=z2:commands.append(f'fill {cx+x} {114+y} {cz+z1} {cx+x} {114+y} {cz+z2} {block}')
for x in range(-8,9):
    outer=math.floor(math.sqrt(64-x*x))
    inner=math.floor(math.sqrt(36-x*x)) if abs(x)<=6 else -1
    if inner<0:row(x,2,-outer,outer,'stone_bricks')
    else:
        row(x,2,-outer,-inner-1,'stone_bricks');row(x,2,inner+1,outer,'stone_bricks')
    inner_top=math.floor(math.sqrt(49-x*x)) if abs(x)<=7 else -1
    if inner_top<0:row(x,3,-outer,outer,'stone_brick_slab[type=bottom]')
    else:
        row(x,3,-outer,-inner_top-1,'stone_brick_slab[type=bottom]');row(x,3,inner_top+1,outer,'stone_brick_slab[type=bottom]')
for x in range(-6,7):
    extent=math.floor(math.sqrt(36-x*x))
    inner=math.floor(math.sqrt(4-x*x)) if abs(x)<=2 else -1
    if inner<0:row(x,2,-extent,extent,'water')
    else:
        row(x,2,-extent,-inner-1,'water');row(x,2,inner+1,extent,'water')
for path_x,z1,z2 in [(-44,-34,-10),(44,-33,-10),(-45,10,29),(43,10,24)]:
    for x in range(path_x-3,path_x+4): row(x,0,z1,z2,'stone_bricks' if abs(x-path_x)==3 else 'gravel')
    for z in range(z1+3,z2,8):
        for x in (path_x-5,path_x+5):
            row(x,1,z,z,'spruce_fence');row(x,2,z,z,'lantern')
commands.append('save-all flush')
with (ROOT/'.lab/server/console-commands.txt').open('a',encoding='utf-8') as f:f.write('\n'.join(commands)+'\n')
(ROOT/'pack/bastion-visual-corrections.txt').write_text('\n'.join(commands)+'\n','utf-8')
print('Visual corrections queued:',len(commands))
