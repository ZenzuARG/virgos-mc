package mc.virgos.forestry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

public final class AlternativeJournalTest {
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        Path file = Path.of(args[0]).resolve("alternatives.tsv");
        Journal journal = new Journal(file);
        List<String> alternatives = List.of("minecraft:azalea", "minecraft:flowering_azalea");
        String id = journal.prepareDeclared("owner", "world", alternatives.get(0), List.of("0,64,0"), alternatives);
        byte[] before = Files.readAllBytes(file);
        check(journal.reserve(id, "minecraft:oak_sapling", 9) == 0, "oak is not a declared azalea seed");
        check(Arrays.equals(before, Files.readAllBytes(file)), "wrong seed leaves bytes unchanged");
        check(journal.reserve(id, "minecraft:flowering_azalea", 4) == 1, "prefer own valid flowering drop, minimum only");
        journal = new Journal(file);
        check(journal.groups().get(0).material().equals("minecraft:flowering_azalea"), "choice survives restart");
        check(journal.groups().get(0).alternatives().equals(alternatives), "preserve all allowed alternatives");
        before = Files.readAllBytes(file);
        check(journal.reserve(id, "minecraft:azalea", 9) == 0, "selected group stays coherent");
        check(Arrays.equals(before, Files.readAllBytes(file)), "unconsumed alternative leaves bytes unchanged");
        journal.complete(id, "0,64,0");
        String fallback = journal.prepareDeclared("owner", "world", alternatives.get(0), List.of("1,64,0"), alternatives);
        journal.seal(fallback);
        journal = new Journal(file);
        check(journal.groups().get(0).selected() && journal.groups().get(0).material().equals("minecraft:azalea"), "declared no-drop fallback persists");
        check(Files.readString(file).startsWith("forestry-journal-v2\n"), "explicit storage version");
        System.out.println("AlternativeJournal PASS: own-drop-first, coherent alternatives, fallback, restart and rejected hash");
    }
}
