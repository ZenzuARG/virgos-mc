package mc.virgos.addonsqa;

import java.nio.file.Path;
import java.util.Set;

/** Exact allowlist, not a configurable path prefix. Caller supplies toRealPath(). */
public final class LabGuard {
    private static final Path ROOT = Path.of("D:/proyectos/mc-server-lab/create-addons-20261025").toAbsolutePath().normalize();
    private static final Set<String> VARIANTS = Set.of("baseline", "crafts", "bells", "cei", "combined", "baseline-after");
    public static boolean allowedCanonical(Path cwd, boolean dedicated, int port, String world) {
        if (!dedicated || port != 25575 || !"virgos_world".equals(world)) return false;
        Path absolute = cwd.toAbsolutePath().normalize();
        return VARIANTS.stream().anyMatch(v -> ROOT.resolve(v).resolve("server").equals(absolute));
    }
    public static boolean id(String id) { return id != null && id.matches("[A-Za-z0-9_-]{1,48}"); }
    public static void position(int x, int y, int z) {
        if (x < 32 || x > 160 || y < 60 || y > 100 || z < -32 || z > 96)
            throw new IllegalArgumentException("outside bounded fixture");
    }
    private LabGuard() { }
}
