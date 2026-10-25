package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;
import mc.virgos.dhcompat.payload.PayloadOwnership;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;

@Mixin(value = FullDataPayload.class, remap = false)
public abstract class FullDataPayloadMixin implements PayloadOwnership.Payload {
    @Unique private final transient PayloadOwnership.Slot virgos$leaseSlot = new PayloadOwnership.Slot();
    @Override public PayloadOwnership.Slot virgos$slot() { return virgos$leaseSlot; }
}
