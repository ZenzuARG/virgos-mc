package mc.virgos.forestry;

import java.util.List;
import java.util.Set;

/** Only pre-.3 public constructor/accessors and vanilla identities are used. */
public final class CatalogCompatibilityProbe {
    public static void main(String[] args) throws Exception {
        Catalog catalog = new Catalog();
        var oak = catalog.find(List.of("minecraft:oak_log", "minecraft:oak_wood"), List.of("minecraft:oak_leaves"), Set.of("minecraft:oak_sapling"));
        System.out.println("oak=" + oak.id() + ":" + oak.widths() + ":" + oak.fallback());
        System.out.println("oak-observed=" + oak.observed(Set.of("minecraft:oak_leaves")));
        var legacy = new Catalog.Definition("fixture", List.of("log"), List.of("leaf"), List.of("seed"), "seed", List.of(2), "READY_STATIC", List.of("leaf"));
        System.out.println("legacy-widths=" + legacy.widths());
        System.out.println("legacy-accepts=" + legacy.accepts(List.of("log"), List.of("leaf"), Set.of("seed")));
        System.out.println("legacy-observed=" + legacy.observed(Set.of("leaf")));
        System.out.println("reject=" + legacy.accepts(List.of("other"), List.of("leaf"), Set.of("seed")));
    }
}
