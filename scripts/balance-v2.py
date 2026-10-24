"""Build reviewable v2 overrides. Only writes the isolated candidate."""
from pathlib import Path
import copy, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.lab/v2'
DEST=[OUT/'server-overrides',OUT/'server']
changes=[]
def write(rel,value):
    for base in DEST:
        p=base/rel;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')

sets=json.loads((OUT/'structure-sets-original.json').read_text())
tuning={
 'integrated_villages/regular_villages':(30,20),
 'idas/idas_common':(26,15),'idas/idas_small':(24,16),
 'idas/idas_rare':(60,32),'idas/idas_nether':(45,28),
 'dungeons_arise/major_structures':(80,52),
 'dungeons_arise/minor_structures':(48,30),
 'incendium/greater_structures':(40,24),
 'incendium/lesser_structures':(26,16),
 'terralith/rare_village':(56,28),
}
for key,original in sets.items():
    data=copy.deepcopy(original);p=data['placement']
    short=key.split('/')[1]+'/'+key.rsplit('/',1)[1][:-5]
    if short in tuning:p['spacing'],p['separation']=tuning[short]
    # Keep Kayra ships a 44.8 MB legacy NBT template. Upgrading it exhausted
    # the 6 GiB lab heap during native location/generation. Keep the other 30
    # major structure types; do not require a large heap just for this castle.
    if short=='dungeons_arise/major_structures':
        data['structures']=[s for s in data['structures'] if s['structure']!='dungeons_arise:keep_kayra']
    if short in {'dungeons_arise/major_structures','dungeons_arise/minor_structures','terralith/rare_village'}:
        p['exclusion_zone']={'other_set':'integrated_villages:regular_villages','chunk_count':10}
    if data!=original:
        assert p['spacing']>p['separation']>=0
        write('kubejs/'+key,data)
        changes.append({'file':key,'before':original['placement'],'after':p})

# One-way priority: villages -> large dungeons -> IDAS. No cyclic exclusions.
tags=json.loads((OUT/'structure-tags-original.json').read_text())
for name in ['common_avoid','rare_avoid','small_avoid','underground_rare_avoid']:
    key=f'data/idas/tags/worldgen/structure_set/{name}.json'
    data=copy.deepcopy(tags[key])
    data['values']+=['integrated_villages:regular_villages','dungeons_arise:major_structures']
    write('kubejs/'+key,data)
    changes.append({'file':key,'added':data['values'][len(tags[key]['values']):]})

# Preserve themed loot and unique equipment. Reduce only bulk end-game materials
# in the added structure packs; existing boss rewards and vanilla loot stay intact.
loot_changes=[];repairs=[]
def rebalance(node,edits):
    if isinstance(node,list):
        for n in node:rebalance(n,edits)
    elif isinstance(node,dict):
        name=node.get('name','')
        replacements={'minecraft:netherite_block':'minecraft:netherite_scrap',
                      'minecraft:netherite_ingot':'minecraft:netherite_scrap',
                      'minecraft:diamond_block':'minecraft:diamond',
                      'minecraft:enchanted_golden_apple':'minecraft:golden_apple'}
        if node.get('type') in {'minecraft:item','item'} and name in replacements:
            node['name']=replacements[name]
            functions=[f for f in node.get('functions',[]) if f.get('function') not in {'minecraft:set_count','set_count'}]
            functions.append({'function':'minecraft:set_count','count':1})
            node['functions']=functions;edits.append({'from':name,'to':node['name'],'count':1})
        for n in node.values():rebalance(n,edits)
for a in json.loads((OUT/'additions.json').read_text()):
    if a['project'] not in {'idas','when-dungeons-arise','when-dungeons-arise-seven-seas','integrated-villages','integrated-stronghold'}:continue
    with zipfile.ZipFile(ROOT/'.cache/pack/downloads'/a['filename']) as z:
        for name in z.namelist():
            if '/loot_tables/chests/' not in name or not name.endswith('.json'):continue
            raw=z.read(name).decode('utf-8');fixed=False
            try:data=json.loads(raw,strict=False)
            except json.JSONDecodeError:
                decoder=json.JSONDecoder(strict=False);documents=[]
                while raw.strip():
                    raw=raw.lstrip();doc,end=decoder.raw_decode(raw);documents.append(doc);raw=raw[end:]
                assert len(documents)==2 and documents[0]['pools']==documents[1]['pools'],name
                data=documents[0];fixed=True;repairs.append({'file':name,'repair':'remove duplicated JSON document with identical pools'})
            edits=[];rebalance(data,edits)
            if edits or fixed:write('kubejs/'+name,data);loot_changes.append({'file':name,'edits':edits})

