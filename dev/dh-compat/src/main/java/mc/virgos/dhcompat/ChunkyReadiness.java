package mc.virgos.dhcompat;

import java.lang.reflect.InvocationTargetException;

/** Probe the pinned Chunky getter without linking optional Chunky API classes. */
public final class ChunkyReadiness {
    private ChunkyReadiness() {}

    public static boolean providerReady(ClassLoader loader) {
        try {
            Class<?> provider = Class.forName("org.popcraft.chunky.ChunkyProvider", false, loader);
            provider.getMethod("get").invoke(null);
            return true;
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getCause();
            if (cause instanceof IllegalStateException && "Chunky is not loaded.".equals(cause.getMessage())) {
                return false;
            }
            if (cause instanceof RuntimeException runtime) throw runtime;
            if (cause instanceof Error error) throw error;
            throw new IllegalStateException("Chunky provider probe failed", cause);
        } catch (ReflectiveOperationException exception) {
            // An installed but incompatible provider is not a temporary readiness failure.
            throw new IllegalStateException("Pinned Chunky provider API is unavailable", exception);
        }
    }
}
