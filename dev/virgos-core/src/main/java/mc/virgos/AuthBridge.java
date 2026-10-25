package mc.virgos;

import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.util.ReferenceCountUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundCustomPayloadPacket;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerAbilitiesPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Method;
import java.util.UUID;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** AuthMe API calls only occur on the server thread, never Netty's event loop. */
public final class AuthBridge {
    private Object api;
    private Method getPlayer;
    private Method isAuthenticated;
    private boolean ready;
    private final AtomicInteger blockedPayloads = new AtomicInteger();
    private final AtomicInteger blockedMovement = new AtomicInteger();
    private record Anchor(ServerLevel level,double x,double y,double z,float yaw,float pitch) {}
    private final Map<UUID,Anchor> anchors=new HashMap<>();

    public void initialize(MinecraftServer server) {
        if (!server.isDedicatedServer()) return;
        try {
            Class<?> bukkit = Class.forName("org.bukkit.Bukkit");
            Object manager = bukkit.getMethod("getPluginManager").invoke(null);
            Object plugin = Class.forName("org.bukkit.plugin.PluginManager")
                .getMethod("getPlugin", String.class).invoke(manager, "AuthMe");
            if (plugin == null) throw new IllegalStateException("AuthMe is missing");
            Class<?> type = Class.forName("fr.xephi.authme.api.v3.AuthMeApi", true, plugin.getClass().getClassLoader());
            api = type.getMethod("getInstance").invoke(null);
            isAuthenticated = type.getMethod("isAuthenticated", Class.forName("org.bukkit.entity.Player"));
            getPlayer = bukkit.getMethod("getPlayer", UUID.class);
            ready = true;
            VirgosCore.LOG.info("Virgos: AuthMe bridge ready; mod payload guard enabled");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            ready = false;
            VirgosCore.LOG.error("Virgos: authentication bridge unavailable; player access will be refused", exception);
        }
    }

    public boolean authenticated(ServerPlayer player) {
        if (!player.server.isSameThread()) throw new IllegalStateException("AuthMe accessed off server thread");
        if (VirgosCore.UPDATE_GATE == null || !VirgosCore.UPDATE_GATE.accepted(player)) return false;
        if (!ready) return false;
        try {
            Object bukkitPlayer = getPlayer.invoke(null, player.getUUID());
            return bukkitPlayer != null && Boolean.TRUE.equals(isAuthenticated.invoke(api, bukkitPlayer));
        } catch (ReflectiveOperationException exception) {
            ready = false;
            VirgosCore.LOG.error("Virgos: AuthMe API failed; refusing gameplay", exception);
            return false;
        }
    }

    public void attach(ServerPlayer player) {
        if (!ready) {
            player.connection.disconnect(Component.literal("Virgos-MC está en mantenimiento de autenticación."));
            return;
        }
        var channel = player.connection.connection.channel();
        anchor(player);
        // A joined player has already completed Forge's LOGIN handshake. PLAY
        // custom payloads contain mod actions and must pass AuthMe as well.
        channel.eventLoop().execute(() -> {
            if (channel.pipeline().get("virgos_auth") != null) return;
            channel.pipeline().addBefore("packet_handler", "virgos_auth", new ChannelInboundHandlerAdapter() {
                private final PreAuthPayloads preAuth = new PreAuthPayloads();
                private final AtomicInteger pending = new AtomicInteger();

                @Override
                public void channelRead(ChannelHandlerContext context, Object message) throws Exception {
                    if(message instanceof ServerboundMovePlayerPacket || message instanceof ServerboundPlayerInputPacket || message instanceof ServerboundPlayerAbilitiesPacket) {
                        if(pending.incrementAndGet()>128){pending.decrementAndGet();context.close();return;}
                        player.server.execute(()->{
                            try {
                                if(!player.connection.connection.isConnected() || !authenticated(player)){blockedMovement.incrementAndGet();return;}
                                if(message instanceof ServerboundMovePlayerPacket packet)packet.handle(player.connection);
                                else if(message instanceof ServerboundPlayerInputPacket packet)packet.handle(player.connection);
                                else if(message instanceof ServerboundPlayerAbilitiesPacket packet)packet.handle(player.connection);
                            } finally {pending.decrementAndGet();}
                        });
                        return;
                    }
                    if (!(message instanceof ServerboundCustomPayloadPacket payload)) {
                        super.channelRead(context, message);
                        return;
                    }
                    if (pending.incrementAndGet() > 128) {
                        pending.decrementAndGet();
                        ReferenceCountUtil.safeRelease(payload.getData());
                        context.close();
                        return;
                    }
                    player.server.execute(() -> {
                        try {
                            // Only bounded, single-use compatibility/release handshakes may
                            // precede AuthMe. Release acceptance still goes through UPDATE_GATE;
                            // movement, mod actions and voice audio remain authentication-gated.
                            boolean allowedHello = preAuth.allow(payload.getIdentifier().toString(), payload.getData());
                            if (!player.connection.connection.isConnected() || (!authenticated(player)&&!allowedHello)) {
                                blockedPayloads.incrementAndGet();
                                ReferenceCountUtil.safeRelease(payload.getData());
                                return;
                            }
                            // handle() dispatches to Ketting/Forge and releases its buffer.
                            // Executing here makes the auth check and mod dispatch ordered
                            // with login/logout commands on the same server thread.
                            payload.handle(player.connection);
                        } catch (Exception exception) {
                            if (payload.getData().refCnt() > 0) ReferenceCountUtil.safeRelease(payload.getData());
                            VirgosCore.LOG.warn("Virgos: rejected malformed custom payload from {} on {}", player.getScoreboardName(), payload.getIdentifier(), exception);
                            player.connection.disconnect(Component.literal("Paquete de mod inválido. Reconectá con el paquete Virgos-MC."));
                        } finally {
                            pending.decrementAndGet();
                        }
                    });
                }
            });
        });
    }

    private Anchor anchor(ServerPlayer player) {
        return anchors.computeIfAbsent(player.getUUID(),ignored->{
            if(player.getY()<player.level().getMinBuildHeight()) {
                var level=player.server.overworld();var spawn=level.getSharedSpawnPos();
                return new Anchor(level,spawn.getX()+.5,spawn.getY(),spawn.getZ()+.5,level.getSharedSpawnAngle(),0);
            }
            return new Anchor(player.serverLevel(),player.getX(),player.getY(),player.getZ(),player.getYRot(),player.getXRot());
        });
    }

    /** Keep a real position while AuthMe temporarily changes flight abilities. */
    public void protectPosition(ServerPlayer player) {
        boolean authenticated=authenticated(player);
        Anchor position=authenticated ? anchors.remove(player.getUUID()) : anchor(player);
        if(position==null)return;
        if(authenticated)VirgosCore.MOD_SYNC.authenticated(player);
        if(!player.isAlive())return;
        player.setDeltaMovement(Vec3.ZERO);player.fallDistance=0;
        player.teleportTo(position.level,position.x,position.y,position.z,position.yaw,position.pitch);
        if(authenticated && player.isSpectator()) {
            player.getAbilities().mayfly=true;player.getAbilities().flying=true;player.onUpdateAbilities();
        }
    }

    public void detach(ServerPlayer player){anchors.remove(player.getUUID());}

    public boolean ready() { return ready; }
    public int blockedPayloads() { return blockedPayloads.get(); }
    public int blockedMovement() { return blockedMovement.get(); }
}
