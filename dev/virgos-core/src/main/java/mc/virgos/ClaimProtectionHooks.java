package mc.virgos;

import java.util.Objects;
import java.util.UUID;
import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;

/** One volatile immutable binding prevents resolver/authentication pairs from tearing. */
public final class ClaimProtectionHooks {
    @FunctionalInterface
    public interface Resolver {
        ClaimPermissionDecision resolve(UUID actor, ResourceLocation dimension, BlockPos target, String permissionId);
    }

    public record Binding(Resolver resolver, Predicate<ServerPlayer> authenticated) {
        public ClaimPermissionDecision resolve(ServerPlayer actor, ResourceLocation dimension,
                                               BlockPos target, String permissionId) {
            try {
                ClaimPermissionDecision decision = resolver.resolve(actor.getUUID(), dimension, target, permissionId);
                if (decision == null) return ClaimPermissionDecision.DENY;
                if (decision == ClaimPermissionDecision.ALLOW && !authenticated.test(actor))
                    return ClaimPermissionDecision.DENY;
                return decision;
            } catch (RuntimeException unavailable) {
                return ClaimPermissionDecision.DENY;
            }
        }
    }

    private static volatile Binding binding = new Binding((actor, dimension, target, permission) -> ClaimPermissionDecision.NATIVE,
        actor -> false);

    private ClaimProtectionHooks() {}

    public static void bind(Resolver resolver, Predicate<ServerPlayer> authenticated) {
        binding = new Binding(Objects.requireNonNull(resolver), Objects.requireNonNull(authenticated));
    }

    public static Binding snapshot() { return binding; }
}
