package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.fullData.*;
import io.netty.buffer.CompositeByteBuf;
import java.util.concurrent.ConcurrentMap;
import mc.virgos.dhcompat.payload.PayloadOwnership;
import org.spongepowered.asm.mixin.*;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(value = FullDataPayloadReceiver.class, remap = false)
public abstract class FullDataPayloadReceiverMixin implements PayloadOwnership.Receiver, mc.virgos.dhcompat.payload.RequestedPayloadReceiver {
    @Shadow @Final private ConcurrentMap<Integer, CompositeByteBuf> buffersById;
    @Unique private final PayloadOwnership.Owner virgos$receiverOwner = new PayloadOwnership.Owner();
    @Override public PayloadOwnership.Owner virgos$owner() { return virgos$receiverOwner; }

    @Unique public Runnable virgos$claim(FullDataPayload payload) {
        return PayloadOwnership.claim(this, (PayloadOwnership.Payload) payload,
                () -> buffersById.remove(payload.dtoBufferId));
    }

    @Redirect(method = "decodeDataSource", at = @At(value = "INVOKE",
            target = "Ljava/util/concurrent/ConcurrentMap;get(Ljava/lang/Object;)Ljava/lang/Object;"),
            require = 1, remap = false)
    private Object virgos$completedBuffer(ConcurrentMap<?, ?> map, Object key, FullDataPayload payload) {
        return PayloadOwnership.lookup(this, (PayloadOwnership.Payload) payload, () -> map.get(key));
    }

    @Redirect(method = "decodeDataSource", at = @At(value = "INVOKE",
            target = "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;"),
            require = 2, remap = false)
    private Object virgos$removeOnlyUnclaimed(ConcurrentMap<?, ?> map, Object key, FullDataPayload payload) {
        return PayloadOwnership.remove((PayloadOwnership.Payload) payload, () -> map.remove(key));
    }

    @Inject(method = "close", at = @At("HEAD"), require = 1, remap = false)
    private void virgos$invalidateReceiver(CallbackInfo callback) { virgos$receiverOwner.close(); }
}
