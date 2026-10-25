package mc.virgos.qa.trace;

import mc.virgos.qa.DhPayloadTrace;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.core.network.session.NetworkSession", remap = false)
public abstract class NetworkSessionTraceMixin {
    @Inject(method = "tryHandleMessage(Lcom/seibel/distanthorizons/core/network/messages/AbstractNetworkMessage;)V", at = @At("HEAD"), require = 1, remap = false)
    private void virgos$arrival(@Coerce Object message, CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.arrival(this, message);
    }
}
