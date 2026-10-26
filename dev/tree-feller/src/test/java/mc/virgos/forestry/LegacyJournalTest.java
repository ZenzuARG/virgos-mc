package mc.virgos.forestry;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Base64;
import java.util.HexFormat;

public final class LegacyJournalTest {
    private static String encoded(String value) { return Base64.getUrlEncoder().withoutPadding().encodeToString(value.getBytes(StandardCharsets.UTF_8)); }
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        Path file = Path.of(args[0]).resolve("legacy.tsv");
        String body = encoded("group:old") + "\t" + encoded("owner;world;DARK_OAK_SAPLING;0;0,64,0/0,64,1") + "\n"
            + encoded("placed:world:8,64,8") + "\t" + encoded("1") + "\n";
        String checksum = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body.getBytes(StandardCharsets.UTF_8)));
        Files.writeString(file, checksum + "\n" + body);
        byte[] before = Files.readAllBytes(file);
        Journal journal = new Journal(file);
        check(journal.healthy() && journal.groups().size() == 1 && journal.knownPlaced("world:8,64,8"), "legacy intents and markers read");
        check(journal.groups().get(0).material().equals("DARK_OAK_SAPLING") && journal.groups().get(0).selected(), "do not reinterpret legacy species");
        check(Arrays.equals(before, Files.readAllBytes(file)), "read must not silently migrate file");
        check(journal.reserve("old", "minecraft:azalea", 1) == 0 && Arrays.equals(before, Files.readAllBytes(file)), "legacy reject unchanged");
        journal.complete("old", "0,64,0");
        journal = new Journal(file);
        check(journal.healthy() && journal.groups().get(0).pending().equals(java.util.List.of("0,64,1")), "accepted mutation preserves pending legacy state");
        check(journal.knownPlaced("world:8,64,8") && Files.readString(file).startsWith("forestry-journal-v2\n"), "explicit v2 snapshot preserves markers");
        System.out.println("LegacyJournal PASS: v1 read/reject byte-stable; accepted v2 write preserves pending state");
    }
}
