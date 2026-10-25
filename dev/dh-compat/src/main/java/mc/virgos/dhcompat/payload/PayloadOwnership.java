package mc.virgos.dhcompat.payload;

import java.util.Objects;
import java.util.concurrent.*;
import java.util.function.*;

/** One-shot ownership for completed requested payloads, without extending fragment TTL. */
public final class PayloadOwnership {
    private PayloadOwnership() { }
    public interface Receiver { Owner virgos$owner(); }
    public interface Payload { Slot virgos$slot(); }

    /** One receiver belongs to one native ClientNetworkState/session. No global registry. */
    public static final class Owner {
        private boolean closed;
        public synchronized void close() { closed = true; }
        private synchronized Lease claim(Supplier<Object> remove) {
            if (closed) return null;
            Object buffer = remove.get();
            return buffer == null ? null : new Lease(this, buffer);
        }
        private synchronized Object take(Lease lease) {
            if (lease.owner != this) return null;
            Object buffer = closed ? null : lease.buffer;
            lease.buffer = null;
            return buffer;
        }
    }

    private static final class Lease {
        final Owner owner;
        Object buffer; // Accessed only under the owning receiver's monitor.
        Lease(Owner owner, Object buffer) { this.owner = owner; this.buffer = buffer; }
        void discard() { synchronized (owner) { buffer = null; } }
    }

    /** Transient attachment to the received payload, never serialized. */
    public static final class Slot {
        private Lease lease;
        private synchronized Lease claim(Owner owner, Supplier<Object> remove) {
            if (lease == null) lease = owner.claim(remove);
            return lease != null && lease.owner == owner ? lease : null;
        }
        private synchronized boolean claimed() { return lease != null; }
        private synchronized Object lookup(Owner owner, Supplier<Object> nativeLookup) {
            return lease == null ? nativeLookup.get() : owner.take(lease);
        }
    }

    public static Runnable claim(Receiver receiver, Payload payload, Supplier<Object> remove) {
        Lease lease = payload.virgos$slot().claim(receiver.virgos$owner(), remove);
        return lease == null ? () -> { } : lease::discard;
    }

    public static Object lookup(Receiver receiver, Payload payload, Supplier<Object> nativeLookup) {
        return payload.virgos$slot().lookup(receiver.virgos$owner(), nativeLookup);
    }

    public static Object remove(Payload payload, Supplier<Object> nativeRemove) {
        return payload.virgos$slot().claimed() ? null : nativeRemove.get();
    }

    /** Keeps the original future, callback and Throwable; only decorates its executor handoff. */
    public static <T, R> CompletableFuture<R> handleAsync(CompletableFuture<T> source,
            BiFunction<? super T, Throwable, ? extends R> callback, Executor executor,
            Function<T, Runnable> claim) {
        Objects.requireNonNull(callback);
        Objects.requireNonNull(executor);
        Handoff handoff = new Handoff();
        CompletableFuture<R> result = source.handleAsync(callback, command -> {
            // CompletableFuture calls execute only after this source is complete. No extra stage.
            if (!source.isCompletedExceptionally()) {
                T response = source.getNow(null);
                if (response != null) handoff.setCleanup(claim.apply(response));
            }
            try {
                executor.execute(() -> {
                    handoff.begin();
                    try { command.run(); }
                    finally { handoff.end(); }
                });
            } catch (RuntimeException | Error rejected) {
                handoff.discard();
                throw rejected;
            }
        });
        result.whenComplete((value, error) -> handoff.discard());
        return result;
    }

    /** Cancellation cannot revoke the buffer from an already-running native callback. */
    private static final class Handoff {
        private Runnable cleanup;
        private boolean running;
        private boolean discarded;
        void setCleanup(Runnable cleanup) {
            boolean dispose;
            synchronized (this) {
                dispose = discarded;
                if (!dispose) this.cleanup = cleanup;
            }
            // Cancellation can happen inside claim.apply, before cleanup is published.
            if (dispose && cleanup != null) cleanup.run();
        }
        synchronized void begin() { running = true; }
        void end() {
            Runnable release;
            synchronized (this) { running = false; discarded = true; release = cleanup; cleanup = null; }
            if (release != null) release.run();
        }
        void discard() {
            Runnable release;
            synchronized (this) {
                discarded = true;
                if (running) return;
                release = cleanup; cleanup = null;
            }
            if (release != null) release.run();
        }
    }
}
