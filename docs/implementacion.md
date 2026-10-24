# Implementación de Virgos-MC

## Auditoría de recetas — 2026-10-20

Se retiraron las exclusiones de recetas de KubeJS y se habilitaron las opciones nativas de fabricación de Lightman's Currency. El servidor conserva las recetas de los mods tal como las entrega cada mod; las condiciones internas de esos mods siguen siendo la autoridad. `pack/disabled-recipes.json` queda vacío y la mejora de mochilas de Sophisticated Backpacks vuelve a mostrar la progresión de hierro, oro y diamante en JEI.

El arranque público validado cargó 22.071 recetas y removió cero. Se corrigió además la receta de herrería de Elytra de Incendium para 1.20.1. Quedan cinco advertencias de Every Compat sobre variantes decorativas de Ars Nouveau/Cataclysm con ingredientes inexistentes; no afectan recetas de progresión y no se inventaron sustitutos para ellas.

Registro histórico de la implementación. El estado vigente, los hallazgos y sus pruebas están en [roadmap y auditoría](roadmap-auditoria.md); la dirección del proyecto está en la [visión](vision-servidor.md). Los resultados de versiones anteriores se conservan como evidencia fechada.

## Evidencia histórica — 0.1.0-rc1

El paquete completo ya está instalado en la raíz pública, puerto 25565 y mundo `virgos_world`. Se conservaron la base original, sus cuentas y las credenciales de Playit. El laboratorio está detenido. La conexión Forge por el dominio, el respaldo de cierre y el reinicio final están comprobados. El servidor quedó encendido con AuthMe, progreso y arena habilitados.

| Entrega | Estado comprobado | Evidencia / alcance |
| --- | --- | --- |
| Paquete reproducible | Cliente y servidor arrancan; instaladores ZIP y mrpack generados | 86 mods requeridos en cliente; hashes y descarga real del instalador comprobados |
| Configuración | 86 valores en diez archivos y exclusiones de recetas aplicados | Configuraciones cargadas; no equivale a probar cada máquina de todos los mods |
| AuthMe y modo offline | Dos clientes registran/login; acciones previas bloqueadas; posición protegida | Pruebas de misiones, hechizos, logout y resincronización de OPAC |
| Misiones personales | 66 misiones y ocho grupos en español | Persistencia y estados separados de dos UUID; recompensas sin duplicar |
| Cooperación | Tres encuentros habilitados; 14 pruebas lógicas; dos clientes completan Resonancia | Sellos, recompensas y cancelación al logout; bajas de oleadas simuladas por consola, dificultad pendiente de sesión humana |
| Protección | Bases privadas, estaciones públicas, magia desde fuera del claim y pistones probados | No se garantiza cobertura de todas las contraptions/deployers de Create |
| Spawn y arena | Bastión v4 y anfiteatro v3 construidos y exportados | 147542 y 5359 bloques auditados; cuatro salidas y camino sur transitados sin daño |
| Magia | Límites personales de Iron y Ars validados con lanzamientos reales | Diez pruebas lógicas, tres casos Iron y cinco Ars; no limita universalmente armas/armaduras |
| Recuperación de equipo | Propietario recupera mochila/comida, otra identidad bloqueada | También se abrió el cadáver del dueño dentro del claim principal del spawn |
| Rendimiento | 20 TPS con dos clientes; mediana 4,5 ms y p95 11,1 ms en muestra de un minuto | No prueba ocho jugadores, grandes fábricas ni perfil con shaders |
| Distribución | ZIP, mrpack y guía preparados | PowerShell 5.1 instaló/verificó los 86 mods; cuatro opciones visuales sin prueba conjunta |
| Restauración | Seis mundos restaurados y copia arrancada; spawn auditado | Copia de 786 archivos; candidato final posterior de 802 archivos preservado |

Los informes están en `.lab/reports`. Esta versión ofrece un balance inicial para empezar a jugar; equipo final, economía de máquinas y dificultad real de grupo requieren observar una partida del grupo y ajustar valores. Las ideas más amplias del documento de diseño siguen siendo expansión.

