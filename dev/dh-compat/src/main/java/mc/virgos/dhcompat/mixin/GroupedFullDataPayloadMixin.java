package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;
import com.seibel.distanthorizons.core.multiplayer.server.FullDataSourceRequestHandler;
import mc.virgos.dhcompat.GroupedPayloads;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Change the loop-local payload before both fragment sending and final-response capture. */
@Mixin(value = FullDataSourceRequestHandler.class, remap = false)
public abstract class GroupedFullDataPayloadMixin {
    @ModifyVariable(
        method = "lambda$tick$0(Lcom/seibel/distanthorizons/core/multiplayer/server/DataSourceRequestGroup;Ljava/util/Map$Entry;)V",
        at = @At(value = "INVOKE", ordinal = 0,
            target = "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;"),
        index = 3, require = 1, remap = false)
    private FullDataPayload virgos$uniqueGroupedResponse(FullDataPayload encoded) {
        return GroupedPayloads.forResponse(encoded);
    }
}
