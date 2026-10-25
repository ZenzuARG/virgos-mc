package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.client.*;
import com.seibel.distanthorizons.core.network.messages.fullData.FullDataSourceResponseMessage;
import java.util.concurrent.*;
import java.util.function.BiFunction;
import mc.virgos.dhcompat.payload.*;
import org.spongepowered.asm.mixin.*;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(value = AbstractFullDataNetworkRequestQueue.class, remap = false)
public abstract class FullDataRequestQueueMixin {
    @Shadow @Final public ClientNetworkState networkState;

    @Redirect(method = "sendNextRequest", at = @At(value = "INVOKE",
            target = "Ljava/util/concurrent/CompletableFuture;handleAsync(Ljava/util/function/BiFunction;Ljava/util/concurrent/Executor;)Ljava/util/concurrent/CompletableFuture;"),
            require = 1, remap = false)
    private CompletableFuture<Object> virgos$handoff(CompletableFuture<FullDataSourceResponseMessage> source,
            BiFunction<FullDataSourceResponseMessage, Throwable, Object> callback, Executor executor) {
        return PayloadOwnership.handleAsync(source, callback, executor, response -> response.payload == null
                ? () -> { }
                : ((RequestedPayloadReceiver) networkState.fullDataPayloadReceiver).virgos$claim(response.payload));
    }
}