## Registro

- Se comprobó el proceso público existente: Ketting 0.6.1, Forge 47.4.22 y Java 17. La base tiene AuthMe y Playit Companion, sin contenido instalado aún.
- Se confirmó la selección de 79 mods principales, cuatro opcionales y WorldEdit como herramienta de construcción. La resolución de dependencias y las pruebas se harán sobre archivos reales.
- Se excluyó Amendments por un conflicto reproducido con el atril de Iron's Spells. El aviso opcional de Supplementaries se desactivó en el cliente; no había bloques del spawn que migrar.
- Se corrigió `pack.mcmeta` del controlador local de pruebas. Este controlador queda excluido de cualquier entrega para los amigos.
- Se corrigieron cuatro datos incompatibles de los mods mediante overrides de KubeJS. El último arranque del laboratorio no registró errores de carga.
- Se creó un puente con AuthMe que descarta payloads de acciones Forge antes de autenticarse. El login y las acciones de Heracles posteriores funcionan en un cliente real; esto no sustituye las pruebas específicas de protección pendientes.
- Se separaron J (códice), B (mochila), M (mapa), N (marcador), H (historial de muertes) y P (claims). Se preparó un recurso propio con traducciones del códice y se ocultó la barra de edición de FancyMenu.
- El generador `build-bastion.py` construyó una ciudad original con cuatro puertas, plaza, archivo, taller, posada, mercado y jardín. La revisión visual y funcional continúa.
- Las exclusiones históricas de recetas de mejoras de almacenamiento, mochilas anidadas y objetos de expansión fueron retiradas. El anidamiento funcional y los límites de uso de mochilas siguen controlados por configuración, no ocultando recetas.
- `virgos_balance.js` cargó correctamente en el reinicio y reportó cero recetas removidas por el balance de Virgos.
- El Bastión está en 672,114,736 y el spawn en 672,115,752. Tiene claims de servidor para la ciudad y los cuatro accesos; el nombre y los permisos públicos se configuraron separadamente de las bases personales.
- La primera revisión detectó agua desbordada, conexiones de vallas/vidrios sin actualizar y una pérgola incompleta. Se corrigió la plantilla y se aplicó `bastion-repair-v2`, con techos de escaleras, soportes de lámparas y escaleras interiores de torres. El audit está en `.lab/server/virgos-reports/bastion-audit.json`.
- Se verificó la identidad 13e2e728-2a7a-36a6-84ee-5c289cf4cc02 con bienvenida completada y la identidad 32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e inicialmente pendiente. La evidencia guardada está en `.lab/reports/quests-two-identities.json`. Después se completó también la segunda como prueba de autenticación.
- Se reprodujo una caída al vacío al reconectar un espectador: AuthMe deshabilitaba el vuelo temporalmente. La integración ahora bloquea paquetes de movimiento antes del login, conserva un ancla de posición e impide daño en ese estado. La prueba de 20 segundos conservó 20 de vida; hubo una corrección visual inicial de cuatro bloques, luego se mantuvo cerca de Y=200 y el login restauró Y=200 exacto. Se comprobó movimiento normal y vuelo después del login.
- Se fijó `virgos_core` en `pack/custom-artifacts.lock.json`; staging verifica todos los hashes antes de copiar y rechaza cambios con el laboratorio o cliente abiertos. El controlador QA requiere la opción explícita `--qa` y nunca forma parte de los artefactos de entrega.
- La base original quedó en `backups/full/virgos-20261017-152626-base-antes-del-paquete.zip`. Se restauraron 233 archivos en `.lab/restore-check/base-20261017-152626` y se verificó cada SHA-256. Esta prueba confirma integridad de archivos, todavía no un arranque recuperado.
- La revisión v3 detectó una interferencia entre la torre y la escalera del archivo y 59 posiciones de grava vacías. La reparación borraba bloques antiguos después de rellenar los nuevos cimientos. V4 hace ese borrado antes del relleno y trasladó las escaleras al otro lado del edificio. La auditoría y los cuatro recorridos reales quedaron sin fallas (`qa-spawn-gates.json`).
- La cocina pública entregó una porción de arroz cocinado al jugador sin OP (`qa-public-cooked-recipe.json`). Los dos fogones se configuraron encendidos tanto en el mundo como en el generador.
- La reconexión en supervivencia conservó 618.5,115,787.5 durante diez segundos sin autenticar, con 20 de vida, y mantuvo ese lugar tras el login. La cuenta no volvió forzosamente al spawn.
- Se detectó la pantalla de OPAC bloqueada en “Syncing…” después de autenticar: su handshake inicial se descartaba antes del login. La integración reinicia el handshake después de autenticar, sin reproducir acciones previas. La interfaz volvió a mostrar nombre, color y 0/25 zonas; la prueba posterior permitió reclamar y liberar una zona con permisos normales.
- Se probó un cofre en una parcela de VirgosQA1: VirgosQA2 no pudo abrirlo ni romperlo en creativo. Tras liberar esa parcela y reclamarla con el comando normal de VirgosQA2, el mismo cofre se abrió. Se liberó la parcela y se retiraron cofre/plataforma temporales (`.lab/reports/qa-private-claims.json`).
- El menú de claims volvió a sincronizar también después de `/logout` y otro login en la misma conexión. La interfaz principal tiene traducciones en español y muestra 0/25 zonas tras limpiar las pruebas.
- `Progression` verifica logros personales al lanzar hechizos. Iron permite comunes/poco comunes desde el inicio, raros con Explorador, épicos con Especialista+Resonancia y legendarios con Maestro+Umbral. Ars permite nivel 1 desde el inicio, nivel 2 con Explorador y nivel 3 con Especialista+Forja. Estos límites afectan magia; no constituyen un balance completo de todas las armas, armaduras y accesorios.
- Se probaron tres casos reales de pergaminos Iron y cinco de libros Ars, sin OP: básicos permitidos, regalos avanzados bloqueados, y los mismos objetos permitidos al otorgar los logros. Informes: `qa-magic-progression.json` y `qa-ars-progression.json`. Los logros, libros y efectos de prueba se retiraron luego. Ketting emitió avisos de tipo de entidad desconocido para los proyectiles, sin detener la prueba; la protección frente a esos proyectiles sigue pendiente.
- Las reglas cooperativas rechazan identidades duplicadas, entrada tardía, un jugador alternando dos sellos y una victoria con participantes ausentes. Pausan y abortan después de diez segundos sin un integrante válido; los enemigos deben haberse creado antes de reconocer una oleada vacía. Todavía no están conectadas a una arena jugable.
- Se restauraron 769 archivos del respaldo `virgos-20261017-160552-spawn-v4-verificado.zip` con sus hashes. Al revisar las dimensiones se encontró que el respaldo sólo enumeraba Overworld/Nether/End; el script ahora incluye todas las carpetas hermanas del mundo creadas por Ketting. Se prepara un respaldo nuevo que incluya también Aether, Twilight y la dimensión de Iron.
- El respaldo corregido es `backups/full/virgos-20261017-161921-spawn-magia-todas-dimensiones.zip`: 786 archivos y seis carpetas de mundos, incluidas 15 entradas de las dimensiones de mods. Se restauró en `.lab/restore-check/all-dimensions-20261017-161921`, arrancó con 84 mods en localhost:25576, auditó los 147542 bloques del Bastión y se apagó limpiamente (`restore-runtime-verification.json`). Esa copia de prueba quedó apagada.
- El anfiteatro está en 672,78,1048 y se alcanza desde el camino sur. V1 bajaba bien pero una escalera colocada demasiado baja impedía regresar sin saltar. V2 corrigió la altura: `qa-arena-walk.json` registra ida y vuelta sin salto ni daño. V3 añadió una base continua bajo la grava al encontrar dos huecos fuera del eje central; su auditoría comprobó 5359 bloques sin ausencias, bloques distintos ni fallas de recorrido.
- La arena usa el sub-claim de servidor `arena`: permite daño de mobs, daño de jugadores a entidades y uso de objetos. El Bastión mantiene `playersByMobs=OFF` e `itemUse=Nobody` con sus excepciones de estaciones/libros. La comprobación se hizo con comandos de lectura de ambos perfiles. Los límites de construcción permanecen protegidos.
- Las tres expediciones tienen controlador servidor con registro durable de reconocimientos pendientes, tres rondas de sellos/combate y limpieza de enemigos. La plantilla inicial usa husks, strays, vindicators y ravagers; no se presenta como un jefe de Cataclysm. La arena permanece deshabilitada hasta completar la prueba multijugador. Se preparó `client/qa-secondary` con una segunda identidad Forge para esa prueba; ambos perfiles QA están excluidos de la distribución.

