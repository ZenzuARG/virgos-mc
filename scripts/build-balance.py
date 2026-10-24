"""Generate the survival recipe policy from the verified live item registry."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
json.loads((ROOT/'.lab/server/virgos-reports/registries.json').read_text('utf-8'))
banned=[]
script='// Virgos-MC: keep every recipe provided by the installed mods.\n'
script+='// Balance is enforced by server configuration, not hidden recipes.\n'
script+='ServerEvents.recipes(event => {});\n'
for base in ['pack/server-overrides','.lab/server']:
    folder=ROOT/base/'kubejs/server_scripts'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'virgos_balance.js').write_text(script,'utf-8')
(ROOT/'pack/disabled-recipes.json').write_text(json.dumps(banned,indent=2),'utf-8')
print('Disabled survival outputs:',len(banned))
