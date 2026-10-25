package mc.virgos.dhcompat;

import com.seibel.distanthorizons.api.enums.worldGeneration.EDhApiDistantGeneratorMode;
import com.seibel.distanthorizons.api.enums.worldGeneration.EDhApiGeneratorPlan;

/** Existing-data requests do not compete with Chunky's missing-terrain generation. */
public final class ChunkyLodServingPolicy {
    private ChunkyLodServingPolicy() { }

    public static boolean preserveCachedServing(boolean dedicatedServer,
        EDhApiDistantGeneratorMode mode, EDhApiGeneratorPlan configuredPlan) {
        return dedicatedServer && mode == EDhApiDistantGeneratorMode.PRE_EXISTING_ONLY
            && configuredPlan == EDhApiGeneratorPlan.CHUNKS_ONLY;
    }
}
