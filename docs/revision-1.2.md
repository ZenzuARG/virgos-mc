# Virgos-MC 1.2 — Pueblo vivo

La expansión suma actividades cortas y servicios al pueblo sin reiniciar el mundo ni cambiar las 154 misiones anteriores. La versión **1.2.0 está publicada**; `pack/current-release.json` enlaza `.lab/reports/v12-final.json`. Se comprobó el dominio público y la conexión de voz UDP, con respaldo completo posterior y reinicio validado.

## Contenido

| Componente | Versión fijada | Uso y límite |
| --- | --- | --- |
| Bountiful + Kambrik | 6.0.4 / 6.1.1 | Encargos de cocina, taller y caminos. Sin vencimiento; premios modestos, sin rangos. |
| Exposure | 1.7.16 | Cámaras, películas, fotografías y álbumes. |
| Small Ships | 2.0.2 | Navegación en grupo. Recetas nativas de cañones y munición disponibles; daño naval y destrucción permanecen desactivados por configuración. |
| Immersive Melodies | 0.8.0 | Instrumentos, alcance de 24 bloques y volumen reducido. Sin aparición de músicos entre los mobs. |
| Every Compat | 1.20-2.9.27 | Variantes de madera. Integraciones con Chipped y Lightman's Currency excluidas para limitar registros y evitar errores. |
| Create: Alex's Caves Compat | 1.6.2 | Procesamiento y construcción. Corregido un JSON de receta; la receta nativa de la bomba nuclear queda disponible. |
| Easy NPC | 7.16.0 | Alma, Bruno, Lía y Nora. Guías de tres páginas; edición reservada a administradores. No ejecutan comandos privilegiados. |
| Lightman's Currency | 2.3.0.6 | Ocho puestos físicos de trueque, uno por identidad. Acuñadora y recetas nativas disponibles; los intereses y recompensas automáticas siguen desactivados. |
| DecentHolograms | 2.10.2 | Un cartel del mercado visible a corta distancia. |
| DiscordSRV | 1.30.5 | Chat y avisos en LaLechebanda → #virgos-mc. Solo servidor; Discord opcional para jugar. |

Son 98 archivos requeridos de mods y dependencias en el cliente, más cuatro opciones visuales. El instalador conserva la selección de launcher y las preferencias del jugador.

## Integración

- `/virgos menu` reúne nueve accesos a ayuda. **J** contiene 186 misiones en 26 capítulos; los seis nuevos enseñan mercado, encargos, fotografías, barcos, música/decoración y procesos de Create/Alex's Caves.
- El mercado está en **620, 115, 787**, conectado a la plaza por un camino. La plantilla es propia y aditiva: no vuelve a colocar el pueblo Cynera ni copia datos del laboratorio.
- Las reservas se guardan por UUID local. Mantener el mismo nombre exacto sigue siendo necesario en el servidor offline. Una reserva no se libera por romper o retirar el puesto; las transferencias requieren mantenimiento administrativo.
- Las ofertas consumen stock. El dueño deposita los productos; el comprador paga los objetos configurados. No hay tienda administrativa de compra ilimitada ni venta de equipo exclusivo de expediciones.
- OPAC permite usar puestos, tablón y diálogos dentro del spawn, manteniendo bloqueada la construcción. Las funciones de grupos y las protecciones anteriores se conservan.
- La traducción del mercado repara archivos españoles malformados del mod mediante el paquete de recursos, sin modificar los JAR oficiales.
- Discord está conectado: chat comprobado en ambos sentidos, bloqueo antes de AuthMe y comandos `!jugadores`/`!ayuda` verificados con un cliente Forge real. Configuración y evidencia en [Discord](discord.md). Simple Voice Chat conserva su túnel UDP existente.

## Pruebas y recuperación

El informe `.lab/reports/v12-acceptance.json` recoge pruebas con dos identidades reales de Forge, usadas de forma secuencial: login, reserva ajena rechazada, propiedad del almacén, pago y stock, transferencia de una mochila conservando sus datos, entrega de encargos, diálogos después de reiniciar y protección de la plaza. Se sincronizaron 18.415 recetas de servidor y cliente sin diferencias.

La plaza se inspeccionó visualmente y se comprobaron sus 9.584 posiciones, incluido el despeje del techo antiguo. El acceso se recorrió caminando. El instalador pasó 22 comprobaciones de migración y conservación de archivos; la configuración de TLauncher tiene 16 comprobaciones adicionales.

`v12-promotion.json` identifica el respaldo completo anterior y el archivo de reversión. No se copiaron mundos, inventarios, cuentas ni comerciantes de prueba desde el laboratorio. `v12-final.json` registra las comprobaciones públicas y el respaldo posterior. Los textos de los cuatro NPC y el cartel se corrigieron a UTF-8 y se verificaron nuevamente después del último reinicio.

## Pendientes concretos

- Probar audio entre micrófonos y carga real con ocho jugadores y fábricas. No se sustituyen esas pruebas con una medición de TPS en vacío.
- TLauncher se verificó mediante sus archivos de configuración y pruebas del instalador; no se instaló ni abrió su aplicación en esta PC.
- Persisten avisos de la plataforma híbrida y de integraciones opcionales de la versión anterior. El primer intento de conexión venció tanto en laboratorio como en la prueba pública; en ambos casos la reconexión funcionó. La causa sigue pendiente de diagnóstico; se documenta cómo volver a entrar.

## Fuentes y artefactos

Los archivos exactos, sus URL oficiales y hashes están en `pack/mods.lock.json`, `pack/administration.lock.json` y `pack/custom-artifacts.lock.json`. La lista de proyectos y fuentes está en [el plan de expansión](expansion-1.2.md). La corrección de recursos usa el [filtro de paquetes documentado por Minecraft](https://feedback.minecraft.net/hc/en-us/articles/6731464524941-Minecraft-Java-Edition-1-19).
