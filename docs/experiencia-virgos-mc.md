# Diseño de la experiencia de Virgos-MC

> Propuesta original del 17 de octubre, conservada como referencia. La [visión vigente](vision-servidor.md) define el objetivo del servidor y el [roadmap auditado](roadmap-auditoria.md) registra lo implementado y probado. Las duraciones y sistemas más amplios de este documento son ideas de expansión, no promesas de funciones instaladas.

Diseño del 17 de octubre de 2026 para Minecraft Java 1.20.1, hasta ocho jugadores y progreso híbrido: cada persona desarrolla su personaje y su base a su ritmo; algunas expediciones requieren cooperación. La selección de contenido está cerrada para la primera versión completa; la instalación y validación son la etapa siguiente.

**Recomendación:** combinar exploración, magia y tecnología con cuatro niveles de equipo, expediciones repetibles y un pueblo que todos puedan mejorar. Quien juega más tendrá más proyectos, variedad y recursos; quien juega menos podrá preparar un equipo útil y participar de una aventura completa en una sesión.

El progreso libre produce diferencias de riqueza y equipamiento. El objetivo del balance es que esas diferencias no vuelvan irrelevantes a los demás ni permitan que una sola persona agote las aventuras del grupo.

**Misiones y protección propuestas: Heracles + Open Parties and Claims + Xaero's World Map.** Sustituyen a FTB en este diseño. La revisión de identidad y progreso ofrece un mejor fundamento para el servidor en modo offline, pero todavía no es una combinación probada con Ketting y AuthMe. La [comparación de alternativas](alternativas-ftb.md) documenta la elección y la prueba necesaria.

## Cómo se jugaría

Al entrar, el jugador encuentra una guía en español y un pueblo con espacios para talleres, huertas, transporte y comercio. Puede construir su casa, elegir una primera rama y explorar. Las ramas se pueden combinar y cambiar: ingeniería con Create, magia con Iron's Spells, combate, exploración y cocina/construcción.

Ese pueblo será el **Bastión Virgos**, una ciudadela de unos 160 × 160 bloques integrada en el Overworld. Desde su plaza se sale caminando por cuatro arcos monumentales hacia el terreno generado. El [diseño del spawn y los plugins](spawn-y-plugins.md) fija su estética, espacios, protección y forma de colocación.

La preparación de una expedición puede hacerse por separado. Cuando coinciden dos o más amigos, se reúnen para un encuentro de 20 a 40 minutos como objetivo de diseño. La finalización otorga progreso a quienes participaron. El encuentro queda disponible para repetirlo con otro grupo; el primero que lo completa no se lleva una oportunidad exclusiva.

Como punto de partida, propongo PvE y protección de bases. El PvP quedaría para duelos consensuados. La dificultad depende de la zona y de la actividad elegida: que un veterano avance no vuelve peligrosos todos los alrededores de un recién llegado.

## Progreso individual y aventuras compartidas

Los siguientes niveles son una estructura propuesta del paquete, no niveles que los mods ya compartan entre sí.

| Nivel | Camino personal | Actividad cooperativa | Recompensa principal |
| --- | --- | --- | --- |
| Inicio | Refugio, mochila básica, comida, primer hechizo y máquina sencilla | Construcción del pueblo, opcional | Herramientas para empezar y acceso a todas las ramas |
| Explorador | Cuevas, estructuras, equipo especializado y transporte | Primera expedición para 2 personas | Primera especialización de aventura y trofeo |
| Especialista | Fábricas, mejores hechizos, equipo elegido por estilo | Expediciones para 2–4 personas | Nuevas variantes de equipo y habilidades de expedición |
| Maestro | Grandes construcciones, colecciones y automatización avanzada | Desafíos para 3–4 personas; eventos especiales para más | Cosméticos, títulos y variantes finales con ventajas y desventajas |

Las expediciones desbloquean parte del equipo de aventura avanzado. Las herramientas de construcción, la cocina y la mayor parte de Create siguen teniendo un recorrido individual. Así, un constructor no necesita completar todos los jefes para disfrutar de su rama.

No habría esperas semanales obligatorias ni requisitos de conexión diaria. Para un grupo de ocho, exigir que los ocho estén presentes bloquearía demasiadas actividades; reservaría esa escala para eventos ocasionales.

### Tres expediciones propias

Estas mecánicas requieren scripts o un pequeño mod propio. Son diseños a prototipar; Alex's Caves, Create e Iron's Spells no las incluyen como un sistema conjunto.

