# Verificacion de Virgos-MC — 17/10/2026

Registro histórico de la plataforma inicial, anterior al paquete de contenido. Para el estado vigente, consultar [roadmap y auditoría](roadmap-auditoria.md).

Base final: Minecraft 1.20.1 / Forge 47.4.22 / Ketting 0.6.1, Java 17 portable, AuthMe 6.0.1 y Playit Companion Forge 0.1.2.

## Pruebas realizadas

- Descargas oficiales verificadas por SHA256/SHA512; versiones fijadas en `versions.lock.json`.
- `preparar.ps1` ejecutado correctamente, incluida una segunda ejecucion sobre el proyecto preparado. Sintaxis PowerShell revisada.
- Se corrigio un fallo del acceso `iniciar.bat`: la consola heredaba un entorno donde `Get-FileHash` no estaba disponible. La verificacion ahora usa las implementaciones SHA256/SHA512 de .NET y los accesos `.bat` establecen rutas de modulos de Windows PowerShell solo para su propio proceso.
- Arranque hasta `Done`, carga de AuthMe y conexion automatica de Companion con la cuenta vinculada.
- Consulta Minecraft Server List Ping local y mediante el dominio publico: version 1.20.1, protocolo 763 y MOTD Virgos-MC.
- Cliente de protocolo Minecraft 1.20.1 conectado en modo offline a `virgos-mc.playit.plus` a traves de Playit. Registro correcto, comando bloqueado antes de login, solicitud de login tras reconectar, expulsion al usar clave incorrecta e inicio de sesion con la clave correcta. Resultado en `auth-verification.json`.
- Cuenta de prueba eliminada con `/unregister`. No se asigno OP a nadie. Pueden quedar archivos de jugadores de prueba en el mundo inicial.
- Apagado con `stop`: todas las dimensiones guardadas. Evidencia en `verification-server.log`.
- Reinicio final desde `iniciar.bat` en una consola visible: `Done (8.760s)` a las 12:47:21. Las comprobaciones local y publica volvieron a responder OK, con 0/10 jugadores y el MOTD correcto. El servidor quedo encendido.
- Dominio fijo `virgos-mc.playit.plus` asignado por USD 0 adicionales. Tunel cambiado de Global Anycast a Brazil, South America. Captura en `playit-virgos-mc.png`.

## Compatibilidad observada

PacketEvents 2.14.0 expulsaba conexiones publicas de Companion con `PacketEvents failed to inject into a channel`. Se retiro antes de validar la configuracion final. La ocultacion del inventario de AuthMe dependiente de ese plugin quedo desactivada; el registro y el bloqueo de comandos antes de autenticarse se comprobaron por el tunel.

La prueba valida arranque, conexion y autenticacion. Queda pendiente una sesion con el cliente grafico, una prueba de carga con diez jugadores y la validacion del futuro paquete de mods. No hay mods de contenido instalados todavia.
