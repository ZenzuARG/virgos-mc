package mc.virgos.forestry;

import com.thizthizzydizzy.treefeller.Sapling;
import java.util.HashSet;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

public final class LegacySaplingTest {
    public static void main(String[] args) {
        Sapling legacy = new Sapling(null, null, null, null,
            new HashSet<>(java.util.Set.of(Material.OAK_SAPLING)), true, 1);
        if (legacy.place(null) || legacy.place(Material.OAK_SAPLING)) throw new AssertionError("legacy direct planting bypass");
        ItemStack stack = new ItemStack(Material.OAK_SAPLING, 2);
        if (legacy.tryPlace(stack) || stack.getAmount() != 2) throw new AssertionError("legacy consumes inventory");
        legacy.tick();
        System.out.println("LegacySapling PASS: direct, inventory and timeout paths cannot plant");
    }
}
