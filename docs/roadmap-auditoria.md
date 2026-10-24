# Roadmap y auditoría de Virgos-MC

**Virgos-MC v1.0.0 entregada el 18 de octubre de 2026.** La auditoría de la versión 0.2 produjo los quince trabajos de esta tabla; sus soluciones están implementadas y verificadas, conforme a la [visión del servidor](vision-servidor.md). El alcance incluye instalación, contenido, progreso, cooperación, protección, voz, recuperación y operación. Se revisaron los archivos efectivos, el código propio, el instalador y las pruebas de juego; la actualización conservó mundos e IDs de progreso. Los informes con nombre `v03` corresponden a la candidata interna utilizada para validar el cierre de v1.

## Resultado inicial

La revisión estática encuentra 86 JAR de servidor, tres plugins, 83 misiones y seis carpetas de mundos. Sus hashes, identidades de mods, referencias de objetos, dependencias de misiones y política efectiva de balance coinciden con lo previsto. El respaldo automático de SimpleBackups contiene únicamente `virgos_world`; no cubre las otras cinco carpetas ni cuentas y permisos. Evidencia: `.lab/reports/audit-baseline.json`.

## Trabajo de esta revisión

| ID | Prioridad | Hallazgo o necesidad | Solución y aceptación | Estado |
| --- | --- | --- | --- | --- |
| R01 | Alta | Respaldo automático incompleto en Ketting. | Copias completas consistentes al apagar y mantenimiento automático cuando esté vacío; verificar seis mundos, bases de datos y restauración aislada. Informar el alcance del respaldo parcial durante sesiones largas. | Completado |
| R02 | Alta | Arranque normal y gestionado validan componentes distintos. | Un manifiesto vigente y un validador compartido, con rechazo de hashes incorrectos, duplicados y herramientas QA. | Completado |
| R03 | Alta | Una actualización que cambia el nombre de un JAR se confunde con un mod ajeno. | Reconocer exclusivamente archivos gestionados por el manifiesto anterior y respaldarlos antes de reemplazar; conservar mods ajenos y rechazar cambios inesperados. | Completado |
| R04 | Alta | El diario de aportes necesita validación de datos y recuperación ante escrituras interrumpidas. | Validar proyecto, UUID, cantidad y recibo; impedir sobrescribir una operación pendiente; pruebas de recuperación sin duplicar aportes. | Completado |
| R05 | Media | Umbral todavía no tuvo una prueba completa con tres clientes. | Completar tres fases con tres identidades reales, comprobar mínimos, pausa/cancelación y premios; distinguir simulación de combate de dificultad humana. | Completado |
| R06 | Media | La guía de Forja cobra todos los materiales por ronda, pero el código los reparte entre rondas. | Unificar códice, manual y mensajes: 8 placas de hierro, luego 4 de latón, luego 1 mecanismo. | Completado |
| R07 | Media | La misión inicial acepta sólo una cama blanca y el menú de ayuda no presenta las funciones nuevas. | Aceptar cualquier cama sin cambiar el ID de misión; ayuda navegable y estado personal de expediciones/proyectos. | Completado |
| R08 | Media | Faltan comprobaciones repetibles que cubran la entrega completa. | Auditoría ejecutable de inventario, hashes, configuración, misiones, copias y salud; informe sin credenciales. | Completado |
| R09 | Media | Los documentos de diseño mezclan planes antiguos con funciones instaladas. | Visión vigente, roadmap con evidencias, manual breve y referencias claras al estado implementado. | Completado |
| R10 | Media | El mantenimiento de Companion depende de un parche local y del nombre del túnel. | Fijar la variante, probar arranque y reconexión pública/voz; conservar fuente, original y procedimiento de reconstrucción. | Completado |
| R11 | Media | Compatibilidad y protección requieren revisar los límites efectivos, no sólo que arranque. | Auditar dependencias y logs; volver a comprobar autenticación, claims, spawn, muerte, botín y comandos de administración según los cambios. | Completado |
| R12 | Media | La entrega necesita una recuperación y publicación completas. | Respaldo verificado, restauración en localhost, instalador actualizado y prueba pública final; dejar únicamente producción encendida. | Completado |
| R13 | Media | El cliente muestra un aviso de recetas de JEI durante la sincronización optimizada de ModernFix. | Comprobar recetas recibidas y orden de eventos; mantener la ruta estándar si evita usar recetas locales de respaldo. Comparar los IDs de recetas entre cliente y servidor. | Completado |
| R14 | Media | Durante la copia, un archivo de auditoría cambió y el tamaño enumerado quedó desactualizado. La verificación frenó correctamente el reinicio. | Obtener tamaño y hash del mismo archivo abierto, impedir escrituras durante su copia y apartar ZIP inválidos. Prueba con modificación después de enumerar. | Completado |
| R15 | Alta | Un registro nuevo quedó guardado en SQLite, pero el login automático encontró temporalmente la entrada negativa anterior de la caché de AuthMe. | Desactivar la caché de base de datos manteniendo consultas asíncronas, reiniciar y repetir registro/login públicos. No cambiar contraseñas ni cuentas reales. | Completado |

