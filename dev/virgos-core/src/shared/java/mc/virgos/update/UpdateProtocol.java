package mc.virgos.update;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Consumer;
import java.util.function.Supplier;

/** Client-to-server release handshake. The protocol version is separate from the release fingerprint. */
public final class UpdateProtocol {
    private static final String PROTOCOL = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
        new ResourceLocation("virgos", "update"), () -> PROTOCOL,
        PROTOCOL::equals, PROTOCOL::equals);
    private static boolean registered;

    private UpdateProtocol() {}

    public record ClientHello(String release, String fingerprint) {
        public static void encode(ClientHello value, FriendlyByteBuf buffer) {
            buffer.writeUtf(value.release == null ? "" : value.release, 160);
            buffer.writeUtf(value.fingerprint == null ? "" : value.fingerprint, 160);
        }

        public static ClientHello decode(FriendlyByteBuf buffer) {
            return new ClientHello(buffer.readUtf(160), buffer.readUtf(160));
        }
    }

    public static synchronized void register(Consumer<Context> receiver) {
        if (registered) return;
        CHANNEL.messageBuilder(ClientHello.class, 0, NetworkDirection.PLAY_TO_SERVER)
            .encoder(ClientHello::encode)
            .decoder(ClientHello::decode)
            .consumerMainThread((message, context) -> {
                receiver.accept(new Context(message, context));
                context.get().setPacketHandled(true);
            })
            .add();
        registered = true;
    }

    public record Context(ClientHello hello, Supplier<NetworkEvent.Context> network) {}
}
