# Jugar en Virgos-MC

## Primer ingreso

Usá siempre el mismo nombre exacto, incluyendo mayúsculas. Registrate con `/register contraseña contraseña`; los siguientes ingresos usan `/login contraseña`. Elegí una contraseña exclusiva para este servidor. Si alguien ya registró tu nombre, contactá al administrador antes de crear otra identidad.

El pueblo del spawn tiene cuatro arcos que salen caminando al mundo. La plaza, el taller y la cocina son públicos; la construcción está protegida. Alejate de sus accesos para reclamar tu base. Las camas conservan el punto de reaparición.

**Dormir:** alcanza con que una sola persona se acueste para pasar la noche en el mundo principal, aunque los demás sigan explorando. Se mantienen las condiciones normales de uso de las camas, como no tener monstruos cerca.

**Si no sabés qué hacer:** pulsá **J → 01 · Empezar → Empezá por acá**. `/virgos guia` abre ayuda por temas; `/virgos progreso` muestra el próximo paso. No hace falta completar todos los mods.

**Nuevo en 2.0:** mundo y progreso nuevos, con Terralith, aldeas integradas, grandes mazmorras y nuevas rutas de jefes. El códice reúne **244 misiones y guías en diez capítulos**: Empezar, Tu hogar, Create, Magia, Explorar, Cocina, Aventuras, Jefes, Cooperar y El pueblo. `/virgos menu` reúne la ayuda.

La lista muestra el nombre y estado de cada misión. Usá la búsqueda del capítulo, los filtros **Pendientes / Para reclamar** y las flechas de página. Clic en una misión abre sus objetivos, explicación y recompensas. **A+ / A−** ajustan el tamaño de la interfaz; la rueda recorre páginas y, sobre los capítulos, las secciones que no entren en pantalla. **Ver mapa original** conserva la vista de conexiones de Heracles.

## Tu perfil y el de tus amigos

`/perfil` o **J → Mi perfil** muestra tiempo conectado, rango de Virgos, nivel de experiencia, misiones, criaturas derrotadas, muertes, distancia a pie y nadando, minería, fabricación y pesca. La pestaña **Misiones** desglosa el avance por capítulo. **Jugadores** permite consultar a quienes ya tengan registro; también funciona `/perfil Nombre` o `/estadisticas Nombre`.

El tiempo incluye AFK y no da recompensas. El nivel de experiencia puede bajar al morir o encantar; el rango depende de reconocimientos del códice. Los perfiles desconectados muestran su último registro guardado. Todo corresponde al mundo v2 y su reinicio; no muestra inventarios ni ubicaciones de bases.

## Mercado y encargos

Caminá desde la plaza al sudoeste, hasta **620, 80, 787**. Bruno explica el mercado y Lía los encargos. Hablales con la mano vacía.

1. Elegí un puesto libre entre los ocho numerados. Acercate y usá `/virgos mercado reservar N`, reemplazando N por su número.
2. Abrí el puesto y su almacén. Configurá una oferta en modo **trueque**: qué entregás, qué pedís y cuántas unidades.
3. Depositá mercadería. Cada venta consume existencias; las ofertas no generan objetos. Conservá la comparación de datos NBT para mochilas y equipo especial.
4. Revisá la oferta con un amigo. Los clientes pueden comprar, pero sólo el dueño administra el almacén. No retires el bloque del mercado; pedí ayuda para transferir una reserva.

El tablón está en **632, 80, 787**. Tomá un encargo adecuado a tus materiales y volvé con el papel y los objetos pedidos: se consumen al cobrar. **No vencen** y entregan provisiones modestas. Son opcionales y no dan rangos. `/virgos guia mercado` y `/virgos guia encargos` recuerdan los pasos.

