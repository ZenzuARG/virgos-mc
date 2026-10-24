# Playit Premium — Virgos-MC

Direccion fija: **virgos-mc.playit.plus**. Es un subdominio incluido en Premium, activado con coste adicional de USD 0. Mantener la suscripcion y la asignacion del dominio para conservarlo operativo.

El tunel y la conexion integrada se llaman **Virgos-MC**.
Panel: https://playit.gg/account/tunnels/3f1f2a29-3512-4d61-be0d-37fa1bc1a85e/overview

## Integracion

Se usa `mods/playit_companion-forge-0.1.2-virgos.1.jar`, exclusivamente del lado del servidor. No hace falta instalar Playit en Windows, abrir puertos del router ni instalar nada de Playit en los clientes. Las credenciales permanecen en la configuracion local del mod; no borrar esa configuracion ni volver a reclamar un agente cada vez que se inicia.

Playit Companion crea y mantiene su propio tunel. El panel puede mostrar `No configuration` en el origen: el mod gestiona la conexion internamente. El nombre del agente puede indicar Chile como centro de conexion, mientras la region del tunel muestra Brasil: son extremos distintos de la ruta.

## Region elegida

Entrada Premium: **Brazil, South America**. En la prueba orientativa desde esta PC, el sitio oficial de medicion dio aproximadamente 45 ms a Sao Paulo, 39 ms a Chile y 222 ms mediante Global Anycast hacia California. Son muestras de conectividad, no una garantia del ping final de todos los jugadores.

El panel indica que este agente antiguo no soporta Chile como region de entrada de un tunel. Sudamerica/Brasil si es compatible; por eso se aplico esa opcion. El dominio se conserva al cambiar de region y resuelve el puerto mediante SRV. Evitar compartir una IP numerica, porque puede cambiar.

## Limites comprobados

La [documentacion oficial](https://playit.gg/support/playit-companion-mc-java-plugin-and-mod/) advierte que Companion ya no se mantiene. Se eligio por el requisito de mantener el tunel dentro del servidor y se probaron las conexiones reales. No asumir que todas las funciones nuevas del agente de escritorio estan disponibles en este complemento.

PacketEvents 2.14.0 no es compatible con el canal de conexion que utiliza Companion en esta combinacion: expulsaba las conexiones publicas. Se retiro. AuthMe permanece activo, con bloqueo de acciones antes del login; la ocultacion del inventario que depende de PacketEvents queda desactivada. No agregar PacketEvents ni plugins que lo requieran sin revisar esta incompatibilidad.

Para comprobar el servicio ejecutar `comprobar-publico.bat`. Para cambiar el dominio o la region usar el panel anterior. No se contrataron dominios de pago adicionales.

## Ruta de Forge en el paquete completo

La conexión directa de Companion 0.1.2 usa un hilo Netty propio. Forge 47.4.22 rechaza sus respuestas de LOGIN porque `EffectiveSide` no lo identifica como servidor. Se reprodujo el error «Unexpected custom data from client» en la entrada pública, mientras la conexión local completaba el handshake.

`config/playit-companion/custom_tunnels.css` activa el reenvío TCP incorporado para `#minecraft-java` a `127.0.0.1:25565`. Así la conexión entra por el listener normal de Forge. Se mantienen la cuenta, región y dominio; no se instala otro agente. La selección de esta ruta está soportada por el [código de Companion](https://github.com/playit-cloud/playit-companion/blob/main/core/src/main/java/gg/playit/PlayitAgent.java).

Este reenvío presenta las conexiones al servidor como localhost. No usar bans por IP ni sesiones automáticas por IP; administrar por nombre y contraseña. AuthMe ya tiene sesiones automáticas, tempban por IP y límites por IP desactivados. La contraseña sigue siendo obligatoria en cada conexión.

Prueba de esta ruta: cliente Forge completo conectado por `virgos-mc.playit.plus`, login, OPAC, códice y spawn correctos. Informe: `.lab/reports/qa-public-connection.json`.

## Voz integrada desde 0.2

Simple Voice Chat 2.6.24 usa un túnel UDP separado del juego: `practically-accountant.tun.ply.gg:2685`, Premium Brasil, en el mismo agente integrado Virgos-MC. El nombre del túnel debe permanecer **simple-voice-chat**: Companion 0.1.2 reconoce ese nombre, mientras el tipo actual del panel es `mc-simple-voice-chat`.

Companion aporta su propio socket de voz y gestiona internamente UDP. La configuración base reserva `127.0.0.1:24454`, pero el adaptador de Companion sustituye ese socket y no requiere un listener local adicional. No se instala un programa, servicio ni agente adicional. Los jugadores sólo actualizan el paquete. El servidor comunica la dirección de voz al cliente automáticamente.

Se retiraron las entradas de ejemplo desactivadas de `custom_tunnels.css`: con un túnel UDP presente provocaban una excepción de `DisabledCompatLayer.protocolName`. La regla TCP de Minecraft se conserva. No agregar otro reenvío personalizado de voz encima del adaptador nativo.

Virgos Core admite únicamente el saludo de compatibilidad de voz antes de autenticarse; filtra emisión y recepción de audio con el estado de AuthMe. Esto no convierte el modo offline de Minecraft en una conexión cifrada segura: el propio mod advierte sobre esa limitación. Las grabaciones internas del mod están deshabilitadas y la voz es opcional.

Configuración: `config/voicechat/voicechat-server.properties`. Alcance 32 bloques, susurro 8, grupos habilitados. Documentación oficial: [configuración de voz](https://modrepo.de/minecraft/voicechat/wiki/server_config).

### Corrección local de Companion para UDP

La versión oficial 0.1.2 lee el identificador del paquete IPv4 desde el inicio del contenido en vez de los dos bytes finales del buffer. Esto desplazaba los campos de ruta y producía «Could not match UDP packet to a tunnel». La variante local `0.1.2-forge+virgos.1` cambia únicamente esa instrucción (`ALOAD 8` → `ALOAD 4`) en `DatagramChannelHandler`; las demás clases y recursos originales permanecen idénticos.

El original y su SHA512 quedan registrados en `versions.lock.json`. La variante local está en `pack/local/`, verificada mediante SHA256 tanto al preparar como al iniciar. El parche se reproduce con `dev/playit-udp-fix/build.ps1`; la comprobación de entradas ZIP y despliegue está en `deploy.py`. No sustituirlo por la descarga oficial 0.1.2 mientras se use voz. Código original: [PlayitAgent.java](https://github.com/playit-cloud/playit-companion/blob/main/core/src/main/java/gg/playit/PlayitAgent.java).

Verificación del 18 de octubre: eco UDP oficial recibido por el endpoint público; cliente Forge conectado a `virgos-mc.playit.plus`, login AuthMe y conexión de voz autenticada/validada. Informe `qa-v02-public-voice.json`; ningún error de enrutamiento UDP tras el parche. Falta la escucha humana con micrófonos reales: esta prueba valida transporte y conexión, no volumen ni calidad del micrófono de cada amigo.
