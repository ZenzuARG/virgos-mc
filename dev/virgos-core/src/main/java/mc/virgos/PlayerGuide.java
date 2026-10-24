package mc.virgos;

import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Read-only help. Commands that change player state are suggested, never run by a click. */
public final class PlayerGuide {
    private record Page(String title, List<String> lines, Map<String,String> suggestions) {}
    private static final Map<String,Page> PAGES = new LinkedHashMap<>();
    static {
        page("mercado", "Un puesto para cada vecino", List.of(
            "Mercado: 620, 80, 787, al sudoeste de la plaza. Ocho puestos; uno por persona.",
            "Acercate a uno libre y escribí /virgos mercado reservar 1 (cambiá 1 por su número).",
            "Abrí el puesto, entrá a su almacén y configurá una oferta en modo TRUEQUE.",
            "Elegí qué entregás y qué recibís; depositá mercadería en el almacén. Sin stock no se vende.",
            "Comprobá cantidades y datos del objeto. Para mochilas y equipo, conservá la comparación NBT.",
            "Los demás pueden comprar; sólo el propietario gestiona el almacén. No hay ingresos AFK ni acuñación.",
            "No retires ni muevas el bloque del mercado. Para cambiar de titular, pedí ayuda al administrador."),
            Map.of("Preparar reserva", "/virgos mercado reservar 1"));
        page("encargos", "Encargos para una sesión corta", List.of(
            "El tablón del mercado está en 632, 80, 787. Clic derecho para ver encargos.",
            "Elegí uno acorde a tus materiales. Leé la cantidad requerida y la recompensa antes de tomarlo.",
            "Llevá el encargo y los objetos pedidos; volvé al tablón para entregarlos. Se consumen al cobrar.",
            "Los encargos no vencen. Entregan provisiones pequeñas, no rangos ni recursos de jefes.",
            "J conserva tus misiones permanentes; Bountiful es una actividad opcional y repetible."));
        page("fotografia", "Un álbum del servidor", List.of(
            "Buscá @exposure en JEI. Fabricá cámara y película; la cámara necesita película cargada.",
            "Revisá controles y ajustes de la cámara. Una toma consume un fotograma: encuadrá primero.",
            "Revelá la película y prepará las fotografías con las recetas de JEI y el cuarto oscuro.",
            "Guardá copias en un álbum o en marcos. No hace falta visitar todas las dimensiones para empezar.",
            "J → El pueblo: ruta de fotografía. Propuesta: un retrato, tu base y una salida en grupo."));
        page("navegacion", "Viajar juntos por el agua", List.of(
            "Buscá @smallships en JEI. Empezá con una nave pequeña y revisá materiales y pasajeros.",
            "Prepará un muelle con agua profunda y espacio para girar. Colocá la nave y probá cerca de casa.",
            "Leé sus controles, vela, inventario y desembarco antes de cargar objetos valiosos.",
            "Los barcos sirven para transporte y exploración. Cañones y daño por colisión están desactivados.",
            "Marcá el muelle en el mapa; no bloquees accesos ajenos. Nadie necesita ser artillero para viajar."));
        page("musica", "Música para la posada", List.of(
            "Buscá @immersive_melodies en JEI. Probá una flauta o un laúd antes de fabricar instrumentos grandes.",
            "Abrí el instrumento y elegí una melodía. Revisá volumen y cómo detenerla.",
            "El alcance es de 24 bloques. Acordá los ensayos con quienes están construyendo cerca.",
            "Podés combinar música con fotografías y reuniones; no concede bonificaciones de combate.",
            "J → El pueblo: música, prácticas cortas y decoración con materiales que ya conozcas."));
        page("inicio", "Empezar sin perderse", List.of(
            "1. Iniciá sesión. J abre tus misiones; elegí Empezar y la misión Empezá por acá.",
            "2. Cada misión se completa con una casilla o detectando un objeto en tu inventario. Después tocá RECLAMAR.",
            "3. Salí caminando del Bastión, marcá una base y protegé sus chunks.",
            "4. Elegí una rama. Los tutoriales de mods son opcionales y podés seguir varias.",
            "Si una misión dice VER REQUISITO, abrila: muestra la misión anterior que tenés que reclamar. No hace falta volver a conseguir un objeto que ya tenés.",
            "/perfil muestra tus horas, nivel y avance. /perfil Nombre consulta a un amigo.",
            "Elegí un tema abajo. Los botones de comandos sólo preparan el texto: revisalo antes de Enter."));
        page("progreso", "Qué desbloquea cada paso", List.of(
            "Explorador: bienvenida + pico de hierro; reclamá su misión. Abre magia rara y glifos de nivel 2. Cama y protección quedan como guías opcionales.",
            "Especialista: completá UNA rama: Ingeniería Create, Hechicería Iron o Ars. Reclamá su reconocimiento.",
            "Resonancia, Forja y Umbral: expediciones cooperativas opcionales que dan recompensas y reconocimientos propios.",
            "Maestro: reclamá la recompensa de Umbral para habilitar el último escalón de magia que todavía no aprendiste.",
            "Un hechizo que ya está dentro de tu libro se puede lanzar. El códice ordena lo que aprendés después, no te quita lo que ya tenés.",
            "No hay niveles por horas AFK. Regalos no conceden reconocimientos. Construcción y cocina siguen a tu ritmo."),
            Map.of("Ver mi avance", "/virgos progreso"));
        page("magia", "Magia sin trabas", List.of(
            "1. Abrí J → 04 · Magia y elegí la ruta Iron o Ars. Las misiones de materiales se muestran juntas después de Explorador.",
            "2. Si ya tenés tinta, pergamino, mesa o libro, dejalo en tu inventario y abrí la misión: la detección es automática.",
            "3. Completá la casilla u objeto y tocá RECLAMAR. La recompensa del códice registra el siguiente rango.",
            "4. Si un hechizo ya aparece en tu libro, podés lanzarlo aunque todavía no hayas terminado la misión de la ruta.",
            "Si dice VER REQUISITO, abrí la misión para ver exactamente qué paso anterior falta. No repitas materiales a ciegas.",
            "Iron: la rareza marca el siguiente escalón. Ars: los glifos siguen el mismo orden. El grupo no bloquea una magia que ya aprendiste."),
            Map.of("Ver mi avance", "/virgos progreso"));
        page("bases", "Proteger tu base", List.of(
            "1. Alejate del Bastión y de terrenos ajenos. F3+G muestra chunks de 16 × 16.",
            "2. Parate en el chunk que querés proteger y prepará /oclaims claim abajo.",
            "3. Leé la confirmación; P abre bases y grupos. Repetí para todos los chunks de tu casa.",
            "Disponés de 25 chunks personales; no quedan cargados permanentemente.",
            "Revisá permisos de cofres, máquinas y construcción antes de invitar a alguien.",
            "Liberar quita la protección del chunk actual. Usalo sólo si estás seguro del lugar."),
            Map.of("Preparar reclamo", "/oclaims claim", "Preparar liberación", "/oclaims unclaim"));
        page("grupo", "Compartir con confianza", List.of(
            "P abre Open Parties and Claims: usá sus pantallas de grupo y configuración de protección.",
            "Invitá sólo personas de confianza y revisá qué permite tu configuración a los miembros.",
            "Probá acceso a un cofre vacío y construcción con un amigo antes de guardar objetos valiosos.",
            "Ser parte de una party no comparte misiones ni rangos. Cada uno reclama sus recompensas.",
            "Lootr: cada persona abre el mismo cofre compatible. Minerales y drops originales de jefes se reparten."));
        page("mods", "Aprender los mods", List.of(
            "JEI: inventario, buscá un objeto, R para receta y U para usos. @create filtra por mod.",
            "Create: usá Ponder al posar el cursor. Aprendé rueda, ejes, estrés y una máquina antes de escalar.",
            "Ars: cuaderno + glifos; maná personal y fuente de aparatos son recursos distintos.",
            "Iron: leé rareza, maná y enfriamiento. Un hechizo que ya está en tu libro se puede lanzar; /virgos progreso muestra el próximo rango.",
            "Alex’s Caves: compendio, tablillas e investigación; la brújula de biomas no reemplaza sus pistas.",
            "J → capítulos 13 a 20: tutoriales de tecnología, magia, cuevas, hogar, cocina y viajes."));
        page("expediciones", "Preparar una expedición", List.of(
            "Arena: camino sur del Bastión, 672, 78, 1048. Lleguen con comida y equipo.",
            "Cada jugador se une a la misma prueba; uno inicia. Resonancia necesita 2, Forja 2 y Umbral 3.",
            "Todos tocan un sello activo y mantienen clic derecho con mano vacía en sellos distintos, 8 segundos.",
            "Forja: 8 placas de hierro, luego 4 de latón, luego 1 mecanismo; los aportes se consumen.",
            "En Forja tocá un sello cada 6 segundos para refrigerar. Umbral tiene 3 fases y 3 sellos.",
            "Faltar 10 segundos cancela. Reclamá las recompensas en J después de ganar."),
            Map.of("Ver estado", "/virgos expedicion estado", "Unirme a Resonancia", "/virgos expedicion unirse resonancia",
                "Iniciar grupo", "/virgos expedicion iniciar", "Salir del grupo", "/virgos expedicion salir"));
        page("recuperar", "Volver a casa y recuperar equipo", List.of(
            "Dormí en tu cama para fijar reaparición. N marca una ubicación; M abre el mapa.",
            "Los sacos de Comforts no cambian tu reaparición. No hay un /home general.",
            "Al morir: H abre el historial de Corpse; buscá coordenadas y dimensión.",
            "Sólo el dueño recupera su cadáver. Llevá provisiones de reserva para llegar.",
            "Si está inaccesible, avisá al administrador con coordenadas. Conservá el mismo nombre exacto."));
        page("voz", "Hablar y escuchar", List.of(
            "Iniciá sesión y pulsá O. Elegí micrófono y auriculares; Bloq Mayús es pulsar para hablar.",
            "Proximidad: 32 bloques; susurro: 8. Podés crear grupos privados desde el menú.",
            "Si no escuchás: revisá conexión, dispositivo de salida, volumen y si están en el mismo grupo.",
            "Si no te oyen: revisá entrada, permiso de micrófono de Windows y la tecla en Controles.",
            "No necesitás instalar Playit ni abrir puertos. La voz es opcional y requiere login."));
        page("comandos", "Comandos de uso diario", List.of(
            "/virgos progreso — reconocimientos y próximo paso.",
            "/oclaims claim / unclaim — proteger o liberar el chunk donde estás.",
            "/virgos expedicion estado — ronda, integrantes y materiales.",
            "/virgos pueblo — proyectos colectivos y tu aporte. Aportar consume materiales.",
            "/login clave — ingresar. /register clave clave — solamente la primera vez.",
            "No compartas claves en chat ni capturas. Las teclas se revisan en Opciones → Controles."),
            Map.of("Ver pueblo", "/virgos pueblo", "Preparar aporte a cocina", "/virgos pueblo aportar cocina"));
    }
    private static void page(String id,String title,List<String> lines){page(id,title,lines,Map.of());}
    private static void page(String id,String title,List<String> lines,Map<String,String> commands){PAGES.put(id,new Page(title,lines,commands));}
    public static LiteralArgumentBuilder<CommandSourceStack> command(String name) {
        return Commands.literal(name).executes(c->show(c.getSource(),"inicio"))
            .then(Commands.argument("tema",StringArgumentType.word())
                .suggests((c,b)->SharedSuggestionProvider.suggest(PAGES.keySet(),b))
                .executes(c->show(c.getSource(),StringArgumentType.getString(c,"tema"))));
    }
    public static int show(CommandSourceStack source,String topic) {
        var player=source.getPlayer();
        if(player!=null&&!VirgosCore.AUTH.authenticated(player))return 0;
        var page=PAGES.get(topic);
        if(page==null){source.sendFailure(Component.literal("Tema desconocido. Usá /virgos guia."));return 0;}
        source.sendSuccess(()->Component.literal("§6Virgos · "+page.title()),false);
        for(String line:page.lines())source.sendSuccess(()->Component.literal("§f"+line),false);
        page.suggestions().forEach((label,command)->source.sendSuccess(()->Component.literal("§a["+label+"] ")
            .withStyle(s->s.withClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND,command))),false));
        var nav=Component.literal("§7Guía: ");
        PAGES.forEach((id,p)->nav.append(Component.literal("§b["+id+"] ").withStyle(s->s.withClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND,"/virgos guia "+id)))));
        source.sendSuccess(()->nav,false);
        return 1;
    }
}
