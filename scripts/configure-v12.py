"""Produce scoped expansion overrides and stage them only in the stopped lab."""
from pathlib import Path
import json,re,shutil,zipfile
R=Path(__file__).resolve().parents[1];L=R/'.lab/server';OUT=R/'.lab/v12/overrides';CLIENT=R/'.lab/v12/client-overrides'
assert json.loads((L/'process.json').read_text())['finished']
def write(rel,text,client=False):
    for base in [OUT,L]+([CLIENT,R/'client/standard'] if client else []):
        p=base/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,'utf-8')
def settings(rel,changes,client=False):
    src=(L/rel).read_text('utf-8');section='';lines=[];seen=set()
    for line in src.splitlines():
        s=line.strip()
        if s.startswith('['):section=s[1:-1]
        if '=' in s and not s.startswith('#'):
            key=s.split('=',1)[0].strip();full=section+'.'+key if section else key
            if full in changes:
                line=line[:len(line)-len(line.lstrip())]+key+'='+changes[full];seen.add(full)
        lines.append(line)
    assert seen==set(changes),(rel,set(changes)-seen)
    write(rel,'\n'.join(lines)+'\n',client)
settings('config/everycomp-hazardous.toml',{'module.blacklist':'["chipped", "lightmanscurrency"]'},True)
settings('config/lightmanscurrency-server.txt',{'bank_accounts.interest':'0.0','compat.claim_purchasing.allowClaimPurchase':'false','compat.claim_purchasing.allowForceloadPurchase':'false'})
settings('config/lightmanscurrency-common.txt',{
 'crafting.canCraftNetworkTrader':'true','crafting.canCraftTraderInterface':'true',
 'crafting.canCraftAuctionStand':'true','crafting.canCraftTaxCollector':'true',
 'crafting.canCraftATMCard':'true','crafting.coin_mint.canCraftCoinMint':'true',
 'crafting.coin_mint.canMint':'true','crafting.coin_mint.canMelt':'true',
 'events.startingRewards':'false','villagers.addCustomWanderingTrades':'false',
 'villagers.addBanker':'false','villagers.addCashier':'false',
 'loot.entities.enabled':'false','loot.entities.allowFakePlayerDrops':'false','loot.chests.enabled':'false'},True)
settings('virgos_world/serverconfig/smallships-server.toml',{
 'Ship.General.Modifier.shipGeneralCannonDestruction':'0.0','Ship.General.Modifier.shipGeneralCannonDamage':'0.0',
 'Ship.General.shipGeneralCollisionDamage':'0.0'})
# Keep default configurations for new dimensions consistent with the overworld.
small=(L/'virgos_world/serverconfig/smallships-server.toml').read_text('utf-8')
write('defaultconfigs/smallships-server.toml',small)
for world in L.glob('virgos_world*'):
    if world.is_dir() and (world/'serverconfig').exists():
        write(str(world.relative_to(L)/'serverconfig/smallships-server.toml'),small)
mel=json.loads((L/'config/immersive_melodies.json').read_text());mel.update(maxAudibleDistance=24,instrumentVolumeFactor=.65,forceMobsToPickUp=False,rightClickToDropEntityInstrumentPermissionLevel=2)
mel['mobInstrumentFactors']={k:0 for k in mel['mobInstrumentFactors']}
write('config/immersive_melodies.json',json.dumps(mel,indent=2)+'\n',True)
bounty=json.loads((L/'config/bountiful/bountiful.json').read_text());bounty.update(shouldBountiesHaveTimersAndExpire=False,boardUpdateFrequency=120,maxNumRewards=1)
write('config/bountiful/bountiful.json',json.dumps(bounty,indent=2)+'\n')
def pool(rows):
    return {'replace':True,'content':{f'virgos_{i}':{'type':'item','content':item,'amount':{'min':lo,'max':hi},'unitWorth':worth} for i,(item,lo,hi,worth) in enumerate(rows)}}
