package mc.virgos.forestry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

/** Unchanged public v1 command sequence, runnable against both diagnostic .1 and .2. */
public final class JournalDifferentialProbe {
    public static void main(String[] args) throws Exception {
        Path file = Path.of(args[0]).resolve("journal.tsv");
        Journal journal = new Journal(file);
        String id = journal.prepare("owner", "world", "DARK_OAK_SAPLING", List.of("0,64,0", "0,64,1", "1,64,0", "1,64,1"));
        System.out.println("overlap-rejected=" + (journal.prepare("owner", "world", "OAK_SAPLING", List.of("0,64,0")) == null));
        byte[] before = Files.readAllBytes(file);
        System.out.println("wrong-seed=" + journal.reserve(id, "OAK_SAPLING", 12));
        System.out.println("reject-hash=" + Arrays.equals(before, Files.readAllBytes(file)));
        System.out.println("reserve=" + journal.reserve(id, "DARK_OAK_SAPLING", 2));
        journal = new Journal(file);
        System.out.println("remaining=" + journal.groups().get(0).unreserved());
        journal.complete(id, "0,64,0");
        journal.markPlaced("world:8,64,8", true);
        journal = new Journal(file);
        System.out.println("pending=" + journal.groups().get(0).pending());
        System.out.println("material=" + journal.groups().get(0).material());
        System.out.println("placed=" + journal.knownPlaced("world:8,64,8"));
    }
}
