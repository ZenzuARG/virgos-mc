package mc.virgos;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.function.Supplier;

/** Preserves KubeJS stream and forgetting semantics for generated resources. */
public final class KubeJsGeneratedStreams {
    private KubeJsGeneratedStreams() {}

    public static InputStream open(Supplier<byte[]> cache, Runnable forget, boolean forgetAfterRead) {
        synchronized (cache) {
            InputStream stream = new ByteArrayInputStream(cache.get());
            if (forgetAfterRead) forget.run();
            return stream;
        }
    }
}
