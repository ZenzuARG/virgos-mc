package mc.virgos;

import java.util.UUID;
import java.util.function.BooleanSupplier;
import java.util.function.Supplier;

/** Pure admission and postcondition checks for the personal-claim menu action. */
public final class ClaimEntryFlow {
    public enum State { FREE, OWNED, OTHER, UNAVAILABLE }
    public enum Result { OWNED, STALE, DENIED, FAILED }
    public record Target(String dimension, int x, int z, State state) {
        public boolean sameChunk(Target other) {
            return other != null && dimension.equals(other.dimension) && x == other.x && z == other.z;
        }
    }

    private ClaimEntryFlow() {}

    public static State classify(boolean present, UUID owner, UUID player) {
        if (!present) return State.FREE;
        if (owner == null) return State.UNAVAILABLE;
        return owner.equals(player) ? State.OWNED : State.OTHER;
    }

    public static boolean personalModeAllowed(boolean administrative, boolean personal, UUID player,
                                               UUID impersonated, UUID claimOwner) {
        return !administrative && personal && player != null
            && (impersonated == null || player.equals(impersonated))
            && (claimOwner == null || player.equals(claimOwner));
    }

    public static Result claim(Target opened, Supplier<Target> lookup, BooleanSupplier admitted,
                               Runnable nativeClaim) {
        try {
            if (!admitted.getAsBoolean()) return Result.DENIED;
            Target before = lookup.get();
            if (opened.state() != State.FREE || !opened.sameChunk(before) || before.state() != State.FREE)
                return Result.STALE;
            nativeClaim.run();
            Target after = lookup.get();
            return opened.sameChunk(after) && after.state() == State.OWNED ? Result.OWNED : Result.FAILED;
        } catch (RuntimeException failure) {
            return Result.FAILED;
        }
    }
}
