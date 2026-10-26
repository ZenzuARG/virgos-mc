package mc.virgos.forestry;

import java.nio.file.Path;
import java.util.List;
import java.util.Set;

public final class PlantingLayoutTest {
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        Catalog catalog = new Catalog();
        for (String color : List.of("blue", "red", "green", "purple")) {
            var family = catalog.definitions().stream().filter(value -> value.id().equals("ars_nouveau:" + color + "_archwood_sapling")).findFirst().orElseThrow();
            check(family.widths().equals(List.of(2)), "Ars mature core is 2x2");
            check(family.plantingWidths().equals(List.of(1)) && family.minimumPlantsFor(2) == 1, "one sapling must never become four reserved seeds");
            check(!family.anchorResolved(), "do not invent an anchor among buttress roots");
            check(!family.accepts(family.trunks(), family.foliage(), Set.copyOf(family.seeds())), "unresolved anchor denies activation");
        }
        for (var family : catalog.definitions()) if (family.id().startsWith("quark:")) {
            check(family.anchorResolved() && family.minimumPlantsFor(1) == 1, "Quark inherited one-seed path");
        }
        var spruce = catalog.definitions().stream().filter(value -> value.id().equals("minecraft:spruce")).findFirst().orElseThrow();
        check(spruce.minimumPlantsFor(1) == 1 && spruce.minimumPlantsFor(2) == 4, "existing matching grids unchanged");
        Journal journal = new Journal(Path.of(args[0]).resolve("one-seed.tsv"));
        String id = journal.prepareDeclared("owner", "world", "quark:blue_blossom_sapling", List.of("0,64,0"), List.of("quark:blue_blossom_sapling"));
        check(journal.reserve(id, "quark:blue_blossom_sapling", 4) == 1, "one valid plant consumes only one own drop");
        journal = new Journal(Path.of(args[0]).resolve("one-seed.tsv"));
        check(journal.groups().get(0).required() == 1 && journal.groups().get(0).pending().size() == 1, "existing journal preserves minimum and layout");
        System.out.println("PlantingLayout PASS: Ars mature4/seed1 metadata, unresolved anchor denied; six Quark one-seed candidates; legacy grids and journal preserved; native UNPROVEN");
    }
}
