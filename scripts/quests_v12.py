"""Optional, Spanish practical tutorials; no new rewards or progression gates."""
def extend(quest,quests,check,item_task):
 def chain(group,prefix,rows):
  previous='bienvenida'
  for key,title,item,text in rows:
   identifier=prefix+'_'+key
   ending=('\n\nObjetivo: llevá el objeto en el inventario; se detecta sin consumirlo. Practicá el paso descrito.' if item else '\n\nActividad guiada: realizá o revisá los pasos y marcá la casilla. No se detecta automáticamente esta acción.')
   quest(identifier,title,group,item or 'minecraft:book',text+ending,item_task(item) if item else check('Ya lo revisé / practiqué'),[previous]);previous=identifier
 chain('21 · Mercado entre vecinos','mercado',[
  ('visita','Encontrar el mercado',None,'Desde la plaza caminá al sudoeste: 620, 115, 787. Bruno explica los puestos y Lía el tablón. /virgos menu reúne las guías. El mercado está dentro del mismo mundo y no requiere un teletransporte.'),
  ('reserva','Un puesto propio',None,'Elegí uno de los ocho puestos numerados. Acercate y escribí /virgos mercado reservar seguido del número. Leé la respuesta: un puesto ocupado no cambia de dueño. Cada persona conserva una reserva aunque mueva el bloque; no lo retires del mercado.'),
  ('oferta','Definir un trueque',None,'Abrí tu puesto y su almacén/configuración. Elegí una oferta en modo TRUEQUE: un objeto que entregás y otro que pedís a cambio. Empezá con materiales comunes y cantidades pequeñas. Verificá el sentido del intercambio antes de habilitarlo.'),
  ('stock','Sin mercadería no hay venta',None,'Depositá el producto en el almacén del puesto. Las ventas consumen ese stock y dejan lo recibido. Tener el icono de una oferta no crea objetos. Reservá espacio para cobrar y revisá tus existencias cuando vuelvas.'),
  ('datos','Cuidar objetos especiales',None,'Una mochila, una herramienta encantada o una fotografía tiene datos propios. Conservá la comparación NBT y probá con objetos de poco valor antes de vender equipo especial. Una mochila vacía y otra llena no son equivalentes.'),
  ('compra','Probar con un vecino',None,'Pedile a un compañero que revise la oferta, compre una vez y confirme lo recibido. Compará existencias antes y después. Sólo el dueño administra el almacén. No hay tienda administrativa infinita ni dinero por estar conectado.'),
  ('base','Comerciar desde casa','lightmanscurrency:shelf_oak','También podés fabricar una estantería de Lightman y ponerla en tu base. El bloque conserva propiedad y almacén. Revisá cómo permitir a clientes interactuar sin abrir tus cofres ni tus máquinas; no des acceso general a la base.')])
 chain('22 · Encargos sin apuro','encargo',[
  ('tablon','Leer antes de aceptar',None,'El tablón Bountiful está en 632, 115, 787. Abrilo y compará objetos pedidos, cantidades y recompensa. Elegí una tarea acorde a tu sesión; no necesitás completar todas las ofertas.'),
  ('tomar','Un encargo en el bolsillo','bountiful:bounty','Tomá un encargo del tablón y revisá su descripción en el inventario. Los encargos de Virgos no vencen. Conservá el papel para poder entregarlo cuando tengas los materiales.'),
  ('preparar','Separar lo que vas a entregar',None,'Reuní exactamente los objetos indicados. No uses el material reservado para tu próxima herramienta. Cocinar, fabricar e intercambiar con compañeros son formas válidas de prepararte.'),
  ('cobrar','Volver al tablón',None,'Llevá el encargo y sus materiales al tablón para completarlo. La entrega consume los objetos pedidos y da las provisiones indicadas. Mirá el inventario después de cobrar. El códice J conserva por separado tus misiones permanentes.'),
  ('ritmo','No es una obligación diaria',None,'Los encargos son repetibles y opcionales: no desbloquean rangos ni sustituyen expediciones. Si hoy preferís construir o explorar, podés hacerlo. No hay rachas diarias que perder.')])
 chain('23 · Fotografía y recuerdos','foto',[
  ('camara','Preparar una cámara','exposure:camera','Buscá @exposure en JEI. Fabricá la cámara y revisá su interfaz, ajustes y controles. Una cámara sin película no tiene fotogramas disponibles.'),
  ('pelicula','Cargar película','exposure:black_and_white_film','Comenzá con película en blanco y negro. Cargala en la cámara siguiendo su interfaz; revisá fotogramas restantes. Prepará una escena antes de disparar, porque cada toma consume uno.'),
  ('encuadre','Tu primera composición',None,'Probá cerca del pueblo con buena luz. Elegí un motivo, encuadrá y tomá una fotografía. Pedí a un compañero que pose o usá un edificio; no hace falta viajar a una dimensión peligrosa.'),
  ('revelar','Revelar e imprimir','exposure:lightroom','Consultá las recetas de revelado y de la mesa de cuarto oscuro en JEI. Seguí las etapas desde la película expuesta hasta la fotografía; no confundas la película virgen con la revelada.'),
  ('album','Armar una historia','exposure:album','Guardá fotos en un álbum. Propuesta: la plaza, tu primer taller y una salida con amigos. Decidí el orden para contar una historia y reservá los originales que quieras conservar.'),
  ('exhibir','Una pared de recuerdos','exposure:photograph_frame','Colocá un marco en tu terreno y exhibí una foto. Podés compartir copias o acordar un álbum colectivo; la actividad es creativa y no da ventajas de combate.')])
 chain('24 · Navegación en grupo','barco',[
  ('plan','Elegir una travesía',None,'Buscá @smallships en JEI y compará tamaño, materiales y pasajeros. Marcá un destino accesible por agua y un punto de regreso. Empezá con una ruta corta antes de transportar equipo valioso.'),
  ('nave','La primera nave','smallships:oak_cog','Fabricá un cog de roble. Prepará agua profunda y espacio para colocarlo y girar. Revisá sus controles, vela y cómo desembarcar antes de llevar pasajeros.'),
  ('carga','Preparar sin sobrecargar',None,'Llevá comida, cama o saco de dormir, herramientas y materiales de reparación indicados por el mod. Separá provisiones de viaje y mercadería. Marcá el muelle en Xaero para encontrarlo al volver.'),
  ('tripulacion','Una prueba con amigos',None,'Suban cerca de la costa y prueben navegación y desembarco. Acuerden quién dirige y cómo avisan una parada. Usen la voz de proximidad o un grupo privado si necesitan coordinarse a distancia.'),
  ('convivir','Puertos abiertos',None,'No bloquees muelles ni salidas ajenas. Virgos desactiva recetas de cañones y el daño de colisión: los barcos amplían transporte y exploración. Consultá /virgos guia navegacion cuando necesites recordar el plan.')])
 chain('25 · Música y construcción','arte',[
  ('instrumento','Una melodía sencilla','immersive_melodies:flute','Buscá @immersive_melodies en JEI y fabricá una flauta. Abrí su interfaz, elegí una melodía y probá cómo detenerla antes de tocar cerca de otros.'),
  ('ensayo','Escuchar a los demás',None,'El alcance está limitado a 24 bloques. Acordá el volumen y horario de ensayo con quienes construyen cerca. No superpongas canciones sin ponerse de acuerdo; pueden alternar instrumentos o presentaciones.'),
  ('laud','Una reunión en la posada','immersive_melodies:lute','Prepará un laúd y organizá una reunión corta. La música, la comida y las fotos permiten compartir tiempo aunque cada jugador tenga distinto equipo o progreso.'),
  ('paleta','Maderas que combinan',None,'Every Compat añade variantes compatibles con las maderas del paquete. Buscá el bloque decorativo en JEI y compará materiales. Algunas combinaciones masivas se excluyen para cuidar memoria; Chipped conserva sus variantes originales.'),
  ('proyecto','Un rincón habitable',None,'Elegí tres materiales y construí un rincón de descanso en tu base: asiento, iluminación y una fotografía. Protegé el chunk y comprobá que puertas y acceso funcionen. Es una meta creativa, sin recompensa de poder.')])
 chain('26 · Create y las cuevas','industria_cueva',[
  ('descubrir','Explorar antes de automatizar',None,'Create: Alex’s Caves Compat agrega procesos para materiales de las cuevas. Primero investigá la cueva con sus pistas y conseguí muestras; después buscá usos con U. La fábrica no sustituye el descubrimiento.'),
  ('receta','Leer entrada, salida y probabilidad',None,'En JEI revisá la máquina, el ingrediente exacto, el tiempo y las probabilidades. Una receta de mineral triturado exige mineral; no es generación gratuita. Los resultados secundarios pueden ser probabilísticos.'),
  ('piloto','Probar un lote pequeño',None,'Procesá una unidad manualmente y comprobá el resultado. Después conectá un cofre de entrada, filtro y salida suficiente. Conservá muestras de los materiales de investigación antes de enviar todo a una línea.'),
  ('limites','Una industria segura',None,'Usá apagado por redstone, mantené todo dentro del claim y evitá objetos tirados. Las recetas nativas de Create y Alex\'s Caves están disponibles; usá JEI para ver si requieren mesa, máquina o componentes especiales. /virgos progreso explica los rangos; los procesos nuevos no conceden reconocimientos cooperativos.')])
