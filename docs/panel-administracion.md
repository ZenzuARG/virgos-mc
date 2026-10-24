# Panel de administración de Virgos-MC

Abrí **Panel Virgos-MC** en el escritorio, o `panel.bat` dentro de `D:\proyectos\mc-server`.
También podés entrar en **http://127.0.0.1:8765** mientras el panel esté funcionando.

## Uso diario

1. Pulsá **Encender servidor**. Esperá a que el indicador diga **Abierto**; cargar el paquete puede llevar varios minutos.
2. Jugá normalmente. Podés cerrar el navegador: Minecraft sigue funcionando.
3. Al terminar, pulsá **Apagar**. Esperá a que termine **Creando respaldo** y aparezca **Apagado** antes de apagar la PC.

El panel vuelve a conectarse a una instancia iniciada en segundo plano. No hace falta encender otra.
La PC debe seguir encendida y conectada a Internet para que puedan jugar.

## Qué podés hacer

- **Vista general:** estado real de Minecraft, conectados, tiempo encendido, versión y última copia verificada. Guardar, encender, apagar y reiniciar.
- **Consola:** salida en vivo y comandos sin `/`. Hay accesos para `list`, `tps`, `virgos status` y ayuda; arriba/abajo recuperan los comandos de esa sesión. La confirmación muestra exactamente lo que vas a ejecutar.
- **Jugadores:** consultar horas, rango, misiones y estadísticas; llevar al spawn, expulsar, bloquear o permitir entrada y dar/quitar OP. Las estadísticas pueden tener un minuto de demora. Las cuentas sin actividad ni registro no aparecen sólo por estar en la caché de nombres.
- **Permisos:** leer LuckPerms, crear grupos vacíos, agregar/quitar miembros y permitir/denegar/quitar reglas globales por jugador o grupo. Agregar un grupo conserva los otros grupos. Los permisos temporales o con contexto se consultan aquí y se modifican desde la consola.
- **Respaldos:** crear una copia completa verificada. Si el servidor estaba encendido, se guarda, se apaga, se copia y vuelve a arrancar. Esta acción interrumpe la partida y pide confirmación. Si falla la copia, no se reinicia automáticamente. Las copias solicitadas con este botón llevan etiqueta `manual` y no entran en la limpieza automática.

## Ejemplo: un grupo de moderadores

1. En **Permisos**, pulsá **Leer permisos actuales**.
2. Creá un grupo llamado `moderadores`.
3. Elegí **Grupo → moderadores**, ingresá `minecraft.command.kick`, elegí **Permitir** y aplicá. Repetí con los permisos concretos que quieras otorgar.
4. Elegí **Jugador → nombre**, seleccioná `moderadores` y pulsá **Agregar al grupo**.

Las reglas guardadas se vuelven a leer desde LuckPerms después del cambio. Las respuestas y errores del plugin aparecen en Consola. Algunos comandos de mods usan niveles OP en lugar de nodos de LuckPerms. Referencias: [uso de LuckPerms](https://luckperms.net/wiki/Usage) y [comandos de permisos](https://luckperms.net/wiki/Permission-Commands).

**OP da privilegios amplios.** Sólo se permite desde el botón para cuentas registradas en AuthMe. El panel no asigna OP ni cambia permisos automáticamente al abrirse. Las reglas de `default` afectan a todos.

## Si algo falla

- **Abierto** significa que Minecraft respondió localmente. No confirma por sí solo la ruta pública de Playit; `comprobar-publico.bat` comprueba esa dirección.
- Si no abre la página, volvé a abrir el acceso del escritorio. `panel.bat` muestra errores de arranque. Revisá `.runtime/admin-panel-error.log` si fuera necesario.
- Si Minecraft no arranca, abrí **Consola → Arranque, respaldos y registro del panel**. Ahí se ven los errores del controlador aunque no exista un `latest.log` nuevo.
- Si aparece **control externo** o la instancia fue iniciada con `iniciar.bat`, se muestra el estado pero no se envían comandos. Apagá desde aquella consola con `stop` y usá el panel para el siguiente arranque.
- Para restauraciones, seguí [operación y recuperación](operacion-y-recuperacion.md). El panel no sobrescribe mundos ni ofrece restaurar una copia sobre la partida activa.

## Alcance técnico

Aplicación local Node.js, sin dependencias descargadas, servicios de Windows ni cambios de mods o del instalador. Usa el Node ya disponible en esta PC. Sirve sólo `127.0.0.1:8765`; no requiere túnel Playit, RCON ni puertos públicos adicionales. Verifica Host, Origin y un token por sesión, limita solicitudes y bloquea la carga en marcos de otras páginas. No compartas el panel por un túnel.

El controlador existente conserva la propiedad del proceso de Minecraft, por lo que cerrar el panel o el navegador no detiene el mundo. Los arranques y respaldos nuevos usan una reserva exclusiva de control para evitar operaciones simultáneas. Las claves y tokens reconocibles se ocultan en la vista de consola; las contraseñas de AuthMe no se leen. El panel consulta únicamente nombre y última conexión de esa base. Los cambios de permisos se envían a LuckPerms y se consultan mediante su exportación local, sin modificar su base de datos directamente.

Fuentes: `scripts/admin-panel`. Estado y registro: `.runtime/admin-panel*.json`, `.runtime/admin-panel-actions.jsonl`. Se incluyen las fuentes en los respaldos completos, dentro de `scripts`.

Pruebas automatizadas: `node --disable-warning=ExperimentalWarning --test scripts/admin-panel/test.cjs`. La comprobación de interfaz usa Playwright del entorno de desarrollo; no es necesario para usar el panel. Evidencias de esta instalación: `.lab/admin-panel`.
