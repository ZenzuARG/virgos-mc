package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.client.ClientNetworkState;
import com.seibel.distanthorizons.core.world.DhClientWorld;
import mc.virgos.dhcompat.DeferredConfigWorld;
import mc.virgos.dhcompat.OrderedInitialization;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = DhClientWorld.class, remap = false)
public abstract class DhClientWorldMixin implements DeferredConfigWorld {
    @Unique private OrderedInitialization.InitialConfig virgos$initialConfig;
    @Unique private ClientNetworkState virgos$networkState;

    @Redirect(method = "<init>", at = @At(value = "INVOKE",
        target = "Lcom/seibel/distanthorizons/core/multiplayer/client/ClientNetworkState;sendConfigMessage()V"),
        require = 1, remap = false)
    private void virgos$deferInitialConfig(ClientNetworkState state) {
        // Mixin field initializers run at constructor return, after this call site.
        if (virgos$initialConfig == null) virgos$initialConfig = new OrderedInitialization.InitialConfig();
        virgos$networkState = state;
        virgos$initialConfig.defer(state::sendConfigMessage);
    }

    @Inject(method = "<init>", at = @At("RETURN"), require = 1, remap = false)
    private void virgos$sendInitialConfigAfterConstruction(CallbackInfo callback) {
        // The old publication callback could be skipped when SharedApi replaced the
        // world during login. DH must advertise the client config before requesting
        // any local LOD work, otherwise the client stays permanently not-ready.
        if (virgos$networkState != null) virgos$networkState.sendConfigMessage();
    }

    @Override public void virgos$sendInitialConfig() {
        if (virgos$initialConfig != null) virgos$initialConfig.published();
    }
}
