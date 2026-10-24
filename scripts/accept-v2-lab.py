"""Freeze lab acceptance from completed reports and the exact tested artifacts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,runpy
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2';L=V/'server'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(L/'process.json')['exitCode']==0
assert read(R/'client/qa-v2/virgos-qa/process.json')['exitCode']==0
assert not list((L/'kubejs').rglob('zz_qa*'))
ui=read(V/'final-ui.json');assert ui['passed'] and len(ui['checks'])==8
installer=read(V/'installer-integration.json');assert installer['passed'] and installer['required']==114
world=read(V/'worldgen-tests.json');assert len(world['tests'])==17 and all(t['located'] for t in world['tests'])
assert all(t['generated'] for t in world['tests'] if t['type']=='structure')
audit=read(L/'virgos-reports/auditoria-pueblo-v2-audit.json')
assert audit['checked']==90518 and not any(audit[k] for k in ['unsupported','missing','wrongBlocks','blockedWalkChecks','routeProblems'])
log=(L/'console.log').read_text('utf-8',errors='replace')
cleanup=log.rfind('Unmarked all force loaded chunks in minecraft:overworld');assert cleanup>=0
assert 'No force loaded chunks were found in minecraft:overworld' in log[cleanup:]
assert 'Loaded 3/3 KubeJS server scripts' in log
assert len(list((L/'config/heracles/quests').glob('*.json')))==244
assert (V/'clockwork-village-loaded.png').stat().st_size>10000
nbt=runpy.run_path(str(R/'scripts/inspect-nbt.py'))['read_nbt']
score=nbt(L/'virgos_world/data/scoreboard.dat')['']['data']
assert all(not s['Name'].lower().startswith('virgosqa') for s in score.get('PlayerScores',[]))
for p in (L/'virgos_world/data/openpartiesandclaims/player-claims').glob('*.nbt'):
    if not p.stem.startswith('00000000-'):assert not nbt(p)['']['dimensions'],p
# The final combined audit verifies the manually pruned vines against this
# blueprint; record that verified patch without rerunning construction.
marker=L/'virgos_world/virgos-build-pueblo-v2-state.json';m=read(marker)
m['blueprintSha256']=sha(L/'config/virgos/pueblo-v2.blocks.json.gz')
m['verifiedPatch']='Removed entrance vines; final combined audit passed with zero route failures'
marker.write_text(json.dumps(m,indent=2),'utf-8')
core=R/'dev/virgos-core/build/libs/virgos_core-2.0.0.jar';codex=core.with_name('virgos_codex-2.0.0.jar')
assert sha(core)==sha(L/'mods'/core.name)
assert sha(codex)==sha(R/'client/qa-v2/mods'/codex.name)
out={'passed':True,'completed':datetime.now(timezone.utc).isoformat(),'coreSha256':sha(core),'codexSha256':sha(codex),'clientMemoryMb':6144,'worldProbes':len(world['tests']),'uiChecks':ui['checks'],'spawnBlocks':audit['checked'],'evidence':['runtime-checks.json','profile-offline-test.json','final-ui.json','worldgen-tests.json','generated-content.json','installer-integration.json','server/virgos-reports/auditoria-pueblo-v2-audit.json'],'limits':['No eight-player load test','No human microphone listening test','No full new-boss combat balance playtest','Public endpoint and Discord release still pending']}
(V/'acceptance.json').write_text(json.dumps(out,indent=2)+'\n','utf-8');print(json.dumps(out,indent=2))
