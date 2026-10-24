# Revisión final para abrir Virgos-MC

Revisión del 18/10/2026 sobre Minecraft 1.20.1, Forge 47.4.22, Ketting 0.6.1 y paquete 1.2.0. Estado: **listo para la primera sesión del grupo**. El servidor quedó abierto y respondió por el dominio público después del checkpoint final.

## Correcciones

- Receta de cortapiedras de Cataclysm: el archivo original apuntaba a `azure_seastone_brick_stair`, inexistente. La sobreescritura usa `azure_seastone_brick_stairs` y conserva los materiales y la cantidad. No cambia el JAR del mod.
- Auditoría: compara los valores de JSON/TOML aunque los mods reescriban espacios o comentarios. Incorpora la interacción con NPC ya aprobada y los límites de barcos e instrumentos. Devuelve error si falla alguna comprobación.
- AuthMe permite 120 segundos para cargar el mundo y registrarse/iniciar sesión. El bloqueo previo, contraseña obligatoria y sesiones por IP desactivadas se conservan.
- Instalador revisión 5: añade Discord al LEEME y al manual incluido. Mismos mods, Forge y carpetas; no requiere reinstalar a quienes ya usan 1.2.0. Se conservó la entrega anterior en `backups/client-release-before-final-review`.
- Arranque gestionado: `scripts/iniciar-segundo-plano.ps1` abre un controlador oculto independiente del comando de herramientas. El proceso anterior desapareció sin registrar un cierre normal durante la revisión; se conservó el estado de disco y se comprobaron las bases SQLite antes de relanzar. No se atribuye una causa definitiva sin evidencia.
- Pueblo y mercado: la referencia de auditoría combina los dos planos aprobados, para que los puestos nuevos no se confundan con daños en el pueblo anterior. Se revisaron 85.437 posiciones sin bloques faltantes ni rutas obstruidas. Quedó una diferencia de crecimiento natural: una enredadera; no impide el paso. La auditoría separada del mercado comprobó 9.584 posiciones sin diferencias. `auditoria-pueblo-v12` es una referencia de revisión, no un plano para reconstruir el spawn.

## Evidencia

- `.lab/reports/final-ready-static.json`: inventario y hashes, política efectiva, 186 misiones, dependencias y cobertura de los seis mundos.
- `.lab/reports/final-ready-downloads.json`: 105 URL del instalador disponibles.
- `.lab/reports/final-ready-installer.json`: 22 comprobaciones de perfiles, reparación, migración y conservación de preferencias.
- `.lab/reports/final-ready-tlauncher.json`: 16 comprobaciones del formato de configuración de TLauncher.
- `.lab/reports/final-ready-sqlite.json`: integridad de AuthMe y CoreProtect tras la salida inesperada.
- `.lab/reports/final-ready-before-backup.json`: copia previa verificada, con 1.489 archivos y seis mundos.
- `.lab/reports/final-ready-public.json`: cliente Forge real entrando por el dominio público; bloqueo previo al registro, autenticación, voz conectada, menú, diálogo de NPC y rechazo del checkpoint cuando hay jugadores.
- `.lab/reports/final-ready-recipes.json`: 18.415 recetas iguales en cliente y servidor, con sincronización de JEI.
- `virgos-reports/auditoria-pueblo-v12-audit.json` y `virgos-reports/mercado-v12-audit.json`: pueblo y mercado.
- `.lab/reports/final-ready.json`: cierre, conexión real, reinicio, Discord, UDP y copia posterior.

El checkpoint final guardó las seis dimensiones, terminó con código 0 y verificó **1.496 archivos** en `backups/full/virgos-20261018-210408-auto.zip` antes de reiniciar automáticamente. Incluye los cambios del servidor y la configuración privada de Discord. El cliente de prueba se cerró, su cuenta fue desregistrada y se retiró la herramienta de QA del perfil estándar.

Después del reinicio se comprobó el protocolo de Minecraft tanto por localhost como por `virgos-mc.playit.plus`, la respuesta UDP del túnel de voz y la entrega en Discord de los avisos de apagado e inicio, en ese orden. La prueba con un cliente real se realizó antes de este último reinicio. Las comprobaciones de carga y micrófonos del grupo siguen siendo las indicadas abajo.

## Entrega a los amigos

Corrección durante la primera sesión (18/10/2026): se habilitó `Ender_Chests = "E"` únicamente en la configuración de claims del servidor, para poder abrir el cofre de Ender del spawn. Se aplicó con `opac server-claims-config set claims.protection.exceptions.groups.block.interact.Ender_Chests E`, sin reiniciar ni desconectar jugadores, y se guardó en la configuración y sus plantillas. La consulta en vivo devuelve `Every`; la protección general, rotura de bloques, cofres normales y configuración de claims personales conservan sus valores anteriores. Evidencia: `.lab/reports/hotfix-ender-chest.json`. La reapertura del cofre queda para confirmar con el jugador que reportó el caso.

Compartir `dist/Virgos-MC-1.2.0-instalar.zip`. Extraer todo → EMPEZAR → elegir launcher → Instalar. El mensaje `dist/INVITACION-VIRGOS-MC.txt` está preparado para copiar al grupo. No compartir la carpeta del servidor ni respaldos administrativos: contienen cuentas y credenciales.

La dirección es **virgos-mc.playit.plus**. La primera vez: `/register tuClave tuClave`; después `/login tuClave`. J abre misiones, `/virgos menu` reúne la ayuda y O configura la voz. Discord: LaLechebanda → #virgos-mc.

## Validaciones que quedan para la primera sesión

- Instalar y entrar desde el TLauncher real de un amigo: se verificaron sus archivos y el instalador, pero no se abrió esa aplicación en esta PC.
- Escuchar micrófonos desde dos redes: el transporte UDP y la conexión del cliente son comprobables; volumen y calidad necesitan personas.
- Medir ocho jugadores y fábricas, y ajustar la dificultad cooperativa jugando con equipo desigual. Las pruebas anteriores con daño de consola no validan dificultad humana.
- Si el primer ingreso vence durante la carga, volver a Multijugador e intentar otra vez. No se declara resuelta su causa sin reproducción y diagnóstico. La ampliación de AuthMe solo da más tiempo después del ingreso; no modifica el handshake de Forge.

Los avisos conocidos de la plataforma híbrida y compatibilidad opcional siguen documentados. CoreProtect no reemplaza un respaldo completo para máquinas con NBT. Playit Companion usa la variante local ya fijada; no actualizar mods o plugins por separado sin probar la combinación.
