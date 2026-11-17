package mc.virgos;

import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/** Deterministic claim-menu action checks without a Minecraft client or server. */
public final class ClaimEntryFlowTest {
    private static final ClaimEntryFlow.Target FREE = target("overworld", 4, 7, ClaimEntryFlow.State.FREE);

    public static void main(String[] args) {
        UUID self = UUID.randomUUID();
        UUID foreign = UUID.randomUUID();
        require(ClaimEntryFlow.personalModeAllowed(false, true, self, null, null), "Default personal mode is admitted");
        require(ClaimEntryFlow.personalModeAllowed(false, true, self, self, self), "Explicit self target is admitted");
        require(!ClaimEntryFlow.personalModeAllowed(true, true, self, null, null), "Administrative modes cannot bypass limits");
        require(!ClaimEntryFlow.personalModeAllowed(false, false, self, null, null), "Server and party modes are not personal claims");
        require(!ClaimEntryFlow.personalModeAllowed(false, true, self, foreign, null), "Foreign impersonation is rejected before mutation");
        require(!ClaimEntryFlow.personalModeAllowed(false, true, self, null, foreign), "Foreign native claim target is rejected");
        require(ClaimEntryFlow.classify(false, null, self) == ClaimEntryFlow.State.FREE, "Missing claim is free");
        require(ClaimEntryFlow.classify(true, null, self) == ClaimEntryFlow.State.UNAVAILABLE, "Missing owner fails closed");
        require(ClaimEntryFlow.classify(true, self, self) == ClaimEntryFlow.State.OWNED, "Existing own claim remains owned");
        require(ClaimEntryFlow.classify(true, UUID.randomUUID(), self) == ClaimEntryFlow.State.OTHER, "Foreign claim stays foreign");
        var current = new AtomicReference<>(FREE);
        var calls = new AtomicInteger();
        var result = ClaimEntryFlow.claim(FREE, current::get, () -> true, () -> {
            calls.incrementAndGet();
            current.set(target("overworld", 4, 7, ClaimEntryFlow.State.OWNED));
        });
        require(result == ClaimEntryFlow.Result.OWNED && calls.get() == 1, "Successful native claim opens permissions");
        result = ClaimEntryFlow.claim(FREE, current::get, () -> true, calls::incrementAndGet);
        require(result == ClaimEntryFlow.Result.STALE && calls.get() == 1, "Repeated claim must not run again");
        for (var denied : new ClaimEntryFlow.Target[] {
                target("overworld", 4, 7, ClaimEntryFlow.State.OTHER),
                target("overworld", 4, 7, ClaimEntryFlow.State.UNAVAILABLE),
                target("overworld", 5, 7, ClaimEntryFlow.State.FREE),
                target("nether", 4, 7, ClaimEntryFlow.State.FREE)}) {
            current.set(denied);
            result = ClaimEntryFlow.claim(FREE, current::get, () -> true, calls::incrementAndGet);
            require(result == ClaimEntryFlow.Result.STALE && calls.get() == 1, "Stale or unavailable target cannot mutate claims");
        }
        current.set(FREE);
        result = ClaimEntryFlow.claim(FREE, current::get, () -> false, calls::incrementAndGet);
        require(result == ClaimEntryFlow.Result.DENIED && calls.get() == 1, "Authentication or personal-mode rejection prevents native call");
        result = ClaimEntryFlow.claim(FREE, current::get, () -> true, () -> {});
        require(result == ClaimEntryFlow.Result.FAILED, "Native limit or permission denial must not open permissions");
        result = ClaimEntryFlow.claim(FREE, current::get, () -> true,
            () -> current.set(target("overworld", 4, 7, ClaimEntryFlow.State.OTHER)));
        require(result == ClaimEntryFlow.Result.FAILED, "Foreign postcondition must not open permissions");
        result = ClaimEntryFlow.claim(FREE, () -> FREE, () -> true, () -> { throw new IllegalStateException("fixture"); });
        require(result == ClaimEntryFlow.Result.FAILED, "Native failure stays closed");
        System.out.println("Claim entry: target, admission, native delegation and ownership postconditions PASS");
    }

    private static ClaimEntryFlow.Target target(String dimension, int x, int z, ClaimEntryFlow.State state) {
        return new ClaimEntryFlow.Target(dimension, x, z, state);
    }

    private static void require(boolean valid, String message) {
        if (!valid) throw new AssertionError(message);
    }
}