## Orden de ejecución

1. Conservar la entrega y datos actuales; completar el inventario y las comprobaciones estáticas.
2. Resolver recuperación, arranque y actualización de clientes.
3. Corregir progresión, aportes y claridad de la interfaz; ejecutar pruebas de reglas y de fallos.
4. Validar el paquete en laboratorio, incluidas tres identidades para Umbral y una restauración completa.
5. Publicar una actualización selectiva, comprobar el dominio y la voz, actualizar las evidencias y cerrar el objetivo.

No se declara resuelto un hallazgo sólo por escribir una prueba o una propuesta. El cierre registra el archivo cambiado, el resultado observado y su límite.

## Evidencias de implementación

Los informes están en `.lab/reports`; los nombres `v03` identifican la candidata de pruebas. `v1-class-equivalence.json` comprueba que las 24 clases compiladas de esa candidata y el JAR publicado como 1.0.0 son idénticas. Sólo cambia la versión del recurso de metadatos.

| Área | Implementación y resultado | Evidencia |
| --- | --- | --- |
| Arranque | `validar-entrega.ps1` compartido por ambos controladores; rechaza un plugin alterado, un JAR QA ajeno y entradas duplicadas. | `startup-validation-v03.json` |
| Instalación | Descarga y verifica antes de sustituir; conserva los JAR anteriores y el manifiesto en `respaldos-actualizacion`. 22 comprobaciones de migración, rutas, perfiles y preferencias; reparación real de una instalación existente a 87 mods requeridos de v1. | `installer-v3-unit.json`, `installer-v1-repair.json` |
| Aportes | Diario validado, recibos durables y confirmación del inventario en `player.dat` antes de cerrar una donación; recuperación idempotente y aislamiento de escritura fallida. Aporte real de trigo y límites personales comprobados. | `core-v1-checks.txt`, `qa-v03.json` |
| Umbral | Dos jugadores no alcanzan; tres identidades completan fases de 480/320/160 de vida. Pausa por ausencia, barreras, reconocimientos individuales y cancelación al desloguearse comprobados. Se simuló el daño de combate. | `qa-v03.json` |
| Claridad y progreso | Forja muestra los suministros correctos por ronda; la misión conserva su ID y acepta una cama roja real sin consumirla. Ayuda con enlaces y aportes personales. | `qa-v03.json`, `v03-help-and-community.png` |
| Lootr | Dos clientes abrieron el mismo cofre. Retirar una pila con el primero dejó intacto el inventario de botín del segundo. | `qa-lootr-v03.json` |
| Spawn | Auditoría de 147.542 bloques y rutas sin piezas faltantes, soportes inválidos ni pasos bloqueados en laboratorio. En la copia restaurada aparecieron dos capas naturales de nieve, sin bloqueo de rutas. | `spawn-audit-v03.json`, `restore-runtime-verification.json` |
| Recetas | `smart_ingredient_sync=false` en ambos lados conserva las demás optimizaciones de ModernFix. JEI usa recetas sincronizadas y las 14.516 IDs del cliente coinciden con el servidor. | `recipe-sync-v1.json` |
| Recuperación | Copia completa de 1.106 archivos verificados; restauración en carpeta nueva, arranque en localhost, auditoría del spawn, carga de seis mundos y apagado limpio. | `restore-runtime-verification.json` |
| Integridad de copias | Un archivo de prueba cambió de tres a 253.952 bytes después de enumerarlo. El respaldo corregido guardó tamaño, contenido y hash coherentes. La primera copia rechazada se conservó fuera de `backups/full`. | `backup-concurrency-v1.json`, `checkpoint-v1-first-attempt.json` |
| Auditoría final | 86 JAR, tres plugins, 83 misiones y seis carpetas de mundos; ninguna comprobación fallida. Las tres diferencias textuales son comentarios y valores predeterminados añadidos por ModernFix, Voice Chat y CoreProtect; los valores configurados coinciden. | `audit-v1-final.json` |
| Mantenimiento real | Con un jugador rechaza el reinicio. Vacío, guarda y apaga, verifica 1.120 archivos de las seis carpetas y vuelve a iniciar con todos los servicios propios disponibles. | `public-v1-before-restart.json`, `checkpoint-v1.json` |
| Registro | Tres registros consecutivos por el dominio, login automático en 1,2–2,1 segundos, voz y recetas correctas. Se borraron únicamente las cuentas de prueba. Caché de base de datos desactivada en configuración activa y plantilla. | `auth-registration-v1.json`, `public-v1-cache-disabled-1.json`, `public-v1-cache-disabled-2.json`, `public-v1-cache-disabled-3.json` |
| Playit y mantenimiento de fuentes | Parche recompilado en una carpeta aislada: SHA256 idéntico al desplegado. Se conserva el original, las fuentes y los insumos locales de compilación. Reconexión de Forge y voz comprobada después del reinicio final. | `playit-rebuild-v1.json`, `public-v1.json`, `v1-source-archive.json`; [reconstrucción](mantenimiento-fuentes.md) |
| Protección y administración | Apertura/rotura ajena, proyectil y pistón entre claims bloqueados; cadáver recuperado sólo por su dueño. Consulta de cambios vanilla/Create y premios personales comprobados. La interfaz de claims vuelve a sincronizar después del login. | `qa-private-claims.json`, `qa-claim-boundary.json`, `qa-corpse-recovery.json`, `qa-v02-admin.json`, `qa-claims-after-auth.json` |
| Configuración definitiva | OPAC usa su sistema `default`, sin referencia al complemento ausente. Se aplicó con el servidor detenido, respaldó y comprobó tras arrancar. La copia final conserva 1.120 archivos de seis mundos. | `v1-final-config.json`, `.runtime/last-backup.json` |
| Cierre de entrega | 145 comprobaciones sobre los artefactos publicados, plantillas empaquetadas, hashes del cliente reparado, fuentes del parche, evidencias de juego y procesos actuales. Sólo producción queda encendida; cliente QA y laboratorios apagados. | `v1-release-final.json`, `public-v1.json`, `recipe-sync-v1-public.json` |

