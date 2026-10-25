package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

import java.util.concurrent.atomic.AtomicInteger;

/** Reuse the same allocation sequence as native direct/partial payload construction. */
@Mixin(value = FullDataPayload.class, remap = false)
public interface FullDataPayloadIdAccessor {
    @Accessor(value = "lastBufferId", remap = false)
    static AtomicInteger virgos$lastBufferId() {
        throw new AssertionError("Native payload ID accessor was not transformed");
    }
}
