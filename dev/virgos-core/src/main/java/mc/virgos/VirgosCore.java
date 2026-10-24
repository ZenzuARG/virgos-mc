package mc.virgos;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;
import org.slf4j.Logger;
import mc.virgos.update.ClientUpdateServer;
import mc.virgos.update.UpdateProtocol;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Mod(VirgosCore.ID)
public final class VirgosCore {
    public static final String ID = "virgos_core";
    public static final Logger LOG = LogUtils.getLogger();
    public static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();
    public static final AuthBridge AUTH = new AuthBridge();
    public static final ModResync MOD_SYNC = new ModResync();
    public static final Progression PROGRESSION = new Progression();
    public static final Expeditions EXPEDITIONS = new Expeditions();
    public static final CommunityProjects COMMUNITY = new CommunityProjects();
    public static final BossRewards BOSSES = new BossRewards();
    public static final Maintenance MAINTENANCE = new Maintenance();
    public static ClientUpdateServer UPDATE_GATE;
    public static final TownServices TOWN = new TownServices();
    public static final PlayerProfiles PROFILES = new PlayerProfiles();
    private final Set<UUID> greeted = new HashSet<>();
    private final WorldTools worldTools = new WorldTools();

    public VirgosCore() {
        mc.virgos.profile.ProfileProtocol.register(ignored->{});
        UPDATE_GATE = ClientUpdateServer.load(Path.of("config/virgos/client-update.json"), JSON);
        UpdateProtocol.register(message -> UPDATE_GATE.receive(message));
        MinecraftForge.EVENT_BUS.register(this);
        MinecraftForge.EVENT_BUS.register(PROGRESSION);
        MinecraftForge.EVENT_BUS.register(EXPEDITIONS);
        MinecraftForge.EVENT_BUS.register(BOSSES);
    }

    @SubscribeEvent
    public void started(ServerStartedEvent event) {
        MOD_SYNC.initialize();
        AUTH.initialize(event.getServer());
        PROGRESSION.initialize(event.getServer());
        EXPEDITIONS.initialize(event.getServer());
        COMMUNITY.initialize(event.getServer());
        MAINTENANCE.initialize(event.getServer());
        TOWN.initialize(event.getServer());
        PROFILES.initialize(event.getServer());
        try {
            Path folder = Path.of("virgos-reports");
            Files.createDirectories(folder);
            Files.writeString(folder.resolve("registries.json"), JSON.toJson(Map.of(
                "items", ForgeRegistries.ITEMS.getKeys().stream().map(Object::toString).sorted().toList(),
                "itemTags", ForgeRegistries.ITEMS.tags().getTagNames().map(tag->tag.location().toString()).sorted().toList(),
                "recipes", event.getServer().getRecipeManager().getRecipes().stream().map(recipe->recipe.getId().toString()).sorted().toList(),
                "blocks", ForgeRegistries.BLOCKS.getKeys().stream().map(Object::toString).sorted().toList(),
                "entities", ForgeRegistries.ENTITY_TYPES.getKeys().stream().map(Object::toString).sorted().toList())));
        } catch (Exception exception) {
            LOG.error("Could not export registry audit", exception);
        }
    }

    @SubscribeEvent
    public void login(PlayerEvent.PlayerLoggedInEvent event) {
        VoiceGuard.forget(event.getEntity().getUUID());
        if (event.getEntity() instanceof ServerPlayer player) {
            UPDATE_GATE.begin(player);
            AUTH.attach(player);
        }
    }

    @SubscribeEvent
    public void logout(PlayerEvent.PlayerLoggedOutEvent event) {
        if(event.getEntity() instanceof ServerPlayer player)PROFILES.logout(player);
        greeted.remove(event.getEntity().getUUID());
        VoiceGuard.forget(event.getEntity().getUUID());
        PROGRESSION.detach(event.getEntity().getUUID());
        if(event.getEntity() instanceof ServerPlayer player){AUTH.detach(player);MOD_SYNC.detach(player);UPDATE_GATE.detach(player);}
    }

