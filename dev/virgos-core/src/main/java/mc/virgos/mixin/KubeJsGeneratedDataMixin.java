package mc.virgos.mixin;

import com.mojang.logging.LogUtils;
import dev.latvian.mods.kubejs.util.Lazy;
import java.io.InputStream;
import java.util.concurrent.atomic.AtomicBoolean;
import mc.virgos.KubeJsGeneratedStreams;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Serialize only reads and invalidation of the same generated-resource cache. */
@Pseudo
@Mixin(targets = "dev.latvian.mods.kubejs.script.data.GeneratedData", remap = false)
public abstract class KubeJsGeneratedDataMixin {
    @Unique private static final AtomicBoolean virgos$reported = new AtomicBoolean();
    @Shadow(remap = false) public abstract Lazy<byte[]> data();
    @Shadow(remap = false) public abstract boolean alwaysForget();

    @Inject(method = "get()Ljava/io/InputStream;", at = @At("HEAD"), cancellable = true, require = 1, remap = false)
    private void virgos$openGeneratedResource(CallbackInfoReturnable<InputStream> callback) {
        Lazy<byte[]> cache = data();
        InputStream stream = KubeJsGeneratedStreams.open(cache, cache::forget, alwaysForget());
        if (virgos$reported.compareAndSet(false, true))
            LogUtils.getLogger().info("Virgos: synchronized KubeJS generated-resource streams active");
        callback.setReturnValue(stream);
    }
}
