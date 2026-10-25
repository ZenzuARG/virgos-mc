package mc.virgos.mixin;

import mc.virgos.KettingParticleData;
import net.minecraft.network.syncher.SynchedEntityData;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Preserve Ketting's validation except for valid particle-option subtype changes. */
@Pseudo
@Mixin(targets = "org.kettingpowered.ketting.utils.EntityDataUtils", remap = false)
public final class KettingParticleDataMixin {
    private KettingParticleDataMixin() {}

    @Inject(method = "classesMatch", at = @At("HEAD"), cancellable = true, require = 1, remap = false)
    private static void virgos$allowParticleOptions(SynchedEntityData.DataItem<?> item,
                                                   Object replacement,
                                                   CallbackInfoReturnable<Boolean> callback) {
        if (KettingParticleData.compatible(item, replacement)) callback.setReturnValue(true);
    }
}
