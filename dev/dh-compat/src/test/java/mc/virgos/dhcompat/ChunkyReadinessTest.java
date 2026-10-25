package mc.virgos.dhcompat;

import org.popcraft.chunky.ChunkyProvider;

public final class ChunkyReadinessTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    /** Same flag-before-binding order observed in DH 3.3.3 bytecode. */
    private static final class NativeSetup {
        boolean listenerBound;
        int bindings;

        void attempt() {
            if (!listenerBound && !ChunkyReadiness.providerReady(getClass().getClassLoader())) return;
            if (listenerBound) return;
            listenerBound = true;
            ChunkyProvider.get();
            bindings++;
        }
    }

    public static void main(String[] args) {
        var delayed = new NativeSetup();
        delayed.attempt();
        check(!delayed.listenerBound && delayed.bindings == 0, "Unloaded provider must preserve unbound state for a normal retry");
        ChunkyProvider.loaded = true;
        delayed.attempt();
        delayed.attempt();
        check(delayed.listenerBound && delayed.bindings == 1, "Provider becoming ready must bind once through native setup");
        var ready = new NativeSetup();
        ready.attempt();
        check(ready.bindings == 1, "Already-ready provider must retain immediate native binding");

        var genuineFailure = new IllegalStateException("Unexpected provider corruption");
        ChunkyProvider.failure = genuineFailure;
        try {
            ChunkyReadiness.providerReady(ChunkyReadinessTest.class.getClassLoader());
            throw new AssertionError("Unexpected provider exceptions must propagate");
        } catch (IllegalStateException error) {
            check(error == genuineFailure, "Unexpected provider exception identity must be preserved");
        } finally {
            ChunkyProvider.failure = null;
        }
        System.out.println("Chunky readiness: defer, native retry once, ready control and genuine error propagation passed");
    }
}
