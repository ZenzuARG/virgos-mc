package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.generation.queues.RemoteWorldRetrievalQueue;
import com.seibel.distanthorizons.core.generation.tasks.DataSourceRetrievalResult;
import com.seibel.distanthorizons.core.generation.tasks.ERetrievalResultState;
import com.seibel.distanthorizons.core.pos.DhSectionPos;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Keeps the native "LODs left" estimate live as remote requests complete. */
@Mixin(value = RemoteWorldRetrievalQueue.class, remap = false)
public abstract class RemoteWorldRetrievalQueueMixin {
    @Shadow private long estimatedTotalChunkCount;

    @Inject(method = "lambda$submitRetrievalTask$0(JJLcom/seibel/distanthorizons/core/generation/tasks/DataSourceRetrievalResult;)V",
            at = @At("HEAD"), require = 1, remap = false)
    private void virgos$decrementEstimate(long startedAt, long sectionPos,
                                           DataSourceRetrievalResult result, CallbackInfo callback) {
        if (result.state != ERetrievalResultState.SUCCESS) return;
        long completed = (long) DhSectionPos.getChunkWidth(sectionPos) * DhSectionPos.getChunkWidth(sectionPos);
        synchronized (this) {
            estimatedTotalChunkCount = Math.max(0L, estimatedTotalChunkCount - completed);
        }
    }
}
