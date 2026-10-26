package mc.virgos.forestry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Standalone public-interface probes; no Bukkit, world, or user data. */
public final class JournalTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Path file = Path.of(args[0]).resolve("journal.tsv");
        Journal journal = new Journal(file);
        check(journal.healthy(), "fresh journal healthy");
        String group = journal.prepare("owner", "world", "DARK_OAK_SAPLING", List.of("0,64,0", "0,64,1", "1,64,0", "1,64,1"));
        byte[] prepared = Files.readAllBytes(file);
        check(journal.prepare("owner", "world", "DARK_OAK_SAPLING", List.of("0,64,0")) == null, "overlap denied");
        check(java.util.Arrays.equals(prepared, Files.readAllBytes(file)), "reject preserves bytes");
        check(journal.reserve(group, "OAK_SAPLING", 20) == 0, "wrong species untouched");
        check(journal.reserve(group, "DARK_OAK_SAPLING", 2) == 2, "own drops preferred");
        journal = new Journal(file);
        check(journal.reserve(group, "DARK_OAK_SAPLING", 9) == 2, "remaining minimum only after restart");
        check(journal.reserve(group, "DARK_OAK_SAPLING", 9) == 0, "no extra loot consumed");
        journal.complete(group, "0,64,0");
        journal = new Journal(file);
        check(journal.groups().get(0).pending().size() == 3, "partial placement durable");
        journal.markPlaced("world:4,64,4", true);
        check(new Journal(file).knownPlaced("world:4,64,4"), "direct placement durable");
        journal.markPlaced("world:4,64,4", false);
        check(!journal.knownPlaced("world:4,64,4"), "growth clears stale marker");
        Files.writeString(file, "corrupt");
        Journal broken = new Journal(file);
        check(!broken.healthy(), "corruption fail closed");
        byte[] before = Files.readAllBytes(file);
        check(broken.prepare("a", "b", "OAK_SAPLING", List.of("0,0,0")) == null, "unhealthy denies");
        check(java.util.Arrays.equals(before, Files.readAllBytes(file)), "failed operation leaves data unchanged");
        System.out.println("Journal PASS: reservation, restart, idempotency, provenance, reject hash");
    }
}
