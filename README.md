# Virgos-MC

Servidor y paquete **2.0.0**, instalador revisión **11**, para Minecraft Java **1.20.1**, Forge **47.4.22** y Ketting **0.6.1**. Proyecto: `D:\proyectos\mc-server`. [Revisión final para jugar](docs/revision-2.0.md).

**Dirección: `virgos-mc.playit.plus`**, sin puerto. En esta PC también funciona `localhost:25565`. Hace falta el cliente completo con Forge; un cliente vanilla no puede entrar.

## Jugar

1. Compartí el `Virgos-MC-2.0.0-instalar.zip` generado en `dist/` o en el release de GitHub. Tus amigos extraen todo y abren **EMPEZAR.bat**. Eligen TLauncher u oficial; el asistente descarga Java 17 para el perfil oficial y usa el Java automático de TLauncher para ese perfil. Para actualizar desde una versión anterior, elijan la misma carpeta y **Revisar / reparar**.
2. Seguí [la guía de jugadores](docs/guia-jugadores.md): el perfil oficial se configura automáticamente; TLauncher también configura automáticamente carpeta, Forge y memoria, con un botón para restaurar sus ajustes anteriores. La guía de instalación y el manual del juego ahora están separados.
3. Entrá al dominio. La primera vez usá `/register contraseña contraseña`; después, `/login contraseña`. Conservá siempre el mismo nombre exacto.
4. Abrí el códice con **J**. El pueblo amurallado tiene cuatro arcos para salir caminando, taller y cocina públicos. El camino sur lleva al anfiteatro cooperativo.

No hay whitelist y se usa `online-mode=false`, como pidió el propietario. AuthMe controla las cuentas locales. La advertencia de cifrado offline de Simple Voice Chat es esperable bajo esta política. DiscordSRV usa `#virgos-mc` también para la consola; su aviso de canal compartido es intencional. Nadie recibe OP automáticamente; registrá primero la cuenta real antes de asignarle permisos de administración desde la consola.

## Encender y apagar

- **Recomendado: `Panel Virgos-MC` en el escritorio, `administrar.bat` o `panel.bat`.** Abre un panel local con estado visible, botones para encender/apagar/reiniciar, consola, jugadores, permisos y respaldos. Esperá **Abierto** para jugar y **Apagado** después del respaldo antes de apagar la PC. Cerrar el navegador no apaga Minecraft. [Guía del panel](docs/panel-administracion.md).
- `iniciar.bat`: abre la consola normal y arranca el servidor con 1 GB inicial y 8 GB máximos. Esperá `Dedicated server took` y la inicialización de AuthMe, Discord y Playit. Para guardar y apagar, escribí `stop` en esa consola.
- Si el servidor fue iniciado en segundo plano por Codex, `comando.bat` envía comandos y `detener.bat` guarda y apaga. Sus respuestas están en `logs/latest.log`. No hace falta abrir otra instancia.
- `comprobar.bat` y `comprobar-publico.bat` consultan el estado local y por Playit.

La PC debe permanecer encendida y conectada. Playit Companion funciona dentro del servidor, sin aplicación ni servicio de Windows. El dominio Premium utiliza entrada regional de Brasil. Detalles de la ruta y sus limitaciones en [Playit](docs/playit.md).

## Contenido de esta versión

- Alex's Caves y Alex's Mobs, Create y complementos, Iron's Spells, Ars Nouveau, mochilas, cocina, decoración, estructuras, Aether, Twilight Forest y Cataclysm.
- 244 misiones personales en español, agrupadas en 10 capítulos con búsqueda y filtros, preparación rápida, tres proyectos comunitarios y premios de primera victoria para ocho jefes. Mapa, 25 chunks de protección por persona y recuperación de equipo mediante Corpse.
- Mercado con ocho puestos de trueque, cuatro NPC con guías, encargos sin vencimiento, fotografía con Exposure, Small Ships e instrumentos. `/virgos menu` reúne la ayuda.
- Tres expediciones propias: Resonancia cambia los sellos, Forja consume suministros de Create y requiere refrigeración, Umbral enfrenta a tres o más jugadores con un guardián de tres fases. Daño y curación limitados dentro de la arena.
- Rangos personales que limitan la magia avanzada incluso al recibir objetos regalados. Create, construcción y cocina conservan su progreso individual. Las recetas excluyen varias mejoras de almacenamiento excesivas y mochilas anidadas.
- Simple Voice Chat: O abre el menú; Bloq Mayús para hablar. UDP independiente mediante el mismo Companion y Playit Premium Brasil. No requiere aplicación adicional.
- Mods de rendimiento y plugins AuthMe/LuckPerms/CoreProtect/DecentHolograms/DiscordSRV. CoreProtect audita colocación y rotura, incluidos bloques de Create; restauración de inventarios y entidades desactivada. Para máquinas modded y NBT, usar respaldo completo.
- Chat compartido con **LaLechebanda → #virgos-mc**, avisos de conexión y ayuda con `!jugadores`, `!ip`, `!ayuda` y `!voz`. Discord es opcional y no cambia el instalador. [Uso y configuración](docs/discord.md).

