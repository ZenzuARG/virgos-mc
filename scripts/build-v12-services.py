"""Build additive market services in reserved, unoccupied spawn grounds."""
from pathlib import Path
import json,gzip,uuid,struct,zipfile,re
R=Path(__file__).resolve().parents[1];OUT=R/'.lab/v12/overrides'
def write(rel,value):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value,'utf-8')
palette=[];blocks={};bes=[]
def block(x,y,z,s):
 if s not in palette:palette.append(s)
 blocks[(x,y,z)]=palette.index(s)
def fill(x1,y1,z1,x2,y2,z2,s):
 for x in range(x1,x2+1):
  for y in range(y1,y2+1):
   for z in range(z1,z2+1):block(x,y,z,s)
def sign(x,y,z,lines):
 block(x,y,z,'minecraft:oak_sign[rotation=0,waterlogged=false]')
 messages=[json.dumps(json.dumps({'text':s,'color':'dark_green'},ensure_ascii=False),ensure_ascii=False) for s in lines]
 bes.append({'x':x,'y':y,'z':z,'nbt':'{is_waxed:1b,front_text:{messages:['+','.join(messages)+'],color:"black",has_glowing_text:0b}}'})
# This is an additive small plaza; it never reapplies the village blueprint.
fill(599,114,774,635,114,800,'minecraft:stone_bricks')
fill(600,115,775,634,123,799,'minecraft:air')
fill(600,114,775,634,114,799,'minecraft:gravel')
fill(634,114,785,672,114,789,'minecraft:gravel')
fill(635,115,785,669,117,789,'minecraft:air')
stalls=[]
for row,z in enumerate([780,794]):
 for col,x in enumerate([604,612,620,628]):
  n=row*4+col+1;stalls.append([x,115,z])
  facing='south' if row==0 else 'north'
  fill(x-2,114,z-1,x+2,114,z+1,'minecraft:spruce_planks')
  for dx in [-2,2]:
   for dz in [-1,1]:fill(x+dx,115,z+dz,x+dx,117,z+dz,'minecraft:stripped_spruce_log[axis=y]')
  for dx in range(-3,4):fill(x+dx,118,z-2,x+dx,118,z+2,'minecraft:'+('green' if (dx+3)%2==0 else 'white')+'_wool')
  block(x,115,z,'lightmanscurrency:shelf_oak[facing='+facing+']')
  sign(x,115,z+(2 if row==0 else -2),['Puesto '+str(n),'Reservar:', '/virgos mercado','reservar '+str(n)])
  block(x-1,117,z,'minecraft:lantern[hanging=true,waterlogged=false]')
block(632,115,787,'bountiful:bountyboard')
for x,z in [(600,787),(634,775),(634,799)]:
 fill(x,115,z,x,117,z,'minecraft:spruce_fence');block(x,118,z,'minecraft:lantern[hanging=false,waterlogged=false]')
sign(633,115,789,['Encargos','Sin vencimiento','Clic en tablón','/virgos guia'])
blueprint={'schema':2,'name':'Mercado Virgos 1.2','origin':[599,114,774],'spawn':[672,115,752],'palette':palette,'fills':[],
 'blocks':[[*p,i] for p,i in blocks.items()],'blockEntities':bes,'walkChecks':[],'routes':[]}
