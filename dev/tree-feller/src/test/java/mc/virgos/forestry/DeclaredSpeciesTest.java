package mc.virgos.forestry;

import com.thizthizzydizzy.treefeller.DetectedTree;
import com.thizthizzydizzy.treefeller.Option;
import com.thizthizzydizzy.treefeller.Tree;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.bukkit.Material;

public final class DeclaredSpeciesTest {
    public static void main(String[] args) throws Exception {
        String config = Files.readString(Path.of(args[0]).resolve("upstream-config.yml"));
        String azalea = config.lines().filter(line -> line.contains("sapling: [AZALEA, FLOWERING_AZALEA]")).findFirst().orElseThrow();
        if (!azalea.contains("OAK_LOG") || !azalea.contains("AZALEA_LEAVES")) throw new AssertionError("wrong upstream fixture");
        Tree tree = new Tree(new ArrayList<>(List.of(Material.OAK_LOG, Material.OAK_WOOD)),
            new ArrayList<>(List.of(Material.AZALEA_LEAVES, Material.FLOWERING_AZALEA_LEAVES)));
        Set<Material> expected = Set.of(Material.AZALEA, Material.FLOWERING_AZALEA);
        Option.SAPLING.treeValues.put(tree, new HashSet<>(expected));
        Set<Material> selected = Forestry.declaredSeeds(null, tree);
        if (!selected.equals(expected) || selected.contains(Material.OAK_SAPLING)) {
            throw new AssertionError("declared azalea alternatives lost: " + selected);
        }
        System.out.println("DeclaredSpecies PASS: actual upstream azalea definition retains both seeds, never oak");
    }
}
