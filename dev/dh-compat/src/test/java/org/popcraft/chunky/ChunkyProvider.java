package org.popcraft.chunky;

/** Test-only shape of the pinned provider; never included in the addon jar. */
public final class ChunkyProvider {
    public static boolean loaded;
    public static RuntimeException failure;

    public static Object get() {
        if (failure != null) throw failure;
        if (!loaded) throw new IllegalStateException("Chunky is not loaded.");
        return ChunkyProvider.class;
    }
}
