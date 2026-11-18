package mc.virgos;

import java.util.UUID;

/** Pure reduction rules shared by the narrow native adapter and offline fixtures. */
public final class ClaimPermissionAdmission {
    private ClaimPermissionAdmission() {}

    public static boolean human(boolean serverPlayer, boolean fakePlayer, boolean sameEntity,
                                UUID actual, UUID accessor, UUID impersonation, boolean explosion) {
        return serverPlayer && !fakePlayer && sameEntity && !explosion && actual != null
            && actual.equals(accessor) && (impersonation == null || actual.equals(impersonation));
    }

    public static String permission(String optionId) {
        if (optionId == null) return null;
        if (optionId.startsWith("playerConfig.")) optionId = optionId.substring("playerConfig.".length());
        return switch (optionId) {
            case "claims.protection.exceptions.blocksByPlayers" -> "building";
            case "claims.protection.exceptions.groups.block.interact.Chests",
                 "claims.protection.exceptions.groups.block.interact.Barrels",
                 "claims.protection.exceptions.groups.block.interact.Ender_Chests",
                 "claims.protection.exceptions.groups.block.interact.Shulker_Boxes" -> "storage";
            case "claims.protection.exceptions.groups.block.interact.Furnaces",
                 "claims.protection.exceptions.groups.block.interact.Hoppers" -> "machines";
            case "claims.protection.exceptions.groups.block.interact.Controls",
                 "claims.protection.exceptions.groups.block.interact.Doors" -> "doors";
            default -> null;
        };
    }

    public static boolean exception(boolean nativeValue, ClaimPermissionDecision decision,
                                    boolean human, boolean veto, boolean broad, boolean building) {
        return exception(nativeValue, decision, human, veto, broad, building, false);
    }

    public static boolean exception(boolean nativeValue, ClaimPermissionDecision decision,
                                    boolean human, boolean veto, boolean broad, boolean building,
                                    boolean defaulted) {
        if (!human || decision == ClaimPermissionDecision.NATIVE) return nativeValue;
        if (decision != ClaimPermissionDecision.ALLOW || broad && !building) return false;
        // A forced server default cannot acquire a new grant from a parcel policy.
        if (defaulted) return nativeValue;
        return !veto;
    }

    public static boolean protect(boolean nativeProtected, ClaimPermissionDecision decision,
                                  boolean human, boolean exempt) {
        return nativeProtected || human && !exempt && decision == ClaimPermissionDecision.DENY;
    }
}
