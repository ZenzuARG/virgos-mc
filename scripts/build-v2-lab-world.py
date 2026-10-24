"""Apply reviewed blueprints sequentially to the local-only v2 candidate."""
from pathlib import Path
import json,time
ROOT=Path(__file__).resolve().parents[1];LAB=ROOT/'.lab/v2/server'
props=(LAB/'server.properties').read_text();assert 'server-port=25575' in props and 'server-ip=127.0.0.1' in props
def command(text):
    with (LAB/'console-commands.txt').open('a',encoding='utf-8') as f:f.write(text+'\n')
def wait(test,seconds=900):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if test():return
        if json.loads((LAB/'process.json').read_text()).get('finished'):raise RuntimeError('Lab stopped')
        time.sleep(2)
    raise TimeoutError('Lab operation timed out')
def log():return (LAB/'logs/latest.log').read_text('utf-8',errors='replace')
wait(lambda:'Done (' in log(),240)
for name in ['pueblo-v2','mercado-v2','arena-virgos-v3']:
    state=LAB/'virgos_world'/('virgos-build-'+name+'-state.json')
    def complete():
        try:return json.loads(state.read_text()).get('complete',False)
        except (FileNotFoundError,json.JSONDecodeError):return False
    if not complete():command('virgos build '+name);wait(complete)
    command('virgos audit '+name);print('Built and requested audit:',name,flush=True);time.sleep(3)
for cmd in ['setworldspawn 672 80 752','gamerule spawnRadius 0','gamerule doInsomnia false','gamerule playersSleepingPercentage 0','time set 6000','weather clear','virgos servicios instalar','save-all flush']:command(cmd)
print('Candidate town, market, arena and services staged. Visual/protection tests still required.',flush=True)
