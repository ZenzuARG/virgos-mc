package mc.virgos.forestry;

import java.util.List;
import java.util.Set;

public final class CatalogTest {
    public static void main(String[] args) throws Exception {
        Catalog catalog = new Catalog();
        if (catalog.definitions().stream().filter(value -> !value.id().startsWith("minecraft:")).count() != 64) throw new AssertionError("inventory lost");
        var azalea = catalog.find(List.of("minecraft:oak_log", "minecraft:oak_wood"),
            List.of("minecraft:azalea_leaves", "minecraft:flowering_azalea_leaves"), Set.of("minecraft:azalea", "minecraft:flowering_azalea"));
        if (azalea == null || !azalea.fallback().equals("minecraft:azalea") || azalea.seeds().contains("minecraft:oak_sapling")) throw new AssertionError("wrong azalea identity");
        if (catalog.find(List.of("minecraft:stone"), List.of("minecraft:oak_leaves"), Set.of("minecraft:oak_sapling")) != null) throw new AssertionError("do not trust arbitrary seed overrides");
        var apple = catalog.definitions().stream().filter(value -> value.id().equals("regions_unexplored:apple_oak_sapling")).findFirst().orElseThrow();
        if (apple.observed(Set.of("minecraft:oak_leaves")) || !apple.observed(Set.of("regions_unexplored:apple_oak_leaves", "minecraft:oak_leaves"))) throw new AssertionError("generic oak must not be misclassified as apple oak");
        if (!catalog.seed("minecraft:azalea") || catalog.seed("minecraft:stone")) throw new AssertionError("pending seed allowlist");
        long gaps = catalog.definitions().stream().filter(value -> !value.status().equals("READY_STATIC")).count();
        if (gaps == 0) throw new AssertionError("do not fake full growth coverage");
        System.out.println("Catalog PASS: 64 inventory entries, declared azalea, arbitrary mismatch rejected, explicit gaps=" + gaps + "; native bindings UNPROVEN");
    }
}
