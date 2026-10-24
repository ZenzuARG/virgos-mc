"""Stable additive codex content; completed quests and ranks are preserved."""
def extend(quest, quests, check, advancement):
    def description(key, value): quests[key]['display']['description']=value
    description('resonancia', 'Dos o más Exploradores. Ronda 1: sellos oeste y este; ronda 2: este y norte; ronda 3: oeste y norte. Todos deben tocar un sello activo y sostener los dos ocho segundos. Después, combate. Los enemigos no dan drops ni XP. Ausentarse diez segundos cancela la prueba.')
    description('forja', 'Dos o más Especialistas con Resonancia. Aportes del grupo: ronda 1, 8 placas de hierro; ronda 2, 4 placas de latón; ronda 3, 1 mecanismo de precisión. Usá /virgos expedicion aportar antes de cargar oeste y este. En combate, un compañero toca cualquier sello cada seis segundos para mantener la refrigeración: sin ella los enemigos son invulnerables. Se pierden los aportes si abandonan.')
    description('inicio_cama', 'Conseguí una cama de cualquier color. Dormir en cama fija tu regreso; los sacos de Comforts no reemplazan la cama. La misión reconoce la cama en tu inventario, sin consumirla.')
    quests['inicio_cama']['tasks']['objetivo']['item']='#minecraft:beds'
    description('umbral', 'Tres o más Especialistas con Forja. El Guardián del Bastión es un devastador con tres fases: cada tercio de vida cierra su barrera y exige activar los tres sellos otra vez. No se pueden saltar fases con un golpe enorme. Los jefes de Cataclysm conservan sus propias estructuras y mecánicas. La victoria concede Maestro al reclamar el códice.')
    description('botin', 'Lootr ofrece botín individual en los contenedores convertidos. Los drops originales de los jefes siguen siendo compartidos; el capítulo Trofeos personales agrega un premio único por jugador a ocho grandes jefes. No se duplican sus drops raros.')
    quest('preparacion', 'Entrar tarde también tiene lugar', '09 · Preparación rápida', 'minecraft:clock',
          'Completá Explorador y reclamá los tres suministros siguientes una sola vez. Podés combinar roles: no son clases permanentes. Alcanzan para preparar una aventura inicial; no regalan Especialista ni Maestro. Un amigo puede prestarte equipo sin completar tus expediciones.', check(), ['explorador'])
    kits = [
        ('vanguardia','Vanguardia: sostener el frente','minecraft:shield',[('minecraft:shield',1),('minecraft:iron_chestplate',1),('minecraft:cooked_beef',8)],'Usá escudo, cobertura y una salida segura. El equipo defensivo sigue importando; avisá por voz cuándo necesitás ayuda.'),
        ('hechiceria','Magia: empezar sin una fábrica','irons_spellbooks:common_ink',[('irons_spellbooks:common_ink',4),('minecraft:paper',16),('minecraft:lapis_lazuli',8)],'Prepará un libro con ataque común, movilidad y apoyo. Las tintas ayudan a empezar; las mesas, el libro y los hechizos siguen siendo parte de tu aventura. La rareza alta exige tu progreso personal.'),
        ('apoyo','Apoyo: cocinar y mantener al grupo','farmersdelight:cooking_pot',[('farmersdelight:cooking_pot',1),('farmersdelight:vegetable_soup',8),('minecraft:torch',32)],'Prepará comida antes de salir y ocupate de los mecanismos cuando otro luche. En los jefes, recibir ataques o lanzar hechizos durante el encuentro también cuenta como participación.')]
    for key,title,icon,items,text in kits:
        quest('kit_'+key,title,'09 · Preparación rápida',icon,text,check(),['preparacion'])
        quests['kit_'+key]['rewards']={str(i):{'type':'heracles:item','item':{'id':item,'count':count}} for i,(item,count) in enumerate(items)}
    quest('balance_arena','El equipo ayuda; el grupo decide','09 · Preparación rápida','minecraft:iron_sword',
          'Sólo en expediciones, daño final por segundo/ráfaga: Resonancia 20/10, Forja 30/18, Umbral 40/24. Se comparte entre todos los blancos de un atacante, incluidos ataques de área. Curación por jugador: 4/6/8 puntos por segundo. Un corazón son dos puntos. El mundo normal conserva el daño de sus mods. No hay topes de horas ni reinicios del progreso.',check(),['preparacion'])
    quest('voz','Hablar durante la aventura','10 · Bastión compartido','minecraft:note_block',
          'Simple Voice Chat: pulsá O para elegir micrófono y auriculares; Bloq Mayús para hablar. El servidor utiliza alcance 32 bloques, susurro 8 y grupos privados opcionales. Iniciá sesión antes de hablar o escuchar. El instalador trae el mod y el servidor informa el túnel automáticamente. Podés jugar sin micrófono.',check(),['bienvenida'])
    extra=[]
    for key,title,item,count,reward in [
        ('cocina','Despensa del Bastión','minecraft:wheat',192,('farmersdelight:vegetable_soup',16)),
        ('taller','Taller comunitario','create:andesite_alloy',192,('create:andesite_casing',8)),
        ('caminos','Materiales para conectar bases','create:track',384,('create:track',64))]:
        identifier='pueblo_'+key;extra.append(identifier)
        quest(identifier,title,'10 · Bastión compartido',item,
              f'El grupo aporta {count} de {item} desde el Bastión con /virgos pueblo aportar {key}. Los objetos se consumen y cada persona puede aportar como máximo un tercio: hacen falta al menos tres. Al completarlo, cada Explorador recibe esta recompensa una vez, incluso si se incorporó después. Son suministros para construir juntos; las rutas y edificios los diseña el grupo.',advancement('virgos:'+identifier),['explorador'],reward)
    for key,title in [('guardian','Guardián del End'),('monstruosidad','Monstruosidad de netherita'),('heraldo','El Heraldo'),('ignis','Ignis'),('remanente','Remanente ancestral'),('maledictus','Maledictus'),('forjado','Ferrous Wroughtnaut'),('dragon','Dragón del End')]:
        identifier='jefe_'+key;extra.append(identifier)
        quest(identifier,title,'11 · Trofeos personales','minecraft:diamond',
              'Premio único de primera victoria. Permanecé vivo y a menos de 40 bloques al morir el jefe, habiendo participado durante al menos tres segundos: daño equivalente al 1% de su vida, o tres aportes de apoyo (recibir ataques/lanzar hechizos espaciados). La actividad debe ser reciente. El botín original sigue en el mundo para repartir. Repetir la victoria ayuda a tus amigos, pero no vuelve a dar este premio.',advancement('virgos:'+identifier),['explorador'],('minecraft:diamond',2))
    return extra