- Prueba cooperativa con dos clientes reales: tres fases de sellos, reconocimientos individuales y cancelación por logout sin recompensa (`qa-expeditions.json`). Las oleadas se eliminaron mediante daño de consola para verificar la lógica; no se considera una medición de dificultad. Un encuentro aparte comprobó daño de un husk real a un participante (`qa-arena-pve.json`).
- Los carteles de los sellos interceptaban el clic; se movieron a un lateral y se actualizó la plantilla. Se agregó una excepción de interacción limitada a lodestones en el sub-claim de arena. El permiso de romper sigue cerrado.
- Un proyectil real de Ars rompió madera libre y no pudo romper el mismo bloque dentro de una parcela ajena; un pistón externo tampoco desplazó el bloque protegido (`qa-claim-boundary.json`). La primera ejecución del montaje QA falló por preparar bloques antes de cargar el chunk; se corrigió el montaje y se repitió con control positivo.
- Se exportó `anfiteatro-virgos-v3.schem` y se agregó al manifiesto del spawn.
- El instalador Windows PowerShell 5.1 verificó 85 mods en caché, descargó el restante y volvió a verificar los 86. La distribución usa URLs y hashes: no contiene cuentas, mundos, el controlador QA ni binarios de Minecraft (`client-installer-verification.json`).
- Spark registró mediana 4.5 ms y percentil 95 de 11.1 ms en la ventana de un minuto con dos clientes QA. Es una muestra de arena/spawn, no una prueba con ocho jugadores o grandes fábricas (`performance-two-qa-clients.json`).

