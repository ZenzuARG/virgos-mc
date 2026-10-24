"""Compare a connected QA client's recipes with the server's exported registry."""
from pathlib import Path
import argparse, importlib.util, json, time
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--public',action='store_true');a=p.parse_args()
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
target=ROOT/'client/standard/virgos-qa/recipes-audit.json'
old=target.stat().st_mtime if target.exists() else 0
q.action(2,{'action':'audit_recipes'})
q.wait(lambda:target.exists() and target.stat().st_mtime>old)
time.sleep(.3)
client=json.loads(target.read_text('utf-8'))
server=ROOT if a.public else ROOT/'.lab/server'
registry=json.loads((server/'virgos-reports/registries.json').read_text('utf-8'))
sc=set(registry['recipes']);cc=set(client['recipes'])
report={'checked':datetime.now(timezone.utc).isoformat(),'public':a.public,
        'jeiSynced':client['jeiSynced'],'jeiFallback':client['jeiFallback'],
        'serverRecipes':len(sc),'clientRecipes':len(cc),'missing':sorted(sc-cc),'extra':sorted(cc-sc),
        'setting':'mixin.perf.smart_ingredient_sync=false',
        'passed':client['jeiSynced'] and not client['jeiFallback'] and sc==cc}
out=ROOT/('.lab/reports/recipe-sync-v1-public.json' if a.public else '.lab/reports/recipe-sync-v1.json')
out.write_text(json.dumps(report,indent=2)+'\n','utf-8')
print(json.dumps(report));raise SystemExit(0 if report['passed'] else 1)
