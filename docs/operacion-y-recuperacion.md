# Operar y recuperar Virgos-MC

Abrí `iniciar.bat` y esperá `Done` y el puente AuthMe. `validar.bat` comprueba previamente los 103 componentes fijados, Java y EULA. Un JAR faltante, cambiado o ajeno impide arrancar y se conserva para revisión. No se descargan versiones nuevas automáticamente.

Para el arranque gestionado sin ventana, `scripts/iniciar-segundo-plano.ps1` crea un controlador independiente y oculto usando el Node disponible. El controlador conserva la entrada de `comando.bat`, el apagado de `detener.bat` y los respaldos. Consultá `.runtime/runner.log`, `.runtime/runner-error.log` y `logs/latest.log`; un archivo de estado antiguo por sí solo no demuestra que el proceso siga vivo.

El arranque gestionado también recupera un cierre inesperado de la JVM: con `autoRestartOnUnexpectedExit` activo en `config/virgos/maintenance.json`, intenta hasta tres reinicios con quince segundos entre ellos. Un `stop` intencional sigue el flujo normal de guardado y respaldo. Si se agotan los intentos, revisá los tres registros anteriores y el estado `unexpected`/`restartAttempt` de `.runtime/active-run.json`. Si el log termina sin `Stopping the server`, `Done` ni una línea final del controlador, probablemente Windows o el proceso controlador fueron terminados desde fuera; esta recuperación no puede reanimar un controlador que también fue cerrado.

Para apagar, escribí `stop` en la consola. Si está iniciado en segundo plano, usá `detener.bat`. Esperá también **Respaldo completo verificado**: primero se guardan y cierran Minecraft y las bases de datos, después se copia y verifica. No cierres la PC durante ese proceso.

## Copias automáticas

`config/virgos/maintenance.json` define el mantenimiento:

- Respaldo completo tras cada apagado normal con `iniciar.bat` o `scripts/run-public.cjs`.
- Si hubo jugadores desde el último arranque, pasaron al menos 120 minutos desde la última copia completa y el servidor lleva diez minutos vacío, guarda, apaga, respalda y reinicia. Con jugadores conectados se aplaza; no los expulsa.
- Desde consola, `virgos checkpoint` solicita el mismo ciclo cuando no hay jugadores. Un jugador sin permisos no puede ejecutarlo.
- Conserva hasta doce copias automáticas o 30 GiB, siempre al menos las dos más recientes. Las copias manuales y previas a actualizaciones no se borran por esta política.

Las copias completas incluyen las seis carpetas `virgos_world*`, inventarios, misiones, claims, AuthMe, LuckPerms, CoreProtect, mods y configuración. Se verifica el SHA256 de cada archivo y se registra el resultado en `.runtime/last-backup.json`. No incluyen Java, bibliotecas descargables ni fuentes de desarrollo. Las fuentes de v1 tienen una copia privada independiente, descrita en [mantenimiento de fuentes](mantenimiento-fuentes.md).

SimpleBackups sigue haciendo copias parciales del mundo principal durante sesiones largas. En Ketting no cubre las otras cinco carpetas ni las bases de datos de plugins. Si nunca queda vacío y nadie lo apaga, la última copia completa puede tener más de dos horas. Un cierre abrupto no genera una copia consistente; el controlador intenta recuperarse sin hacer una copia sobre el estado posiblemente incompleto. Revisá logs antes de restaurar o de volver a iniciar si se repite.

No borres `.runtime/active-run.json` mientras funcione el servidor o el respaldo. Evita abrir una segunda consola durante ese proceso. Si la copia falla, el controlador informa el error y no continúa el reinicio automático.

Cada archivo se lee con un único acceso que impide escrituras durante su hash y copia; así el manifiesto usa el tamaño realmente copiado. Si una verificación falla, el ZIP se aparta en `backups/unverified` y se conserva el registro de la última copia válida. Evitá editar configuración durante el mantenimiento.

## Restaurar sin pisar la partida

1. Detené producción y conservá una copia de su estado actual con `respaldo.bat`.
2. Ejecutá en PowerShell, desde el proyecto:

```powershell
.\scripts\restaurar-respaldo.ps1 -ArchivePath 'D:\proyectos\mc-server\backups\full\NOMBRE.zip' -RestoreTo 'D:\proyectos\mc-server\.lab\restore-check\recuperacion'
```

3. El destino debe ser nuevo. El script verifica rutas, tamaños y hashes de todos los archivos. Conservá las seis carpetas de mundo y los datos de plugins como una unidad; mezclar fechas puede desincronizar inventarios, aportes y cuentas.
4. Antes de arrancar una copia de prueba, retirale Companion a una carpeta de reserva, poné `server-ip=127.0.0.1` y un puerto distinto. Desactivá su mantenimiento automático y usá otro puerto de voz. Nunca arranques una restauración con el túnel público activo.
5. Java y las bibliotecas se reconstruyen desde las versiones fijadas o se copian desde una instalación verificada. En esta PC, `scripts/verify-restored-server.cjs` arranca únicamente una copia ya aislada bajo `.lab/restore-check`, audita el spawn y la apaga.
6. Recién después de comprobar la copia se planifica el reemplazo de producción, con el servidor detenido. El restaurador no lo hace automáticamente y `deploy-release.py` no debe reutilizarse sobre un mundo en uso.

