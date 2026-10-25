package mc.virgos.qa.trace;

import mc.virgos.qa.DhPayloadTrace;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.core.multiplayer.client.AbstractFullDataNetworkRequestQueue", remap = false)
public abstract class FullDataRequestQueueTraceMixin {
    @Inject(method = "handleNetResponse(Lcom/seibel/distanthorizons/core/multiplayer/client/AbstractFullDataNetworkRequestQueue$NetRequestTask;Lcom/seibel/distanthorizons/core/network/messages/fullData/FullDataSourceResponseMessage;Ljava/lang/Throwable;)V", at = @At("HEAD"), require = 1, remap = false)
    private void virgos$compression(@Coerce Object request, @Coerce Object response,
                                    Throwable failure, CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.compression(this, request, response);
    }
}
