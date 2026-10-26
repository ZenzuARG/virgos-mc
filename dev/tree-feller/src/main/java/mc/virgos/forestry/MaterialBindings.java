package mc.virgos.forestry;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

/** Binds actual injected registry keys, never guessed enum-name spelling. Native validation happens at runtime. */
public final class MaterialBindings {
    private final Map<String, Material> values = new HashMap<>();
    private final Set<String> ambiguous = new HashSet<>();
    public MaterialBindings() {
        if (!Bukkit.isPrimaryThread()) throw new IllegalStateException("Material bindings require the server thread");
        for (Material material : Material.values()) {
            if (material.name().startsWith("LEGACY_")) continue;
            String key = material.getKey().toString();
            Material previous = values.putIfAbsent(key, material);
            if (previous != null && previous != material) ambiguous.add(key);
        }
    }
    public Material block(String key, boolean planting) {
        Material material = values.get(key);
        if (material == null || ambiguous.contains(key) || !material.isBlock()
                || !material.getKey().toString().equals(key)) throw new IllegalArgumentException("Unresolved block key: " + key);
        if (Bukkit.createBlockData(material).getMaterial() != material) throw new IllegalStateException("Block round trip failed: " + key);
        if (planting && (!material.isItem() || new ItemStack(material).getType() != material)) {
            throw new IllegalStateException("Seed item round trip failed: " + key);
        }
        return material;
    }
    public Material pending(String key) {
        // Exact old enum identifiers are accepted solely for preserved v1 intents, not for new catalog inference.
        if (key.contains(":")) return block(key, true);
        Material old = java.util.Arrays.stream(Material.values()).filter(value -> value.name().equals(key)).findFirst().orElseThrow();
        return block(old.getKey().toString(), true);
    }
}
