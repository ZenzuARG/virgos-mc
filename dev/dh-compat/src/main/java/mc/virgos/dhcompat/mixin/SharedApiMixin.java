package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.api.internal.SharedApi;
import com.seibel.distanthorizons.core.world.AbstractDhWorld;
import mc.virgos.dhcompat.DeferredConfigWorld;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = SharedApi.class, remap = false)
public abstract class SharedApiMixin {
    @Inject(method = "setDhWorld", at = @At("RETURN"), require = 1, remap = false)
    private static void virgos$afterWorldPublished(AbstractDhWorld world, CallbackInfo callback) {
        if (world instanceof DeferredConfigWorld deferred && SharedApi.getAbstractDhWorld() == world) {
            deferred.virgos$sendInitialConfig();
        }
    }
}