- Recuperación de muerte dentro del claim de arena: una cuenta ajena no abrió el cadáver; su dueño recuperó tres panes y una mochila desde la interfaz real (`qa-corpse-recovery.json`). Se permite únicamente interactuar con `corpse:corpse`; el propio mod conserva la comprobación de dueño.

- Better Combat se comprobó con la tecla normal de ataque contra un husk a 1.5 bloques dentro de la arena: vida 20 → 14.096 y avance del combo. Los primeros intentos colocaban el objetivo detrás del sello o en el borde del alcance (`qa-arena-melee.json`).

- Publicación: se copiaron seis mundos y las configuraciones a la raíz, conservando `world*`, Playit y AuthMe. La base previa está en `virgos-20261017-170857-base-prepublicacion.zip`; el candidato completo está en `virgos-20261017-172316-candidato-rc1.zip`.
- La entrada directa de Companion falló con el handshake de Forge por el grupo del hilo Netty. Se configuró su reenvío TCP incorporado hacia localhost:25565, sin modificar el JAR ni instalar un agente externo. El dominio fijo completó el handshake, login, sincronización de OPAC y carga del mundo (`qa-public-connection.json`). La UI Heracles abrió por J a través de esa conexión.
- El cadáver del dueño pudo abrirse también dentro del claim principal del Bastión, en supervivencia y sin OP (`qa-public-corpse-city.json`). Después se retiró el cadáver de prueba.
- Las conexiones reenviadas aparecen como localhost: se conservan el login por contraseña y las sesiones automáticas desactivadas. No se deben usar bans por IP sobre esta ruta. La cuenta pública de pruebas fue eliminada mediante AuthMe y se cerró el cliente QA.