| Tecla | Función |
| --- | --- |
| J | Abrir el Códice; **Mi perfil** está en su pantalla principal |
| B | Mochila |
| M | Mapa mundial |
| N | Nuevo marcador |
| Inicio | Lista de marcadores |
| F9 | Ajustes del mapa, sin interferir con transferencias de inventario |
| P | Bases y grupos |
| H | Historial de muertes |
| Acento grave (`) | Cambiar pestaña de información de objetos; G queda para Curios |
| R / U sobre un objeto | Receta / usos en JEI |
| V | Lanzar hechizo de Iron |
| R en el mundo | Rueda de hechizos de Iron |
| F6 / F7 / F8 | Activar shaders / elegir shaderpack / recargar shaders |
| O | Menú de voz y configuración inicial |
| Bloq Mayús | Mantener para hablar |

El Códice tiene una categoría propia en **Opciones → Controles → Códice de Virgos**. Sus botones muestran la tecla realmente asignada. Al actualizar, se reparan las teclas faltantes del paquete y un Códice sin asignación recibe **J**. Si antes abrías el Códice con otra tecla de Heracles, esa tecla pasa al nuevo control independiente; una asignación personal del nuevo control tiene prioridad. Se desactiva el control redundante de Heracles para evitar abrir dos pantallas.

La prioridad de los valores predeterminados es Códice, acciones de mods y accesos de plugins. Los shaders quedan en **F6–F8** para no interferir con hechizos, curios y voz. Las combinaciones de JEI dentro del inventario y los modificadores contextuales de Create se conservan: no son acciones globales simultáneas. Los controles personales se conservan; si todavía se solapan, el juego avisa y el instalador deja `virgos-keybinding-conflicts.json` para revisarlos en Controles. Una tecla que desactivaste se mantiene desactivada, salvo el acceso principal al Códice.

Para proteger el chunk en el que estás: `/oclaims claim`; para liberarlo: `/oclaims unclaim`. Hay 25 chunks personales y no hay carga permanente. Revisá los permisos antes de invitar amigos a tu party. Las misiones siguen siendo individuales.

## Proteger la primera base

1. Alejate del spawn. **F3+G** muestra los límites de los chunks, columnas de 16 × 16 bloques.
2. Parate en un chunk libre y escribí `/oclaims claim`. Leé la confirmación: si hubo error, no está protegido.
3. Repetí en cada chunk que ocupe tu casa, huerta o máquinas. **P** abre la pantalla de bases y grupos.
4. Revisá los permisos de acceso y construcción. Probá con un cofre vacío y un amigo antes de guardar objetos valiosos.
5. Para liberar únicamente el chunk actual: `/oclaims unclaim`. Al hacerlo, pierde esa protección.

`/virgos guia bases` muestra estos pasos y botones que preparan los comandos en el chat; revisalos antes de Enter. `/virgos guia grupo` explica cómo compartir. La party no comparte misiones ni rangos.

## Elegir el próximo objetivo

| Paso | Qué hacer | Qué habilita |
| --- | --- | --- |
| Explorador | Completar Primeros pasos y reclamar su reconocimiento | Magia rara de Iron y glifos de Ars de nivel 2 |
| Especialista | Completar una rama: Create, Iron o Ars; reclamar el reconocimiento | Preparación para los desafíos avanzados |
| Resonancia | Dos Exploradores superan la prueba | Con Especialista, magia épica de Iron |
| Forja | Dos Especialistas con Resonancia superan la prueba | Con Especialista, glifos de Ars de nivel 3 |
| Umbral / Maestro | Tres Especialistas con Forja superan Umbral y reclaman Maestro | Magia legendaria y glifos máximos |

Los capítulos enseñan Create, Ars, Iron, Alex's Caves, hogar/mochilas, cocina, exploración y juego en grupo. Son prácticas opcionales: los objetivos de inventario se detectan sin consumir el objeto; las actividades de lectura se marcan manualmente. No dan rangos por hacer clic ni añaden premios repetibles. La v2 comienza desde cero para todos.

**Rutas nuevas:** Explorar presenta el terreno, aldeas y mazmorras; Create incluye mecanismos de Integrated Dungeons y recursos de Alex's Caves. Jefes guía las invocaciones de Meet Your Fight y la preparación para Bosses of Mass Destruction. Aventuras cubre Aquamirae, Deep Aether, Incendium y Nullscape. Las casillas de lectura son una guía, no una verificación automática de haber vencido un jefe. Revisá JEI: las invocaciones avanzadas consumen trofeos previos y materiales de Create.

El códice entrega los reconocimientos al **reclamar la recompensa**, no sólo al completar el objetivo. `/virgos` abre la ayuda con enlaces a progreso, expediciones y pueblo. `/virgos progreso` muestra tus desbloqueos mágicos. Los objetos regalados no evitan esos requisitos. La misión de descanso acepta una cama de cualquier color.

## Expediciones

El camino sur lleva al anfiteatro en **672, 78, 1048**. Resonancia requiere dos Exploradores; Forja, dos Especialistas con Resonancia; Umbral, tres Especialistas con Forja. Cada participante usa `/virgos expedicion unirse resonancia` (o `forja`, `umbral`) y uno inicia con `/virgos expedicion iniciar`.

En cada ronda, todos deben tocar un sello y mantener clic derecho con la mano vacía en sellos distintos durante ocho segundos. Después se combate. Son tres rondas. Si falta alguien vivo, activo y autenticado dentro de la arena durante diez segundos, se cancela; se puede volver a intentar. `/virgos expedicion estado` muestra la ronda y los aportes pendientes de Forja. `/virgos expedicion salir` abandona.

- **Resonancia:** oeste + este, luego este + norte, finalmente oeste + norte.
- **Forja:** el grupo aporta 8 placas de hierro en la primera ronda, 4 placas de latón en la segunda y 1 mecanismo de precisión en la tercera. Usá `/virgos expedicion aportar`. Se consumen incluso si abandonan. En combate alguien debe tocar un sello cada seis segundos para mantener la refrigeración.
- **Umbral:** un Guardián del Bastión, basado en el devastador, con tres fases de vida y activación de los tres sellos entre fases. Cataclysm conserva sus jefes en las estructuras del mundo.

Dentro de las expediciones se limita el daño final por jugador, compartido entre todos sus blancos: 20/30/40 puntos por segundo y ráfagas de 10/18/24, según la prueba. La curación tiene topes de 4/6/8 puntos por segundo. Un corazón equivale a dos puntos. El mundo normal conserva el combate de sus mods.

Las recompensas del códice se reciben una vez por persona. Podés repetir para ayudar a amigos. Los enemigos de la prueba no dan botín ni experiencia; no se guarda ni reemplaza tu inventario al entrar. Prepará equipo, comida y curación.

## Preparación, comunidad y jefes

El capítulo **Preparación rápida** entrega suministros modestos una vez después de Explorador. Podés combinar vanguardia, magia y apoyo sin elegir una clase permanente.

`/virgos pueblo` muestra los proyectos comunes. En el Bastión, `/virgos pueblo aportar cocina`, `taller` o `caminos` consume los materiales indicados. Cada persona puede aportar hasta un tercio: hacen falta al menos tres. Al terminar, cada Explorador puede reclamar una recompensa personal en el códice, también si llega más tarde. Ustedes deciden dónde construir con esos suministros.

**Trofeos personales** agrega un premio único a ocho jefes para quienes participen y estén vivos cerca al terminar. El códice detalla los requisitos de actividad. Sus drops originales siguen siendo compartidos; los cofres convertidos por Lootr mantienen su botín individual.

## Voz

Iniciá sesión y pulsá **O** para configurar micrófono y auriculares. Mantené **Bloq Mayús** para hablar: alcance de 32 bloques, susurro de 8. Hay grupos privados opcionales. El túnel se configura automáticamente; tus amigos no abren puertos ni instalan Playit. Podés jugar sin micrófono. Si cambiaste estas teclas antes, revisá la categoría Voice Chat en Controles.

## Discord

En **LaLechebanda → #virgos-mc**, el chat se comparte con Minecraft. Podés conversar desde cualquiera de los dos lados; en el juego tenés que iniciar sesión primero. Discord es opcional y no requiere instalar nada adicional para Virgos-MC.

- `!jugadores`: quién está conectado.
- `!ip`: dirección del servidor y versión.
- `!ayuda`: misiones y protección de bases.
- `!voz`: orientación para usar la voz.

La voz de proximidad continúa dentro de Minecraft. El canal de voz de Discord sirve para conversar con el grupo y funciona por separado.

## Si algo falla

Guardá la captura del error y el archivo `logs/latest.log` de la carpeta de juego para el administrador. No compartas archivos de cuentas ni contraseñas. Si faltan mods, cerrá Minecraft y el launcher, abrí **EMPEZAR.bat** y tocá **Instalar** o **Revisar / reparar**. El asistente verifica y repone archivos. Empezá sin shaders; si agregaste mods visuales por tu cuenta, avisá al administrador.
