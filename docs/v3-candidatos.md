# Virgos-MC v3 — candidatos de cliente

Esta lista es el alcance de pruebas de la v3. El servidor y el mundo actual se conservan; los mods de esta hoja que sean sólo de cliente no cambian el contenido ni obligan a reiniciar el progreso.

## Lote A — laboratorio actual

| Área | Componente | Destino | Estado | Decisión de diseño |
| --- | --- | --- | --- | --- |
| Rendimiento | ModernFix, FerriteCore, Embeddium, Entity Culling, ImmediatelyFast, Dynamic FPS | Cliente; varias piezas también en servidor | Instalados | Base de rendimiento. Se miden arranque, FPS y memoria antes de sumar otra optimización. |
| Rendimiento | FastSuite, Placebo, Clumps | Servidor/cliente según el archivo | Instalados | Reducen trabajo de recetas y entidades de experiencia; se mantienen porque ya pasaron la prueba de arranque. |
| Render | Oculus 1.8.0 + Embeddium | Cliente | **Instalado por defecto, shaders apagados** | Oculus queda disponible para quien tenga margen. `enableShaders=false` y `shaderPack=` son la configuración inicial. |
| Render | First-person Model 2.7.3 | Cliente opcional | En laboratorio | Mejora la lectura de manos y cuerpo en primera persona. |
| Animación | Not Enough Animations 1.12.6 | Cliente opcional | En laboratorio | Añade animaciones de interacción sin cambiar estadísticas ni combate. |
| Cámara | Better Third Person 1.9.0 | Cliente opcional | En laboratorio | Cámara alternativa; se valida con Create, hechizos y monturas. |
| Audio | Sound Physics Remastered 1.5.1 | Cliente opcional | En laboratorio | Reverberación y atenuación espacial; revisar consumo de CPU en cuevas y fábricas. |
| Audio | Ambient Environment 11.0.0.1 | Cliente opcional | En laboratorio | Ambiente visual ligero. |
| Audio | AmbientSounds 6.3.11 + CreativeCore 2.12.40 | Cliente opcional | **Añadido a v3-lab** | Paisaje sonoro por bioma; se prueba junto con Sound Physics para evitar duplicación molesta. |
| Animación | Eating Animations 5.1.0 + GML 4.0.10 | Cliente opcional | **Añadido a v3-lab** | Feedback visual de comida y pociones; sin impacto en recetas ni balance. |

Oculus se instala como mod de cliente para que el menú y el soporte estén disponibles. El paquete de shader se descarga desde su publicación oficial durante la instalación y se deja sin seleccionar; activar shaders sigue siendo una decisión del jugador.

## Lote B — candidatos para una segunda prueba

| Componente | Motivo | Riesgo o condición |
| --- | --- | --- |
| 3D Skin Layers 1.9.0 Forge | Capas de skin en 3D, sólo cliente | La propia página documenta sombras extrañas con shaders; probarlo con Oculus antes de incluirlo. |
| Better F3 | Depura el HUD y deja la información esencial más legible | Licencia ARR y cambio de interfaz; sólo se agrega si el grupo lo prefiere. |
| Entity Model Features + Entity Texture Features | Más modelos y texturas animadas | Puede cruzarse con Oculus y resourcepacks; requiere una prueba de arranque y de mobs de Alex. |
| Euphoria Patcher | Perfiles visuales para Complementary | Se reserva para la prueba con shaders; no se instala en equipos de bajo rendimiento. |

## Lote C — no se agrega todavía

- **Tectonic:** cambia la forma del terreno y puede dejar una frontera visual entre chunks viejos y nuevos. No se agrega mientras se conserva `virgos_world`.
- **Towns and Towers / Structory:** son buenas opciones para estructuras en chunks vírgenes, pero antes hay que medir frecuencia y solapamientos con When Dungeons Arise, Integrated Dungeons and Structures y YUNG's. Se prueban en una copia del mundo, nunca directamente sobre producción.
- **Más optimizadores de render:** no se apilan por cantidad. Embeddium, ModernFix, FerriteCore, Entity Culling e ImmediatelyFast forman la base; el siguiente candidato sólo entra si una medición muestra una mejora y no agrega warnings nuevos.

## Pruebas de aceptación

1. Arranque limpio con el perfil estándar, sin shaders activos.
2. Arranque con cada lote visual opcional habilitado y regreso al menú sin crash.
3. Entrada al servidor, voz, JEI, Create, hechizos, claims, Lootr y perfil.
4. Medición con shaders apagados en una PC modesta: memoria Java, FPS en spawn y tiempo hasta menú.
5. Medición con Complementary Reimagined en perfiles Potato/Low/Medium en una PC con margen.
6. Revisión de `latest.log` para crashes, warnings nuevos de mixins y errores de audio.

La entrega final se construye una sola vez después de cerrar este lote y la prueba de mundo. No se publica este candidato local ni se actualiza Discord todavía.
