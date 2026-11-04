package mc.virgos;

import net.minecraft.network.FriendlyByteBuf;
import mc.virgos.update.UpdateProtocol;

/** Connection-local allowlist; this never grants gameplay authentication. */
public final class PreAuthPayloads {
    private boolean voiceHandshakeSeen;
    private boolean clientHandshakeSeen;
    private static final int MAX_HELLO_BYTES = 1 + 2 * (2 + 160 * 3);
    private static final int MAX_DH_PAYLOAD_BYTES = 64 * 1024;

    public boolean allow(String channel, FriendlyByteBuf data) {
        if (!voiceHandshakeSeen && channel.equals("voicechat:request_secret") && data.readableBytes() == 4) {
            voiceHandshakeSeen = true;
            return true;
        }
        if (!clientHandshakeSeen && channel.equals("virgos:update") && isClientHello(data)) {
            clientHandshakeSeen = true;
            return true;
        }
        if (channel.equals("distant_horizons:msg")) {
            return allowDistantHorizonsPayload(data);
        }
        return false;
    }

    private boolean allowDistantHorizonsPayload(FriendlyByteBuf data) {
        if (data.readableBytes() < 3 || data.readableBytes() > MAX_DH_PAYLOAD_BYTES) return false;
        var view = new FriendlyByteBuf(data.duplicate());
        try {
            // Forge DH uses a one-byte protocol version followed by a two-byte message id.
            // DH messages are read-only LOD negotiation/data requests; allowing the bounded
            // channel before AuthMe is required so the client can complete serverReady and
            // request the server snapshot before the user runs /login.
            return view.readUnsignedByte() == 16;
        } catch (RuntimeException malformed) {
            return false;
        }
    }

    private static boolean isClientHello(FriendlyByteBuf data) {
        if (data.readableBytes() == 0 || data.readableBytes() > MAX_HELLO_BYTES) return false;
        // Inspect a borrowed view; Forge still owns and decodes the original buffer.
        var view = new FriendlyByteBuf(data.duplicate());
        try {
            if (view.readUnsignedByte() != 0) return false; // ClientHello discriminator.
            UpdateProtocol.ClientHello.decode(view);
            return !view.isReadable();
        } catch (RuntimeException malformed) {
            return false;
        }
    }
}
