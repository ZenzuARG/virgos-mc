package mc.virgos.update;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Rejection callbacks may remove players or synchronously trigger logout. */
public final class ClientUpdateTimeoutTest {
    public static void main(String[] args) {
        UUID expired = UUID.randomUUID(), fresh = UUID.randomUUID();
        Map<UUID, Long> pending = new HashMap<>();
        pending.put(expired, 0L);
        pending.put(fresh, 9_999L);
        int[] rejected = {0};
        ClientUpdateServer.expirePending(pending, 10_000L, id -> {
            if (!id.equals(expired)) throw new AssertionError("Fresh client rejected");
            rejected[0]++;
            pending.remove(id);
            pending.remove(fresh); // A disconnect callback may detach another entry.
        });
        if (rejected[0] != 1 || !pending.isEmpty()) throw new AssertionError("Timeout cleanup failed");
        pending.put(fresh, 10_000L);
        ClientUpdateServer.expirePending(pending, 19_999L, id -> {
            throw new AssertionError("Validation window shortened");
        });
        if (!pending.containsKey(fresh)) throw new AssertionError("Pending client lost");
        System.out.println("Client update timeout: reentrant cleanup and grace checks passed");
    }
}
