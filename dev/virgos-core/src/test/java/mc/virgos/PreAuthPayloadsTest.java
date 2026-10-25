package mc.virgos;

import io.netty.buffer.Unpooled;
import net.minecraft.network.FriendlyByteBuf;

public final class PreAuthPayloadsTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static FriendlyByteBuf hello() {
        var data = new FriendlyByteBuf(Unpooled.buffer());
        data.writeVarInt(0);
        data.writeUtf("2.0.0-r11", 160);
        data.writeUtf("virgos-client-2.0.0-r11", 160);
        return data;
    }

    public static void main(String[] args) {
        var guard = new PreAuthPayloads();
        var data = hello();
        try {
            int index = data.readerIndex();
            check(guard.allow("virgos:update", data), "Release hello must reach validation before authentication");
            check(data.readerIndex() == index && data.refCnt() == 1, "Inspection must not consume or release payload");
            check(!guard.allow("virgos:update", data), "Repeated pre-auth hello must be blocked");
            check(new PreAuthPayloads().allow("virgos:update", data), "Reconnect needs independent handshake state");
            check(!new PreAuthPayloads().allow("heracles:action", data), "Gameplay remains blocked");
            data.writeByte(1);
            check(!new PreAuthPayloads().allow("virgos:update", data), "Trailing bytes must be blocked");
            data.writerIndex(data.writerIndex() - 1);
            data.setByte(0, 1);
            check(!new PreAuthPayloads().allow("virgos:update", data), "Unknown discriminator must be blocked");
            data.clear().writeByte(0);
            data.writeVarInt(481);
            check(!new PreAuthPayloads().allow("virgos:update", data), "Invalid string length must be blocked");
            data.clear();
            check(!new PreAuthPayloads().allow("virgos:update", data), "Empty hello must be blocked");
            data.writeZero(1_000);
            check(!new PreAuthPayloads().allow("virgos:update", data), "Oversized hello must be blocked");
            data.clear().writeInt(1);
            check(guard.allow("voicechat:request_secret", data), "Existing voice compatibility hello must pass");
            check(!guard.allow("voicechat:request_secret", data), "Voice hello remains single-use");
            data.writeByte(1);
            check(!new PreAuthPayloads().allow("voicechat:request_secret", data), "Voice payload size stays bounded");
        } finally {
            data.release();
        }
        System.out.println("Pre-auth payloads: release, reconnect, malformed frames and voice checks passed");
    }
}
