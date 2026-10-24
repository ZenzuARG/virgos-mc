package mc.virgos;

import de.maxhenkel.voicechat.api.ForgeVoicechatPlugin;
import de.maxhenkel.voicechat.api.VoicechatPlugin;
import de.maxhenkel.voicechat.api.VoicechatConnection;
import de.maxhenkel.voicechat.api.events.*;
import net.minecraft.server.MinecraftServer;
import java.util.Set;
import java.util.HashSet;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;

/** UDP workers only read an immutable snapshot. AuthMe stays on the game thread. */
@ForgeVoicechatPlugin
public final class VoiceGuard implements VoicechatPlugin {
    private static volatile Set<UUID> authenticated=Set.of();
    private static volatile boolean registered;
    private static volatile de.maxhenkel.voicechat.api.VoicechatServerApi api;
    private static final AtomicLong blocked=new AtomicLong();
    public String getPluginId(){return "virgos_auth_voice";}
    public void registerEvents(EventRegistration events) {
        events.registerEvent(MicrophonePacketEvent.class,event->{if(!allowed(event.getSenderConnection())){event.cancel();blocked.incrementAndGet();}});
        events.registerEvent(EntitySoundPacketEvent.class,VoiceGuard::filter);
        events.registerEvent(LocationalSoundPacketEvent.class,VoiceGuard::filter);
        events.registerEvent(StaticSoundPacketEvent.class,VoiceGuard::filter);
        events.registerEvent(VoicechatServerStartedEvent.class,event->api=event.getVoicechat());
        registered=true;
        VirgosCore.LOG.info("Virgos: voice authentication guard registered");
    }
    private static boolean allowed(VoicechatConnection connection){return connection!=null&&authenticated.contains(connection.getPlayer().getUuid());}
    private static void filter(PacketEvent<?> event) {
        if(!allowed(event.getReceiverConnection())||(event.getSenderConnection()!=null&&!allowed(event.getSenderConnection()))){event.cancel();blocked.incrementAndGet();}
    }
    public static void refresh(MinecraftServer server) {
        var ready=new HashSet<UUID>();
        for(var player:server.getPlayerList().getPlayers())if(VirgosCore.AUTH.authenticated(player))ready.add(player.getUUID());
        authenticated=Set.copyOf(ready);
    }
    public static void forget(UUID id){var next=new HashSet<>(authenticated);next.remove(id);authenticated=Set.copyOf(next);}
    public static void clear(){authenticated=Set.of();}
    public static void authenticated(net.minecraft.server.level.ServerPlayer player){
        try {
            Object events=Class.forName("de.maxhenkel.voicechat.Voicechat").getField("SERVER").get(null);
            if(events!=null&&Boolean.TRUE.equals(events.getClass().getMethod("isCompatible",UUID.class).invoke(events,player.getUUID())))
                events.getClass().getMethod("initializePlayerConnection",net.minecraft.server.level.ServerPlayer.class).invoke(events,player);
        }catch(ReflectiveOperationException error){VirgosCore.LOG.error("Voice synchronization after authentication failed",error);}
    }
    public static String status(){
        long connected=api==null?0:authenticated.stream().filter(id->{var c=api.getConnectionOf(id);return c!=null&&c.isConnected();}).count();
        return "vozAuth="+registered+"; vozConectados="+connected+"; vozBloqueada="+blocked.get();
    }
}
