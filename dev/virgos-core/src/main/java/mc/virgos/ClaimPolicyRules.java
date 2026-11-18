package mc.virgos;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Shared effective-permission calculation for enforcement and the player preview. */
public final class ClaimPolicyRules {
    public static final List<String> GROUPS = List.of("familia", "amigos", "visitantes");
    public static final Set<String> PERMISSIONS = Set.of("storage", "machines", "doors", "building");
    public enum Source { INDIVIDUAL, GROUPS, DEFAULT }
    public record Effective(boolean allowed, Source source, List<String> groups) {}
    private ClaimPolicyRules() {}

    public static ClaimPermissionDecision decision(JsonObject policy, UUID player, String permission) {
        if (policy == null || !PERMISSIONS.contains(permission)) return ClaimPermissionDecision.NATIVE;
        return effective(policy, player, permission).allowed()
            ? ClaimPermissionDecision.ALLOW : ClaimPermissionDecision.DENY;
    }

    public static JsonObject object(JsonObject parent, String name) {
        return parent != null && parent.has(name) ? parent.getAsJsonObject(name) : new JsonObject();
    }
    public static Effective effective(JsonObject policy, UUID player, String permission) {
        if (!PERMISSIONS.contains(permission)) throw new IllegalArgumentException("Unknown managed permission");
        JsonObject person = new JsonObject();
        for (var entry : object(policy, "individuals").entrySet())
            if (UUID.fromString(entry.getKey()).equals(player)) person = entry.getValue().getAsJsonObject();
        JsonElement individual = object(person, "permissions").get(permission);
        if (individual != null) return new Effective("ALLOW".equals(individual.getAsString()), Source.INDIVIDUAL, List.of());
        List<String> allowing = new ArrayList<>();
        for (String id : GROUPS) {
            JsonObject group = object(object(policy, "groups"), id);
            JsonElement enabled = object(group, "permissions").get(permission);
            if (enabled == null || !enabled.getAsBoolean() || !group.has("members")) continue;
            for (JsonElement row : group.getAsJsonArray("members")) {
                if (player.equals(UUID.fromString(row.getAsJsonObject().get("id").getAsString()))) {
                    allowing.add(id);
                    break;
                }
            }
        }
        return new Effective(!allowing.isEmpty(), allowing.isEmpty() ? Source.DEFAULT : Source.GROUPS, List.copyOf(allowing));
    }
    public static void validate(JsonObject policy) {
        if (policy.has("groups")) {
            JsonObject groups = requiredObject(policy.get("groups"));
            for (String id : GROUPS) {
                if (!groups.has(id)) continue;
                JsonObject group = requiredObject(groups.get(id));
                validatePermissions(group, false);
                if (!group.has("members")) continue;
                if (!group.get("members").isJsonArray()) throw new IllegalArgumentException("Members must be an array");
                Set<UUID> seen = new HashSet<>();
                for (JsonElement member : group.getAsJsonArray("members")) {
                    JsonObject row = requiredObject(member);
                    if (!seen.add(uuid(row.get("id")))) throw new IllegalArgumentException("Duplicate member");
                    if (row.has("name")) text(row.get("name"));
                }
            }
        }
        if (policy.has("individuals")) {
            Set<UUID> seen = new HashSet<>();
            for (var entry : requiredObject(policy.get("individuals")).entrySet()) {
                if (!seen.add(uuid(new com.google.gson.JsonPrimitive(entry.getKey()))))
                    throw new IllegalArgumentException("Duplicate individual UUID");
                JsonObject person = requiredObject(entry.getValue());
                if (person.has("name")) text(person.get("name"));
                validatePermissions(person, true);
            }
        }
    }
    private static void validatePermissions(JsonObject holder, boolean individual) {
        if (!holder.has("permissions")) return;
        JsonObject permissions = requiredObject(holder.get("permissions"));
        for (String id : PERMISSIONS) {
            if (!permissions.has(id)) continue;
            JsonElement value = permissions.get(id);
            if (!individual) {
                if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isBoolean())
                    throw new IllegalArgumentException("Group permission must be boolean");
            } else if (!Set.of("ALLOW", "DENY").contains(text(value))) {
                throw new IllegalArgumentException("Invalid individual permission");
            }
        }
    }
    static JsonObject requiredObject(JsonElement value) {
        if (value == null || !value.isJsonObject()) throw new IllegalArgumentException("Expected an object");
        return value.getAsJsonObject();
    }
    static String text(JsonElement value) {
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString())
            throw new IllegalArgumentException("Expected text");
        return value.getAsString();
    }
    static UUID uuid(JsonElement value) {
        String raw = text(value);
        UUID uuid = UUID.fromString(raw);
        if (!uuid.toString().equalsIgnoreCase(raw)) throw new IllegalArgumentException("Invalid UUID");
        return uuid;
    }
}