La cobertura anterior de claims, cadáveres y límites mágicos se conserva donde no cambió la implementación. No equivale a probar cada interacción de todos los mods. CoreProtect sigue limitado a la restauración comprobada de bloques vanilla; las máquinas con NBT se recuperan mediante copias completas. Los avisos de compatibilidad de Moonlight/Ketting y algunos modelos internos de depuración siguen registrados; no se interpreta un arranque correcto como ausencia total de advertencias.

## Entrega y estado de cierre

- Servidor público operativo en **virgos-mc.playit.plus**, con AuthMe, progreso, arena, proyectos, voz y mantenimiento disponibles. Cliente Forge real conectado tras la configuración final; 14.516 recetas sincronizadas. La muestra de ese cliente dio 20 TPS y 5,399 ms por tick.
- Instalador **`dist/Virgos-MC-1.0.0-instalar.zip`**, revisión 3. SHA256: `177a35d05cdc194f389c708e17e414341038e22af391c71aa6ea1409c60dce9d`. Extraer todo → EMPEZAR → elegir launcher. Reparación desde la instalación anterior verificada; instrucciones en la [guía de jugadores](guia-jugadores.md).
- Última copia completa de cierre: **`backups/full/virgos-20261018-023556-auto.zip`**, 1.120 archivos verificados. SHA256: `f8d99b6ee78d9f4e54ac18c7232c16229a777556923a8bd257cebfd7c7acaa9d`. La restauración aislada anterior comprobó el mismo procedimiento con seis mundos; no se reemplazó la partida pública.
- Fuentes e instaladores preservados aparte en **`backups/virgos-v1-fuentes-*.zip`**, con manifiesto y verificación de cada entrada. Procedimiento en [mantenimiento de fuentes](mantenimiento-fuentes.md).

