package mc.virgos.qa.trace;

import mc.virgos.qa.DhPayloadTrace;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayloadReceiver", remap = false)
public abstract class FullDataPayloadReceiverTraceMixin {
    private static final String RECEIVE = "receiveChunk(Lcom/seibel/distanthorizons/core/network/messages/fullData/FullDataSplitMessage;)V";
    private static final String DECODE = "decodeDataSource(Lcom/seibel/distanthorizons/core/multiplayer/fullData/FullDataPayload;)Lcom/seibel/distanthorizons/core/sql/dto/FullDataSourceV2DTO;";
    private static final String COMPUTE = "lambda$receiveChunk$0(Lcom/seibel/distanthorizons/core/network/messages/fullData/FullDataSplitMessage;Ljava/lang/Integer;Lio/netty/buffer/CompositeByteBuf;)Lio/netty/buffer/CompositeByteBuf;";

    @Inject(method = RECEIVE, at = @At("HEAD"), require = 1, remap = false)
    private void virgos$fragment(@Coerce Object message, CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.fragment(this, message);
    }
    @Inject(method = RECEIVE, at = @At("RETURN"), require = 1, remap = false)
    private void virgos$fragmentReturn(@Coerce Object message, CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.fragmentReturn();
    }
    @Inject(method = COMPUTE, at = @At("HEAD"), require = 1, remap = false)
    private static void virgos$existing(@Coerce Object message, Integer key, @Coerce Object composite,
                                       CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.compute(composite, "native_compute_before");
    }
    @Inject(method = COMPUTE, at = @At("RETURN"), require = 1, remap = false)
    private static void virgos$assembled(@Coerce Object message, Integer key, @Coerce Object composite,
                                        CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.compute(callback.getReturnValue(), "native_compute_return");
    }
    @Inject(method = DECODE, at = @At("HEAD"), require = 1, remap = false)
    private void virgos$decode(@Coerce Object payload, CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.decode(this, payload);
    }
    @ModifyArg(method = DECODE, at = @At(value = "INVOKE", target = "Ljava/util/Objects;requireNonNull(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;"), index = 0, require = 1, remap = false)
    private Object virgos$nativeLookup(Object value) {
        return DhPayloadTrace.observeNativeLookup(value);
    }
    @Inject(method = DECODE, at = @At(value = "INVOKE", target = "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;"), require = 1, remap = false)
    private void virgos$remove(@Coerce Object payload, CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.remove(this, payload);
    }
    @Inject(method = DECODE, at = @At(value = "INVOKE", target = "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;", shift = At.Shift.AFTER), require = 1, remap = false)
    private void virgos$removed(@Coerce Object payload, CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.removed(this, payload);
    }
    @Inject(method = DECODE, at = @At("RETURN"), require = 1, remap = false)
    private void virgos$decoded(@Coerce Object payload, CallbackInfoReturnable<Object> callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.decoded();
    }
    @Inject(method = "close()V", at = @At("HEAD"), require = 1, remap = false)
    private void virgos$close(CallbackInfo callback) {
        if (DhPayloadTrace.enabled()) DhPayloadTrace.closed(this);
    }
}