p=OUT/'config/virgos/mercado-v12.blocks.json.gz';p.parent.mkdir(parents=True,exist_ok=True)
with gzip.GzipFile(filename=str(p),mode='wb',mtime=0) as f:f.write(json.dumps(blueprint,ensure_ascii=False).encode())
def npc(key,name,pos,topic,text,profession):
 u=uuid.uuid5(uuid.NAMESPACE_URL,'virgos-mc/services/'+key);ints=struct.unpack('>4i',u.bytes)
 def s(v):return json.dumps(v,ensure_ascii=False)
 lessons={
  'inicio':['J abre tus misiones. Empezá por Primeros pasos y Aprender el servidor. Completá el objetivo y reclamá la recompensa para activar tu reconocimiento.','Salí por los arcos para buscar una base. F3+G muestra chunks; /oclaims claim protege el que pisás. P abre permisos. /virgos menu reúne la ayuda.','Create, magia, cocina y exploración avanzan a tu ritmo. Las expediciones exigen compañeros. /virgos progreso muestra tu siguiente paso.'],
  'mercado':['Elegí uno de los ocho puestos. Acercate y usá /virgos mercado reservar N con su número. Cada persona puede reservar uno; no muevas el bloque.','Abrí el puesto. El botón de cofre entra al almacén; la flecha de la oferta abre su edición. Usá Trueque, elegí lo que pedís y lo que entregás.','El cofre lateral muestra existencias. Depositá el producto allí. Las ventas consumen stock. Conservá la comparación NBT para equipo y mochilas. /virgos guia mercado da más ayuda.'],
  'encargos':['Abrí el tablón de al lado. Elegí un encargo acorde a tus materiales y llevate su papel. Mirá las cantidades pedidas y la recompensa. No vencen.','Conseguí los materiales, sostené el papel y hacé clic derecho en el tablón. Se consumen los materiales y recibís las provisiones. No entrega rangos.','Los encargos son opcionales y repetibles. Las misiones permanentes siguen en J. Podés dejar un trabajo para otra sesión sin perder una racha.'],
  'fotografia':['Buscá @exposure en JEI. Fabricá cámara y película; cargala antes de fotografiar. Probá con una escena cerca del pueblo y buena luz.','Revelá la película y usá el cuarto oscuro siguiendo JEI. Guardá fotografías en un álbum o exhibilas en marcos dentro de tu base.','Propuesta: un retrato del grupo, tu primer taller y una expedición. J tiene un capítulo de fotografía. /virgos guia fotografia recuerda los pasos.']}
 entries=[]
 def button(label,target=None):
  action_id=uuid.uuid5(u,label+':'+str(target))
  action_nbt='[I;'+','.join(map(str,struct.unpack('>4i',action_id.bytes)))+']'
  return '{Name:'+s(label)+',Label:'+s('go_'+(target or 'close'))+',Type:"DEFAULT",Actions:[{Id:'+action_nbt+',PermLevel:0,Type:'+s('OPEN_NAMED_DIALOG' if target else 'CLOSE_DIALOG')+((',Cmd:'+s(target)) if target else '')+'}]}'
 entries.append('{Name:'+s(name)+',Label:"default",Text:'+s(text)+',Buttons:['+button('Ver guía','guia')+','+button('Hasta luego')+']}')
 for i,lesson in enumerate(lessons[topic]):
  label='guia' if i==0 else 'paso'+str(i+1)
  nextlabel='paso'+str(i+2) if i<2 else 'default'
  entries.append('{Name:'+s(name)+',Label:'+s(label)+',Text:'+s(lesson)+',Buttons:['+button('Siguiente' if i<2 else 'Volver',nextlabel)+','+button('Cerrar')+']}')
 dialog='{Type:"STANDARD",DialogDataSet:['+','.join(entries)+']}'
 return '{id:"easy_npc:villager",UUID:[I;'+','.join(map(str,ints))+'],Pos:['+','.join(str(v)+'d' for v in pos)+'],Rotation:[180f,0f],NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,Tags:["virgos_service"],CustomName:'+s(json.dumps({'text':name,'color':'gold'},ensure_ascii=False))+',CustomNameVisible:1b,VillagerData:{type:"minecraft:plains",profession:"minecraft:'+profession+'",level:2},ActionData:{ActionPermissionLevel:0,ActionEventSet:{ON_INTERACTION:[{Type:"OPEN_DEFAULT_DIALOG"}]}},DialogData:'+dialog+'}'
npcs=[npc('guia','Alma · Guía',[673.5,115,750.5],'inicio','Bienvenido al pueblo. J abre tus misiones y /virgos menu reúne la ayuda. Tu progreso es personal; las expediciones importantes necesitan compañeros. ¿Empezamos?','librarian'),
 npc('mercado','Bruno · Mercado',[619.5,115,786.5],'mercado','Ocho puestos, uno por vecino. Acercate a uno libre y reservá su número con /virgos mercado reservar. Depositás tu mercadería y acordás un trueque. Nadie vende recursos infinitos aquí.','toolsmith'),
 npc('encargos','Lía · Encargos',[630.5,115,786.5],'encargos','¿Tenés un rato corto? El tablón ofrece trabajos de cocina, taller y caminos. No vencen y sus premios son provisiones. Revisá siempre qué materiales entregarás antes de cobrar.','farmer'),
 npc('cronista','Nora · Cronista',[677.5,115,752.5],'fotografia','Cada visita merece una historia. Exposure permite tomar fotografías y armar álbumes. Empezá por un retrato del grupo; después buscá tu lugar favorito del mundo.','cartographer')]
write('config/virgos/services.json',json.dumps({'schema':1,'stalls':stalls,'npcs':npcs},indent=2,ensure_ascii=False)+'\n')
# Repair upstream malformed JSON and missing optional tags without changing the official JAR.
with zipfile.ZipFile(R/'.cache/pack/downloads/create_alexscaves_compat-1.20.1-1.6.2.jar') as z:
 n='data/create_alexscaves_compat/recipes/mixing/marine_snow.json'
 fixed=re.sub(r',\s*([\]}])',r'\1',z.read(n).decode());json.loads(fixed)
 write('kubejs/'+n,fixed)
 for key in ['energy_28800','fuel']:
  write('kubejs/data/create_new_age/tags/items/nuclear/'+key+'.json',json.dumps({'replace':True,'values':[]}))
# An unused IDAS bank compatibility table has malformed references in LC.
write('kubejs/data/lightmanscurrency/loot_tables/chest/village/idas_taiga_large_bank.json',json.dumps({'type':'minecraft:chest','pools':[]}))
print('Market:',len(blocks),'blocks;',len(npcs),'NPCs;',len(stalls),'player shops.')
