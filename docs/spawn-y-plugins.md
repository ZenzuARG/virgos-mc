# Spawn y plugins de Virgos-MC

> Actualización 0.1.0-rc1: la selección ya se implementó y se probó en el alcance documentado en [implementación](implementacion.md). Este texto conserva decisiones y propuestas de diseño; para instalar y jugar seguí la [guía actual](guia-jugadores.md).

Diseño para la primera versión completa, 17 de octubre de 2026. **El Bastión Virgos está construido en el Overworld del laboratorio, con cuatro salidas físicas al terreno.** Centro: 672,114,736; aparición: 672,115,752. Todavía no fue publicado en el servidor abierto.

La revisión v4 corrigió el desborde de la fuente, soportes y conexiones, la escalera del archivo y los cimientos de los caminos. La auditoría de 147.542 bloques terminó sin faltantes ni obstáculos en los puntos y rutas comprobados. Un cliente sin OP cruzó las cuatro puertas a pie, abrió la mesa comunal, cocinó una porción de arroz y recibió un rechazo al intentar romper la mesa en creativo. El combate, los hechizos y las máquinas requieren pruebas adicionales de protección.

Las cinco plantillas reales están en `pack/spawn`: ciudadela y cuatro accesos. WorldEdit exportó los bloques del mundo; se verificaron hashes, dimensiones, paleta e índices del formato Sponge v2. Las estaciones públicas se usan con la mano vacía. Los fogones de la posada quedan encendidos.

## Una ciudadela de piedra madera y cobre

La estética combina un pueblo medieval con talleres de Create y un archivo de magia: piedra clara y andesita en la base, abeto y roble oscuro en estructuras, tejados oscuros, detalles de cobre envejecido y luz cálida. Jardines, enredaderas y un arroyo cercano suavizan las murallas. Los materiales de color se concentran en puntos reconocibles para que la decoración conserve unidad.

La superficie construida inicial será de unos **160 × 160 bloques**, ajustada al lugar. La plaza central tendrá unos 32 bloques de ancho. Las cuatro puertas serán arcos de **12–16 bloques de paso y 20–24 de altura**, con torres laterales y espacio para ver el paisaje exterior. Serán recorridos abiertos; una puerta móvil de Create sería un detalle posterior y siempre conservaría un paso alternativo.

La silueta tendrá tres alturas: edificios bajos de 8–12 bloques, murallas y torres intermedias, y una torre del archivo de unos 36–40 bloques. En el centro, una fuente con un astrolabio de cobre y el emblema de Virgos-MC dará un punto reconocible de reunión. La estructura principal usará bloques estáticos; no habrá grandes mecanismos funcionando sólo como adorno.

La paleta final se revisará con el cliente estándar sin shaders. Los shaders opcionales mejorarán luz y atmósfera, pero la orientación, los carteles y las entradas seguirán siendo legibles para todos.

## Recorrido y espacios

| Espacio | Ubicación conceptual | Uso |
| --- | --- | --- |
| Plaza y fuente | Centro | Primera aparición, reunión y orientación; visión directa hacia las cuatro salidas |
| Archivo Virgos | Noroeste | Guía del códice, biblioteca, historia y exposición de trofeos |
| Taller y estación | Noreste | Demostraciones pequeñas de Create, bancos de trabajo y reserva para una línea de tren |
| Posada y mercado | Suroeste | Cocina común, descanso y puestos para futuros intercambios entre jugadores |
| Jardines y patio de preparación | Sureste | Reunirse antes de una expedición, práctica segura y acceso al camino exterior |
| Cuatro arcos | Norte, sur, este y oeste | Cruzar caminando hacia el mismo Overworld |
| Caminos exteriores | Desde cada arco | Transición gradual al terreno, con puentes y senderos que se estrechan al alejarse |

Los servicios se explicarán con carteles cortos y el mismo vocabulario del códice. Habrá estaciones básicas útiles, sin cofres que entreguen equipo avanzado ilimitado. Los puestos de mercado serán inicialmente construcciones; no implican una economía automática. Un máximo inicial de seis habitantes decorativos evita llenar la plaza de entidades.

Los cuatro caminos se prolongarán aproximadamente 100–150 bloques y se adaptarán al relieve. Se reservará acceso libre alrededor de las salidas para que nadie pueda cerrar una puerta con un claim privado. Las primeras bases podrán construirse fuera de esa franja, con señalización clara del límite.

## Integración con el mundo generado