# Correct an upstream stale village ID, retaining every installed contributor.
village_key='data/minecraft/tags/worldgen/structure/village.json'
villages=['minecraft:village_'+b for b in ['plains','desert','savanna','snowy','taiga']]
for a in json.loads((OUT/'mods.lock.json').read_text())['artifacts']:
    if 'server' not in a.get('sides',[]):continue
    file=ROOT/'.cache/pack/downloads'/a['filename']
    if not file.exists():continue
    with zipfile.ZipFile(file) as z:
        if village_key in z.namelist():villages+=json.loads(z.read(village_key))['values']
villages=[v for v in villages if v!='integrated_villages:swamp_village']
villages.append('integrated_villages:sunken_village')
unique=list({json.dumps(v,sort_keys=True):v for v in villages}.values())
write('kubejs/'+village_key,{'replace':True,'values':unique})
repairs.append({'file':village_key,'repair':'swamp_village does not exist; use sunken_village and retain installed contributors'})

# IDAS includes optional BYG/BOP and Ice & Fire resources even without those mods.
idas=next(a for a in json.loads((OUT/'additions.json').read_text()) if a['project']=='idas')
with zipfile.ZipFile(ROOT/'.cache/pack/downloads'/idas['filename']) as z:
    for name in z.namelist():
        if name.startswith('data/idas/tags/worldgen/biome/') and name.endswith('.json'):
            data=json.loads(z.read(name));changed=False
            for i,value in enumerate(data['values']):
                if isinstance(value,str) and value.startswith(('byg:','biomesoplenty:')):
                    data['values'][i]={'id':value,'required':False};changed=True
            if changed:
                data['replace']=True
                write('kubejs/'+name,data)
        if '/loot_tables/' in name and name.endswith('.json') and b'iceandfire:' in z.read(name):
            write('kubejs/'+name,{'type':'minecraft:chest','pools':[]})
    write('kubejs/data/idas/integrated_structure_spawners/dread_citadel.json',{'mobs':[{'name':'minecraft:stray','weight':1}]})

# A short, repeatable boss chain ties trophies to Create without daily limits.
recipes=json.loads((OUT/'myf-recipes-original.json').read_text())
keys={
 'fossil_bait':{'B':{'item':'create:andesite_alloy'}},
 'haunted_bell':{'S':{'item':'meetyourfight:mossy_tooth'},'G':{'item':'create:brass_ingot'}},
 'devils_ante':{'D':{'item':'meetyourfight:phantoplasm'}},
 'dusk_key':{'D':{'item':'meetyourfight:fortunes_favor'},'S':{'item':'create:precision_mechanism'}},
}
for name,updates in keys.items():
    key=f'data/meetyourfight/recipes/{name}.json';data=copy.deepcopy(recipes[key]);data['key'].update(updates)
    write('kubejs/'+key,data)

# Native recipes are intentionally left intact. Claims protect bases and do
# not depend on hiding a movement item from JEI.
js="""// Virgos-MC: native recipes stay available.
ServerEvents.recipes(event => {});
"""
for base in DEST:
    p=base/'kubejs/server_scripts/virgos_v2.js';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(js,'utf-8')
(OUT/'balance-report.json').write_text(json.dumps({'structureChanges':changes,'lootChanges':loot_changes,'upstreamRepairs':repairs,
 'bossRecipeChanges':keys,'disabledRecipes':[],
 'status':'candidate-requires-runtime-validation'},ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'structureChanges':len(changes),'lootTablesAdjusted':len(loot_changes),'bossRecipes':len(keys)}))
