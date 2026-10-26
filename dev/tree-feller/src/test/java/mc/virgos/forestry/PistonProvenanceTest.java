package mc.virgos.forestry;

import org.bukkit.Material;

/** Pure selection seam shared by extension/retraction; this is not a Bukkit/native piston fixture. */
public final class PistonProvenanceTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        for (Material log : new Material[]{Material.OAK_LOG, Material.SPRUCE_LOG, Material.BIRCH_LOG,
                Material.JUNGLE_LOG, Material.ACACIA_LOG, Material.DARK_OAK_LOG,
                Material.MANGROVE_LOG, Material.CHERRY_LOG}) {
            check(Forestry.tracksMoved(log, false), "unknown supported log must acquire piston provenance: " + log);
            check(Forestry.tracksMoved(log, true), "known supported log remains tracked: " + log);
        }
        check(!Forestry.tracksMoved(Material.STONE, false), "do not broaden non-log tracking");
        check(!Forestry.tracksMoved(Material.STRIPPED_OAK_LOG, false), "do not add unsupported species/forms");
        check(Forestry.tracksMoved(Material.STRIPPED_OAK_LOG, true), "preserve existing known-source tracking");
        System.out.println("PistonProvenance PASS: UNKNOWN supported logs tracked; known behavior preserved; native events UNPROVEN");
    }
}
