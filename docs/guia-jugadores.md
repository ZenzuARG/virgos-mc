# Instalar Virgos-MC

1. Descargá **Virgos-MC-2.0.0-instalar.zip** y elegí **Extraer todo**.
2. Abrí **EMPEZAR.bat**. Cerrá Minecraft y tu launcher.
3. Elegí **TLauncher** o **Minecraft Launcher oficial** y tocá **Instalar Virgos-MC**.
4. Esperá a que termine y seguí los pasos de la ventana. Después, en el juego: **Multijugador → Virgos-MC**.

Necesitás Windows x64, tu launcher instalado, Internet y unos 10 GB libres. El asistente descarga Java 17 para el perfil oficial, usa el Java automático de TLauncher y prepara Forge 47.4.22 con los 116 archivos de mods y dependencias. No pide contraseñas ni permisos de administrador. La primera descarga puede tardar varios minutos; el launcher descarga los archivos restantes de Minecraft al abrir el juego.

**Launcher oficial:** se agrega el perfil **Virgos-MC**, con carpeta propia y **8192 MB (8 GB)** de memoria. Elegilo y tocá Jugar. Si no aparece, activá **Modificadas** en Instalaciones. Tenés que haber abierto el launcher e iniciado sesión al menos una vez.

**TLauncher:** abrilo una vez y cerralo antes de instalar. Al terminar, tocá **Abrir mi launcher → Entrar al juego**. El asistente detecta la configuración normal de TLauncher, selecciona la carpeta, Forge 1.20.1, memoria y Java automático. La primera entrada usa Complementary Unbound en perfil Low. Si el equipo no lo soporta, desactivalo con F6 y volvé a entrar; no elijas ForgeOptiFine ni otro paquete de TL MODS. La carpeta es un ajuste general de TLauncher: tus otras partidas se conservan; para volver a ellas, cerrá TLauncher y tocá **Restaurar TL**. **Revisar / reparar** vuelve a configurar Virgos-MC.

El instalador asigna **8192 MB (8 GB) como mínimo al cliente de Minecraft**, tanto en instalaciones nuevas como al usar **Revisar / reparar**. Durante la instalación podés elegir **8, 10 o 12 GB**; 8 GB es el valor recomendado y los valores mayores requieren memoria física suficiente. Actualiza las selecciones anteriores de 4, 5 o 6 GB sin cambiar otros perfiles ni preferencias; conserva un respaldo de las preferencias migradas. TLauncher configura ambas propiedades de memoria y **Restaurar TL** conserva su función de recuperación. Se recomiendan **16 GB de RAM total** para la opción de 8 GB y **24 GB o más** para 10–12 GB, dejando memoria al sistema operativo; en equipos con menos memoria, cierre otras aplicaciones y tenga en cuenta que puede haber lentitud. Este ajuste no cambia la memoria del servidor. El primer inicio del paquete puede tardar varios minutos.

Si usás TLauncher portable, en **Opciones de carpeta y memoria** indicá su archivo `tlauncher-2.0.properties`. Si la configuración no es reconocida, el asistente la conserva y muestra el motivo. La integración se comprobó con el formato de TLauncher 2.899; no instala ni reemplaza el launcher.

La primera vez en el servidor: `/register tuClave tuClave`. Después: `/login tuClave`. Conservá siempre el mismo nombre exacto y elegí una clave exclusiva para el servidor.

Para jugar otro día, abrí directamente tu launcher. Para reparar una descarga, repetí EMPEZAR; conserva los archivos correctos. Si algo falla, **Abrir registros** permite encontrar `instalacion.log`, `forge.log` y `error.log` para pedir ayuda.

**Si ya lo tenés instalado:** extraé el instalador nuevo, elegí la misma carpeta y usá **Revisar / reparar**. Conserva mundos, controles y preferencias del micrófono. Guarda las versiones anteriores de mods en `respaldos-actualizacion`. Si encuentra un mod ajeno o un archivo anterior modificado, lo conserva y pide revisión. Dentro del servidor, **O** abre la voz y **Bloq Mayús** sirve para hablar.

Dirección alternativa para agregar el servidor: **virgos-mc.playit.plus**. Las misiones, teclas, bases y expediciones están en [Cómo jugar](manual-jugadores.md).

Si el primer ingreso muestra «Took too long to log in» o tiempo de espera agotado, volvé a Multijugador y entrá nuevamente. Se observó al iniciar las pruebas del paquete; la reconexión funcionó. Si vuelve a fallar, compartí `latest.log` con el administrador.

La versión 2.0 estrena mundo y reinicia inventario, misiones, bases y estadísticas. Conservá el nombre y contraseña que ya usabas. Consultá tu progreso con `/perfil`, o el de un amigo con `/perfil Nombre`.
