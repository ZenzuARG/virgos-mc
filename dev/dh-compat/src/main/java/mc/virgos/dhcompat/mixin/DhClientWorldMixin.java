package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.client.ClientNetworkState;
import com.seibel.distanthorizons.core.world.DhClientWorld;
import mc.virgos.dhcompat.DeferredConfigWorld;
import mc.virgos.dhcompat.OrderedInitialization;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(value = DhClientWorld.class, remap = false)
public abstract class DhClientWorldMixin implements DeferredConfigWorld {
    @Unique private OrderedInitialization.InitialConfig virgos$initialConfig;

    @Redirect(method = "<init>", at = @At(value = "INVOKE",
        target = "Lcom/seibel/distanthorizons/core/multiplayer/client/ClientNetworkState;sendConfigMessage()V"),
        require = 1, remap = false)
    private void virgos$deferInitialConfig(ClientNetworkState state) {
        // Mixin field initializers run at constructor return, after this call site.
        if (virgos$initialConfig == null) virgos$initialConfig = new OrderedInitialization.InitialConfig();
        virgos$initialConfig.defer(state::sendConfigMessage);
    }

    @Override public void virgos$sendInitialConfig() {
        if (virgos$initialConfig != null) virgos$initialConfig.published();
    }
}