- Se pregeneró un círculo de radio 512 bloques alrededor de 672,736: Chunky informó 4225 chunks procesados en 66 segundos. Después se apagó limpiamente y se archivaron únicamente los datos de UUID de pruebas; no hay OP ni cuentas QA activas.

- Respaldo de cierre público: `backups/full/virgos-20261017-173805-publicado-rc1.zip`, 990 archivos, seis mundos, CRC de todas las entradas y hashes de core/configuración/ruta comprobados (`public-final-backup.json`).

- Reinicio final verificado: dominio público responde, AuthMe/progreso/arena activos, cero jugadores y ningún chunk forzado. Servidor encendido en segundo plano; `detener.bat` guarda y apaga. Informe: `.lab/reports/public-final-runtime.json`.

## Instalador para jugadores, revisión 2

El archivo para compartir es `dist/Virgos-MC-0.1.0-rc1-instalador-v2.zip`. Su entrada es `EMPEZAR.bat`: asistente Windows con selección de TLauncher/oficial, progreso, reintentos, registros y botones para copiar. El paquete del juego sigue en 0.1.0-rc1; esta revisión cambia la instalación.

- Descarga Java 17 portable, Forge 47.4.22 y los 86 mods estándar desde sus fuentes, con hashes fijados. Java queda dentro de la carpeta del juego, sin instalador global. La lista de servidores incluye Virgos-MC y el perfil inicial activa la interfaz en español.
- Oficial: Forge se prepara en una carpeta aislada y se copian sus bibliotecas/versiones. Se agrega un perfil con carpeta propia, Java y 5120 MB; los dos posibles archivos de perfiles se respaldan antes de editarlos. No se leen ni copian archivos de cuentas.
- TLauncher: prepara la carpeta completa. El usuario pega el directorio, asigna memoria y selecciona la versión exacta mediante los pasos del asistente. La configuración general de TLauncher se cambia desde su interfaz; hay que anotar el directorio anterior para otras partidas. No se instala un launcher ni se automatiza su inicio de sesión.
- La reparación conserva `servers.dat`, `options.txt` y los mundos. Los mods ajenos bloquean la operación. Las configuraciones propias del paquete se vuelven a aplicar. El `.mrpack` sigue como alternativa avanzada, con la limitación de ForgeCDN documentada anteriormente.
- La guía de instalación ahora es corta. Las misiones, teclas y expediciones pasan a `docs/manual-jugadores.md` y al archivo `COMO-JUGAR.txt` del ZIP.

