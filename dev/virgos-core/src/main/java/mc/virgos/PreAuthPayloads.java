package mc.virgos;

import net.minecraft.network.FriendlyByteBuf;
import mc.virgos.update.UpdateProtocol;

/** Connection-local allowlist; this never grants gameplay authentication. */
public final class PreAuthPayloads {
    private boolean voiceHandshakeSeen;
    private boolean clientHandshakeSeen;
    private boolean dhSessionConfigSeen;
    private boolean dhLevelInitRequestSeen;
    private static final int MAX_HELLO_BYTES = 1 + 2 * (2 + 160 * 3);
    private static final int MAX_DH_HANDSHAKE_BYTES = 8 * 1024;

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
            return allowDistantHorizonsHandshake(data);
        }
        return false;
    }

    private boolean allowDistantHorizonsHandshake(FriendlyByteBuf data) {
        if (data.readableBytes() < 3 || data.readableBytes() > MAX_DH_HANDSHAKE_BYTES) return false;
        var view = new FriendlyByteBuf(data.duplicate());
        try {
            // Forge DH uses a one-byte protocol version followed by a two-byte message id.
            if (view.readUnsignedByte() != 16) return false;
            int messageId = view.readUnsignedShort();
            if (messageId == 4 && !dhSessionConfigSeen) {
                dhSessionConfigSeen = true;
                return true;
            }
            if (messageId == 3 && !dhLevelInitRequestSeen) {
                dhLevelInitRequestSeen = true;
                return true;
            }
        } catch (RuntimeException malformed) {
            return false;
        }
        return false;
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