No quedan tareas de implementación abiertas en R01–R15. La siguiente tabla conserva las validaciones de experiencia que requieren al grupo; no se presentan como pruebas ya realizadas ni como garantías de rendimiento.

## Validación con el grupo

La ampliación v2 se cerró el 19/10/2026: mundo nuevo, generación y botín ajustados, pueblo auditado, 244 misiones con interfaz de lista, perfiles, cliente oficial actualizado, prueba pública de voz y recetas, respaldo limpio y reemplazo del instalador en Discord. El detalle y las limitaciones están en [la revisión 2.0](revision-2.0.md), con evidencia final en `.lab/v2/final.json`. Las pruebas de experiencia con el grupo de la tabla siguen vigentes.

| Prueba | Resultado esperado | Cuándo |
| --- | --- | --- |
| Primera instalación en TLauncher de un amigo | Completa los pasos sin asistencia técnica y entra al mundo. | Primera sesión tras actualizar. |
| Voz entre dos redes y micrófonos reales | Se oyen con volumen adecuado, proximidad y grupos. | Primera sesión tras actualizar. |
| Expedición con equipo desigual | Ambos jugadores tienen tareas útiles; la dificultad no depende sólo del veterano. | Dos sesiones de juego. |
| Ocho jugadores y fábricas | Mantiene tiempos de tick útiles con carga real; se revisa el perfil si aparecen tirones. | Cuando coincida el grupo. |

Estas pruebas son la aceptación de experiencia. No se sustituyen por cuentas de prueba ni por daño aplicado desde consola.

## Referencias técnicas

- [SimpleBackups](https://wiki.chaotictrials.de/docs/1.20.x/wiki/simple-backups/): guardado y frecuencia del respaldo de mundo. La cobertura concreta de esta instalación se comprobó dentro del ZIP.
- [Playit Companion](https://playit.gg/support/playit-companion-mc-java-plugin-and-mod/): el complemento original no se mantiene. Virgos conserva su variante local probada para cumplir el uso integrado solicitado.
- [Simple Voice Chat](https://modrepo.de/minecraft/voicechat/wiki/server_config): transporte UDP y configuración de voz.
- [Caché de AuthMe 6.0.1](https://github.com/AuthMe/AuthMeReloaded/blob/6.0.1/authme-core/src/main/java/fr/xephi/authme/datasource/CacheDataSource.java): refresco asíncrono después de registrar, revisado al diagnosticar R15. La incidencia concreta se observó en el cliente y en la base de datos local.
