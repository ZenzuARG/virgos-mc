package mc.virgos.forestry;

import java.lang.reflect.Method;
import org.bukkit.Bukkit;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/** Uses the existing game classloader only. No synthetic events or full-pass grants. */
public final class NativeGuard {
    private String diagnostic = "UNTESTED";
    public String diagnostic() { return diagnostic; }
    private static Method method(Object receiver, String name, Object... args) throws ReflectiveOperationException {
        Class<?> type = receiver instanceof Class<?> clazz ? clazz : receiver.getClass();
        for (Method candidate : type.getMethods()) {
            if (!candidate.getName().equals(name) || candidate.getParameterCount() != args.length) continue;
            Class<?>[] parameters = candidate.getParameterTypes();
            boolean match = true;
            for (int i = 0; i < args.length; i++) {
                if (parameters[i] == boolean.class && args[i] instanceof Boolean) continue;
                if (!parameters[i].isInstance(args[i])) { match = false; break; }
            }
            if (match) return candidate;
        }
        throw new NoSuchMethodException(type.getName() + "." + name);
    }
    private static Object call(Object receiver, String name, Object... args) throws ReflectiveOperationException {
        return method(receiver, name, args).invoke(receiver instanceof Class<?> ? null : receiver, args);
    }
    private static Object handle(Player player) throws ReflectiveOperationException {
        if (!Bukkit.isPrimaryThread() || player == null || !player.isOnline()) throw new IllegalStateException("No authenticated server-thread actor");
        return call(player, "getHandle");
    }
    private static Object protection(Object playerHandle) throws ReflectiveOperationException {
        ClassLoader loader = playerHandle.getClass().getClassLoader();
        Object server = call(Bukkit.getServer(), "getServer");
        Class<?> core = Class.forName("mc.virgos.VirgosCore", true, loader);
        Object auth = core.getField("AUTH").get(null);
        if (!Boolean.TRUE.equals(call(auth, "authenticated", playerHandle))) throw new IllegalStateException("Authentication refused");
        Class<?> api = Class.forName("xaero.pac.common.server.api.OpenPACServerAPI", true, loader);
        return call(call(api, "get", server), "getChunkProtection");
    }
    private static Object position(ClassLoader loader, Block block) throws ReflectiveOperationException {
        return Class.forName("net.minecraft.core.BlockPos", true, loader)
            .getConstructor(int.class, int.class, int.class).newInstance(block.getX(), block.getY(), block.getZ());
    }
    private static Object constant(ClassLoader loader, String type, String value) throws ReflectiveOperationException {
        return Class.forName(type, true, loader).getField(value).get(null);
    }
    public boolean breaking(Player player, ItemStack axe, Block block) {
        try {
            Object actor = handle(player);
            Object guard = protection(actor);
            ClassLoader loader = actor.getClass().getClassLoader();
            Object level = call(block.getWorld(), "getHandle");
            String craft = Bukkit.getServer().getClass().getPackageName();
            Class<?> item = Class.forName(craft + ".inventory.CraftItemStack", true, Bukkit.getServer().getClass().getClassLoader());
            Object stack = call(item, "asNMSCopy", axe);
            Object denied = call(guard, "onBlockInteraction", actor,
                constant(loader, "net.minecraft.world.InteractionHand", "MAIN_HAND"), stack, level,
                position(loader, block), constant(loader, "net.minecraft.core.Direction", "UP"), true, false, true);
            diagnostic = Boolean.FALSE.equals(denied) ? "ALLOW" : "OPAC_DENY";
            return Boolean.FALSE.equals(denied);
        } catch (ReflectiveOperationException | LinkageError | RuntimeException error) {
            diagnostic = "UNAVAILABLE:" + error.getClass().getSimpleName();
            return false;
        }
    }
    public boolean placing(Player player, Block block, org.bukkit.Material material) {
        try {
            Object actor = handle(player);
            Object guard = protection(actor);
            Object state = call(Bukkit.createBlockData(material), "getState");
            Object level = call(block.getWorld(), "getHandle");
            Object denied = call(guard, "onEntityPlaceBlock", state, actor, level,
                position(actor.getClass().getClassLoader(), block));
            diagnostic = Boolean.FALSE.equals(denied) ? "ALLOW" : "OPAC_DENY";
            return Boolean.FALSE.equals(denied);
        } catch (ReflectiveOperationException | LinkageError | RuntimeException error) {
            diagnostic = "UNAVAILABLE:" + error.getClass().getSimpleName();
            return false;
        }
    }
}