    @SubscribeEvent
    public void unauthenticatedDamage(LivingAttackEvent event) {
        if(event.getEntity() instanceof ServerPlayer player && !AUTH.authenticated(player))event.setCanceled(true);
    }

    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        var server = event.getServer();
        UPDATE_GATE.tick(server);
        VoiceGuard.refresh(server);
        worldTools.tick(server);
        EXPEDITIONS.tick(server);
        PROFILES.tick();
        if(server.getTickCount()%20==0){COMMUNITY.tick();BOSSES.tick(server);MAINTENANCE.tick();}
        if(server.getTickCount()%5==0){
            for(ServerPlayer player:server.getPlayerList().getPlayers())AUTH.protectPosition(player);
            MOD_SYNC.tick(server);
        }
        if (server.getTickCount() % 20 != 0) return;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            if (!AUTH.ready()) {
                player.connection.disconnect(Component.literal("Virgos-MC está en mantenimiento de autenticación."));
            } else if (AUTH.authenticated(player) && greeted.add(player.getUUID())) {
                player.sendSystemMessage(Component.literal("§6Bienvenido a Virgos-MC. §fJ abre tus misiones; /virgos menu reúne la ayuda de progreso, bases y pueblo.").withStyle(s->s.withClickEvent(new net.minecraft.network.chat.ClickEvent(net.minecraft.network.chat.ClickEvent.Action.RUN_COMMAND,"/virgos menu"))));
            }
        }
    }

    @SubscribeEvent
    public void stopping(ServerStoppingEvent event) {
        PROFILES.stopping();
        worldTools.saveProgress();
        EXPEDITIONS.stopping();
        greeted.clear();
        MOD_SYNC.clear();
        VoiceGuard.clear();
    }

    @SubscribeEvent
    public void commands(RegisterCommandsEvent event) {
        var root = Commands.literal("virgos").executes(context -> {
            var player = context.getSource().getPlayer();
            if (player != null && !AUTH.authenticated(player)) return 0;
            context.getSource().sendSuccess(() -> Component.literal("§6Virgos-MC§r\nMisiones [J] · Mapa [M] · Bases [P] · Mochila [B]\nVoz [O], hablar con Bloq Mayús. Teclas configurables en Controles.\nReclamá las recompensas del códice para activar tus rangos.\nEl Bastión tiene cuatro salidas caminando; la arena está al sur.\n"),false);
            for(var link:Map.of("[Guía paso a paso]","/virgos guia","[Proteger mi base]","/virgos guia bases","[Mi progreso]","/virgos progreso","[Expediciones]","/virgos expedicion","[Proyectos del pueblo]","/virgos pueblo").entrySet())
                context.getSource().sendSuccess(()->Component.literal("§b"+link.getKey()).withStyle(style->style.withClickEvent(new net.minecraft.network.chat.ClickEvent(net.minecraft.network.chat.ClickEvent.Action.RUN_COMMAND,link.getValue()))),false);
            return 1;
        });
        root.then(Commands.literal("status").requires(source -> source.hasPermission(2)).executes(context -> {
            context.getSource().sendSuccess(() -> Component.literal("AuthMe=" + AUTH.ready() + "; payloads bloqueados=" + AUTH.blockedPayloads() + "; movimientos bloqueados="+AUTH.blockedMovement()+"; " + PROGRESSION.status()+"; "+EXPEDITIONS.status()+"; "+VoiceGuard.status()+"; "+COMMUNITY.status()+"; "+MAINTENANCE.status()+"; "+worldTools.status()), false);
            return 1;
        }));
        root.then(Commands.literal("progreso").executes(context->PROGRESSION.describe(context.getSource())));
        root.then(PlayerGuide.command("guia"));
        root.then(PROFILES.command("perfil"));
        root.then(PlayerGuide.command("ayuda"));
        root.then(Commands.literal("menu").executes(c->TownServices.menu(c.getSource())));
        root.then(TOWN.commands());
        root.then(TOWN.adminCommands());
        root.then(Commands.literal("checkpoint").requires(source->source.hasPermission(2)).executes(context->MAINTENANCE.request(context.getSource())));
        root.then(EXPEDITIONS.commands());
        root.then(COMMUNITY.commands());
        root.then(Commands.literal("audit").requires(source -> source.hasPermission(2)).executes(context -> worldTools.audit(context.getSource()))
            .then(Commands.argument("template",StringArgumentType.word()).executes(context->worldTools.audit(context.getSource(),StringArgumentType.getString(context,"template")))));
        root.then(Commands.literal("terrain").requires(source -> source.hasPermission(2))
            .then(Commands.argument("x", IntegerArgumentType.integer(-29000000, 29000000))
            .then(Commands.argument("z", IntegerArgumentType.integer(-29000000, 29000000))
            .then(Commands.argument("radius", IntegerArgumentType.integer(16, 256))
            .then(Commands.argument("step", IntegerArgumentType.integer(1, 32)).executes(context ->
                worldTools.scan(context.getSource(), IntegerArgumentType.getInteger(context, "x"), IntegerArgumentType.getInteger(context, "z"), IntegerArgumentType.getInteger(context, "radius"), IntegerArgumentType.getInteger(context, "step"))))))));
        root.then(Commands.literal("build").requires(source -> source.hasPermission(2)).executes(context -> worldTools.build(context.getSource()))
            .then(Commands.argument("template",StringArgumentType.word()).executes(context -> worldTools.build(context.getSource(),StringArgumentType.getString(context,"template")))));
        root.then(Commands.literal("survey").requires(source -> source.hasPermission(2))
            .then(Commands.argument("x", IntegerArgumentType.integer(-29000000, 29000000))
            .then(Commands.argument("z", IntegerArgumentType.integer(-29000000, 29000000))
            .then(Commands.argument("radius", IntegerArgumentType.integer(16, 4096))
            .then(Commands.argument("step", IntegerArgumentType.integer(4, 128)).executes(context ->
                worldTools.survey(context.getSource(), IntegerArgumentType.getInteger(context, "x"), IntegerArgumentType.getInteger(context, "z"), IntegerArgumentType.getInteger(context, "radius"), IntegerArgumentType.getInteger(context, "step"))))))));
        event.getDispatcher().register(root);
        event.getDispatcher().register(PROFILES.command("perfil"));
        event.getDispatcher().register(PROFILES.command("estadisticas"));
    }
}