pools={
 'virgos_cocina':pool([('minecraft:wheat',12,24,20),('minecraft:carrot',12,24,20),('minecraft:potato',12,24,20),('minecraft:cod',4,8,70),('minecraft:pumpkin',3,6,90)]),
 'virgos_taller':pool([('create:andesite_alloy',2,4,130),('create:shaft',4,8,65),('minecraft:glass',8,16,35),('minecraft:brick',8,16,35)]),
 'virgos_caminos':pool([('minecraft:gravel',16,32,18),('minecraft:stone_bricks',12,24,25),('minecraft:oak_sapling',4,8,70),('minecraft:lantern',2,4,130)]),
 'virgos_provisiones':pool([('minecraft:bread',2,4,140),('minecraft:cooked_cod',2,4,150),('minecraft:torch',8,16,35),('minecraft:paper',4,8,80),('minecraft:flower_pot',1,2,280)])}
for key,value in pools.items():write('config/bountiful/bounty_pools/'+key+'.json',json.dumps(value,indent=2)+'\n')
# Replace every built-in decree's reward route, including random village boards.
with zipfile.ZipFile(R/'.cache/pack/downloads/Bountiful-6.0.4+1.20.1-forge.jar') as z:
    for name in z.namelist():
        if '/bounty_decrees/' not in name or not name.endswith('.json'):continue
        key=Path(name).stem
        target='virgos_cocina' if key in ['farmer','fisherman','butcher','shepherd'] else 'virgos_taller' if key in ['inventor','armorer','toolsmith'] else 'virgos_caminos'
        write('config/bountiful/bounty_decrees/'+key+'.json',json.dumps({'replace':True,'objectives':[target],'rewards':['virgos_provisiones']},indent=2)+'\n')
# Restrict NPC editing to administrators; all players may read dialogs normally.
path='config/easy_npc/security.cfg';s=(L/path).read_text()
s=re.sub(r'(?m)^(feature\.[^=]+)=.*$',r'\1=ADMIN',s)
s=re.sub(r'(?m)^executeAsUserCommandAllowList.ALL=.*$','executeAsUserCommandAllowList.ALL=',s)
write(path,s)
for rel in ['virgos_world/serverconfig/openpartiesandclaims-server.toml','defaultconfigs/openpartiesandclaims-server.toml']:
    source=R/rel
    if not source.exists():continue
    s=source.read_text('utf-8')
    for key,extra in [('forcedBlockProtectionExceptionList',['lightmanscurrency:shelf_oak','bountiful:bountyboard']),('forcedEntityProtectionExceptionList',['hand$easy_npc:villager']),('itemUseProtectionExceptionList',['bountiful:bounty','exposure:camera','exposure:album','exposure:signed_album','immersive_melodies:flute','immersive_melodies:lute'])]:
        m=re.search(r'(?m)^(\s*'+key+r'\s*=\s*)(\[.*\])$',s);assert m,key
        values=json.loads(m[2]);values=list(dict.fromkeys(values+extra))
        s=s[:m.start(2)]+json.dumps(values)+s[m.end(2):]
    write(rel,s)
# Audit rare renewables before enabling the integration; retain processing and decorative recipes.
blocked=[]
with zipfile.ZipFile(R/'.cache/pack/downloads/create_alexscaves_compat-1.20.1-1.6.2.jar') as z:
    for name in z.namelist():
        if not name.startswith('data/') or '/recipes/' not in name or not name.endswith('.json'):continue
        if any(x in name for x in ['/mixing/uranium','/mixing/amber','/mixing/fissile','/compacting/uranium','/compacting/fissile','/filling/uranium']):
            ns=name.split('/')[1];rid=ns+':'+name.split('/recipes/')[1][:-5];blocked.append(rid)
write('kubejs/server_scripts/virgos_expansion.js',"// Virgos-MC: keep every recipe supplied by the installed mods.\n"
      "// Economy, claims and naval damage are controlled by native configuration.\n"
      "ServerEvents.recipes(event => {});\n")
(R/'.lab/v12/configuration.json').write_text(json.dumps({'barterFirst':True,'noCurrencyMinting':False,'noTimedBounties':True,'everyCompatExcludedModules':['chipped','lightmanscurrency'],'blockedIntegrationRecipes':[]},indent=2)+'\n')
print('Expansion configuration staged; native recipes remain available.')
