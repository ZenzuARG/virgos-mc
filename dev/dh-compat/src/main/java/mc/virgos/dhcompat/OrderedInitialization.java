package mc.virgos.dhcompat;

import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/** Small ordering primitives shared by the pinned compatibility injections. */
public final class OrderedInitialization {
    private OrderedInitialization() {}

    public static void onEventLoop(BooleanSupplier inEventLoop, Consumer<Runnable> enqueue, Runnable transition) {
        if (inEventLoop.getAsBoolean()) transition.run();
        else enqueue.accept(transition);
    }

    public static final class InitialConfig {
        private Runnable pending;

        public void defer(Runnable send) {
            if (pending != null) throw new IllegalStateException("Initial config already deferred");
            pending = send;
        }

        public void published() {
            Runnable send = pending;
            pending = null;
            if (send != null) send.run();
        }
    }
}
