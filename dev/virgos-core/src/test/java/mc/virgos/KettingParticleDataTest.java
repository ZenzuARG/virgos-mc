package mc.virgos;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.SimpleParticleType;
import org.joml.Vector3f;

public final class KettingParticleDataTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        // Registry initialization requires the Forge launcher. Exercise the pure
        // predicate here; the serializer adapter is checked in an isolated server.
        var simple = new SimpleParticleType(false) {};
        var dust = new DustParticleOptions(new Vector3f(0, 1, 0), 2);
        check(KettingParticleData.compatible(true, simple, dust), "Simple-to-dust particle change must pass");
        check(KettingParticleData.compatible(true, dust, simple),
            "Dust-to-simple particle change must pass");
        check(KettingParticleData.compatible(true, simple, simple), "Same particle type remains valid");
        check(!KettingParticleData.compatible(true, simple, "invalid"), "Unrelated replacement must not bypass Ketting");
        check(!KettingParticleData.compatible(false, 1, 2), "Other serializers must retain the original guard");
        check(!KettingParticleData.compatible(false, simple, dust), "Particles cannot bypass a nonparticle serializer");
        check(!KettingParticleData.compatible(true, null, dust),
            "Null handling must remain with Ketting");
        check(!KettingParticleData.compatible(true, simple, null), "Null replacement must retain Ketting handling");
        System.out.println("Ketting particle data: polymorphism, serializer isolation and nonmutation checks passed");
    }
}
