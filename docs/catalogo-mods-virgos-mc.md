# Selección de mods de Virgos-MC

> La selección ya se implementó y su estado vigente está en [roadmap y auditoría](roadmap-auditoria.md). Este texto conserva decisiones y propuestas de diseño; para instalar y jugar seguí la [guía actual](guia-jugadores.md). Simple Voice Chat ya está integrado por UDP público; CoreProtect registra bloques con las limitaciones de restauración documentadas.

Selección del 17 de octubre de 2026 para Minecraft Java 1.20.1, Forge 47.4.22 y hasta ocho jugadores. **79 mods principales, nueve opciones de presentación y una herramienta de construcción.** Oculus queda en el cliente base con shaders apagados; las demás opciones se mantienen separadas. Las bibliotecas obligatorias se suman aparte; Playit Companion ya pertenece a la base instalada.

Las versiones de abajo son la selección original. Los archivos instalados y comprobados con Ketting y AuthMe están fijados en `pack/mods.lock.json`, `pack/custom-artifacts.lock.json`, `pack/administration.lock.json` y `versions.lock.json`; estos manifiestos tienen prioridad sobre el inventario de diseño.

El [diseño de experiencia](experiencia-virgos-mc.md) define el progreso y el [diseño del spawn](spawn-y-plugins.md) define la ciudadela y los plugins. La implementación seguirá lotes pequeños hasta reunir toda esta selección.

