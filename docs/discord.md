# Discord de Virgos-MC

Destino: **LaLechebanda → #virgos-mc**. Servidor `736709362206113802`, canal de texto `1561436921006137527` y aplicación Virgos-MC `1561500718144299008`.

La integración está **activa desde el 18/10/2026** y usa DiscordSRV 1.30.5 únicamente en el servidor. El instalador de los jugadores no cambia. [Abrir el canal](https://discord.com/channels/736709362206113802/1561436921006137527).

## Cómo usarlo

- Chat de Minecraft a Discord y de Discord a Minecraft.
- Avisos de entrada, salida, inicio y apagado normal.
- `!jugadores`: lista de conectados; `!ip`: dirección del servidor; `!ayuda`: guía de misiones y protección; `!voz`: cómo usar la voz.
- Mensajes en español, sin notificaciones por cada logro o muerte, y sin menciones masivas.

Escribe normalmente en #virgos-mc o en el chat del juego: el mensaje aparece en ambos. La consola administrativa y sus errores no se publican en Discord (`DiscordConsoleChannelId` vacío); el diagnóstico completo permanece en `logs/latest.log`. Discord sigue siendo opcional para jugar. Se conserva AuthMe; se comprobó con una cuenta Forge de prueba que el chat previo al registro no llega a Discord y que después del login sí funciona.

La voz de proximidad sigue a cargo de Simple Voice Chat y su túnel UDP existente. DiscordSRV no abre otro puerto ni requiere instalar un programa en Windows.

## Configuración y credencial

Las plantillas sin credenciales están en `templates/discordsrv/`. El archivo oficial y su SHA-256 están fijados en `pack/discordsrv.lock.json` y `pack/administration.lock.json`. La validación cuenta 103 componentes: plataforma, 97 mods y 5 plugins.

El token se guarda localmente en `plugins/DiscordSRV/.token`, mecanismo soportado por DiscordSRV, con permisos de archivo para el usuario de Windows que ejecuta Minecraft. No se coloca en las plantillas, documentación, comandos de arranque ni paquetes de clientes. Los respaldos administrativos que incluyan esa carpeta son privados. Se eliminó el archivo temporal usado para transferir la credencial.

La consola remota, ejecución de comandos desde Discord, sincronización de roles/apodos/baneos, webhooks y módulo de voz de Discord están deshabilitados. El bot es privado y solo se instala en servidores. Server Members Intent y Message Content Intent están activados con autorización del propietario; Presence Intent sigue desactivado. La invitación concede ver canales, enviar mensajes, insertar enlaces, leer historial y añadir reacciones; no concede Administrador.

Los avisos de entrada y salida usan `alerts.yml` con texto simple. Se desactivaron los avisos integrados con avatar porque DiscordSRV 1.30.5 intenta resolver una clase de skins incompatible con Ketting 1.20.1 y genera errores de NMS. El JAR oficial permanece intacto.

## Reinstalación o cambio de token

La configuración inicial ya está terminada. Estos pasos son para mantenimiento:

1. Terminar la configuración de la aplicación: `Server Members Intent` y `Message Content Intent`; instalación solo en servidor y bot privado.
2. Invitar el bot a LaLechebanda y darle acceso al canal de texto virgos-mc. Para estas funciones necesita ver el canal, enviar mensajes e insertar enlaces. Leer historial y añadir reacciones permiten informar si se truncó un mensaje. No necesita Administrador.
3. Detener Minecraft con `detener.bat` y esperar que termine el respaldo.
4. Ejecutar `scripts/configurar-discord.ps1`. Solicita el token sin mostrarlo, comprueba el bot y el canal mediante la API oficial, respalda configuraciones anteriores, instala el JAR y actualiza el manifiesto. También admite `-TokenFile` para una transferencia local controlada. `-ValidateOnly` verifica las plantillas y el JAR sin activar nada.
5. Iniciar el servidor y verificar el aviso en Discord, el chat en ambos sentidos, `!jugadores` y el bloqueo de chat antes de iniciar sesión con AuthMe.

## Verificación realizada

- SHA-256 del JAR coincide con el digest publicado por GitHub.
- Los seis YAML se analizaron con SnakeYAML y se comprobaron las restricciones de consola, autenticación, canal, roles y voz.
- Ketting 1.20.1 cargó DiscordSRV en el laboratorio y completó el arranque. Sin credencial, el plugin se deshabilitó con el mensaje esperado de token faltante. El laboratorio se apagó limpiamente.
- Bot conectado en producción, aviso de arranque visible y dominio público accesible.
- Cliente Forge real a través de Playit: chat Minecraft → Discord y Discord → Minecraft comprobados. AuthMe bloquea el mensaje previo al registro.
- `!jugadores` devolvió la identidad conectada; `!ayuda` respondió con misiones y protección de bases.
- Una segunda conexión pública comprobó los avisos de entrada y salida en texto; no reaparecieron errores de avatar/NMS. El cliente de prueba se cerró correctamente y su herramienta se retiró del perfil estándar.
- Informe separado de las pruebas anteriores de v1.2: `.lab/reports/discord-integration.json`.
- El checkpoint del 18/10/2026 comprobó en producción los avisos de apagado normal e inicio posterior, junto con el respaldo y reinicio automático. Evidencia: `.lab/reports/final-ready.json`. Un cierre forzado del proceso no garantiza el aviso de apagado.

Fuentes: [instalación oficial de DiscordSRV](https://docs.discordsrv.com/installation/initial-setup/), [versión 1.30.5](https://github.com/DiscordSRV/DiscordSRV/releases/tag/v1.30.5) y [avisos por eventos](https://docs.discordsrv.com/alerts/).
