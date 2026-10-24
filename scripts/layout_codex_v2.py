"""Ten short sections, visible learning routes, and readable guide introductions."""
from collections import defaultdict
import re

SECTIONS=[
 ('01 · Empezar',[1,9,12],'minecraft:compass','Tu primera sesión','Cuenta, controles y primeros materiales. Abrí Empezá por acá y seguí los objetivos de supervivencia. Las guías se pueden leer sin completar todos los tutoriales.'),
 ('02 · Tu hogar',[2,17],'minecraft:oak_door','Una base segura','Protección de terrenos, permisos y almacenamiento. Los claims son personales; compartir una party no comparte automáticamente tus misiones.'),
 ('03 · Create',[4,13,26,29],'create:cogwheel','Del primer eje al taller','Aprendé primero energía y transmisión. Después, procesamiento y automatización. La arqueología de las ruinas es una ruta opcional para aplicar lo aprendido.'),
 ('04 · Magia',[5,14,15],'minecraft:enchanted_book','Elegí tu escuela','Ars Nouveau e Iron’s Spellbooks tienen rutas propias. Los rangos personales y las expediciones regulan la magia avanzada; no hace falta dominar ambas escuelas a la vez.'),
 ('05 · Explorar',[3,16,19,27,28],'minecraft:filled_map','Salir con un plan','Preparación, biomas, aldeas y la investigación de Alex’s Caves. Una ruta corta también cuenta: marcá ida, regreso y un objetivo concreto.'),
 ('06 · Cocina',[6,18],'farmersdelight:cooking_pot','Comer y vivir bien','Cultivos, cocina, pesca y vida cotidiana. Abastecer a otros y preparar provisiones son aportes útiles sin competir por el mejor equipo.'),
 ('07 · Aventuras',[7,24,30,33,34],'minecraft:spyglass','Viajes grandes','Fortalezas, navegación y dimensiones. Las ramas son alternativas: prepará la que te interese, acordá una retirada y volvé cuando tengas tiempo.'),
 ('08 · Jefes',[11,31,32],'minecraft:diamond_sword','Retos y trofeos','Meet Your Fight tiene una cadena de cuatro invocadores; otros jefes viven en el mundo. Los trofeos normales se reparten entre jugadores. Los reconocimientos cooperativos están en la sección 09.'),
 ('09 · Cooperar',[8,20],'minecraft:amethyst_shard','Juntos en la arena','Resonancia, Forja y Umbral requieren varias personas activas. Cada integrante conserva su reconocimiento. Podés volver para ayudar sin repetir la recompensa personal.'),
 ('10 · El pueblo',[10,21,22,23,25],'minecraft:bell','La vida entre aventuras','Servicios, mercado, encargos, fotografías y música. Rutas opcionales que dan vida al servidor sin sumar una obligación diaria.')]

def organize(quest,quests,groups,check):
 original=defaultdict(list)
 for identifier,q in list(quests.items()):
  name=next(iter(q['display']['groups']));original[int(name.split(' ',1)[0])].append(identifier)
 for section,numbers,icon,title,description in SECTIONS:
  overview='indice_'+section[:2]
  quest(overview,title,section,icon,description+'\n\nCómo leer este códice\nElegí un capítulo en la izquierda. Buscá una misión por nombre o filtrá Pendientes y Para reclamar. Clic en una fila abre sus pasos; las bloqueadas explican qué falta. Usá las flechas para cambiar de página. Una casilla es lectura o práctica manual; un objeto se detecta en el inventario. Las recompensas se reclaman dentro de cada misión. Mi perfil muestra tus horas y el avance por capítulo. Ver mapa original conserva el diagrama de dependencias.',check('Entendí cómo usar esta sección'))
  quests[overview]['display']['groups']={section:{'position':[-64,0]}}
  quests[overview]['display']['subtitle']='GUÍA DE LA SECCIÓN · Abrí para orientarte'
  row=0
  for number in numbers:
   identifiers=original[number]
   if not identifiers:continue
   route_name=next(iter(quests[identifiers[0]]['display']['groups'])).split(' · ',1)[1]
   for i,identifier in enumerate(identifiers):
    q=quests[identifier]
    # Compact rows preserve reading order; each original route starts a fresh row.
    x=(i%6)*56;y=(row+i//6)*64
    q['display']['groups']={section:{'position':[x,y]}}
    task=next(iter(q['tasks'].values()))['type']
    kind={'heracles:check':'GUÍA','heracles:item':'OBJETO','heracles:advancement':'LOGRO','heracles:changed_dimension':'VIAJE'}.get(task,'OBJETIVO')
    q['display']['subtitle']=f'{route_name} · {kind} · {i+1}/{len(identifiers)}'
    # Avoid long diagonal arrows linking independent tracks across the map.
    q['settings']['showDependencyArrow']=all(dep in identifiers and identifiers.index(dep)//6==i//6 for dep in q['dependencies'])
    text=q['display']['description'].replace('620, 115, 787','620, 80, 787').replace('632, 115, 787','632, 80, 787')
    # Old numerical chapter references become named sections after consolidation.
    lookup={n:name for name,nums,*_ in SECTIONS for n in nums}
    text=re.sub(r'(?i)cap[ií]tulo\s+(\d+)',lambda m:'sección «'+lookup.get(int(m[1]),m[1])+'»',text)
    q['display']['description']=text
   row+=(len(identifiers)+5)//6+1
 groups[:]=[x[0] for x in SECTIONS]
 # Keep the landing page small and understandable without reading a long guide.
 quests['bienvenida']['display']['title']='Empezá por acá'
 quests['bienvenida']['display']['subtitle']='INICIO · Tu primera misión'
 quests['bienvenida']['display']['icon']['item']='minecraft:compass'
 # Prevent overlapping nodes after grouping and keep all existing quest IDs.
 for group in groups:
  positions=[tuple(q['display']['groups'][group]['position']) for q in quests.values() if group in q['display']['groups']]
  assert len(positions)==len(set(positions)),group
