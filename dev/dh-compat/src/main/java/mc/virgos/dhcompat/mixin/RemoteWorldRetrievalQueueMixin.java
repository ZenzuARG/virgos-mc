package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.generation.queues.RemoteWorldRetrievalQueue;
import com.seibel.distanthorizons.core.generation.tasks.DataSourceRetrievalResult;
import com.seibel.distanthorizons.core.generation.tasks.ERetrievalResultState;
import com.seibel.distanthorizons.core.pos.DhSectionPos;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;

/** Keeps the native "LODs left" estimate live as remote requests complete. */
@Mixin(value = RemoteWorldRetrievalQueue.class, remap = false)
public abstract class RemoteWorldRetrievalQueueMixin {
    @Shadow private long estimatedTotalChunkCount;
    @Unique private static final Set<CompletableFuture<?>> virgos$trackedRequests =
            Collections.newSetFromMap(new WeakHashMap<>());

    @Inject(method = "submitRetrievalTask(JB)Ljava/util/concurrent/CompletableFuture;",
            at = @At("RETURN"), require = 1, remap = false)
    private void virgos$trackTerminalRequest(long sectionPos, byte requiredDetail,
                                              CallbackInfoReturnable<CompletableFuture<DataSourceRetrievalResult>> callback) {
        CompletableFuture<DataSourceRetrievalResult> future = callback.getReturnValue();
        if (future == null) return;
        synchronized (virgos$trackedRequests) {
            if (!virgos$trackedRequests.add(future)) return;
        }
        future.whenComplete((result, error) -> {
            if (error instanceof CancellationException) return;
            // A split is not complete: DH replaces the parent section with
            // child requests, whose own terminal completions account for the
            // same chunk area. Every other terminal result must advance the
            // estimate, including a failed request, or the HUD stays frozen.
            if (result != null && result.state == ERetrievalResultState.REQUIRES_SPLITTING) return;
            if (result == null && error == null) return;
            long completedSection = result == null ? sectionPos : result.pos;
            long width = DhSectionPos.getChunkWidth(completedSection);
            long completed = width * width;
            synchronized (this) {
                estimatedTotalChunkCount = Math.max(0L, estimatedTotalChunkCount - completed);
            }
        });
    }
}
