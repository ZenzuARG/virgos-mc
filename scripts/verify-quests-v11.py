from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'pack/server-overrides/config/heracles/quests'
quests={p.stem:json.loads(p.read_text('utf-8')) for p in base.rglob('*.json')}
old={p.stem:json.loads(p.read_text('utf-8')) for p in (ROOT/'config/heracles/quests').rglob('*.json')}
registry=json.loads((ROOT/'.lab/server/virgos-reports/registries.json').read_text('utf-8'))
items=set(registry['items']);tags=set(registry['itemTags']);seen=set();visiting=set();positions=set();groups=set()
def item(value):
    assert (value[1:] in tags if value.startswith('#') else value in items),value
def visit(key):
    assert key not in visiting,('cycle',key)
    if key in seen:return
    visiting.add(key)
    for d in quests[key].get('dependencies',[]):assert d in quests,(key,d);visit(d)
    visiting.remove(key);seen.add(key)
for key,q in quests.items():
    visit(key);item(q['display']['icon']['item'])
    assert q['settings']['individual_progress'] and not q['settings']['repeatable']
    for group,data in q['display']['groups'].items():
        position=(group,*data['position']);assert position not in positions,position
        positions.add(position);groups.add(group)
    for task in q['tasks'].values():
        if task['type']=='heracles:item':item(task['item'])
    if key in old:
        for field in ('tasks','rewards','dependencies','settings'):assert q.get(field)==old[key].get(field),(key,field)
    else:assert not q.get('rewards'),('unintended new reward',key)
assert old.keys()<=quests.keys()
report={'passed':True,'quests':len(quests),'chapters':len(groups),'added':len(quests.keys()-old.keys()),
        'preservedExistingQuestIdsAndRewards':len(old),'registryChecked':True,'acyclicDependencies':True,'uniqueChapterPositions':True}
(ROOT/'.lab/reports/quests-v11-static.json').write_text(json.dumps(report,indent=2),'utf-8')
print(json.dumps(report))
