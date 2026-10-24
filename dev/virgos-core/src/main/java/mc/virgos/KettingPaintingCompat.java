package mc.virgos;

import net.minecraft.world.entity.decoration.Painting;

/** CoreProtect bridge: Bukkit's Art enum does not contain Forge painting variants. */
public final class KettingPaintingCompat {
    private KettingPaintingCompat() {}

    public static String key(Object bukkitPainting) {
        try {
            Object handle = bukkitPainting.getClass().getMethod("getHandle").invoke(bukkitPainting);
            if (!(handle instanceof Painting painting)) {
                throw new IllegalArgumentException("Expected a Minecraft painting");
            }
            return painting.getVariant().unwrapKey().orElseThrow().location().toString();
        } catch (ReflectiveOperationException error) {
            throw new IllegalStateException("Cannot read painting variant", error);
        }
    }
}
