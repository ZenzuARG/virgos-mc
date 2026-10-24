# Virgos-MC v3 — experiencia completa sin reinicio

## Objetivo

Virgos-MC v3 debe ampliar la exploración, la lectura del mundo y la progresión sin borrar el mundo actual, los inventarios, los claims, las misiones ni las cuentas de quienes ya juegan. La entrega será única: no se publica un instalador hasta cerrar el contenido, el balance, el cliente y las pruebas.

## Reglas de compatibilidad

- Se conserva `virgos_world` y sus dimensiones. Antes de cambiar mods se genera una copia completa y se verifica una restauración.
- No se cambia el seed ni se regeneran chunks existentes. Los cambios de estructuras sólo se probarán en chunks nuevos y aislados.
- No se agregan mods que obliguen a reiniciar el progreso o que sustituyan Create, Heracles, OPAC, JEI, Jade, Lootr o AuthMe.
- El cliente visual es opcional. Quien no quiera shaders, primera persona o audio ambiental puede desactivar esos componentes sin quedar fuera del servidor.
- El servidor sigue usando Forge 47.4.22 sobre Ketting 0.6.1 y Java 21.

## Contenido de v3

### Presentación y audio

El laboratorio ya incorpora First-person Model 2.7.3, Not Enough Animations 1.12.6, AmbientSounds 6.3.11, CreativeCore 2.12.40, Eating Animations 5.1.0 y GML 4.0.10 como opciones del cliente. Sound Physics Remastered, Ambient Environment y Better Third Person siguen siendo opcionales. Oculus 1.8.0 pasa a descargarse e instalarse para todos los clientes, pero con `enableShaders=false` y sin shader seleccionado. Complementary Reimagined r5.9.3 se descarga desde su publicación oficial durante la instalación y también queda desactivado por defecto. 3D Skin Layers queda como opción posterior porque puede producir sombras extrañas con shaders. La matriz completa de pruebas está en [v3-candidatos.md](v3-candidatos.md).

### Exploración

Se mantiene la generación instalada (Terralith, Regions Unexplored, Incendium, Nullscape, When Dungeons Arise, Integrated Dungeons and Structures y YUNG's). La expansión de v3 se limita a estructuras que no alteren el terreno ya guardado. Cada estructura nueva tendrá una prueba en un área virgen y una frecuencia registrada para evitar saturación.

### Progresión

El Códice Virgos pasa a ser la ruta de entrada única: capítulos cortos para supervivencia, cocina, Create, magia, cuevas, jefes y dimensiones. Se conserva el progreso existente y se agregan misiones nuevas al final de cada rama. Las recompensas priorizan materiales de construcción, información y acceso a rutas; no se entregan saltos de poder que hagan obsoletos los caminos anteriores.

### Cooperativo

Las misiones personales seguirán siendo individuales. Las expediciones y los jefes tendrán objetivos cooperativos opcionales con recompensas por participante; no se obliga a borrar una base ni a esperar a todo el grupo para avanzar en la historia personal.

### Calidad de vida

Se revisan el perfil, el contador de tiempo, la guía de claims, la lista de recetas y el mercado para que todos expongan el mismo lenguaje. Se mantienen Lootr, Claims, el descanso con una sola persona y el perfil offline para usuarios premium y no premium.

## Fases

1. **Auditoría y respaldo:** clonar mundo y configuraciones, inventariar progreso y establecer un punto de restauración.
2. **Cliente visual:** validar primera persona, animaciones, audio, shaders y Java 21 en el cliente estándar y TLauncher.
3. **Contenido aditivo:** cerrar estructuras y misiones nuevas en laboratorio, con límites de frecuencia y recompensas.
4. **Balance:** probar ocho jugadores, una base con Create, una expedición y un jefe; ajustar carga, botín y tiempos.
5. **Publicación única:** generar el instalador final, validar reparación, actualizar las instrucciones y recién entonces publicarlo en Discord.

## Criterios de salida

- Arranque limpio del servidor y del cliente estándar con 117 mods requeridos y las opciones visuales verificadas.
- Arranque de TLauncher con el mismo paquete y sin OptiFine.
- Dos clientes premium/no premium pueden registrarse, iniciar sesión y conservar perfil, claims, recetas y misiones tras reiniciar.
- No hay estructuras rotas en el spawn ni cofres de Lootr inaccesibles.
- La restauración de la copia recupera mundo, AuthMe, permisos, mercado y progreso.
- El instalador final se publica una sola vez y su hash queda registrado en `pack/current-release.json`.
