package mc.virgos.forestry;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Resource-backed identity/growth metadata; never derives a seed from a trunk name. */
public final class Catalog {
    public record Definition(String id, List<String> trunks, List<String> foliage, List<String> seeds,
                             String fallback, List<Integer> widths, String status, List<String> requiredFoliage,
                             List<Integer> plantingWidths, String anchorMode) {
        /** Preserve the previous public constructor's matched-grid semantics. */
        public Definition(String id, List<String> trunks, List<String> foliage, List<String> seeds,
                          String fallback, List<Integer> widths, String status, List<String> requiredFoliage) {
            this(id, trunks, foliage, seeds, fallback, widths, status, requiredFoliage, widths, "ROOT_GRID");
        }
        public boolean anchorResolved() {
            return anchorMode.equals("ROOT_GRID") && widths.equals(plantingWidths) && !widths.isEmpty();
        }
        /** Metadata count only: an unresolved anchor never authorizes a world operation. */
        public int minimumPlantsFor(int matureWidth) {
            if (!widths.contains(matureWidth)) throw new IllegalArgumentException("Undeclared mature width");
            int seedWidth;
            if (plantingWidths.contains(matureWidth)) seedWidth = matureWidth;
            else if (plantingWidths.size() == 1) seedWidth = plantingWidths.get(0);
            else throw new IllegalArgumentException("Ambiguous planting layout");
            return Math.multiplyExact(seedWidth, seedWidth);
        }
        public boolean observed(Set<String> actualFoliage) {
            return requiredFoliage.stream().anyMatch(actualFoliage::contains);
        }
        public boolean accepts(List<String> declaredTrunks, List<String> declaredFoliage, Set<String> declaredSeeds) {
            return status.equals("READY_STATIC") && anchorResolved() && seeds.containsAll(declaredSeeds)
                && !declaredSeeds.isEmpty() && trunks.containsAll(declaredTrunks) && !declaredTrunks.isEmpty()
                && foliage.containsAll(declaredFoliage) && !declaredFoliage.isEmpty();
        }
    }
    private final List<Definition> definitions = new ArrayList<>();
    public Catalog() throws IOException {
        vanilla("oak", List.of("oak"), List.of("oak"), List.of("oak_sapling"), "oak_sapling", List.of(1));
        vanilla("birch", List.of("birch"), List.of("birch"), List.of("birch_sapling"), "birch_sapling", List.of(1));
        vanilla("spruce", List.of("spruce"), List.of("spruce"), List.of("spruce_sapling"), "spruce_sapling", List.of(1, 2));
        vanilla("jungle", List.of("jungle"), List.of("jungle"), List.of("jungle_sapling"), "jungle_sapling", List.of(1, 2));
        vanilla("dark_oak", List.of("dark_oak"), List.of("dark_oak"), List.of("dark_oak_sapling"), "dark_oak_sapling", List.of(2));
        vanilla("acacia", List.of("acacia"), List.of("acacia"), List.of("acacia_sapling"), "acacia_sapling", List.of(1));
        vanilla("cherry", List.of("cherry"), List.of("cherry"), List.of("cherry_sapling"), "cherry_sapling", List.of(1));
        vanilla("azalea", List.of("oak"), List.of("azalea", "flowering_azalea"),
            List.of("azalea", "flowering_azalea"), "azalea", List.of(1));
        definitions.add(new Definition("minecraft:mangrove", List.of("minecraft:mangrove_log", "minecraft:mangrove_wood"),
            List.of("minecraft:mangrove_leaves", "minecraft:mangrove_roots"), List.of("minecraft:mangrove_propagule"),
            "minecraft:mangrove_propagule", List.of(1), "READY_STATIC", List.of("minecraft:mangrove_leaves")));
        var stream = Catalog.class.getResourceAsStream("/META-INF/virgos-tree-feller/catalog.tsv");
        if (stream == null) throw new IOException("Missing pinned full-pack catalog");
        int count = 0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            for (String line; (line = reader.readLine()) != null;) {
                String[] fields = line.split("\t", -1);
                if (fields.length != 10) throw new IOException("Invalid catalog row");
                List<Integer> widths = fields[5].isEmpty() ? List.of()
                    : Arrays.stream(fields[5].split(",")).map(Integer::valueOf).toList();
                if (widths.stream().anyMatch(width -> width < 1)) throw new IOException("Invalid growth footprint");
                List<Integer> planting = fields[8].isEmpty() ? List.of()
                    : Arrays.stream(fields[8].split(",")).map(Integer::valueOf).toList();
                if (planting.stream().anyMatch(width -> width < 1)) throw new IOException("Invalid seed layout");
                Definition value = new Definition(fields[0], split(fields[1]), split(fields[2]), split(fields[3]), fields[4], widths,
                    fields[6], split(fields[7]), planting, fields[9]);
                if (!value.seeds().contains(value.fallback())) throw new IOException("Fallback outside declared seeds");
                definitions.add(value);
                count++;
            }
        }
        if (count != 64 || definitions.stream().map(Definition::id).distinct().count() != definitions.size()) {
            throw new IOException("Unexpected catalog inventory");
        }
    }
    private static List<String> split(String value) { return value.isEmpty() ? List.of() : List.of(value.split(",")); }
    private void vanilla(String id, List<String> trunks, List<String> foliage, List<String> seeds, String fallback, List<Integer> widths) {
        List<String> logs = new ArrayList<>();
        trunks.forEach(wood -> { logs.add("minecraft:" + wood + "_log"); logs.add("minecraft:" + wood + "_wood"); });
        definitions.add(new Definition("minecraft:" + id, List.copyOf(logs), foliage.stream().map(leaf -> "minecraft:" + leaf + "_leaves").toList(),
            seeds.stream().map(seed -> "minecraft:" + seed).toList(), "minecraft:" + fallback, widths, "READY_STATIC", foliage.stream().map(leaf -> "minecraft:" + leaf + "_leaves").toList()));
    }
    public List<Definition> definitions() { return List.copyOf(definitions); }
    public Definition find(List<String> trunks, List<String> leaves, Set<String> seeds) {
        return definitions.stream().filter(definition -> definition.accepts(trunks, leaves, seeds)).findFirst().orElse(null);
    }
    public boolean seed(String key) { return definitions.stream().anyMatch(definition -> definition.seeds().contains(key)); }
    public boolean trunk(String key) { return definitions.stream().anyMatch(definition -> definition.trunks().contains(key)); }
}
