package mc.virgos.dhcompat.mixin;

import io.netty.channel.Channel;
import io.netty.channel.ChannelConfig;
import mc.virgos.dhcompat.OrderedInitialization;
import net.minecraft.network.Connection;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Pin the 1.20.1 runtime member: do not redirect disconnect/read controls. */
@Mixin(value = Connection.class, remap = false)
public abstract class ConnectionMixin {
    @Shadow private Channel f_129468_;

    @Redirect(
        method = "m_129520_(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketSendListener;)V",
        at = @At(value = "INVOKE", target = "Lio/netty/channel/ChannelConfig;setAutoRead(Z)Lio/netty/channel/ChannelConfig;"),
        require = 1, remap = false)
    private ChannelConfig virgos$orderProtocolReadTransition(ChannelConfig config, boolean autoRead) {
        var loop = f_129468_.eventLoop();
        OrderedInitialization.onEventLoop(loop::inEventLoop, loop::execute, () -> config.setAutoRead(autoRead));
        return config;
    }
}
