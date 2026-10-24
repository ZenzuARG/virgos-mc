package mc.virgos.profile;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;
import java.util.function.Consumer;

/** One bounded, server-to-client snapshot. All queries use authenticated commands. */
public final class ProfileProtocol {
    public static final SimpleChannel CHANNEL=NetworkRegistry.newSimpleChannel(
        new ResourceLocation("virgos","profile"),()->"1",
        version->version.equals("1")||version.equals(NetworkRegistry.ABSENT)||version.equals(NetworkRegistry.ACCEPTVANILLA),
        version->version.equals("1")||version.equals(NetworkRegistry.ABSENT)||version.equals(NetworkRegistry.ACCEPTVANILLA));
    public record Snapshot(String json) {
        public static void encode(Snapshot value,FriendlyByteBuf buffer){buffer.writeUtf(value.json,32767);}
        public static Snapshot decode(FriendlyByteBuf buffer){return new Snapshot(buffer.readUtf(32767));}
    }
    public static void register(Consumer<String> receiver){
        CHANNEL.messageBuilder(Snapshot.class,0,NetworkDirection.PLAY_TO_CLIENT)
            .encoder(Snapshot::encode).decoder(Snapshot::decode)
            .consumerMainThread((message,context)->{receiver.accept(message.json());context.get().setPacketHandled(true);}).add();
    }
}
