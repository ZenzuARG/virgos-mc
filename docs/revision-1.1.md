# Revisión 1.1 · Pueblo y aprendizaje

Esta revisión conserva Minecraft 1.20.1, Forge 47.4.22, el catálogo de mods, las identidades y las reglas de progreso de v1. El cliente sigue usando 87 mods obligatorios y cuatro opciones visuales.

## Pueblo del spawn

Base descargada: [Medieval Spawn Town, de itzvmbie](https://www.planetminecraft.com/project/medieval-spawn-town-1-17-1-18/). El autor ofrece la plantilla para servidores y permite adaptar sus locales. Créditos originales: SaraGrey, CoolMMN, FireVoges, Vmbie, Z3phrin y Cynera Staff. Los árboles del original proceden de Paralon, según su descripción. Se conserva un cartel de crédito en la plaza.

La adaptación usa casas con tejados verdes, plaza abierta, cuatro arcos, cocina y taller señalizados. Se conserva el punto de llegada **672, 115, 752** y los caminos existentes hacia el mundo y el anfiteatro. Se reconstruyen suelo y apoyos que faltaban en la plantilla. Se eliminan portales, barreras, luz invisible, lava y contenidos originales de contenedores y carteles. No se importan entidades ni comandos del autor.

`pack/pueblo-v11.json` registra procedencia y hash; `scripts/build-pueblo-v11.py` genera el plano reproducible. Las plantillas anteriores y las copias completas permanecen disponibles. El plano sólo se aplica mediante el comando administrativo de construcción; no vuelve a regenerarse al arrancar.

## Misiones y comandos

**154 misiones en 20 capítulos**, 71 nuevas. Las 83 anteriores mantienen IDs, tareas, dependencias, recompensas y configuración; se mejoraron únicamente algunos textos. Las nuevas ramas enseñan servidor y claims, Create, Ars, Iron, Alex's Caves, almacenamiento, cocina, viajes y cooperación.

Las prácticas de inventario detectan el objeto sin consumirlo. Las casillas de lectura o práctica manual lo explican expresamente. Las ramas nuevas no entregan recompensas ni rangos adicionales: no aceleran el poder por marcar tutoriales. Los reconocimientos existentes se siguen reclamando en el códice.

`/virgos guia` y `/virgos ayuda` ofrecen nueve temas: inicio, progreso, bases, grupo, mods, expediciones, recuperar, voz y comandos. Los enlaces de acciones preparan el comando en el chat para revisarlo antes de enviarlo. `/virgos progreso` incluye el próximo paso y recuerda reclamar las recompensas.

## Instalador 4

El launcher oficial conserva su perfil independiente. TLauncher recibe automáticamente carpeta, Forge fijado, memoria y selección automática de Java. El asistente guarda una copia original y permite **Restaurar TL**. Reparar no reemplaza esa primera copia; restaurar conserva preferencias ajenas y se detiene si el jugador cambió posteriormente una opción administrada.

La configuración es general de TLauncher. Se comprobó con su formato actual 2.899; versiones o archivos no reconocidos se conservan y producen una explicación. Una instalación portable permite elegir el archivo de ajustes desde Opciones. El instalador no instala TLauncher ni toca archivos de cuentas.

Pruebas: 22 comprobaciones del instalador común y perfiles oficiales, 16 de ajustes de TLauncher, lectura mediante el parser original de TLauncher 2.899, y ejecución completa del instalador en una carpeta de ensayo con espacios. La interfaz propia se revisó renderizada. No se instaló ni abrió la interfaz real de TLauncher en esta PC.

## Evidencia y alcance

- `.lab/reports/quests-v11-static.json`: IDs reales de objetos, grafo sin ciclos, posiciones únicas y conservación de las 83 misiones.
- `.lab/reports/quest-v11-runtime.json`: misión nueva de Create completada por inventario; la llave se conserva.
- `.lab/reports/mision-v11-detalle.png`: descripción legible en el códice real.
- `.lab/reports/guia-v11-suggests-claim.png`: clic prepara `/oclaims claim`, sin ejecutarlo.
- `.lab/reports/pueblo-v11-walk.json`: cruces reales de los cuatro arcos, sin daño.
- `.lab/reports/installer-v4-tlauncher.png`: interfaz del instalador.

Publicada y verificada el 18 de octubre de 2026: `.lab/reports/v11-final.json` registra el cierre exitoso. El servidor responde en `virgos-mc.playit.plus` después del reinicio, con la whitelist desactivada y un respaldo completo verificado de los seis mundos. Se comprobaron el registro, el inicio de sesión, la sincronización de recetas y la conexión de voz mediante un cliente real. El progreso anterior de los jugadores se conserva.

El balance de combate no cambia en esta revisión; siguen pendientes la sesión de ocho jugadores con fábricas y la escucha de voz entre micrófonos humanos.
