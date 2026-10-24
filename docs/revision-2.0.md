# Virgos-MC 2.0

Minecraft 1.20.1, Forge 47.4.22 y Ketting 0.6.1. La v2 estrena mundo e inventarios, misiones, bases y estadísticas desde cero. Las cuentas y contraseñas, el dominio y la voz conservan su configuración. La partida 1.2 permanece respaldada.

## Explorar y construir

- Terralith y ReStoned renuevan el terreno y mantienen los materiales útiles para Create. Alex's Caves conserva sus seis biomas y sus condiciones originales de aparición; algunas cuevas quedan lejos del spawn.
- Integrated Villages aporta ciudades con mecanismos de Create. IDAS, Integrated Stronghold, When Dungeons Arise y Seven Seas suman talleres, ruinas, fortalezas y barcos. Towns and Towers y YUNG's Better Strongholds se retiran para evitar duplicar esas funciones.
- Bosses of Mass Destruction, Meet Your Fight y Aquamirae se suman a Cataclysm, Twilight Forest y los jefes existentes. Deep Aether amplía el Aether; Incendium y Nullscape renuevan Nether y End.
- El pueblo medieval de Cynera se adapta al mundo nuevo, con cuatro salidas caminables, mercado, guías NPC, talleres y camino al anfiteatro. Spawn: **672, 80, 752**. Cofre de ender comprobado con un jugador sin permisos administrativos.

El cliente requiere **116 archivos de mods y dependencias**, más cuatro opciones visuales. El servidor usa **116 JAR de mods** y cinco plugins. WorldEdit queda como herramienta opcional fuera del runtime público porque bloquea el evento de arranque de Ketting. FastSuite y Placebo aceleran la reconstrucción de recetas y sus dependencias en ambos lados. Los nombres y versiones exactos están en los manifiestos `pack/*lock.json`.

Tectonic queda fuera de esta selección: existe un [reporte de incompatibilidad con Alex's Caves 2.0.2 y Forge 1.20.1](https://github.com/Apollounknowndev/tectonic/issues/481). Es un reporte de usuarios en el repositorio del proyecto, no una prueba de todas las combinaciones posibles; para esta versión se priorizó la combinación que pudimos comprobar localmente.

## Misiones, perfil y balance

El códice tiene **244 misiones en 10 capítulos**, lista con títulos legibles, búsqueda, filtros de pendientes y recompensas, paginación y acceso al mapa original. **J** abre el códice. Las guías explican los mods, comandos, protección de bases y preparación cooperativa. Las casillas de lectura se identifican como guías manuales; recoger materiales no los consume salvo que la misión lo indique.

`/perfil` y `/perfil Nombre` muestran horas, nivel de XP, rango, misiones y estadísticas de juego; funcionan también para consultar amigos desconectados. Las horas incluyen AFK y no conceden poder ni rangos. Las estadísticas corresponden a este mundo y no exponen ubicación, inventario ni datos de la cuenta.

Se ajustan 14 distribuciones de estructuras, 47 tablas de botín y cuatro recetas de invocación. Se reduce el botín masivo de diamante y netherita, conservando recompensas distintivas. Los nuevos rituales de Meet Your Fight se enlazan con Create. Continúan los rangos personales, límites de magia, botín individual de Lootr, proyectos comunitarios y expediciones que requieren varios jugadores. No se premia jugar más horas.

Quark conserva construcción y decoración, con sistemas que se superponen desactivados. Guard Villagers tiene patrullas y botín de equipo moderado. Se desactiva la noche eterna del Lich. **Keep Kayra**, una estructura de WDA que provocó una pausa excesiva al convertir su enorme plantilla antigua, queda excluida de la generación; las demás siguen disponibles.

## Instalación

Extraer **Virgos-MC-2.0.0-instalar.zip**, abrir **EMPEZAR.bat** y elegir launcher. Para actualizar, seleccionar la misma carpeta y **Revisar / reparar**. Conserva mundos locales, controles, servidores guardados y preferencias de voz. El asistente configura Forge, carpeta y memoria para el oficial y TLauncher.

En instalaciones nuevas elige 6 GB para equipos con al menos 16 GB de RAM, o 5 GB para equipos con 12 GB. Las actualizaciones conservan la elección anterior; se cambia en **Opciones de carpeta y memoria**. El cliente QA completó el inicio y las pruebas con 6 GB. El servidor tiene un máximo de 8 GB.

## Verificación y límites

El laboratorio verificó la entrada con Forge, autenticación, misiones y cobro de recompensa, perfil propio y de otro jugador desconectado, separación del progreso, ocho casos de navegación, cofre de ender y diálogo de NPC. La auditoría del conjunto de pueblo, mercado y arena examinó **90.518 bloques y 12 recorridos**, sin bloques faltantes, soportes inválidos ni caminos bloqueados.

Se localizaron los seis biomas de Alex's Caves y ejemplos del terreno y de las nuevas familias de estructuras. Se generaron muestras en Overworld, Nether, End y Aether. La ciudad mecánica se revisó con el cliente; los cofres guardados de las muestras verificadas usan Lootr. Los controles de privacidad de dos jugadores de Lootr y la lógica cooperativa conservan sus pruebas anteriores; no equivalen a repetir todos los encuentros con el paquete v2.

El instalador se probó con PowerShell 5.1 y 7, incluyendo archivos empaquetados corruptos y rutas inválidas. Una actualización real de una copia del cliente 1.2 descargó y verificó los 116 archivos requeridos, conservando opciones, voz y un mundo local de prueba. La integración de TLauncher tiene 16 comprobaciones de configuración, ajusta ambos límites de memoria y desactiva temporalmente un shader activo con respaldo reversible cuando detecta Oculus.

La prueba pública de v2 también verificó el ingreso por Playit, bloqueo antes de autenticarse, conexión UDP de voz, las **21.989 recetas** sincronizadas y el perfil en nivel 0 y 0/244 misiones. En esa sesión de un jugador se observaron 20 TPS; ese resultado no mide la carga del grupo completo. La instalación oficial del propietario quedó actualizada y verificada con 6 GB.

Queda para la primera sesión del grupo ajustar la dificultad real de los jefes, escuchar los micrófonos y medir la carga de ocho personas con fábricas. Hay advertencias de plantillas antiguas de algunos mods; no se promete ausencia absoluta de fallos ni compatibilidad con mods adicionales ajenos al paquete.

## Créditos y evidencia

Pueblo basado en [Medieval Spawn Town de Cynera](https://www.planetminecraft.com/project/medieval-spawn-town-1-17-1-18/): itzvmbie, SaraGrey, CoolMMN, FireVoges, Vmbie, Z3phrin y Cynera Staff. Integración y adaptación local para Virgos-MC.

Los informes técnicos, hashes, capturas y pruebas están en `.lab/v2`; el registro de promoción identifica el respaldo de v1 y los datos de QA omitidos. El registro final de publicación se guarda en `.lab/v2/final.json` al terminar las pruebas públicas.
