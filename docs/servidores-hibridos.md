# Eleccion de servidor — revision del 17/10/2026

Se eligio **Forge 1.20.1 + Ketting** porque el objetivo es combinar mods de contenido amplios con plugins Bukkit/Spigot. El conjunto instalado arranco y admite el complemento integrado de Playit y AuthMe. Esto no garantiza la compatibilidad de futuros mods.

| Alternativa | Evaluacion para este proyecto |
| --- | --- |
| Fabric + Cardboard | Cardboard 1.20.1 existe, pero sigue siendo beta y no ofrece compatibilidad universal con Bukkit. Conveniente si el paquete depende de mods Fabric concretos. |
| Forge + Ketting | Elegida. Publica una base Forge 1.20.1 actualizada y un puente Bukkit/Spigot; tambien se declara beta. |
| Forge + Arclight | Alternativa valida a evaluar si un mod falla en Ketting. La release Trials 1.0.6 examinada utiliza una base Forge anterior. |
| Spigot / Paper | Por si solos no cargan mods Forge/Fabric. Paper tampoco garantiza compatibilidad con este hibrido. |
| Mohist / Banner | No se eligieron frente a la base comprobada: Mohist informa falta de mantenimiento en su pagina y Banner no ofrecio una opcion oficial actual claramente verificable. |

Forge 1.20.1 tiene opciones como Create, Ars Nouveau y Alex's Caves que encajan con tecnologia, magia y exploracion. Todavia no se instalaron: primero se valida la base y luego se elige un conjunto de mods con dependencias y cliente reproducible. No mezclar archivos Fabric, NeoForge y Forge solo porque comparten la version de Minecraft.

Fuentes primarias:

- [Ketting](https://kettingpowered.org/) y [codigo 1.20.x](https://github.com/kettingpowered/Ketting-1-20-x).
- [Arclight Trials 1.0.6](https://github.com/IzzelAliz/Arclight/releases/tag/Trials/1.0.6).
- [Cardboard para 1.20.1](https://modrinth.com/mod/cardboard/version/1.20.1-13).
- [Create](https://modrinth.com/mod/create), [Ars Nouveau](https://modrinth.com/mod/ars-nouveau), [Alex's Caves](https://modrinth.com/mod/alexs-caves).