El perfil estándar contiene 116 archivos de mods requeridos, contando dependencias; hay cuatro opciones visuales. El servidor tiene 116 JAR de mods, incluido Virgos Core **2.0.0**, cinco plugins base y el puente opcional de Distant Horizons. WorldEdit queda como herramienta opcional fuera del runtime público porque bloquea el evento de arranque de Ketting. El [catálogo](docs/catalogo-mods-virgos-mc.md) explica la selección; los archivos exactos están fijados en `pack/mods.lock.json`, `pack/custom-artifacts.lock.json` y `pack/administration.lock.json`.

La [visión vigente](docs/vision-servidor.md) combina progreso individual, ayuda para quienes juegan menos y encuentros que requieren colaboración. La [auditoría y roadmap de v1](docs/roadmap-auditoria.md) registra los quince trabajos completados y sus evidencias de cierre. Se comprobaron Umbral con tres clientes, misiones, aportes comunitarios y loot individual. El combate de las pruebas se resolvió con daño de consola: la dificultad, el audio entre micrófonos y la carga de ocho jugadores con fábricas necesitan validación con el grupo. Los límites mágicos no son un bloqueo universal de armas y armaduras.

La versión **2.0** estrena mundo y reinicia inventarios, misiones, bases y estadísticas. Conserva las cuentas AuthMe y sus contraseñas. Suma Terralith/ReStoned, ciudades de Integrated Villages, IDAS, WDA, nuevos jefes, Incendium, Nullscape y Deep Aether. /perfil muestra horas, nivel, rango y misiones; /perfil Nombre permite consultar a un amigo aunque esté desconectado. Las horas no otorgan ventajas. Cambios, créditos y límites de las pruebas en [la revisión 2.0](docs/revision-2.0.md).

## Versionado del sistema

El repositorio público contiene el sistema reproducible: código de Virgos Core/Códice, scripts, KubeJS, plantillas, locks, overrides, documentación y pruebas. El `.gitignore` excluye mundos, respaldos, cuentas AuthMe, configuraciones vivas, credenciales, logs, cachés, binarios descargados e instaladores generados. Los datos de producción se mantienen fuera de Git; para preparar una copia limpia se usan los manifiestos de `pack/` y las plantillas.

Los tags `vMAJOR.MINOR.PATCH` activan `.github/workflows/release.yml`: descarga las dependencias fijadas, compila Core/Códice, regenera el instalador y publica ZIP, MRPack y `release.json` como GitHub Release.

## Mundo y mantenimiento

El mundo activo es `virgos_world`; el pueblo del spawn está en **672, 80, 752**. Las carpetas antiguas `world*` se retiraron porque no participan del servidor; para recuperar el estado actual se conservan los respaldos recientes de `backups/full`. No volver a ejecutar `deploy-release.py` sobre un mundo en uso.

Para pasar la noche alcanza con que duerma una sola persona, independientemente de cuántos estén conectados (`playersSleepingPercentage=0` en el mundo principal). La regla queda guardada con el mundo.

- `respaldo.bat`: con el servidor detenido, respalda los seis mundos, cuentas, permisos, mods y configuración en `backups/full`.
- Al apagar limpiamente con `stop`, los controladores verifican un respaldo completo. Después de una sesión, si pasaron dos horas desde el último respaldo y el servidor lleva diez minutos vacío, realiza guardado, copia y reinicio. No expulsa jugadores para hacerlo.
- `virgos checkpoint`, desde la consola y sin jugadores conectados, solicita ese ciclo de copia y reinicio. Se conservan hasta 12 copias automáticas o 30 GiB, manteniendo al menos dos; las manuales no se eliminan.
- `validar.bat` comprueba todos los componentes antes del arranque. [Operación y recuperación](docs/operacion-y-recuperacion.md) explica diagnóstico, copias y restauración.
- `scripts/restaurar-respaldo.ps1 -ArchivePath RUTA_ZIP -RestoreTo CARPETA_NUEVA_DENTRO_DEL_PROYECTO`: restaura en otra carpeta y verifica cada archivo. No pisa la partida actual.
- `preparar.bat` reconstruye la plataforma base fijada; no instala por sí solo todo el paquete de contenido. Conservá los locks y los respaldos.
- `logs/latest.log`: diagnóstico. `server.properties`: ajustes generales; reiniciar después de modificarlos.

Los respaldos contienen cuentas y credenciales de Playit y Discord: guardalos localmente. Para tus amigos compartí solamente los archivos de `dist` y la guía.

SimpleBackups sigue ofreciendo copias parciales durante sesiones largas; sólo las copias de `backups/full` cubren las seis carpetas de mundos. Los documentos de [diseño](docs/experiencia-virgos-mc.md) e [implementación inicial](docs/implementacion.md) conservan contexto histórico; el estado de v1 está en el roadmap.