Referencias técnicas: [ajustes de TLauncher](https://tlauncher.org/en/settings.html), [Java automático en TLauncher](https://tlauncher.org/en/install-java.html), [CLI del instalador Forge](https://github.com/MinecraftForge/Installer/blob/2.0/src/main/java/net/minecraftforge/installer/SimpleInstaller.java). El flujo dentro de la interfaz de TLauncher requiere una prueba en una PC que lo tenga instalado.

Validación del instalador: Windows PowerShell 5.1, instalación real de Forge y Java, descarga y verificación del mod faltante, 86 hashes correctos, ruta con espacios, ambos tipos de perfiles oficiales y sus respaldos. Trece comprobaciones de conservación y rechazo de entradas inválidas pasaron. Evidencias: `.lab/reports/installer-v2-integration.json`, `installer-v2-unit.json` y vistas de la ventana `installer-v2-tlauncher.png` / `installer-v2-oficial.png`. La instalación se probó en `.lab`; los perfiles reales del usuario y el servidor no se modificaron.

## Actualización 0.2.0-rc1 — 18 de octubre

- Actualización selectiva de 107 archivos; no copia mundos ni datos de jugadores desde el laboratorio. Respaldo completo previo: `backups/full/virgos-20261018-002243-antes-v02.zip`, 1027 archivos verificados. Manifiesto: `pack/upgrade-v02.json`.
- Virgos Core 0.2.0: Resonancia con pares de sellos rotativos; Forja con suministros consumibles y refrigeración; Umbral con devastador de 480 HP base, escala por participantes y tres fases que no pueden saltarse. Mínimos 2/2/3 jugadores. Inventarios conservados al entrar.
- Presupuestos de daño de arena compartidos entre blancos y límites de curación, configurables en `config/virgos/expeditions.json`. El daño de la aventura libre no cambia. Las pruebas no equivalen a balance de dificultad con ocho jugadores y equipo avanzado.
- 83 misiones y 11 capítulos. Nuevas rutas de preparación, tres proyectos comunitarios con aportes consumidos y premios retroactivos para nuevos Exploradores, y ocho premios personales de primera victoria. Los drops originales de jefes siguen compartidos. Los IDs anteriores se conservan.
- Los aportes comunitarios usan un diario previo a la operación y un recibo guardado con el inventario. Tras un reinicio se reconcilian al entrar el jugador. Si se interrumpe una escritura, el sistema se cierra para recuperación; no debe borrarse `virgos-community.json`.
- Simple Voice Chat 2.6.24 en cliente y servidor. Menú O y pulsar para hablar Bloq Mayús en instalaciones nuevas; actualizar añade sólo las teclas que falten. Reinstalar conserva el micrófono y las preferencias del usuario.
- CoreProtect CE24.1 con SQLite, sin registro de comandos ni chat y sin restaurar inventarios o entidades. Colocación/rotura real de piedra y Create registrada; restauración de piedra comprobada. El filtro `create:andesite_casing` fue rechazado por el parser de rollback: para máquinas y NBT usar respaldos completos. No se promete rollback universal modded.

Pruebas: compilación Java17; 14 casos cooperativos, 10 de progresión y pruebas de presupuestos/fases; dos clientes reales completaron Resonancia y Forja, con daño de consola simulado; Umbral rechazó dos participantes. Las fases de Umbral se probaron como reglas deterministas, no con tres jugadores reales. Se verificó premio personal del Ender Guardian, consumo/tope de aportes y persistencia al reiniciar. Informes: `.lab/reports/qa-v02.json`, `qa-v02-admin.json`; captura del códice `v02-codex.png`.

Medición local con dos clientes, sin grandes fábricas: 20 TPS, promedio global 4,317 ms/tick. No es una prueba de ocho jugadores ni garantiza rendimiento bajo generación intensa. Instalador 0.2 probado con 87 mods y actualización real de la carpeta de pruebas; 15 comprobaciones de conservación/validación pasaron en Windows PowerShell5.1.

- Voz pública comprobada: túnel UDP separado, Premium Brasil, `practically-accountant.tun.ply.gg:2685`; mismo agente integrado. Eco UDP recibido y cliente Forge real conectado/autenticado por el dominio del juego. La cuenta temporal se eliminó mediante AuthMe y el cliente se cerró. No se capturó micrófono ni se hizo una prueba humana de escucha. Informe `qa-v02-public-voice.json`.
- Companion oficial 0.1.2 tenía un fallo al leer el identificador de paquetes IPv4 UDP. La variante local `0.1.2-forge+virgos.1` corrige una instrucción; todas las otras clases y recursos son idénticos. Original respaldado, parche reproducible en `dev/playit-udp-fix`, archivo local y hash fijados en `versions.lock.json`. Se probó el reinicio y la entrada pública después del cambio.
- Persiste una advertencia de Ketting al envolver el mundo simulado de Supplementaries/Moonlight durante el arranque. El servidor completa el inicio y las pruebas anteriores; no se considera resuelta ni se presenta el log como totalmente libre de avisos de compatibilidad.
- Pregeneración pública completada sin jugadores: círculo de radio 768 en 672,752. Chunky procesó 9409 chunks en 1 min 47 s; se amplía la zona previamente preparada de 512 bloques. Informe `pregen-v02.json`. La tarea termina, no queda ejecutándose en segundo plano.
