# Alternativas a FTB para Virgos-MC

> Actualización 0.1.0-rc1: la selección ya se implementó y se probó en el alcance documentado en [implementación](implementacion.md). Este texto conserva decisiones y propuestas de diseño; para instalar y jugar seguí la [guía actual](guia-jugadores.md).

Decisión de diseño del 17 de octubre de 2026. Minecraft 1.20.1, Forge 47.4.22, Ketting 0.6.1 y AuthMe, con `online-mode=false`. Los componentes nuevos todavía no se instalaron ni se probaron en el servidor.

## Elección propuesta

**Heracles para misiones, Open Parties and Claims para bases y Xaero's World Map para el mapa.** El objetivo es conservar progreso personal y cooperación sin depender de FTB Teams.

| Necesidad | Componente | Versión candidata para Forge 1.20.1 |
| --- | --- | --- |
| Códice, objetivos y recompensas | [Heracles](https://modrinth.com/mod/odyssey-quests/version/1.1.13), actualmente listado como Odyssey Quests | 1.1.13 |
| Protección y acceso de amigos | [Open Parties and Claims](https://modrinth.com/mod/open-parties-and-claims/version/Ec8wDd9H), OPAC | 0.33.0, beta |
| Gestión de terrenos en el mapa | [Xaero's World Map](https://modrinth.com/mod/xaeros-world-map) | 1.47.0 |

Son candidatos, no un manifiesto definitivo. Heracles necesita Resourceful Lib compatible; el minimapa de Xaero es opcional. Las dependencias obligatorias de Heracles no incluyen FTB. [Descriptor Forge de Heracles](https://github.com/terrarium-earth/Heracles/blob/1.20.x/forge/src/main/resources/META-INF/mods.toml).

## Fundamento para modo offline

En los recorridos revisados de Heracles 1.20.x, el servidor guarda el progreso por UUID y envía al cliente el correspondiente a `ServerPlayer.getUUID()`. Además, omite copiar las misiones individuales al transferir progreso de equipo. [Gestión del progreso](https://github.com/terrarium-earth/Heracles/blob/1.20.x/common/src/main/java/earth/terrarium/heracles/common/handlers/progress/QuestProgressHandler.java).

OPAC también consulta la propiedad del terreno y los grupos usando la identidad del jugador conectado al servidor. [Gestión de entrada del jugador](https://github.com/thexaero/open-parties-and-claims/blob/1.20/Common/src/main/java/xaero/pac/common/server/player/PlayerLoginHandler.java).

**Inferencia técnica:** estos recorridos ofrecen un mejor punto de partida para nuestro servidor que el mecanismo de FTB Teams revisado, que busca el UUID del perfil de sesión del cliente entre los jugadores sincronizados. No encontramos una certificación oficial de esta combinación exacta con Ketting y AuthMe. Revisar código no sustituye entrar con los clientes reales y comprobar persistencia.

La elección responde al riesgo concreto de identidad; no significa que todos los usos de FTB fallen en offline. Su historial conserva una advertencia de falta de soporte de ese modo. [Cliente de FTB Teams](https://github.com/FTBTeam/FTB-Teams/blob/1.20.1/main/common/src/main/java/dev/ftb/mods/ftbteams/data/ClientTeamManagerImpl.java), [historial](https://github.com/FTBTeam/FTB-Teams/blob/1.20.1/main/CHANGELOG.md#1902211).

## Reglas para nuestra experiencia

- **Misiones personales:** escribir `individual_progress=true` en cada misión correspondiente; el valor predeterminado es falso. [Opción en Heracles](https://github.com/terrarium-earth/Heracles/blob/1.20.x/common/src/main/java/earth/terrarium/heracles/api/quests/QuestSettings.java).
- **Casa compartida:** usar permisos de OPAC. Integrarse a un grupo no debe completar misiones personales. Mantener un único sistema de claims y grupos.
- **Expediciones:** registrar participantes activos y autenticados; acreditar el objetivo individualmente desde el servidor. No asumir integración automática entre los grupos de OPAC y Heracles. El encuentro cooperativo requiere desarrollo propio.
- **Recompensas:** hitos de poder una vez por jugador; repeticiones con premios moderados. Comprobar que reconectar o cambiar de grupo no permite cobrarlos otra vez.
- **Identidad:** conservar el mismo nombre de jugador. Cualquier cambio de nombre o de autenticación debe tratarse como una migración de datos y verificarse antes.
- **Rendimiento:** comenzar sin carga forzada de chunks y asignar cuotas iguales de terreno; ampliarlas por necesidad de construcción, sin premiar horas conectado.

OPAC permite gestionar claims desde Xaero e incorpora soporte para Create en Forge. Se publica como beta; su documentación advierte que las mecánicas especiales de otros mods pueden necesitar integración. Eso exige comprobar los hechizos y máquinas elegidos, además de colocar y romper bloques. [Alcance oficial de OPAC](https://modrinth.com/mod/open-parties-and-claims).

## Otra alternativa revisada

[Hardcore Questing Mode (HQM)](https://www.curseforge.com/minecraft/mc-mods/hardcore-questing-mode) tiene un archivo Forge 1.20.1, versión 5.16.0, y sistemas de misiones y equipos. Sus vidas limitadas son opcionales. Queda como reserva: no encontramos evidencia suficiente para atribuirle una ventaja de compatibilidad offline sobre Heracles, cuya opción explícita por misión encaja mejor con este diseño. [Archivos 1.20.1](https://www.curseforge.com/minecraft/mc-mods/hardcore-questing-mode/files/all?page=1&pageSize=20&version=1.20.1), [repositorio](https://github.com/lorddusk/HQM).

## Prueba antes de adoptarlos

En una copia separada, con el mismo Ketting y AuthMe y sin otro túnel público:

1. Entrar con un cliente premium y otro no premium, registrar/login y abrir códice y mapa.
2. Completar una misión con un jugador; comprobar que el otro sigue pendiente incluso después de compartir base o cambiar de grupo.
3. Reiniciar y reconectar: conservar progreso, propietarios y permisos, sin duplicar recompensas.
4. Comprobar que un visitante sin permiso no modifica la base con herramientas, Create, hechizos o explosiones.
5. Antes del login, comprobar también las acciones enviadas por los mods: recompensas, claims e inventarios. La prueba vanilla previa de AuthMe no cubre esos paquetes.

Si aparece un fallo, reproducirlo con el conjunto mínimo y comparar con Forge puro antes de sumar componentes. La adopción queda pendiente de esta prueba, conservando el [diseño de experiencia](experiencia-virgos-mc.md).
