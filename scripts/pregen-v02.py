"""Bounded foreground maintenance; pauses immediately if a player joins."""
from pathlib import Path
import time,json
ROOT=Path(__file__).resolve().parents[1];log=ROOT/'logs/latest.log';cmd=ROOT/'.runtime/public-commands.txt'
def send(s):
    with cmd.open('a',encoding='utf-8') as f:f.write(s+'\n')
start=len(log.read_text('utf-8',errors='replace'));send('list');time.sleep(1)
if 'There are 0 of a max of' not in log.read_text('utf-8',errors='replace')[start:]:raise SystemExit('Players online or no response; pregeneration not started.')
for command in ['chunky world minecraft:overworld','chunky center 672 752','chunky shape circle','chunky radius 768','chunky start']:send(command);time.sleep(.4)
deadline=time.monotonic()+600
while time.monotonic()<deadline:
    text=log.read_text('utf-8',errors='replace')[start:]
    if 'joined the game' in text:
        send('chunky pause');result='paused_for_player';break
    if 'Task finished' in text or 'Task completed' in text:
        result='complete';break
    time.sleep(5)
else:send('chunky pause');result='paused_time_budget'
lines=[line for line in text.splitlines() if '[Chunky]' in line]
(ROOT/'.lab/reports/pregen-v02.json').write_text(json.dumps({'result':result,'center':[672,752],'radius':768,'shape':'circle','log':lines[-12:]},indent=2),'utf-8')
print(result+'\n'+'\n'.join(lines[-3:]),flush=True)
