# Virgos-MC 1.2 — Pueblo vivo

Estado: **1.2.0 publicada y verificada**. Servidor abierto, respaldo posterior comprobado y reinicio validado. Evidencia: `.lab/reports/v12-final.json`.

## Objetivo

Dar al pueblo servicios útiles y actividades cortas para hasta ocho amigos: orientación por personajes, comercio entre jugadores, encargos opcionales, fotografía, música y navegación. Conservar progreso individual, cooperación y las identidades existentes.

## Alcance aprobado

- Exposure, Small Ships, Immersive Melodies, Bountiful, Every Compat y Create: Alex's Caves Compat.
- Easy NPC para habitantes y diálogos; Lightman's Currency para puestos de intercambio y comercio.
- DecentHolograms para señalización breve; menú central conectado con las guías de Virgos.
- Instalador y tutoriales en español, manteniendo IDs y progreso de las 154 misiones existentes.
- Equipar el pueblo con servicios y evaluar las estructuras descargables seleccionadas, preservando caminos y bases.
- DiscordSRV sujeto al acceso al Discord y al canal que indique el propietario; nunca distribuir credenciales.

## Reglas de balance

- Mercado entre jugadores: prioridad al trueque. No crear una tienda administrativa que compre recursos sin límite, ni recompensas por tiempo conectado.
- Las recetas nativas de acuñación y de los puestos quedan disponibles. Los encargos entregan suministros modestos, sin recompensas de jefes, rangos o recursos exclusivos; los intereses y recompensas automáticas siguen desactivados.
- Encargos opcionales; el progreso permanente permanece en Heracles. No exigir rachas diarias.
- Conservar dificultad y desbloqueos existentes. Revisar recetas renovables de Create/Alex's Caves y armas de barcos.
- NPC administrativos invulnerables, sin IA costosa, sin privilegios otorgados por comandos de conversación y con acceso a guías después del login.
- Claims, autenticación, restauración e intercambio de objetos con NBT deben funcionar antes de publicar.

## Ejecución y aceptación

1. Archivos oficiales y dependencias fijados por hash: completo.
2. Laboratorio aislado y configuración de balance: completo.
3. Cuatro NPC, ocho puestos, menú y 32 misiones nuevas: completo.
4. Dos identidades Forge, propiedad, NBT, stock, encargos, protecciones y persistencia: completo. Falta carga real de ocho jugadores.
5. Instalador oficial/TLauncher, 98 archivos requeridos y cuatro visuales opcionales: completo.
6. Publicación selectiva sin copiar mundos de prueba: completa, con acceso público, voz UDP, respaldo de seis mundos y reinicio comprobados.

DiscordSRV está activo en LaLechebanda → #virgos-mc, con chat comprobado en ambos sentidos y AuthMe. No cambia el cliente ni el túnel de voz. [Configuración y pruebas](discord.md). Se conserva el pueblo descargado de Cynera y se añade un mercado propio; no se importó otra taberna ni castillo. Detalles y limitaciones en [la revisión 1.2](revision-1.2.md).

## Fuentes

Archivos y hashes: `.lab/v12/mods.lock.json` y `.lab/v12/administration.lock.json` durante la preparación.

- https://modrinth.com/mod/bountiful
- https://modrinth.com/mod/exposure
- https://modrinth.com/mod/small-ships
- https://modrinth.com/mod/immersive-melodies
- https://modrinth.com/mod/every-compat
- https://modrinth.com/mod/create-alexs-caves-compat
- https://github.com/MarkusBordihn/BOs-Easy-NPC
- https://github.com/Lightman314/LightmansCurrency/wiki/Config-Files
- https://github.com/DecentSoftware-eu/DecentHolograms
