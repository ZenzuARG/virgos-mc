package mc.virgos.qa.trace;

import mc.virgos.qa.DhPayloadTrace;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.core.multiplayer.client.ClientNetworkState", remap = false)
public abstract class ClientNetworkStateTraceMixin {
    @Inject(method = "<init>()V", at = @At("RETURN"), require = 1, remap = false)
    private void virgos$bind(CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.bind(this);
    }
}
