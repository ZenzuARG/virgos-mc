package mc.virgos;

import com.google.gson.JsonObject;
import java.lang.reflect.Field;
import java.util.UUID;

/** Regression checks that do not require starting a Minecraft server. */
public final class ClaimPermissionsTest {
    public static void main(String[] args) throws Exception {
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
