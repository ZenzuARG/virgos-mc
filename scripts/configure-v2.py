"""Apply the reviewed configuration policy to a stopped candidate only."""
from pathlib import Path
from datetime import datetime,timezone
import argparse, json, re, shutil, tomllib
ROOT=Path(__file__).resolve().parents[1];V2=ROOT/'.lab/v2';LAB=V2/'server'
p=argparse.ArgumentParser();p.add_argument('--archive-ocean-preview',action='store_true');args=p.parse_args()
state=json.loads((LAB/'process.json').read_text());assert state.get('finished') and state['exitCode']==0
dest=V2/'server-overrides'; report={}
def edit_toml(relative,updates):
    file=LAB/relative;text=file.read_text('utf-8');before=tomllib.loads(text)
    for key,value in updates.items():
        encoded=json.dumps(value,ensure_ascii=False)
        # All edited leaf names below are unique within their file.
        pattern=r'(?m)^(\s*)(?:'+re.escape(json.dumps(key))+r'|'+re.escape(key)+r')\s*=.*$'
        text,n=re.subn(pattern,lambda m:m[1]+json.dumps(key,ensure_ascii=False)+' = '+encoded,text)
        assert n==1,(relative,key,n)
    after=tomllib.loads(text);assert before!=after or all(key in text for key in updates)
    for base in [LAB,dest]:
        f=base/relative;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,'utf-8')
    report[relative]=updates

edit_toml('config/quark-common.toml',{
 'automation':False,'experimental':False,'oddities':False,
 'Enable Onboarding':False,"Enable 'q' Button":False,
 'Inventory Sorting':False,'Ancient Tomes':False,'Pickarang':False,
 'Glimmering Weald':False,'Big Stone Clusters':False,
 'Nether Obsidian Spikes':False,'Spiral Spires':False,'No More Lava Pockets':False})
edit_toml('config/guardvillagers-common.toml',{
 'How many guards should spawn in a village?':4,'Chance to drop equipment':8.5,
 'Have guards patrol the village regularly?':True,
 'Guards attack all mobs?':False,
 "Allow guard arrows to damage villagers, iron golems, or other guards? The i-frames will still be shown for them but they won't lose any health if this is set to false":False})
edit_toml('config/meetyourfight-common.toml',{
 'slicerDiceMultiplier':1.5,'slicerDiceLuck':False,'aceOfIronLuck':False,
 'blossomingMindBonus':0.5,'blossomingMindCap':5})
bossfile='config/bosses_of_mass_destruction.json5';boss=json.loads((LAB/bossfile).read_text())
boss['lichConfig']['eternalNighttime']=False
boss['gauntletConfig']['spawnAncientDebrisOnDeath']=False
for name in ['lichConfig','obsidilithConfig','gauntletConfig','voidBlossomConfig']:boss[name]['experienceDrop']=400
for base in [LAB,dest]:
    f=base/bossfile;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(boss,indent=2)+'\n','utf-8')
report[bossfile]={'eternalNighttime':False,'spawnAncientDebrisOnDeath':False,'experienceDrop':400,'bossHealth':'author defaults'}
# Clients use the same Quark feature set and menu settings.
client=V2/'client-overrides/config';client.mkdir(parents=True,exist_ok=True)
shutil.copy2(LAB/'config/quark-common.toml',client/'quark-common.toml')

if args.archive_ocean_preview:
    archive=V2/'previews/seed-ocean';assert not archive.exists()
    archive.mkdir(parents=True)
    worldconfigs=V2/'worldconfigs-preview';assert not worldconfigs.exists()
    shutil.copytree(LAB/'virgos_world/serverconfig',worldconfigs)
    for world in list(LAB.glob('virgos_world*')):
        if not world.is_dir():continue
        assert world.resolve().is_relative_to(LAB.resolve()) and (archive/world.name).resolve().is_relative_to(V2.resolve())
        shutil.move(str(world),str(archive/world.name))
    shutil.copytree(worldconfigs,LAB/'virgos_world/serverconfig')
    props=LAB/'server.properties';text=props.read_text()
    text=re.sub(r'(?m)^level-seed=.*$', 'level-seed=-4556043908712459124',text);props.write_text(text,'utf-8')
    report['previewArchive']=str(archive);report['nextSeed']=-4556043908712459124
report['updated']=datetime.now(timezone.utc).isoformat()
(V2/'config-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'configuredFiles':4,'previewArchived':args.archive_ocean_preview}))
