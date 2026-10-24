package mc.virgos;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.chat.Component;
import net.minecraftforge.fml.ModList;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Restart OPAC's read-only initial sync after AuthMe permits mod packets.
 * No unauthenticated gameplay packet is queued or replayed.
 */
public final class ModResync {
    private Object packetHandler;
    private Method send, playerData, hasMod, setHasMod, serverData, loginHandler, resync;
    private Constructor<?> handshake;
    private int networkVersion;
    private boolean ready;
    private final Map<UUID,Integer> pending=new HashMap<>();

    public void initialize() {
        if(!ModList.get().isLoaded("openpartiesandclaims"))return;
        try {
            Class<?> mod=Class.forName("xaero.pac.OpenPartiesAndClaims");
            packetHandler=mod.getMethod("getPacketHandler").invoke(mod.getField("INSTANCE").get(null));
            send=Class.forName("xaero.pac.common.packet.IPacketHandler").getMethod("sendToPlayer",ServerPlayer.class,Object.class);
            handshake=Class.forName("xaero.pac.common.packet.ServerLoginHandshakePacket").getConstructor(int.class);
            networkVersion=Class.forName("xaero.pac.common.packet.util.PacketConstants").getField("NETWORK_VERSION").getInt(null);
            Class<?> playerType=Class.forName("xaero.pac.common.server.player.data.ServerPlayerData");
            playerData=Class.forName("xaero.pac.common.server.player.data.api.ServerPlayerDataAPI").getMethod("from",ServerPlayer.class);
            hasMod=playerType.getMethod("hasMod");setHasMod=playerType.getMethod("setHasMod",boolean.class);
            serverData=Class.forName("xaero.pac.common.server.ServerData").getMethod("from",MinecraftServer.class);
            Class<?> serverType=Class.forName("xaero.pac.common.server.IServerData");
            loginHandler=serverType.getMethod("getPlayerLoginHandler");
            resync=Class.forName("xaero.pac.common.server.player.PlayerLoginHandler").getMethod("handlePostWorldJoin",ServerPlayer.class,serverType);
            ready=true;
        } catch(ReflectiveOperationException exception) {
            VirgosCore.LOG.error("Virgos: OPAC post-authentication sync unavailable",exception);
        }
    }

    public void authenticated(ServerPlayer player) {
        VoiceGuard.authenticated(player);
        if(!ready)return;
        try {
            Object data=playerData.invoke(null,player);
            setHasMod.invoke(data,false);
            send.invoke(packetHandler,player,handshake.newInstance(networkVersion));
            pending.put(player.getUUID(),player.server.getTickCount()+200);
        }catch(ReflectiveOperationException exception) {
            VirgosCore.LOG.error("Virgos: could not restart claim sync for {}",player.getScoreboardName(),exception);
        }
    }

    public void tick(MinecraftServer server) {
        var iterator=pending.entrySet().iterator();
        while(iterator.hasNext()) {
            var entry=iterator.next();
            ServerPlayer player=server.getPlayerList().getPlayer(entry.getKey());
            if(player==null || !VirgosCore.AUTH.authenticated(player)){iterator.remove();continue;}
            try {
                if(Boolean.TRUE.equals(hasMod.invoke(playerData.invoke(null,player)))) {
                    Object data=serverData.invoke(null,server);
                    resync.invoke(loginHandler.invoke(data),player,data);
                    VirgosCore.LOG.info("Virgos: OPAC resynchronized after authentication for {}",player.getScoreboardName());
                    iterator.remove();
                }else if(server.getTickCount()>entry.getValue()) {
                    player.sendSystemMessage(Component.literal("§cNo se pudo sincronizar el mapa de claims. Reconectá con el paquete Virgos-MC."));
                    VirgosCore.LOG.warn("Virgos: OPAC post-auth handshake timeout for {}",player.getScoreboardName());
                    iterator.remove();
                }
            }catch(ReflectiveOperationException exception) {
                VirgosCore.LOG.error("Virgos: claim resynchronization failed",exception);
                iterator.remove();
            }
        }
    }

    public void detach(ServerPlayer player){pending.remove(player.getUUID());}
    public void clear(){pending.clear();}
}
