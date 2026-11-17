package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

/** File-backed regression tests, always confined to a caller-owned external fixture. */
public final class ClaimPolicyStoreTest {
    public static void main(String[] args) throws Exception {
        Path root = args.length == 0 ? Files.createTempDirectory("virgos-policy-store-") : Path.of(args[0]);
        System.out.println("SCRATCH=" + root);
        Files.createDirectories(root);
        nativeRetention(root.resolve("native-retention"));
        Path legacy = root.resolve("legacy.json"), current = root.resolve("v2.json");
        UUID owner = UUID.randomUUID();
        var a = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 4, 7, "main");
        var b = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 5, 7, "main");
        var c = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 6, 7, "custom");
        JsonObject old = new JsonObject();
        JsonObject inherited = policy(true);
        inherited.addProperty("future-field", "retain");
        old.add(a.legacy(), inherited);
        old.add(c.legacy(), policy(false));
        Files.writeString(legacy, old.toString());
        byte[] original = Files.readAllBytes(legacy);
        ClaimPolicyStore store = new ClaimPolicyStore();
        require(store.load(current, legacy), "Valid legacy file loads");
        require(storage(store.policy(a)) && storage(store.policy(b)), "Legacy policy is a read-only default for both chunks");
        require(!store.areaId(a).equals(store.areaId(b)), "Touching chunks are distinct areas by default");
        require(!Files.exists(current), "Loading never writes a migration");
        require(store.edit(a, row -> setStorage(row, false)), "First parcel edit commits");
        require(!storage(store.policy(a)) && storage(store.policy(b)), "One parcel edit cannot alter its neighbor");
        require(java.util.Arrays.equals(original, Files.readAllBytes(legacy)), "Legacy file remains byte-identical");
        require(store.policy(a).get("future-field").getAsString().equals("retain"), "Unknown policy fields survive copy-on-write");
        require(store.join(a, b, false, key -> true), "Explicit join can retain the selected area's policy");
        require(store.areaId(a).equals(store.areaId(b)) && storage(store.policy(a)), "Joined chunks share the chosen policy");
        require(store.edit(a, row -> setStorage(row, false)) && !storage(store.policy(b)), "Editing an explicitly joined area affects its members");
        require(store.split(b), "A chunk can split from a joined area");
        require(!store.areaId(a).equals(store.areaId(b)) && !storage(store.policy(b)), "Splitting preserves permissions before independent edits");
        require(store.edit(b, row -> setStorage(row, true)) && !storage(store.policy(a)), "Split chunk edits remain independent");
        require(store.join(a, c, true, key -> true), "Same-owner chunks may join across native subconfigurations");
        require(store.areaId(a).equals(store.areaId(c)) && !storage(store.policy(c)), "Explicit retention works for either area");
        byte[] before = Files.readAllBytes(current);
        JsonObject memory = store.snapshot();
        var foreign = new ClaimPolicyStore.Key(UUID.randomUUID(), a.dimension(), 7, 7, "main");
        var dimension = new ClaimPolicyStore.Key(owner, "minecraft:the_nether", 4, 7, "main");
        require(!store.join(a, foreign, true, key -> true), "Foreign owners cannot join areas");
        require(!store.join(a, dimension, true, key -> true), "Areas cannot silently span dimensions");
        require(!store.join(a, b, true, key -> !key.equals(b)), "Ownership is checked before joining");
        require(java.util.Arrays.equals(before, Files.readAllBytes(current)) && memory.equals(store.snapshot()), "Rejected operations preserve bytes and memory");
        ClaimPolicyStore failing = new ClaimPolicyStore((path, content) -> { throw new java.io.IOException("fixture write failure"); });
        require(failing.load(current, legacy), "Failure fixture loads");
        JsonObject failedBefore = failing.snapshot();
        require(!failing.edit(a, row -> setStorage(row, true)), "Failed replacement is reported");
        require(!failing.join(a, b, true, key -> true) && !failing.split(c), "Area operations use the same atomic writer");
        require(java.util.Arrays.equals(before, Files.readAllBytes(current)) && failedBefore.equals(failing.snapshot()), "Failed writes cannot publish policy or binding changes");
        ClaimPolicyStore restarted = new ClaimPolicyStore();
        require(restarted.load(current, legacy) && restarted.areaId(a).equals(restarted.areaId(c))
            && storage(restarted.policy(b)) && !storage(restarted.policy(a)), "Area bindings and permissions survive reload");
        Files.writeString(current, "{broken");
        byte[] broken = Files.readAllBytes(current);
        require(!restarted.load(current, legacy) && !restarted.healthy(), "Malformed policy fails closed");
        require(!restarted.edit(a, row -> setStorage(row, true)) && restarted.policy(a) == null, "Corrupt load cannot grant or overwrite");
        require(java.util.Arrays.equals(broken, Files.readAllBytes(current)), "Corrupt bytes remain untouched for recovery");
        Files.delete(current);
        Files.writeString(legacy, "{\"" + a.legacy() + "\":{\"groups\":{\"amigos\":{\"permissions\":{\"storage\":\"yes\"}}}}}");
        require(!restarted.load(current, legacy) && !restarted.edit(a, row -> {}), "Malformed legacy values also block writes");
        System.out.println("Claim policy store: parcel isolation, join/split, atomic failures and reload PASS");
    }

    private static void nativeRetention(Path root) throws Exception {
        Files.createDirectories(root);
        var owner = UUID.randomUUID();
        var a = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 0, 0, "main");
        var b = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 1, 0, "main");
        Path current = root.resolve("v2.json"), legacy = root.resolve("legacy.json");
        var store = new ClaimPolicyStore();
        require(store.load(current, legacy) && store.policy(a) == null, "Fresh parcel uses native policy");
        require(store.join(a, b, true, key -> true), "Fresh chunks can join");
        require(store.policy(a) == null && store.policy(b) == null,
            "Joining native-only chunks preserves native permissions, not managed denials");
        UUID actor = UUID.randomUUID();
        require(nativeDecisions(store, a, actor) && nativeDecisions(store, b, actor),
            "Joined native-only chunks delegate every category at the enforcement decision boundary");
        require(store.split(b) && nativeDecisions(store, b, actor), "Splitting native-only area preserves native decisions");
        require(store.edit(a, row -> {}), "Explicit empty policy can be configured");
        require(ClaimPolicyRules.decision(store.policy(a), actor, "storage") == ClaimPermissionDecision.DENY,
            "Explicit empty policy is distinct from native-only policy");
        require(store.join(a, b, false, key -> true) && nativeDecisions(store, a, actor),
            "Retaining second native area replaces first managed policy without inventing denials");
        JsonObject configured = policy(true);
        configured.getAsJsonObject("groups").getAsJsonObject("amigos").add("members",
            JsonParser.parseString("[{\"id\":\"" + actor + "\",\"name\":\"Offline\"}]"));
        configured.getAsJsonObject("individuals").add(actor.toString(),
            JsonParser.parseString("{\"permissions\":{\"storage\":\"DENY\",\"doors\":\"ALLOW\"}}"));
        require(store.edit(a, row -> configured.entrySet().forEach(e -> row.add(e.getKey(), e.getValue()))),
            "Configure shared group and individual permissions");
        require(store.split(b) && configured.equals(store.policy(a)) && configured.equals(store.policy(b)),
            "Split copies group roster and individual exceptions exactly");
        require(store.edit(b, row -> setStorage(row, false)) && configured.equals(store.policy(a)),
            "Split mutations cannot alter the original area");
        require(store.join(a, b, true, key -> true) && configured.equals(store.policy(b)),
            "Retaining configured area preserves complete policy");
        require(ClaimPolicyRules.decision(store.policy(b), actor, "storage") == ClaimPermissionDecision.DENY
            && ClaimPolicyRules.decision(store.policy(b), actor, "doors") == ClaimPermissionDecision.ALLOW,
            "Retained individual exceptions still override group permissions");
        require(store.split(b), "Separate configured chunk for restart");
        var fresh = new ClaimPolicyStore.Key(owner, "minecraft:overworld", 2, 0, "main");
        require(store.split(fresh), "A standalone native chunk also preserves its policy when split");
        var restarted = new ClaimPolicyStore();
        require(restarted.load(current, legacy) && configured.equals(restarted.policy(a))
            && configured.equals(restarted.policy(b)) && nativeDecisions(restarted, fresh, actor),
            "Reload preserves native-only bindings and all copied configured permissions");
    }

    private static boolean nativeDecisions(ClaimPolicyStore store, ClaimPolicyStore.Key key, UUID actor) {
        return ClaimPolicyRules.PERMISSIONS.stream().allMatch(permission ->
            ClaimPolicyRules.decision(store.policy(key), actor, permission) == ClaimPermissionDecision.NATIVE);
    }

    private static JsonObject policy(boolean value) {
        return JsonParser.parseString("{\"groups\":{\"amigos\":{\"members\":[],\"permissions\":{\"storage\":" + value + "}}},\"individuals\":{}}").getAsJsonObject();
    }
    private static void setStorage(JsonObject row, boolean value) {
        row.getAsJsonObject("groups").getAsJsonObject("amigos").getAsJsonObject("permissions").addProperty("storage", value);
    }
    private static boolean storage(JsonObject row) {
        return row != null && row.getAsJsonObject("groups").getAsJsonObject("amigos").getAsJsonObject("permissions").get("storage").getAsBoolean();
    }
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
}
