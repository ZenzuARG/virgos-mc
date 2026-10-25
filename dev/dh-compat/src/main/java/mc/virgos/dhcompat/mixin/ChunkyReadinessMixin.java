package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.wrapperInterfaces.modAccessor.AbstractChunkyAccessor;
import mc.virgos.dhcompat.ChunkyReadiness;
import net.minecraftforge.fml.ModList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Dedicated-server guard before DH permanently marks its Chunky listener bound. */
@Mixin(value = AbstractChunkyAccessor.class, remap = false)
public abstract class ChunkyReadinessMixin {
    @Shadow private boolean listenerBound;

    @Inject(method = "tryRunFirstTimeSetup()V", at = @At("HEAD"), cancellable = true,
        require = 1, remap = false)
    private void virgos$waitForChunkyProvider(CallbackInfo callback) {
        if (!listenerBound
            && getClass().getName().equals("com.seibel.distanthorizons.forge.wrappers.modAccessor.ChunkyAccessor")
            && ModList.get().isLoaded("chunky")
            && !ChunkyReadiness.providerReady(getClass().getClassLoader())) {
            callback.cancel();
        }
    }
}
