package mc.virgos;

/** Pure security boundary regressions; no Minecraft classes or world state. */
public final class ClaimNativePermissionsTest {
    public static void main(String[] args) {
        var self = java.util.UUID.randomUUID();
        var other = java.util.UUID.randomUUID();
        require(ClaimPermissionAdmission.human(true, false, true, self, self, null, false), "Real self player admitted");
        require(ClaimPermissionAdmission.human(true, false, true, self, self, self, false), "Explicit self impersonation admitted");
        require(!ClaimPermissionAdmission.human(false, false, true, self, self, null, false), "Automation entity excluded");
        require(!ClaimPermissionAdmission.human(true, true, true, self, self, null, false), "Forge fake player excluded");
        require(!ClaimPermissionAdmission.human(true, false, false, self, self, null, false), "Projectile/proxy actor excluded even with same UUID");
        require(!ClaimPermissionAdmission.human(true, false, true, self, other, null, false), "Mismatched accessor excluded");
        require(!ClaimPermissionAdmission.human(true, false, true, self, self, other, false), "Native impersonation excluded");
        require(!ClaimPermissionAdmission.human(true, false, true, self, self, null, true), "Human-triggered explosion excluded");
        require(!ClaimPermissionAdmission.human(true, false, true, null, null, null, false), "Missing identity excluded");
        for (boolean original : new boolean[] {false, true}) {
            require(ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.NATIVE,
                true, false, false, false) == original, "Unmanaged exceptions remain native");
            require(ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                false, false, false, false) == original, "Fake, automation and impersonated access remain native");
            require(!ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.DENY,
                true, false, false, false), "Managed deny overrides an old exception");
            require(!ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                true, true, false, false), "Native veto never admits a new grant");
            require(!ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                true, false, true, false), "Building allow never opens a storage interaction");
            require(ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                true, false, true, true), "Building allows both breaking and null-block placement");
        }
        for (String id : new String[] {"Chests", "Barrels", "Ender_Chests", "Shulker_Boxes"})
            require("storage".equals(ClaimPermissionAdmission.permission("claims.protection.exceptions.groups.block.interact." + id)), "Storage categories");
        require("machines".equals(ClaimPermissionAdmission.permission("claims.protection.exceptions.groups.block.interact.Hoppers")), "Native hopper category");
        require("doors".equals(ClaimPermissionAdmission.permission("claims.protection.exceptions.groups.block.interact.Controls")), "Native controls category");
        require(ClaimPermissionAdmission.permission("claims.protection.exceptions.groups.block.interact.Modded_Machine") == null,
            "Unknown mod machines have no invented blanket coverage");
        for (boolean nativeProtected : new boolean[] {false, true}) {
            require(ClaimPermissionAdmission.protect(nativeProtected, ClaimPermissionDecision.DENY, true, false), "Explicit deny catches native full-access early return");
            require(ClaimPermissionAdmission.protect(nativeProtected, ClaimPermissionDecision.DENY, true, true) == nativeProtected, "Owner/admin/full-pass/disabled protection unchanged");
            require(ClaimPermissionAdmission.protect(nativeProtected, ClaimPermissionDecision.ALLOW, true, false) == nativeProtected, "Deny boundary cannot grant or uncancel anything");
            require(ClaimPermissionAdmission.protect(nativeProtected, ClaimPermissionDecision.DENY, false, false) == nativeProtected, "Non-human paths unchanged");
        }
        System.out.println("ClaimNativePermissionsTest passed");
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