La última prueba real del 3 de noviembre de 2026 restauró 8.572 archivos y arrancó una copia aislada en
`127.0.0.1:25576`, sin túnel público. La copia sin reparar expuso una discrepancia del Bastión; la misma prueba
con `node scripts/verify-restored-server.cjs <carpeta> --rebuild-bastion` reconstruyó el candidato aislado y pasó
la auditoría de 147.542 bloques y las cuatro rutas sin diferencias. Este modo nunca promueve cambios a producción;
esa decisión sigue requiriendo una ventana de mantenimiento y un respaldo previo.

## Diagnóstico

`comprobar-publico.bat` consulta `virgos-mc.playit.plus`. `virgos status`, desde consola, muestra autenticación, progreso, arena, proyectos, voz y mantenimiento. `forge tps` mide los ticks actuales. `scripts/audit-project.py` genera un informe del inventario, balance, misiones y cobertura de respaldo.

El runner gestionado genera además una instantánea automática cada diez minutos en `.runtime/health/`. Incluye `spark health --memory`, `spark tps`, `list` y contadores acotados de entidades totales, ítems tirados, aldeanos y minecarts mediante un objetivo de scoreboard reutilizable. No elimina ni modifica entidades; sólo registra las líneas de evidencia del log. Estos informes son locales: no suben datos ni credenciales a ningún servicio.

### Auditoría de rendimiento reproducible

Con el servidor iniciado mediante el runner gestionado, ejecutá uno de estos escenarios desde PowerShell:

```powershell
python scripts/audit-performance.py exploration --seconds 300
python scripts/audit-performance.py create --seconds 300
python scripts/audit-performance.py multiplayer --seconds 300
```

El script no cambia `view-distance=8` ni `simulation-distance=6`. Captura `spark health --memory`, `spark tps` y un perfil acotado, y deja el informe en `.runtime/performance-audit/`. El escenario debe reproducirse durante la ventana; el perfil sólo se considera evidencia después de revisar su enlace o archivo guardado.

### Pregeneración controlada

La pregeneración nunca se inicia automáticamente ni sobre una suposición de alcance. Primero hacé un respaldo completo y verificá que no haya jugadores conectados; después usá un radio acotado y confirmá explícitamente:

```powershell
python scripts/pregen-managed.py --world minecraft:overworld --center 672 752 --radius 768 --seconds 600 --label spawn --confirm
```

Para Nether, End o dimensiones de mods cambiá `--world` y elegí un centro/radio documentados. El script pausa al detectar un jugador, deja el resultado en `.runtime/pregen/` y no promueve ni borra tareas anteriores.

Los trabajos propuestos están enumerados en `pack/pregen-plan.json`. Los de dimensiones y rutas remotas son
intencionalmente candidatos: no se ejecutan hasta que el grupo haya fijado el destino público y exista un respaldo
posterior al cierre de worldgen.

AuthMe usa SQLite con `DataSource.caching: false` y consultas asíncronas. Esto evita que un registro nuevo lea una entrada negativa antigua de su caché. Las sesiones automáticas por IP siguen desactivadas; cada conexión requiere contraseña. Un cambio de esta opción necesita reiniciar el servidor. OPAC utiliza `primaryPartySystem = "default"`, su sistema de grupos integrado, con claims de propiedad individual.

El Companion de Playit termina la conexión dentro de la PC del servidor, por lo que AuthMe puede registrar `127.0.0.1` como IP para varias personas. Las cuentas siguen siendo filas separadas y sus contraseñas/progreso no se comparten. `displayOtherAccounts` queda desactivado para no mostrar una lista engañosa de cuentas asociadas a esa IP local; no se debe limitar `maxRegPerIp` en este esquema porque bloquearía a los amigos entre sí.

CoreProtect sirve para investigar y revertir bloques vanilla dentro de su alcance comprobado. Para máquinas modded, inventarios o NBT, usá una copia completa. La protección de claims fue probada con accesos, proyectiles y pistones; no se considera demostrada para cada mecanismo de todos los mods.

El parche de Playit está fijado en `versions.lock.json` y su fuente en `dev/playit-udp-fix`. No lo reemplaces por el JAR original sin repetir las pruebas de voz. Los túneles actuales usan TCP de Minecraft y UDP de voz separados dentro del mismo Companion.

Guardá los respaldos localmente: contienen credenciales y cuentas. Para amigos compartí sólo el instalador de `dist`.
