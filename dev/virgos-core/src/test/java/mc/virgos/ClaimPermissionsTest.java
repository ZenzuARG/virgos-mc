package mc.virgos;

import com.google.gson.JsonObject;
import java.lang.reflect.Field;
import java.util.UUID;

/** Regression checks that do not require starting a Minecraft server. */
public final class ClaimPermissionsTest {
    public static void main(String[] args) throws Exception {
        PlayerProfiles registry = new PlayerProfiles();
        Field registryData = PlayerProfiles.class.getDeclaredField("profiles");
        registryData.setAccessible(true);
        @SuppressWarnings("unchecked")
        var known = (java.util.Map<UUID, JsonObject>) registryData.get(registry);
        UUID owner = UUID.randomUUID();
        for (int i = 0; i < 10; i++) {
            JsonObject row = new JsonObject();
            row.addProperty("name", "Known" + i);
            known.put(i == 0 ? owner : UUID.randomUUID(), row);
        }
        @SuppressWarnings("unchecked")
        var profiles = (java.util.List<com.mojang.authlib.GameProfile>) PlayerProfiles.class
            .getMethod("knownPlayers").invoke(registry);
        if (profiles.size() != 10) throw new AssertionError("Known offline profiles must be selectable");
        try { profiles.clear(); throw new AssertionError("Known profile snapshots must be immutable"); }
        catch (UnsupportedOperationException expected) { }
        var selection = ClaimPermissionsPrototype.class.getDeclaredMethod("memberCandidates", UUID.class,
            java.util.List.class, java.util.List.class);
        selection.setAccessible(true);
        @SuppressWarnings("unchecked")
        var candidates = (java.util.List<com.mojang.authlib.GameProfile>) selection.invoke(null, owner,
            profiles, java.util.List.of(profiles.get(1)));
        if (candidates.size() != 9 || candidates.stream().anyMatch(p -> p.getId().equals(owner)))
            throw new AssertionError("Candidates must deduplicate UUIDs and exclude the owner");
        if (candidates.subList(7, candidates.size()).size() != 2)
            throw new AssertionError("Players beyond the first page must remain reachable");
        ClaimPermissionService service = new ClaimPermissionService();
        var context = new ClaimPermissionService.Context(null, null, UUID.randomUUID(), "main", "test:main", "Test");
        Field field = ClaimPermissionService.class.getDeclaredField("data");
        field.setAccessible(true);
        JsonObject data = new JsonObject();
        JsonObject claim = new JsonObject(), groups = new JsonObject(), friends = new JsonObject(), permissions = new JsonObject();
        data.add(context.key(), claim); claim.add("groups", groups); groups.add("amigos", friends); friends.add("permissions", permissions);
        field.set(service, data);
        permissions.addProperty("storage", false);
        if (service.isGroupEnabled(context, ClaimPermissionService.Group.FRIENDS, ClaimPermissionService.Permission.STORAGE))
            throw new AssertionError("Stored false must disable chest permission");
        permissions.addProperty("storage", true);
        if (!service.isGroupEnabled(context, ClaimPermissionService.Group.FRIENDS, ClaimPermissionService.Permission.STORAGE))
            throw new AssertionError("Stored true must enable chest permission");
        if (service.individualDecision(context, UUID.randomUUID(), ClaimPermissionService.Permission.STORAGE) != null)
            throw new AssertionError("Missing exception must inherit");
        System.out.println("Claim permissions: boolean state and inheritance PASS");
    }
}
