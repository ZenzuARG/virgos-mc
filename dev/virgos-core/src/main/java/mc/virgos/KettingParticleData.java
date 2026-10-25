package mc.virgos;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;

/** Narrow exception for the particle serializer's polymorphic value contract. */
public final class KettingParticleData {
    private KettingParticleData() {}

    public static boolean compatible(SynchedEntityData.DataItem<?> item, Object replacement) {
        return compatible(item.getAccessor().getSerializer() == EntityDataSerializers.PARTICLE,
            item.getValue(), replacement);
    }

    static boolean compatible(boolean particleSerializer, Object current, Object replacement) {
        return particleSerializer
            && current instanceof ParticleOptions
            && replacement instanceof ParticleOptions;
    }
}