1. Cerrar los mods de terreno y estructuras, y generar candidatos de mundo en el laboratorio.
2. Elegir una llanura o una terraza amplia con agua y relieve cercano. Las coordenadas y la orientación se fijan después de inspeccionar el terreno; el diseño no presupone una semilla concreta.
3. Crear una plantilla propia del Bastión y exportarla como `.schem`. WorldEdit admite guardar y cargar este formato. [Documentación de esquemas](https://worldedit.enginehub.org/en/latest/usage/clipboard/).
4. Colocarla una sola vez, por módulos, sobre una copia del mundo. Integrar cimientos, pendientes, vegetación y caminos; evitar un gran corte rectangular plano o edificios suspendidos.
5. Revisar el interior y las estructuras naturales cercanas, establecer el punto de aparición en la plaza y aplicar los claims del servidor.
6. Comprobar a pie los cuatro accesos con el cliente estándar, guardar una copia del resultado y retirar las herramientas de edición del servidor público.

La plantilla se entregará junto con sus coordenadas, orientación y lista de bloques utilizados. No se pegará de nuevo en cada arranque ni se regenerará encima de construcciones de jugadores. Será parte permanente del mundo guardado.

No hace falta un mod que genere spawns aleatorios: una plantilla propia permite ajustar estilo, escala y emplazamiento. Tampoco hace falta un mundo de lobby ni un portal al survival. Waystones seguirá formando parte de los viajes opcionales entre destinos descubiertos, sin intervenir en la salida del spawn.

## Protección y aparición

OPAC será el único sistema de protección de terreno, tanto para el spawn como para las bases. Se usarán claims del servidor en la ciudadela y accesos, con excepciones explícitas para estaciones públicas. Se verificará la protección frente a hechizos, explosiones, construcción asistida, máquinas y cambios procedentes de fuera del área.

El punto mundial se situará en una zona segura de la plaza. Los jugadores nuevos aparecerán allí; quienes tengan cama u otro punto válido conservarán su reaparición habitual. Reconectar no debería llevar a todos a la plaza: AuthMe debe conservar la ubicación habitual después del login. Es una condición a comprobar en la configuración y la prueba del paquete.

La plaza tendrá iluminación y protección local contra hostiles. Si la configuración disponible no permite impedir apariciones sólo en esa zona, se implementará esa regla local mediante la integración del paquete. No se cambiará el comportamiento de criaturas de todo el mundo para resolver el spawn.

## Plugins y herramientas elegidos

| Componente | Tipo y versión | Estado y cometido |
| --- | --- | --- |
| [AuthMe Reloaded](https://github.com/AuthMe/AuthMeReloaded) | Plugin Bukkit, 6.0.1 Spigot Legacy | Ya instalado; registro y login, con la prueba adicional de acciones de mods antes de autenticarse |
| [LuckPerms](https://modrinth.com/plugin/luckperms/version/b0mk8uS6) | Plugin Bukkit, 5.5.71 candidata | Seleccionado; permisos administrativos y grupos de plugins |
| Playit Companion | Mod Forge, 0.1.2 | Ya instalado; túnel y dominio `virgos-mc.playit.plus` dentro del servidor |
| [WorldEdit](https://modrinth.com/mod/worldedit) | Mod Forge, 7.2.15 candidata | Herramienta de construcción en laboratorio, para trabajar con los bloques del paquete |
| [spark](https://modrinth.com/mod/spark) | Mod Forge, 1.10.53 candidata | Diagnóstico de rendimiento; una sola variante |
| [Simple Backups](https://modrinth.com/mod/simple-backups) | Mod Forge, 1.20.1-3.1.19 candidata | Copias automáticas del mundo, con retención y límite de disco |

**Habrá dos plugins Bukkit en esta selección: AuthMe y LuckPerms.** El resto de funciones se resuelve con mods o configuración. LuckPerms Bukkit no se da por integrado automáticamente con todas las comprobaciones de permisos de Forge; OPAC conservará inicialmente sus cuotas y permisos propios. No se instalarán dos variantes de LuckPerms para intentar resolverlo.

Los grupos previstos son `jugador`, `moderador`, `constructor` y `administrador`, con permisos explícitos. Ser parte de un grupo administrativo no concede progreso de aventura. El constructor opera en el laboratorio; la edición del mundo público se hace sólo durante mantenimiento. Las cuentas privilegiadas deberán estar registradas y autenticadas antes de asignarles permisos.

Se deja fuera EssentialsX por ahora: las necesidades de viajes y aparición ya tienen solución. También quedan fuera otro plugin de claims, NPC basados en paquetes, anticheat genérico y mapas web permanentes. PacketEvents ya rompió conexiones con la base actual; cualquier dependencia que lo reintroduzca requiere una prueba aislada.

CoreProtect no se usará como garantía universal de restauración de máquinas o inventarios modded. Las copias deben incluir, además del mundo, configuraciones, scripts, paquete, datos de AuthMe y permisos. Simple Backups por sí solo no demuestra que esos directorios externos al mundo estén cubiertos.

## Entrega que debe quedar lista antes de abrir

- Ciudadela colocada en el Overworld, con cuatro salidas transitables y entorno integrado.
- Plantilla, copia del mundo y coordenadas para reconstruirla de forma controlada.
- Estaciones públicas usables tras el login y decoración protegida.
- Misiones iniciales que conduzcan desde la plaza hasta la primera base y aventura.
- Buen rendimiento mirando la plaza, usando el taller y cruzando los arcos sin shaders.
- Reaparición, reconexión, claims y restauración comprobados con cuentas de prueba.