## Exploración y mundo

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Alex's Caves](https://modrinth.com/mod/alexs-caves/version/lC8HHXOF) | 2.0.2 | Cliente y servidor | Cuevas excepcionales; sus recursos y secretos conservan su recorrido de descubrimiento |
| [Alex's Mobs](https://modrinth.com/mod/alexs-mobs/version/XoIASRVU) | 1.22.9 | Cliente y servidor | Fauna y encuentros; limitar densidad y revisar domesticación |
| [Regions Unexplored](https://modrinth.com/mod/regions-unexplored/version/XTrgsfIB) | F-0.5.6+1.20.1 | Cliente y servidor | Único gran paquete de biomas del Overworld |
| [Explorify](https://modrinth.com/mod/explorify/version/CuBdAr31) | v1.6.5 | Servidor | Pequeños lugares para descubrir entre destinos mayores |
| [Towns and Towers](https://modrinth.com/mod/towns-and-towers/version/7ZwnSrVW) | 1.12 | Servidor | Aldeas y puestos; ajustar separación para evitar saturación de estructuras |
| [YUNG's Better Dungeons](https://modrinth.com/mod/yungs-better-dungeons/version/kPiQ6v4q) | 1.20-Forge-4.0.4 | Servidor | Mazmorras; comprobar botín individual |
| [YUNG's Better Mineshafts](https://modrinth.com/mod/yungs-better-mineshafts/version/kVO57zxB) | 1.20-Forge-4.0.4 | Servidor | Minas abandonadas más interesantes |
| [YUNG's Better Strongholds](https://modrinth.com/mod/yungs-better-strongholds/version/rwiShgsc) | 1.20-Forge-4.0.3 | Servidor | Fortalezas renovadas |
| [YUNG's Better Desert Temples](https://modrinth.com/mod/yungs-better-desert-temples/version/lRK2ZA9U) | 1.20-Forge-3.0.3 | Servidor | Templos del desierto |
| [YUNG's Better Jungle Temples](https://modrinth.com/mod/yungs-better-jungle-temples/version/CXQc6EnZ) | 1.20-Forge-2.0.5 | Servidor | Templos de jungla |
| [YUNG's Better Ocean Monuments](https://modrinth.com/mod/yungs-better-ocean-monuments/version/SN4iZ7wf) | 1.20-Forge-3.0.4 | Servidor | Exploración y desafíos bajo el agua |
| [YUNG's Better Nether Fortresses](https://modrinth.com/mod/yungs-better-nether-fortresses/version/2nUEz0zq) | 1.20-Forge-2.0.6 | Servidor | Fortalezas del Nether |
| [YUNG's Better Witch Huts](https://modrinth.com/mod/yungs-better-witch-huts/version/mwlYB7rq) | 1.20-Forge-3.0.3 | Servidor | Cabañas de brujas |
| [YUNG's Bridges](https://modrinth.com/mod/yungs-bridges/version/KgO1gfM2) | 1.20-Forge-4.0.3 | Servidor | Puentes que aparecen en el paisaje |

## Dimensiones

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [The Twilight Forest](https://www.curseforge.com/minecraft/mc-mods/the-twilight-forest/files/all?page=1&pageSize=20&version=1.20.1) | 4.3.2508 | Cliente y servidor | Bosque de aventura; adaptar equipo y requisitos a sus jefes |
| [The Aether](https://modrinth.com/mod/aether/version/2411kUqF) | 1.20.1-1.5.2-neoforge | Cliente y servidor | Islas celestes; revisar movilidad y recompensas con magia externa |

## Magia y combate

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Iron's Spells 'n Spellbooks](https://modrinth.com/mod/irons-spells-n-spellbooks/version/hZaEegS9) | 1.20.1-3.16.3 | Cliente y servidor | Magia de combate y apoyo; costes y potencia por nivel |
| [Ars Nouveau](https://modrinth.com/mod/ars-nouveau/version/Hw2aD01e) | 4.12.7 | Cliente y servidor | Magia creativa y de utilidad; limitar vuelo y automatización avanzada |
| [Better Combat](https://modrinth.com/mod/better-combat/version/rnhiaw3t) | 1.9.0+1.20.1-forge | Cliente y servidor | Único sistema principal de animaciones y ataques cuerpo a cuerpo |
| [Simply Swords](https://modrinth.com/mod/simply-swords/version/Na6e94J1) | 1.70.2-1.20.1 | Cliente y servidor | Estilos de armas; ajustar efectos únicos y abundancia |
| [L_Ender's Cataclysm](https://www.curseforge.com/minecraft/mc-mods/lendercataclysm/files/all?page=1&pageSize=20&version=1.20.1) | 3.31 | Cliente y servidor | Grandes jefes; revisar terreno destruido y poder de sus recompensas |
| [Mowzie's Mobs](https://modrinth.com/mod/mowzies-mobs/version/acYEfsJa) | 1.8.2 | Cliente y servidor | Encuentros con patrones propios; limitar apariciones cerca del inicio |
| [Artifacts](https://modrinth.com/mod/artifacts/version/lrLPBSzq) | 9.5.19 | Cliente y servidor | Accesorios seleccionados; evitar combinaciones de daño o movilidad desmedidas |

## Ingeniería y conexiones

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Create](https://modrinth.com/mod/create/version/8amzvn9x) | mc1.20.1-6.0.8 | Cliente y servidor | Columna de tecnología, logística y transporte |
| [Create: Steam 'n' Rails](https://modrinth.com/mod/create-steam-n-rails/version/7Uk6lWkU) | 1.7.3+forge-mc1.20.1 | Cliente y servidor | Ferrocarriles para conectar bases; archivo de la rama C6 |
| [Create: Connected](https://modrinth.com/mod/create-connected/version/6gnvaVkN) | 1.2.3-mc1.20.1 | Cliente y servidor | Componentes de ingeniería y comodidad; sin otro addon que duplique engranajes |
| [Create Deco](https://modrinth.com/mod/create-deco/version/e9gaSRMd) | 2.0.3-1.20.1-forge | Cliente y servidor | Acabados de talleres, fábricas y estaciones |
| [Create: Copycats+](https://modrinth.com/mod/copycats/version/LlMxIysb) | 3.0.10+mc.1.20.1-forge | Cliente y servidor | Formas con materiales personalizados; limitar uso masivo en zonas densas |
| [Create: Central Kitchen](https://modrinth.com/mod/create-central-kitchen/version/jMB94kRJ) | 1.5.1 | Cliente y servidor | Conectar procesamiento de comida con Create |
| [Ars Creo](https://modrinth.com/mod/ars-creo/version/bLLhDnY2) | 4.3.0 | Cliente y servidor | Conectar Ars con Create; revisar torretas y permisos de terreno |

## Cocina y pesca

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Farmer's Delight](https://modrinth.com/mod/farmers-delight/version/SiIpcZzM) | 1.20.1-1.3.4 | Cliente y servidor | Sistema principal de cocina y agricultura |
| [Delightful](https://modrinth.com/mod/delightful/version/HbEQIqIu) | 3.8.1-1.20.1 | Cliente y servidor | Más recetas e integración; activar sólo aportes útiles para este paquete |
| [Brewin' And Chewin'](https://modrinth.com/mod/brewin-and-chewin/version/9myDFPCD) | 1.20.1-3.2.1 | Cliente y servidor | Fermentación, quesos y bebidas; revisar acumulación de efectos |
| [Aquaculture 2](https://modrinth.com/mod/aquaculture/version/wNiFoROs) | 2.5.7 | Cliente y servidor | Pesca por bioma; equipo de neptunio ajustado al progreso |
| [Aquaculture Delight](https://modrinth.com/mod/aquaculture-delight/version/Qn9bVRpQ) | 1.1.0 | Cliente y servidor | Usar la pesca en la cocina de Farmer's Delight |

## Construcción y decoración

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Supplementaries](https://modrinth.com/mod/supplementaries/version/foXRPXFH) | 1.20-3.1.44-forge | Cliente y servidor | Objetos decorativos y utilitarios del pueblo y las bases |
| [Amendments](https://modrinth.com/mod/amendments/version/nJORWvdh) | 1.20-2.2.6 | Cliente y servidor | Mejoras funcionales y visuales de bloques existentes |
| [Chipped](https://modrinth.com/mod/chipped/version/pi3f4er3) | 3.0.7 | Cliente y servidor | Variantes decorativas sin añadir otra progresión de poder |
| [Handcrafted](https://modrinth.com/mod/handcrafted/version/N7wZwOFy) | 3.0.6 | Cliente y servidor | Muebles para casas, posada y biblioteca |
| [Macaw's Roofs](https://modrinth.com/mod/macaws-roofs/version/31e80GhE) | 2.3.2 | Cliente y servidor | Tejados y remates |
| [Macaw's Bridges](https://modrinth.com/mod/macaws-bridges/version/KImk0Oo1) | 3.1.2 | Cliente y servidor | Puentes construibles por los jugadores |
| [Macaw's Doors](https://modrinth.com/mod/macaws-doors/version/n8BlIUm3) | 1.1.5 | Cliente y servidor | Puertas para edificios; los grandes arcos del spawn serán estructuras |
| [Macaw's Windows](https://modrinth.com/mod/macaws-windows/version/SSIlzrPf) | 2.4.2 | Cliente y servidor | Ventanas y detalles de fachada |
| [Macaw's Fences and Walls](https://modrinth.com/mod/macaws-fences-and-walls/version/HnyfcyJ9) | 1.2.1 | Cliente y servidor | Cercas y límites de jardines |
| [Macaw's Lights and Lamps](https://modrinth.com/mod/macaws-lights-and-lamps/version/H1a9Tx4h) | 1.1.5 | Cliente y servidor | Iluminación funcional y ambiental |

## Vida diaria y botín

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Sophisticated Backpacks](https://modrinth.com/mod/sophisticated-backpacks/version/X7q2xTaV) | 1.20.1-3.26.12.2206 | Cliente y servidor | Mochila básica temprana; anidamiento deshabilitado y mejoras limitadas |
| [Sophisticated Storage](https://modrinth.com/mod/sophisticated-storage/version/vFpp1Lw7) | 1.20.1-1.5.6.2183 | Cliente y servidor | Almacenamiento principal de bases; límites a mejoras de apilado |
| [Lootr](https://modrinth.com/mod/lootr/version/mWTXC1ZX) | 0.7.35.94 | Cliente y servidor | Botín por jugador en los contenedores compatibles |
| [Waystones](https://modrinth.com/mod/waystones/version/Y0IgdaoP) | 14.1.21+forge-1.20.1 | Cliente y servidor | Viajes entre lugares descubiertos; sin salida instantánea de expediciones |
| [Corpse](https://modrinth.com/mod/corpse/version/7fc0hJN6) | forge-1.20.1-1.0.23 | Cliente y servidor | Recuperación de inventario al morir; verificar mochilas y accesorios |
| [Comforts](https://modrinth.com/mod/comforts/version/gBDsc134) | 6.4.0+1.20.1 | Cliente y servidor | Descanso durante viajes; conservar el punto de reaparición de la base |
| [Construction Wand](https://modrinth.com/mod/construction-wand/version/XCgKj8gL) | 1.20.1-2.11 | Cliente y servidor | Construcción rápida consumiendo materiales; respetar claims |
| [Nature's Compass](https://modrinth.com/mod/natures-compass/version/eRSDvCjN) | 1.20.1-1.12.0-forge | Cliente y servidor | Buscar biomas comunes; excluir cuevas especiales y limitar alcance |

## Misiones e interfaz

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Heracles (Odyssey Quests)](https://modrinth.com/mod/odyssey-quests/version/9ZUSHiZa) | 1.1.13 | Cliente y servidor | Heracles: Códice Virgos y misiones con progreso individual explícito |
| [Open Parties and Claims](https://modrinth.com/mod/open-parties-and-claims/version/Ec8wDd9H) | forge-1.20.1-0.33.0 (beta) | Cliente y servidor | Único sistema de claims y grupos; sin carga forzada inicialmente |
| [Xaero's World Map](https://modrinth.com/mod/xaeros-world-map/version/KtEupJvB) | forge-1.20.1-1.47.0 | Cliente | Mapa principal con gestión visual de claims |
| [Xaero's Minimap](https://modrinth.com/mod/xaeros-minimap/version/dB6E0CY9) | forge-1.20.1-26.6.0 | Cliente | Minimapa discreto; radar de entidades y cuevas desactivado donde sea configurable |
| [Just Enough Items (JEI)](https://modrinth.com/mod/jei/version/9jqubC9n) | 15.56.0.205 | Cliente y servidor | Visor principal de recetas y usos; el servidor sincroniza las recetas |
| [Jade 🔍](https://modrinth.com/mod/jade/version/xJQHCmWJ) | 11.13.3+forge | Cliente y servidor | Información contextual breve |
| [Jade Addons (Neo/Forge)](https://modrinth.com/mod/jade-addons-forge/version/l9IrZYLt) | 5.5.1+forge | Cliente y servidor | Información de máquinas y otros mods |
| [AppleSkin](https://modrinth.com/mod/appleskin/version/XdXDExVF) | 2.5.1+mc1.20.1 | Cliente | Lectura de hambre y saturación |
| [Mouse Tweaks](https://modrinth.com/mod/mouse-tweaks/version/7JVXOe3K) | 1.20.1-2.25.1-forge | Cliente | Movimientos cómodos en inventarios |
| [Controlling](https://modrinth.com/mod/controlling/version/LH6Bi6Am) | 12.0.2 | Cliente | Buscar teclas y resolver conflictos |
| [Default Options](https://modrinth.com/mod/default-options/version/AVz3mvZZ) | 18.0.5+forge-1.20.1 | Cliente | Controles iniciales coherentes, sin pisar preferencias guardadas |
| [Enchantment Descriptions](https://modrinth.com/mod/enchantment-descriptions/version/OPgBRfTQ) | 17.1.21 | Cliente | Descripciones de encantamientos |
| [Equipment Compare](https://modrinth.com/mod/equipment-compare/version/x1lxEKIp) | 1.3.7 | Cliente | Comparación de equipo; mantener tooltips breves |
| [FancyMenu](https://modrinth.com/mod/fancymenu/version/2mNmkn9s) | 3.9.14-1.20.1-forge | Cliente | Portada sencilla con entrar, guía y ajustes |

## Integración y balance

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [KubeJS](https://modrinth.com/mod/kubejs/version/hVR2xUSr) | 2001.6.5-build.26+forge | Cliente y servidor | Recetas, textos y eventos de integración propios |
| [KubeJS Create](https://modrinth.com/mod/kubejs-create/version/5vppyenb) | 2001.3.0-build.8+forge | Cliente y servidor | Recetas de Create; build 8 declara Create 6 o superior |

## Rendimiento

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [ModernFix](https://modrinth.com/mod/modernfix/version/bDP3S7Vh) | 5.27.88+mc1.20.1 | Cliente y servidor | Optimización de carga y memoria; medir con Ketting |
| [FerriteCore](https://modrinth.com/mod/ferrite-core/version/DG5Fn9Sz) | 6.0.1 | Cliente y servidor | Reducir memoria de datos internos |
| [FastSuite](https://modrinth.com/mod/fastsuite/version/nhk4VpGm) | 5.1.2 | Cliente y servidor | Procesa recetas de Forge en paralelo y reduce el tiempo de carga de JEI |
| [Placebo](https://modrinth.com/mod/placebo/version/6SkuAGoz) | 8.6.3 | Cliente y servidor | Biblioteca requerida por FastSuite |
| [Embeddium](https://modrinth.com/mod/embeddium/version/UTbfe5d1) | 0.3.31+mc1.20.1 | Cliente | Renderizado del perfil estándar |
| [Entity Culling](https://modrinth.com/mod/entityculling/version/HUUJcFnt) | 1.11.3 | Cliente | Evitar dibujar entidades ocultas; revisar máquinas móviles |
| [ImmediatelyFast](https://modrinth.com/mod/immediatelyfast/version/rvsLEEZU) | 1.5.5+1.20.4-forge | Cliente | Optimizar renderizado inmediato |
| [Clumps](https://modrinth.com/mod/clumps/version/nAHGB5ls) | 12.0.0.4 | Servidor | Agrupar experiencia; verificar recogida y recompensas |
| [Dynamic FPS](https://modrinth.com/mod/dynamic-fps/version/EjdIWWqG) | 3.11.4 | Cliente | Reducir carga cuando la ventana queda en segundo plano |

## Operación

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [spark](https://modrinth.com/mod/spark/version/4FXHDE9F) | 1.10.53-forge | Servidor | Perfilador Forge; no instalar también el plugin |
| [Chunky](https://modrinth.com/mod/chunky/version/4FTDk9wv) | 1.3.146 | Servidor | Pregenerar terreno por zonas tras cerrar mods de mundo |
| [Simple Backups](https://modrinth.com/mod/simple-backups/version/b0VVmLcA) | 1.20.1-3.1.19 | Servidor | Copias automáticas del mundo; complementar con respaldo del proyecto y AuthMe |
| [WorldEdit](https://modrinth.com/mod/worldedit/version/Wrlqaul6) | 7.2.15 | Servidor de construcción | Forge 7.2.15: construir e importar el spawn; retirar del servidor público después |

## Presentación opcional

| Componente y archivo oficial | Versión candidata | Destino | Papel en Virgos-MC |
| --- | --- | --- | --- |
| [Oculus](https://modrinth.com/mod/oculus/version/iQ1SwGc3) | 1.20.1-1.8.0 | Cliente | Menú y soporte de shaders disponibles; apagado por defecto para cuidar equipos modestos |
| [Sound Physics Remastered](https://modrinth.com/mod/sound-physics-remastered/version/x0sJ9PeR) | forge-1.20.1-1.5.1 (alpha) | Cliente | Acústica espacial configurable |
| [Ambient Environment](https://modrinth.com/mod/ambient-environment/version/BYzQMmi7) | 11.0.0.1 | Cliente | Variación visual del ambiente |
| [Better Third Person](https://modrinth.com/mod/better-third-person/version/XkYduFuv) | 1.9.0 | Cliente | Cámara opcional; probar combate y hechizos |
| [First-person Model](https://modrinth.com/mod/first-person-model/version/kxFDUOmS) | 2.7.3 | Cliente | Ver el cuerpo, brazos y animaciones desde primera persona |
| [Not Enough Animations](https://modrinth.com/mod/not-enough-animations/version/kGjMleOz) | 1.12.6 | Cliente | Animaciones de interacción y combate; dependencia visual de First-person Model |
| [AmbientSounds](https://modrinth.com/mod/ambientsounds/version/YOYpWGZg) | 6.3.11 | Cliente | Paisaje sonoro por bioma; requiere CreativeCore |
| [CreativeCore](https://modrinth.com/mod/creativecore/version/ChKayKur) | 2.12.40 | Cliente | Biblioteca para AmbientSounds |
| [Eating Animations](https://modrinth.com/mod/eating-animations/version/WqBpsYBv) | 5.1.0 | Cliente | Animaciones de comida y pociones; requiere GML |
| [GML](https://modrinth.com/mod/gml/version/s7gFqeVL) | 4.0.10 | Cliente | Biblioteca para Eating Animations |

## Conexiones y versiones que deben permanecer juntas

Create queda en **6.0.8**. Se revisaron los descriptores de los archivos candidatos: Central Kitchen 1.5.1 exige Create desde 6.0.8 hasta antes de 6.1.0 y Forge desde 47.4.10; Copycats+ 3.0.10 exige Create 6.0.7 o superior; Ars Creo 4.3.0 y KubeJS Create build 8 declaran Create 6 o superior. Nuestra versión de Forge satisface esos rangos. Esto verifica requisitos declarados, no todos los comportamientos durante el juego. [Central Kitchen](https://modrinth.com/mod/create-central-kitchen), [Copycats+](https://modrinth.com/mod/copycats), [Ars Creo](https://modrinth.com/mod/ars-creo), [KubeJS Create](https://modrinth.com/mod/kubejs-create).

Steam 'n' Rails se seleccionó en su archivo C6 y Create Deco 2.0.3 anuncia la actualización a Create 6. Connected 1.2.3 entra en la franja declarada para Create 6.0.7 o superior. No actualizar uno de estos componentes aisladamente sin revisar los demás. [Steam 'n' Rails](https://modrinth.com/mod/create-steam-n-rails/version/1.7.3+forge-mc1.20.1), [Create Deco](https://modrinth.com/mod/create-deco/version/2.0.3-1.20.1-forge), [Connected](https://modrinth.com/mod/create-connected).

El archivo de Aether termina en `neoforge`, pero esa publicación concreta declara compatibilidad también con Forge 1.20.1. Se selecciona por sus metadatos y no por el nombre solamente. [Publicación de Aether](https://modrinth.com/mod/aether/version/1.20.1-1.5.2-neoforge).

Heracles mantiene progreso individual por misión; OPAC gestiona permisos de terreno y sus propios grupos. Su prueba offline es obligatoria antes de escribir el códice completo. [Decisión sobre FTB](alternativas-ftb.md).

## Bibliotecas y distribución

El instalador posterior resolverá las dependencias de cada archivo y sus rangos, incluidas las transitivas. Entre las familias previstas están Citadel, GeckoLib, Curios, Sophisticated Core, Moonlight, TerraBlender, YUNG's API, Cristel Lib, Resourceful Lib, Balm, Architectury, Cloth Config, Player Animator, Rhino, Bookshelf, Iceberg, Searchables y Konkrete. La lista de familias no es una lista para descargar manualmente: algunas versiones incluyen bibliotecas embebidas y no deben duplicarse.

Las relaciones de la API son un punto de partida; se contrastarán con `mods.toml` y las relaciones de CurseForge. El inventario JSON conserva relaciones publicadas, pero marca explícitamente que la resolución completa está pendiente. Los mods que agregan bloques, objetos y criaturas van en ambos lados. Las herramientas de administración y las credenciales quedan en el servidor. Las opciones visuales no cambian el contenido jugable.

## Reglas de integración

- **Una interfaz principal:** Heracles para objetivos, JEI para recetas, Jade para información contextual y Xaero para orientarse. El códice enlaza cada función y las teclas no se superponen.
- **Cuatro niveles de aventura:** revisar el conjunto de arma, hechizo, armadura, accesorio y comida. Los grandes jefes originales no se consideran cooperativos obligatorios hasta añadir y probar las mecánicas propias.
- **Identidad de cada rama:** Iron's Spells centra combate y apoyo; Ars, utilidad y creatividad; Create, industria y transporte. Vuelo, invocaciones y torretas se prueban contra el diseño de encuentros.
- **Botín:** Lootr en cofres compatibles, recompensas de expedición acreditadas por participante, sin premio exclusivo para quien pega último. Los objetos sueltos y materiales del terreno siguen siendo compartidos.
- **Protección:** propuesta inicial de 25 chunks personales, ampliables por necesidad de construcción; 0 chunks forzados. Los claims del spawn son del servidor y no consumen cupos de jugadores.
- **Movilidad:** el spawn conecta caminando al Overworld. Waystones sirve para rutas descubiertas fuera del recorrido inicial; no agrega portales a las puertas ni rescata de una expedición activa.
- **Mochilas y economía:** sin anidamiento al inicio; límites de apilado y recetas escalonadas. Sin tienda que compre infinitamente recursos automatizados ni recompensas por horas AFK.
- **Mundo:** Regions Unexplored como única ampliación principal de biomas; revisar separación de estructuras. Twilight y Aether son las dos dimensiones adicionales de esta versión.
- **Construcción:** los proyectos grandes pueden usar decoración abundante, con un presupuesto de máquinas activas y bloques complejos por zona. El spawn usa geometría de bloques principalmente estáticos.

## Componentes que quedan fuera de esta versión

| Grupo | Decisión |
| --- | --- |
| FTB Quests, Teams y Chunks | Reemplazados por Heracles, OPAC y Xaero |
| Biomes O' Plenty, Terralith y Tectonic | Mantener una sola elección principal de terreno para cerrar generación |
| When Dungeons Arise y más dimensiones | La selección actual ya tiene muchos destinos; conservar espacio entre aventuras |
| ProjectE, Mystical Agriculture, Apotheosis, Mekanism y grandes redes digitales | Añaden escalas de recursos o poder que exigirían otro balance |
| Quark | Las funciones decorativas elegidas cubren la experiencia actual |
| FramedBlocks, Tom's Storage y otros almacenes | Copycats+, Sophisticated Storage y Create cubren las funciones previstas |
| Farmer's Respite | Su página advierte un problema de generación del café; la cocina queda cubierta por los cinco componentes elegidos |
| Carry On, minería masiva y máquinas con carga propia | Evitar más caminos para mover inventarios, modificar claims o mantener chunks activos |
| Create Enchantment Industry, energía y artillería | Mantener acotados encantamientos, producción y daño a terreno |
| Decursio Stages | No agregar otra dependencia hasta que el prototipo determine si hace falta para requisitos de uso de equipo |
| OptiFine, otro motor de combate y otro visor de recetas | Mantener una sola base por función |

La decisión sobre Farmer's Respite se apoya en su [advertencia de generación](https://modrinth.com/mod/farmers-respite). Las demás exclusiones son decisiones de alcance y balance, no declaraciones generales de incompatibilidad.

## Cierre técnico antes de distribuir

1. Validar login offline, Heracles y OPAC con dos clientes reales y un reinicio.
2. Incorporar los mods de contenido en lotes, resolver dependencias y fijar hashes.
3. Probar inventarios, muerte, recompensas, máquinas, magia y protección; comprobar también acciones antes del login de AuthMe.
4. Terminar mundo y spawn, respaldar y pregenerar por zonas con límites de disco.
5. Medir la PC más modesta y ocho jugadores concurrentes; retirar primero presentación opcional y efectos costosos antes de recortar funciones centrales.
6. Probar una restauración que recupere mundo, cuentas, progreso y paquete coherentes.

Punto de partida: servidor con hasta 8 GB de Java, visión 8 y simulación 6; cliente estándar 5–6 GB sin shaders, ajustado a la RAM real disponible. Son presupuestos de prueba. La muestra con dos clientes dio 20 TPS; falta medir ocho jugadores y grandes fábricas.

## Ampliación 1.2

La selección vigente agrega Bountiful/Kambrik, Exposure, Small Ships, Immersive Melodies, Every Compat con módulos acotados, Create: Alex’s Caves Compat, Easy NPC y Lightman’s Currency. DecentHolograms añade señalización. Versiones, límites y pruebas en [la revisión 1.2](revision-1.2.md). El cliente v3-lab tiene 117 archivos requeridos y nueve opciones visuales; los mods incluyen dependencias.
