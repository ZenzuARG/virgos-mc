"""Apply corrected UTF-8 service text without rebuilding any market blocks."""
from pathlib import Path
import json,gzip,hashlib,shutil,struct,re,uuid,time,zipfile
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def command(value):
 with (R/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write(value+'\n')
def log():return (R/'.runtime/public-console.log').read_text('utf-8',errors='replace')
def wait(test,timeout=300):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if test():return
  time.sleep(1)
 raise RuntimeError('Text verification timed out')
assert not read(R/'.runtime/active-run.json').get('backupInProgress')
old=json.load(gzip.open(R/'config/virgos/mercado-v12.blocks.json.gz','rt',encoding='utf-8'))
source=R/'.lab/v12/overrides/config/virgos/mercado-v12.blocks.json.gz'
new=json.load(gzip.open(source,'rt',encoding='utf-8'))
assert old['blocks']==new['blocks'] and old['palette']==new['palette']
services=read(R/'.lab/v12/overrides/config/virgos/services.json')
assert 'Elegí uno' in services['npcs'][1] and 'Bruno · Mercado' in services['npcs'][1]
assert not any('\u00c3' in s or '\u00c2' in s for s in services['npcs'])
targets=['config/virgos/services.json','config/virgos/mercado-v12.blocks.json.gz','virgos_world/virgos-build-mercado-v12-state.json']
with zipfile.ZipFile(R/'backups/v12-service-text-before.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in targets:z.write(R/name,name)
for rel in targets[:2]:
 for base in [R,R/'pack/server-overrides']:shutil.copy2(R/'.lab/v12/overrides'/rel,base/rel)
wait(lambda:'Virgos: AuthMe bridge ready' in log() and 'Voice chat server started' in log())
for snbt in services['npcs']:
 ints=list(map(int,re.search(r'UUID:\[I;([^]]+)\]',snbt).group(1).split(',')))
 identifier=uuid.UUID(bytes=struct.pack('>4i',*ints))
 command('data merge entity '+str(identifier)+' '+snbt)
for a,b in zip(old['blockEntities'],new['blockEntities']):
 if a!=b:command('data merge block '+ ' '.join(str(b[k]) for k in ['x','y','z'])+' '+b['nbt'])
time.sleep(2)
offset=len(log())
for key in ['guia','mercado','encargos','cronista']:
 identifier=uuid.uuid5(uuid.NAMESPACE_URL,'virgos-mc/services/'+key)
 command('data get entity '+str(identifier)+' DialogData')
command('data get block 633 115 789 front_text')
wait(lambda:all(word in log()[offset:] for word in ['Elegí uno','Alma · Guía','Lía · Encargos','Nora · Cronista','Clic en tablón']),30)
text=log()[offset:];assert '\u00c3' not in text and '\u00c2' not in text
state=R/targets[2];data=read(state);digest=hashlib.sha256(source.read_bytes()).hexdigest();data['blueprintSha256']=digest
temp=state.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n','utf-8');temp.replace(state)
p=R/'.lab/reports/v12-promotion.json';data=read(p);data['marketBlueprintSha256']=digest;data['serviceTextUtf8Verified']=True;p.write_text(json.dumps(data,indent=2)+'\n','utf-8')
(R/'.lab/reports/v12-service-text.json').write_text(json.dumps({'passed':True,'npcCount':4,'changedSigns':1,'marketBlocksChanged':0,'verified':'Round-trip NPC dialog and sign NBT from public server; UTF-8 exact text'},indent=2)+'\n','utf-8')
command('save-all flush');time.sleep(3);command('virgos checkpoint')
print('Public NPC/sign text corrected and verified; final checkpoint requested.',flush=True)