| Expedición | Grupo y duración orientativa | Cooperación necesaria | Vínculo con el mundo |
| --- | --- | --- | --- |
| Resonancia de las profundidades | 2–3, 20–25 min | Dos jugadores mantienen mecanismos separados y alternan quién combate y quién los activa | Exploración y materiales de Alex's Caves |
| La forja arcana | 2–4, 25–35 min | Entregar suministros a tiempo mientras otro jugador controla un ritual y sus defensores | Preparación industrial con Create y recursos mágicos |
| El guardián del umbral | 3–4, 30–40 min | Objetivos simultáneos interrumpen fases del jefe; curación, control y daño tienen utilidad | Jefe seleccionado de Cataclysm si sus eventos permiten adaptarlo |

El mínimo debe comprobarse durante las fases importantes, con jugadores activos y autenticados. Una placa que se pueda dejar presionada con un objeto o una mascota no cumple la finalidad. Debemos contemplar muerte, desconexión, entrada tardía y reinicio de la arena.

Empezaría con una arena reutilizable y una expedición. Las mazmorras privadas simultáneas para cada grupo ampliarían considerablemente el desarrollo y quedarían para una expansión.

## Balance para horarios diferentes

1. **Botín personal en estructuras.** Lootr permite que cada jugador encuentre su propio contenido en los contenedores compatibles. Debemos comprobar las estructuras elegidas. Los bloques extraídos, los enemigos ya muertos y sus objetos sueltos siguen siendo compartidos; las recompensas de jefes se resuelven aparte. [Lootr](https://www.curseforge.com/minecraft/mc-mods/lootr).

2. **Equipo con un techo por nivel.** Cada nivel define rangos de daño, defensa, curación, movilidad y regeneración. Revisamos combinaciones completas: arma, hechizos, accesorios, comida y encantamientos. No basta con rebajar el daño de una espada si un accesorio multiplica todo el conjunto.

3. **Más opciones al final del progreso.** El equipo avanzado permite estilos distintos, coleccionar y especializarse. Evitaría una cadena interminable de multiplicadores de daño y defensa. En desafíos de un nivel anterior, usaríamos un conjunto permitido para ese nivel y equipo de préstamo accesible. Esto necesita validación de inventarios y accesorios; no asumir una normalización automática universal.

4. **Recompensa por participación.** Una expedición reconoce objetivos, apoyo y presencia activa, además del combate. El último golpe no determina quién progresa. El desbloqueo principal se obtiene una vez por personaje; repetir permite ayudar, conseguir consumibles moderados y coleccionables. Sin recompensa de poder por quedarse AFK.

5. **Camino corto para ponerse al día.** Misiones de preparación, equipamiento funcional barato, estaciones compartidas y transporte al punto de reunión. Alguien que vuelve no tiene que repetir decenas de horas de recolección para ser útil. Las recompensas se limitan por hito, sin regalos diarios que premien iniciar sesión.

6. **Comercio útil.** Se pueden intercambiar materiales, comida y equipo corriente. Las pocas habilidades de expedición que exijan una hazaña personal conservan ese requisito aunque otro jugador regale el objeto. Evitaría vender recursos ilimitados a una tienda del servidor: una fábrica funcionando todo el día convertiría tiempo de conexión en riqueza sin límite.

7. **Automatización con presupuesto.** Create conserva su atractivo para quien juega mucho. Empezaríamos con carga forzada de chunks deshabilitada; después podríamos habilitar una cuota pequeña y solamente con el dueño conectado. Los chunks cargados por otros jugadores pueden seguir funcionando: esto reduce carga y acumulación, pero no iguala por sí solo las horas de producción.

8. **Recuperación de muerte razonable.** Propongo tumba recuperable en exploración, si supera las pruebas de inventario, y devolución controlada del equipo de préstamo en expediciones. Evitaría perder permanentemente una mochila completa por un fallo o una desconexión. El mod de tumbas se elige al resolver el paquete y sus dependencias.

Un ejemplo: alguien que juega cuatro horas semanales prepara un equipo de apoyo y entra en una expedición con un amigo que juega veinte. El veterano aporta experiencia, suministros y variedad, pero el encuentro sigue necesitando la participación de ambos. El primero puede aportar curación y mecanismos sin alcanzar la riqueza del segundo.

## Contenido recomendado

La selección comprende 79 mods principales, cuatro opciones visuales y WorldEdit como herramienta de construcción, además de las bibliotecas necesarias. Las versiones candidatas, destinos y condiciones están en [el catálogo](catalogo-mods-virgos-mc.md). La combinación completa debe probarse antes de distribuirla.

| Área | Selección propuesta | Papel en la experiencia |
| --- | --- | --- |
| Cuevas y fauna | Alex's Caves, Alex's Mobs | Expediciones, materiales distintos y un mundo con más vida |
| Magia de combate | Iron's Spells 'n Spellbooks | Daño, apoyo y control; revisar potencia, costes y tiempos de reutilización |
| Ingeniería | Create, Steam 'n' Rails, Connected, Deco y Copycats+ | Talleres, fábricas, trenes y proyectos compartidos |
| Mochilas y almacén | Sophisticated Backpacks y Sophisticated Storage | Comodidad desde temprano; mejoras potentes escalonadas |
| Combate físico | Better Combat y Simply Swords | Armas con estilos propios y animaciones; equilibrar armas únicas del botín |
| Jefes y dimensiones | Cataclysm, Mowzie's Mobs, Twilight Forest y Aether | Encuentros variados y dos dimensiones adicionales |
| Magia de utilidad | Ars Nouveau y Ars Creo | Utilidad mágica y conexión con Create; revisar su solapamiento con Iron's Spells |
| Terreno y estructuras | Regions Unexplored, ocho renovaciones de YUNG's, YUNG's Bridges, Explorify y Towns and Towers | Paisajes y lugares interesantes, con separación ajustada |
| Cocina y pesca | Farmer's Delight, Delightful, Brewin' and Chewin', Aquaculture y Aquaculture Delight | Preparación del grupo, pesca y vida del pueblo; Central Kitchen conecta la cocina con Create |
| Construcción | Supplementaries, Amendments, Chipped, Handcrafted y seis módulos de Macaw | Variedad de edificios, puentes, tejados, muebles e iluminación |
| Viajes y tesoros | Waystones, Lootr, selección de Artifacts | Reunirse rápido, conservar botín para todos y encontrar recompensas especiales |

**Conexiones propuestas entre mods:** Create fabrica suministros de expedición; las cuevas aportan componentes para algunas mejoras; la cocina prepara alimentos útiles para el grupo; la magia aporta control y apoyo. Estas conexiones se implementarían con recetas y recompensas concretas, manteniendo cortos los requisitos entre ramas.

La mochila básica debería llegar pronto. Las mejoras de apilado, alimentación automática y almacenamiento dentro de otras mochilas necesitan límites: comodidad temprana no tiene que significar capacidad prácticamente infinita.

Iron's Spells permite ajustar hechizos individualmente. Sus versiones recientes de 1.20.1 cambiaron el sistema de configuración de hechizos a JSON; los ajustes deben escribirse para la versión fijada, sin copiar configuraciones antiguas. [Cambios oficiales de Iron's Spells](https://iron.wiki/changelog/).

Regions Unexplored queda elegido como único gran paquete de biomas del Overworld. Biomes O' Plenty, Terralith, Tectonic y When Dungeons Arise quedan fuera de esta versión. Se ajustará la separación de las estructuras elegidas antes de generar el mundo definitivo.

Dejaría Apotheosis, ProjectE, Mystical Agriculture y grandes cadenas de generación automática fuera de la selección inicial: incorporar sus progresiones requeriría rehacer el balance propuesto. Tampoco empezaría con grandes colonias de NPC o física de vehículos; primero mediría el margen real de CPU. Son decisiones de alcance, no afirmaciones de incompatibilidad.

## Una interfaz que explique el paquete

La entrada principal sería el **Códice Virgos**, con capítulos en español construidos en Heracles. Su versión Forge 1.20.1 está publicada como Heracles 1.1.13, aunque la página actual del proyecto se llama Odyssey Quests. El códice organizaría objetivos personales, expediciones y ayuda. [Archivo oficial para Forge 1.20.1](https://modrinth.com/mod/odyssey-quests/version/1.1.13).

| Sección del códice | Qué resuelve |
| --- | --- |
| Primeros pasos | Login, controles, proteger una base, mochila, comida y primera rama |
| Mi camino | Misiones de ingeniería, magia, exploración y construcción |
| Expediciones | Número de jugadores, preparación, duración, mecánicas y recompensa |
| Pueblo | Proyectos comunitarios y servicios disponibles |
| Ayuda | Recetas, muerte, transporte y problemas frecuentes |

JEI muestra recetas; Jade explica el bloque o entidad que se mira; AppleSkin ayuda con comida. Open Parties and Claims (OPAC) protegería las bases y Xaero's World Map permitiría gestionar los terrenos desde el mapa. Controlling y Default Options permiten entregar controles coherentes. FancyMenu quedaría para una portada del cliente con acceso al servidor y ayuda.

Los objetos especiales explicarían su nivel, utilidad y requisito en el tooltip. La misma terminología debe aparecer en recetas, misiones y mensajes. Las notificaciones sólo señalarían avances relevantes; evitaría llenar la pantalla de barras y mensajes permanentes.

**Las misiones personales tendrán `individual_progress=true` en Heracles.** Esa opción existe por misión y su valor predeterminado es falso; se establecerá expresamente al escribir el códice. Los grupos de OPAC servirán para permisos de la base. No se presupone que esos grupos se integren automáticamente con el sistema de equipos de Heracles. [Configuración de misiones de Heracles 1.20.x](https://github.com/terrarium-earth/Heracles/blob/1.20.x/common/src/main/java/earth/terrarium/heracles/api/quests/QuestSettings.java).

Las expediciones tendrán un registro propio de participantes. Al terminar, el servidor acreditará el hito a cada participante válido; estar en el mismo grupo o compartir casa no bastará para recibirlo. La validación debe cubrir clientes premium y no premium, progreso al reconectar y tras reiniciar, y restricciones antes del login de AuthMe.

KubeJS, KubeJS Create y datapacks conectarían recetas, textos y eventos. El prototipo de expedición elegirá comandos o API de Heracles para acreditar objetivos desde el servidor, sin asumir un puente automático con KubeJS. Los requisitos personales de uso de equipo requieren comprobar inventarios, Curios y hechizos: ocultar una receta en JEI no impide usar un objeto recibido de otro jugador. Decursio Stages queda en reserva hasta determinar si hace falta; no forma parte de los 79 seleccionados. [KubeJS](https://kubejs.com/wiki/tutorials/), [código de Heracles](https://github.com/terrarium-earth/Heracles/tree/1.20.x).

OPAC incluye integración con Create en Forge y permite compartir acceso a claims personales. Sigue publicado como beta: la protección frente a máquinas, hechizos y explosiones se comprobará con las versiones elegidas. Se usará su sistema de grupos propio y se empezará sin carga forzada de chunks. [Funciones y alcance de OPAC](https://modrinth.com/mod/open-parties-and-claims).

## Servidor y rendimiento

La máquina anfitriona tiene un Ryzen 7 5700X y aproximadamente 32 GB de RAM. El servidor actual usa hasta 4 GB; propongo evaluar **8 GB para el paquete completo**, dejando espacio para Windows y el cliente cuando se juegue en la misma PC. Más memoria no resuelve una máquina o un jefe que consume demasiado tiempo de CPU.

| Perfil | Punto de partida para probar | Condición |
| --- | --- | --- |
| Cliente estándar | 5–6 GB de memoria Java, sin shaders, distancia 8–10 chunks | Ajustar al mínimo real del grupo y medir también memoria fuera de Java |
| Cliente visual | 6–8 GB de memoria Java, shaders opcionales | Oculus y renderizado de Create deben funcionar juntos en las versiones fijadas |
| Servidor | Hasta 8 GB de memoria Java, visión 8 y simulación 6 inicialmente | Medir exploración, fábrica y combate simultáneos con hasta ocho jugadores |

Los dos perfiles de cliente tendrán exactamente el mismo contenido y reglas. Cambiar shaders no debe cambiar qué objetos o mods jugables están disponibles. Con mods de contenido todos necesitarán el paquete Forge; el cliente vanilla que sirve para la base actual dejará de ser suficiente.

ModernFix y FerriteCore son candidatos para carga y memoria. Embeddium, Entity Culling e ImmediatelyFast se evaluarán en el cliente. Spark sirve para encontrar el origen de los problemas, y Chunky para pregenerar terreno una vez cerrada la selección de biomas y estructuras. [ModernFix](https://github.com/embeddedt/ModernFix/blob/1.20/README.md), [FerriteCore](https://modrinth.com/mod/ferrite-core), [spark](https://spark.lucko.me/docs), [Chunky](https://modrinth.com/mod/chunky).

La meta de las pruebas será mantener 20 TPS y margen bajo los 50 ms por tick. Como objetivo inicial, buscaríamos percentil 95 por debajo de 40 ms en recorridos representativos ya generados, registrando por separado los picos de generación y guardado. Son criterios de aceptación, no resultados medidos del futuro paquete. [Explicación de TPS y MSPT](https://spark.lucko.me/docs/guides/TPS-and-MSPT).

Los 79 componentes seleccionados incluyen contenido, interfaz, integración y operación; no son 79 expansiones grandes. Las bibliotecas aumentarán el total de archivos. La medición del paquete decidirá qué efectos y configuraciones ajustar y si alguna incorporación necesita revisión.

## Plugins e integración con la base actual

Mantendría Ketting para el primer ensayo porque la base, AuthMe y Playit Companion ya funcionan juntos. Ketting se declara beta; que dos mods funcionen con Forge no prueba que funcionen entre sí ni con el puente Bukkit. [Ketting](https://kettingpowered.org/).

El contenido, las misiones, los claims y el balance se resolverían principalmente con mods Forge. AuthMe conserva registro/login y Playit Companion el túnel integrado hacia `virgos-mc.playit.plus`. LuckPerms Bukkit queda seleccionado para permisos administrativos. WorldEdit Forge será una herramienta del laboratorio para construir y colocar el spawn. El [plan de plugins](spawn-y-plugins.md) detalla responsabilidades y versiones.

PacketEvents ya causó un fallo de conexión con la combinación actual y fue retirado. No debe volver como dependencia indirecta sin una prueba aislada. Tampoco se instalarían dos sistemas de claims, dos mapas completos o las versiones mod y plugin del mismo perfilador. World Map y Minimap de Xaero son complementarios dentro de una misma selección.

El login debe probarse de nuevo con el paquete: antes de autenticarse no se debería poder abrir mochilas, lanzar hechizos, reclamar recompensas ni modificar inventarios mediante paquetes de los mods. La prueba previa con cliente vanilla no demuestra ese comportamiento. Si AuthMe no puede proteger esas acciones en Ketting, habrá que resolverlo antes de publicar el paquete.

El chat de voz de proximidad queda condicionado a un túnel UDP adicional compatible con la solución integrada. El túnel de Minecraft actual no lo aporta automáticamente; no se instalará una aplicación de Playit por fuera del proyecto para resolverlo.

Si un componente central falla por Ketting, la comparación será reproducirlo en Forge puro. Una eventual migración también debe resolver autenticación y conservar el túnel integrado; no basta con reemplazar el ejecutable del servidor.

## Implementación posterior

| Paso | Resultado concreto | Condición para continuar |
| --- | --- | --- |
| 1. Laboratorio | Copia separada, versiones fijas y cliente reproducible | Arranque, entrada real y reinicio; la copia no activa otro túnel público |
| 2. Núcleo jugable | Create, Alex's Caves, Iron's Spells, mochilas, Lootr, misiones y optimización | Dos clientes completan una ruta corta y conservan inventarios y progreso |
| 3. Primer cooperativo | Una arena, roles intercambiables y recompensa individual | Un jugador no completa la mecánica; dos sí; muerte y desconexión no duplican premios |
| 4. Mundo y spawn | Biomas, estructuras, dimensiones y Bastión Virgos colocado | Generación estable, cuatro salidas físicas y ciudadela protegida |
| 5. Balance y rendimiento | Equipos por nivel, recetas conectadas y perfiles de cliente | Prueba con un jugador nuevo y uno avanzado, además de carga concurrente |
| 6. Apertura | Paquete de cliente, respaldo y procedimiento de restauración | Entrada pública, login, guardado y recuperación comprobados |

El mundo definitivo debe generarse con la selección final de contenido de terreno. El mundo actual se respalda; cualquier sustitución se hace explícitamente en esa etapa. No se elimina ni regenera terreno como parte de este diseño.

Cada versión distribuida fijará mods, dependencias, configuraciones, scripts y recursos del cliente. Una restauración debe recuperar el mundo y el paquete correspondiente juntos. Los datos de AuthMe y las credenciales de Playit pertenecen sólo al servidor.

La primera entrega jugable debería demostrar una sesión completa: entrar, entender el códice, obtener mochila y equipo básico, construir una máquina, usar un hechizo, encontrar botín personal y completar una expedición de dos jugadores. Ese recorrido permite comprobar la propuesta antes de ampliar el catálogo.
