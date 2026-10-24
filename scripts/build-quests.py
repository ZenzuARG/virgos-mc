"""Build the Spanish codex with explicit personal progression and modest rewards.

Heracles 1.1.13 codecs were inspected; live codec/registry and client checks follow.
Quest IDs are stable: changing text never discards a player's completed quest.
"""
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTS = {}
GROUPS = []


def item_task(item, amount=1):
    return {'type': 'heracles:item', 'item': item, 'amount': amount, 'collection': 'AUTOMATIC'}


def check(title='Leído y entendido'):
    return {'type': 'heracles:check', 'title': title}


def advancement(identifier):
    return {'type': 'heracles:advancement', 'advancements': [identifier]}


def dimension(identifier):
    return {'type': 'heracles:changed_dimension', 'to': identifier}


def quest(id, title, group, icon, description, task, deps=(), reward=None, unlock=None):
    if group not in GROUPS:
        GROUPS.append(group)
    index = sum(group in q['display']['groups'] for q in QUESTS.values())
    rewards = {}
    if reward:
        rewards['provisiones'] = {'type': 'heracles:item', 'item': {'id': reward[0], 'count': reward[1]}}
    if unlock:
        rewards['rango'] = {'type': 'heracles:command', 'title': 'Reconocimiento personal',
                            'command': f'advancement grant @s only virgos:{unlock}'}
    QUESTS[id] = {
        'display': {'title': title, 'subtitle': 'Virgos-MC · Tu aventura',
                    'icon': {'type': 'heracles:item', 'item': icon},
                    'description': description,
                    'groups': {group: {'position': [(index % 5 if index // 5 % 2 == 0 else 4-index % 5) * 65, (index // 5) * 75]}}},
        'settings': {'individual_progress': True, 'hidden': 'LOCKED',
                     'unlockNotification': True, 'showDependencyArrow': True,
                     'repeatable': False, 'autoClaimRewards': False},
        'dependencies': list(deps), 'tasks': {'objetivo': task}, 'rewards': rewards}


def route(group, prefix, entries, root='bienvenida'):
    previous = root
    for entry in entries:
        name, title, item, description = entry[:4]
        count = entry[4] if len(entry) > 4 else 1
        id = prefix + '_' + name
        quest(id, title, group, item, description, item_task(item, count), [previous], ('minecraft:bread', 2))
        previous = id
    return previous


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate-v2',action='store_true');options=parser.parse_args()
    v2_content=options.candidate_v2 or json.loads((ROOT/'pack/current-release.json').read_text('utf-8')).get('version','').startswith('2.')
    quest('bienvenida', 'Bienvenido al Bastión', '01 · Primeros pasos', 'minecraft:compass',
          'Este códice es tuyo: el progreso de tus amigos no completa tus misiones. Salí por cualquiera de los cuatro arcos para encontrar el mismo mundo que ves desde la plaza. No hay semanas bloqueadas ni carreras obligatorias. Reclamá las recompensas con el botón del códice.',
          check(), reward=('minecraft:bread', 8))
    quest('cuenta', 'Tu nombre es tu identidad', '01 · Primeros pasos', 'minecraft:tripwire_hook',
          'Usá siempre exactamente el mismo nombre, incluyendo mayúsculas. Registrate con /register contraseña contraseña y luego /login contraseña. Nunca compartas la contraseña ni la reutilices. El servidor guarda misiones, inventario y claims con tu identidad local.', check(), ['bienvenida'])
    quest('proteccion', 'Una base para volver', '01 · Primeros pasos', 'minecraft:shield',
          'Alejate de los accesos protegidos del Bastión. Abrí el mapa y la pantalla de Open Parties and Claims para reclamar hasta 25 chunks. Los claims son personales; podés autorizar a tus amigos. Crear una party no comparte las misiones. No hay chunks cargados permanentemente.', check(), ['bienvenida'])
    quest('botin', 'Un cofre para cada uno', '01 · Primeros pasos', 'minecraft:chest',
          'Los contenedores convertidos por Lootr guardan botín personal: abrilos aunque un amigo ya haya pasado. No se pueden romper ni renovar para farmear. Los drops de jefes normales siguen siendo compartidos; las expediciones Virgos reconocen a cada participante.', check(), ['bienvenida'])
    first = route('01 · Primeros pasos', 'inicio', [
        ('mesa', 'El primer taller', 'minecraft:crafting_table', 'Juntá madera y fabricá una mesa. JEI muestra recetas: R para receta y U para usos.'),
        ('piedra', 'Herramientas confiables', 'minecraft:stone_pickaxe', 'Fabricá un pico de piedra. Explorá cerca, marcá tu base en el mapa y llevá antorchas.'),
        ('hierro', 'Bajo la superficie', 'minecraft:iron_ingot', 'Conseguí ocho lingotes. No necesitás entregar estos objetos: alcanza con llevarlos en el inventario.', 8),
        ('cama', 'Descanso y regreso', 'minecraft:white_bed', 'Fabricá una cama blanca para esta misión y luego teñila como prefieras. Dormir en cama fija tu regreso; los sacos de Comforts no reemplazan la cama.'),
    ])
    quest('explorador', 'Preparado para explorar', '01 · Primeros pasos', 'minecraft:iron_pickaxe',
          'Llevá un pico de hierro y completá los primeros pasos. Reclamá el reconocimiento Explorador. Los caminos de construcción, cocina, industria y magia quedan disponibles a tu ritmo.', item_task('minecraft:iron_pickaxe'), [first, 'proteccion'], ('minecraft:torch', 24), 'explorador')

    route('02 · Hogar y comunidad', 'hogar', [
        ('mochila', 'Todo a mano', 'sophisticatedbackpacks:backpack', 'La mochila básica acompaña desde temprano. Dos mochilas transportadas son suficientes; las mejoras activas funcionan sólo en la equipada.'),
        ('cobre', 'Más espacio', 'sophisticatedbackpacks:copper_backpack', 'Mejorá la mochila con cobre. La capacidad crece, pero no habrá mochilas anidadas ni acumulación ilimitada de mejoras de apilado.'),
        ('almacen', 'Orden en el taller', 'sophisticatedstorage:chest', 'Organizá tus materiales en almacenamiento Sophisticated. Mantené los cofres y sus accesos dentro del claim.'),
        ('cincel', 'Paleta propia', 'chipped:carpenters_table', 'Chipped permite variantes decorativas. Elegí pocos materiales principales y agregá detalles para que tu base tenga identidad.'),
        ('muebles', 'Un lugar habitable', 'handcrafted:hammer', 'El martillo y los muebles de Handcrafted sirven para personalizar interiores. Consultá sus usos en JEI.'),
        ('cuerda', 'Detalles que sirven', 'supplementaries:rope', 'Sumá cuerdas, señales y elementos de Supplementaries a tus construcciones.', 8),
        ('varita', 'Construir con comodidad', 'constructionwand:iron_wand', 'La varita ayuda a construir con tus propios materiales. Respetá los límites del claim y revisá la orientación antes de colocar.'),
    ])
    route('03 · Caminos y descubrimientos', 'viaje', [
        ('mapa', 'Tu cartografía', 'minecraft:compass', 'Xaero guarda tu exploración. Marcá campamentos, rutas y ruinas; compartir coordenadas es una forma útil de colaborar.'),
        ('biomas', 'Un destino natural', 'naturescompass:naturescompass', 'La brújula busca biomas en un radio acotado. Las cuevas de Alex se descubren siguiendo su propia investigación, no con esta brújula.'),
        ('rutas', 'Piedras del camino', 'waystones:warp_stone', 'Primero descubrí los destinos. Los viajes cuestan experiencia y tienen espera; salir del Bastión siempre es caminando.'),
        ('peces', 'Lo que vive en el agua', 'aquaculture:iron_fishing_rod', 'Aquaculture amplía la pesca. Explorá distintos cuerpos de agua para variar tus capturas.'),
        ('animales', 'Compañeros inesperados', 'alexsmobs:animal_dictionary', 'El diccionario explica los animales de Alex y sus interacciones. Leelo antes de acercarte a una especie desconocida.'),
        ('cuevas', 'El cuaderno del investigador', 'alexscaves:cave_book', 'Seguí las pistas de Alex’s Caves y sus tablillas. Cada cueva ofrece una experiencia distinta; llevá suministros y una ruta de salida.'),
    ], root='explorador')

    industry = route('04 · Ingeniería Create', 'create', [
        ('aleacion', 'Aleación de andesita', 'create:andesite_alloy', 'Comenzá por aleación, ejes y engranajes. Mantené presionada la tecla de Ponder indicada en el objeto para ver una demostración.', 8),
        ('rueda', 'El agua trabaja', 'create:water_wheel', 'Montá una pequeña fuente de potencia. No hace falta una granja enorme para empezar.'),
        ('prensa', 'Dar forma', 'create:mechanical_press', 'La prensa abre recetas de placas. Revisá dirección de giro y estrés de la red.'),
        ('mezcla', 'Química de taller', 'create:mechanical_mixer', 'Mezclá en una cuenca; algunas recetas necesitan calor. JEI indica la temperatura requerida.'),
        ('cintas', 'Una línea clara', 'create:belt_connector', 'Las cintas hacen visible el flujo de materiales. Evitá soltar miles de entidades como almacenamiento.'),
        ('laton', 'Del cobre al latón', 'create:brass_ingot', 'Combiná calor y mezcla para producir latón. La producción es progreso técnico, no un atajo a las recompensas cooperativas.', 8),
        ('precision', 'Mecanismos de precisión', 'create:precision_mechanism', 'Armá una secuencia automatizada. Probá primero con pocas piezas antes de escalarla.'),
        ('ensamble', 'Fabricación mecánica', 'create:mechanical_crafter', 'Los ensambladores necesitan una disposición y salida correctas. Usá Ponder.'),
        ('tren', 'La primera estación', 'create:track_station', 'Diseñá estaciones y trenes compactos. Los trenes tienen un límite de 64 bloques y 12 bogies.'),
        ('vias', 'Conectar las bases', 'create:track', 'Coordiná con tus amigos el trazado de una línea. Pedí acceso a los claims por donde pase.', 32),
        ('copias', 'Arquitectura modular', 'copycats:copycat_block', 'Las piezas Copycats adoptan materiales: ideales para detalles sin máquinas de adorno.'),
    ], root='explorador')
    quest('ingeniero', 'Especialista en ingeniería', '04 · Ingeniería Create', 'create:precision_mechanism',
          'Tu taller ya puede abastecer proyectos comunes. Este reconocimiento concede Especialista; también se obtiene por las rutas de magia, sin obligación de completar ambas.', item_task('create:precision_mechanism', 4), [industry], ('minecraft:golden_carrot', 8), 'especialista')

    mage = route('05 · Hechizos y rituales', 'iron', [
        ('tinta', 'La primera tinta', 'irons_spellbooks:common_ink', 'Iron’s Spells utiliza tinta, pergaminos y libros. Empezá con hechizos comunes y aprendé su coste de maná.'),
        ('mesa', 'Mesa de inscripción', 'irons_spellbooks:inscription_table', 'Usá la mesa para preparar tu libro. Cada escuela tiene fortalezas distintas; no necesitás llevarlas todas.'),
        ('pergamino', 'Leer antes de lanzar', 'irons_spellbooks:scroll', 'Conseguí un pergamino. Leé daño, enfriamiento y alcance. Probá los hechizos lejos de construcciones ajenas.'),
        ('rara', 'Afinar tu escuela', 'irons_spellbooks:rare_ink', 'La tinta rara permite avanzar. Combiná ataque, movilidad y apoyo en vez de equipar sólo daño.'),
        ('epica', 'Investigación avanzada', 'irons_spellbooks:epic_ink', 'Guardá los materiales avanzados para tu especialidad. Las habilidades extremas se regulan con progreso personal.'),
    ], root='explorador')
    quest('hechicero', 'Especialista en hechicería', '05 · Hechizos y rituales', 'irons_spellbooks:epic_ink',
          'La experiencia con tintas y pergaminos te reconoce como Especialista. Reclamá la recompensa para registrar el rango.', item_task('irons_spellbooks:epic_ink'), [mage], ('minecraft:golden_carrot', 8), 'especialista')
    ars = route('05 · Hechizos y rituales', 'ars', [
        ('libro', 'Tu propio lenguaje mágico', 'ars_nouveau:novice_spell_book', 'Ars Nouveau permite combinar glifos. Empezá por un efecto y un método de lanzamiento sencillo.'),
        ('escriba', 'Aprender glifos', 'ars_nouveau:scribes_table', 'La mesa de escriba transforma materiales en conocimiento. No es necesario fabricar todos los glifos.'),
        ('fuente', 'Fuente renovable', 'ars_nouveau:source_jar', 'Planificá una fuente de energía moderada y cercana a tu base. Nada queda cargado permanentemente al desconectarte.'),
        ('encanto', 'Encantamiento artesanal', 'ars_nouveau:enchanting_apparatus', 'El aparato y sus pedestales forman un conjunto. Revisá ingredientes y fuente necesaria en el libro y JEI.'),
        ('aprendiz', 'Combinaciones útiles', 'ars_nouveau:apprentice_spell_book', 'El segundo libro amplía posibilidades: utilidad, protección y ayuda al grupo.'),
    ], root='explorador')
    quest('arcanista', 'Especialista arcano', '05 · Hechizos y rituales', 'ars_nouveau:apprentice_spell_book',
          'Completaste el taller arcano básico. También es una ruta válida al rango Especialista.', item_task('ars_nouveau:apprentice_spell_book'), [ars], ('minecraft:golden_carrot', 8), 'especialista')

    route('06 · Cocina y vida cotidiana', 'cocina', [
        ('cuchillo', 'La herramienta del cocinero', 'farmersdelight:flint_knife', 'Un cuchillo permite cortar ingredientes y obtener materiales adicionales.'),
        ('tabla', 'Preparar ingredientes', 'farmersdelight:cutting_board', 'Colocá la tabla en una cocina accesible. Las estaciones del Bastión sirven para preparar el primer viaje.'),
        ('olla', 'Comida para la expedición', 'farmersdelight:cooking_pot', 'Platos variados dan comodidad al grupo. Alimentar a un compañero también es aportar.'),
        ('sopa', 'Raciones completas', 'farmersdelight:vegetable_soup', 'Prepará cuatro raciones de sopa. Los objetos de las misiones de cocina no se consumen.', 4),
        ('pasta', 'Del campo al plato', 'farmersdelight:pasta_with_meatballs', 'Combiná agricultura, ganadería y cocina para comidas que valen el viaje.'),
        ('barril', 'Tiempo de fermentación', 'brewinandchewin:keg', 'Brewin’ and Chewin’ agrega fermentación. Consultá la temperatura de cada receta.'),
        ('red', 'Pesca preparada', 'aquaculture:tackle_box', 'Organizá anzuelos, carnadas y equipo. Aquaculture Delight conecta pesca con cocina.'),
    ])
    quest('decoracion', 'Hacer una casa propia', '06 · Cocina y vida cotidiana', 'minecraft:flower_pot',
          'Macaw, Chipped y Handcrafted amplían ventanas, tejados, puentes y muebles. Construí con tu estilo. No convertimos cada bloque decorativo en una tarea obligatoria: el catálogo de JEI es tu paleta.', check(), ['bienvenida'])

    quest('nether', 'Al otro lado del fuego', '07 · Grandes aventuras', 'minecraft:flint_and_steel',
          'Prepará resistencia al fuego, comida y una ruta de regreso. Las fortalezas renovadas de YUNG tienen recorridos más extensos.', dimension('minecraft:the_nether'), ['explorador'], ('minecraft:golden_carrot', 4))
    quest('twilight', 'El bosque crepuscular', '07 · Grandes aventuras', 'minecraft:diamond',
          'Twilight Forest tiene su propia progresión de jefes. Respetá el orden del libro de avances: las zonas protegidas indican que falta una conquista.', dimension('twilightforest:twilight_forest'), ['explorador'], ('minecraft:torch', 24))
    quest('aether', 'Islas sobre las nubes', '07 · Grandes aventuras', 'minecraft:glowstone',
          'El Aether requiere su portal y equipo adaptado. Evitá saltar entre islas sin una forma segura de regresar.', dimension('aether:the_aether'), ['explorador'], ('minecraft:bread', 8))
    quest('end', 'Un horizonte distinto', '07 · Grandes aventuras', 'minecraft:ender_eye',
          'Explorá las fortalezas y coordiná la primera expedición al End. El dragón normal no sustituye las pruebas cooperativas del Bastión.', dimension('minecraft:the_end'), ['nether'], ('minecraft:ender_pearl', 4))
    quest('cataclysm', 'Ruinas de Cataclysm', '07 · Grandes aventuras', 'minecraft:netherite_scrap',
          'Cataclysm contiene jefes de gran dificultad. No aumentamos su vida sin criterio: aprendé sus ataques, prepará resistencias y pedí ayuda. Sus drops normales deben repartirse entre el grupo.', check(), ['nether'])
    quest('mowzie', 'Rivales con personalidad', '07 · Grandes aventuras', 'minecraft:iron_sword',
          'Los enemigos de Mowzie tienen ventanas de ataque y mecánicas propias. Observá antes de atacar; el equipo por sí solo no reemplaza aprender el encuentro.', check(), ['explorador'])
    quest('combate', 'Un arma que te resulte cómoda', '07 · Grandes aventuras', 'minecraft:diamond_sword',
          'Better Combat y Simply Swords cambian alcance y ritmo. Probá cada tipo en un espacio seguro. La preparación incluye comida y utilidad, además del arma.', item_task('minecraft:diamond_sword'), ['explorador'], ('minecraft:cooked_beef', 4))

    quest('cooperar', 'Nadie activa dos sellos', '08 · Expediciones Virgos', 'minecraft:amethyst_shard',
          'Seguí el camino sur hasta el anfiteatro, en 672, 78, 1048. Cada integrante elige /virgos expedicion unirse resonancia, forja o umbral. Cuando estén listos, uno usa /virgos expedicion iniciar. En cada ronda todos tocan un sello; después mantienen clic derecho, con la mano vacía, en sellos distintos durante ocho segundos. Hay tres rondas de sellos y combate. Las recompensas del códice son personales y se reclaman una sola vez.', check(), ['explorador'])
    quest('resonancia', 'Resonancia de las profundidades', '08 · Expediciones Virgos', 'minecraft:echo_shard',
          'Reuní al menos dos jugadores con Explorador. Usen los sellos oeste y este. Enfrentarán husks, esqueletos glaciales y un devastador. Todos deben permanecer vivos, activos y autenticados en la arena; si falta alguien, la prueba se cancela después de diez segundos. Los enemigos de la prueba no dan botín ni experiencia.', advancement('virgos:resonancia'), ['cooperar'], ('minecraft:golden_carrot', 8))
    quest('forja', 'La forja arcana', '08 · Expediciones Virgos', 'minecraft:blaze_powder',
          'Requiere dos o más jugadores con Especialista y Resonancia. Coordiná los sellos oeste y este antes de cada oleada: esqueletos glaciales, vindicadores y devastadores. Llevá comida, equipo y curación; los inventarios no se reemplazan al entrar.', advancement('virgos:forja'), ['resonancia'], ('minecraft:golden_apple', 2))
    quest('umbral', 'Guardián del umbral', '08 · Expediciones Virgos', 'minecraft:ender_eye',
          'Requiere al menos tres jugadores con Especialista y Forja. Activá los tres sellos y superá las oleadas de vindicadores y devastadores. Es una prueba de coordinación del Bastión; los jefes de Cataclysm se encuentran en sus propias estructuras. Tras la victoria, reclamá esta recompensa para obtener Maestro.', advancement('virgos:umbral'), ['forja'], ('minecraft:golden_apple', 2), 'maestro')
    quest('regresar', 'Volver para acompañar', '08 · Expediciones Virgos', 'minecraft:campfire',
          'Podés acompañar a quienes todavía no terminaron una expedición. Sus reconocimientos se conservan individualmente. Ayudar, construir rutas y preparar comida sigue siendo útil después de completar el códice.', check(), ['umbral'])

    intro_positions = {'bienvenida': [0, 0], 'cuenta': [60, -60], 'proteccion': [0, 80],
                       'botin': [0, -60], 'inicio_mesa': [90, 0], 'inicio_piedra': [180, 0],
                       'inicio_hierro': [270, 0], 'inicio_cama': [270, 80], 'explorador': [180, 80]}
    from quests_v02 import extend
    extra_advancements = extend(quest, QUESTS, check, advancement)
    from quests_v11 import extend as extend_teaching
    extend_teaching(quest, QUESTS, check, item_task)
    from quests_v12 import extend as extend_town
    extend_town(quest, QUESTS, check, item_task)
    if v2_content:
        from quests_v2 import extend as extend_world
        extend_world(quest, QUESTS, check, item_task)
    for id, position in intro_positions.items():
        QUESTS[id]['display']['groups']['01 · Primeros pasos']['position'] = position
    if v2_content:
        from layout_codex_v2 import organize
        organize(quest, QUESTS, GROUPS, check)
    for id, value in QUESTS.items():
        assert set(value['dependencies']) <= QUESTS.keys(), id
        assert value['settings']['individual_progress'] and not value['settings']['repeatable']
    # Detect accidental dependency cycles before Heracles silently changes dependencies.
    def visit(id, visiting):
        if id in visiting:
            raise ValueError('Quest dependency cycle: ' + id)
        for parent in QUESTS[id]['dependencies']:
            visit(parent, visiting | {id})
    for id in QUESTS:
        visit(id, set())
    destinations=[ROOT/'.lab/v2/server-overrides',ROOT/'.lab/v2/server'] if options.candidate_v2 else [ROOT/'pack/server-overrides',ROOT/'.lab/server']
    for base in [p/'config/heracles' for p in destinations]:
        folder = base / 'quests'
        folder.mkdir(parents=True, exist_ok=True)
        for id, value in QUESTS.items():
            (folder / (id + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2), 'utf-8')
        (base / 'groups.txt').write_text('\n'.join(GROUPS) + '\n', 'utf-8')
    # Vanilla advancements persist each recognition by UUID and are referenced by the codex.
    for base in [p/'kubejs/data/virgos/advancements' for p in destinations]:
        base.mkdir(parents=True, exist_ok=True)
        for id in ['explorador', 'especialista', 'maestro', 'resonancia', 'forja', 'umbral'] + extra_advancements:
            (base / (id + '.json')).write_text(json.dumps({'criteria': {'earned': {'trigger': 'minecraft:impossible'}}}), 'utf-8')
    (ROOT / ('.lab/v2/quests-index.json' if options.candidate_v2 else 'pack/quests-index.json')).write_text(json.dumps({id: q['display']['title'] for id, q in QUESTS.items()}, ensure_ascii=False, indent=2), 'utf-8')
    print(f'{len(QUESTS)} personal quests, {len(GROUPS)} chapters; live validation pending.')


if __name__ == '__main__':
    main()
