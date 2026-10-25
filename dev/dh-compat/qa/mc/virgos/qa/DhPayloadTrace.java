package mc.virgos.qa;

import java.io.BufferedWriter;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReferenceArray;
import java.util.function.LongSupplier;

/** Opt-in QA observations only. Never reads the native cache or changes buffers. */
public final class DhPayloadTrace {
    private static final boolean FLIGHT = Boolean.getBoolean("virgos.dh.trace.flight");
    private static final boolean ENABLED = FLIGHT || Boolean.getBoolean("virgos.dh.trace");
    private static final ThreadLocal<Context> CURRENT = new ThreadLocal<>();
    private static final AtomicReferenceArray<Total> TOTALS = new AtomicReferenceArray<>(2048);
    private static final AtomicReferenceArray<Binding> BINDINGS = new AtomicReferenceArray<>(64);
    private static final AtomicLong untracked = new AtomicLong();
    private static final AtomicLong reflectionFailures = new AtomicLong(), traceSequence = new AtomicLong();
    private DhPayloadTrace() { }
    private static final class RuntimeTrace {
        static final Recorder RECORDER = new Recorder(true,
                Path.of("virgos-qa", "dh-payload-trace.jsonl"), 12000, FLIGHT ? 12000 : 1024,
                TimeUnit.MINUTES.toNanos(5), System::nanoTime, () -> { }, FLIGHT);
        static {
            if (FLIGHT) Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try { RECORDER.close(); }
                catch (InterruptedException error) { Thread.currentThread().interrupt(); }
            }, "Virgos-QA-DH-Flight-Shutdown"));
        }
    }
    private record Context(int receiver, int buffer) { }
    private record Binding(int receiver, int session) { }
    private static final class Total {
        final long key;
        final AtomicLong bytes = new AtomicLong();
        Total(long key) { this.key = key; }
    }

    public static boolean enabled() { return ENABLED; }
    public static Object field(Object object, String name) {
        if (object == null) return null;
        for (Class<?> type = object.getClass(); type != null; type = type.getSuperclass()) {
            try {
                Field field = type.getDeclaredField(name);
                field.setAccessible(true);
                return field.get(object);
            } catch (NoSuchFieldException ignored) {
                // Trackable messages inherit futureId from their base class.
            } catch (Throwable ignored) { reflectionFailures.incrementAndGet(); return null; }
        }
        reflectionFailures.incrementAndGet();
        return null;
    }
    private static int number(Object object) { return object instanceof Number n ? n.intValue() : -1; }
    private static long future(Object object) {
        Object value = field(object, "futureId");
        return value instanceof Number n ? n.longValue() : -1;
    }
    private static int id(Object object) { return object == null ? 0 : System.identityHashCode(object); }
    private static int session(int receiver) {
        for (int i = 0; i < BINDINGS.length(); i++) {
            Binding binding = BINDINGS.get(i);
            if (binding != null && binding.receiver == receiver) return binding.session;
        }
        return 0;
    }
    private static void event(String name, int receiver, int buffer, long future,
                              long bytes, long total, boolean flag, int objectId) {
        if (!ENABLED) return;
        emit(name, receiver, session(receiver), buffer, future, bytes, total, flag, objectId);
    }
    private static void emit(String name, int receiver, int session, int buffer, long future,
                             long bytes, long total, boolean flag, int objectId) {
        try {
            RuntimeTrace.RECORDER.offer(name, receiver, session, buffer, future,
                    bytes, total, flag, objectId);
        } catch (Throwable ignored) { untracked.incrementAndGet(); }
    }
    private static long total(int receiver, int buffer, long bytes, boolean first) {
        long key = ((long) receiver << 32) ^ (buffer & 0xffffffffL);
        int hash = (int) (key ^ (key >>> 32));
        hash ^= hash >>> 16;
        for (int offset = 0; offset < TOTALS.length(); offset++) {
            int slot = (hash + offset) & (TOTALS.length() - 1);
            Total value = TOTALS.get(slot);
            if (value == null) {
                Total created = new Total(key);
                if (!TOTALS.compareAndSet(slot, null, created)) { offset--; continue; }
                value = created;
            }
            if (value.key == key) {
                if (first) value.bytes.set(0);
                return value.bytes.addAndGet(Math.max(0, bytes));
            }
        }
        untracked.incrementAndGet();
        return -1;
    }

    public static void bind(Object state) {
        if (!ENABLED) return;
        Object receiver = field(state, "fullDataPayloadReceiver");
        int receiverId = id(receiver), sessionId = id(field(state, "networkSession"));
        for (int i = 0; i < BINDINGS.length(); i++) {
            if (BINDINGS.compareAndSet(i, null, new Binding(receiverId, sessionId))) {
                emit("receiver_session", receiverId, sessionId, -1, -1, 0, 0, true, 0);
                return;
            }
        }
        untracked.incrementAndGet();
    }
    public static void fragment(Object receiver, Object message) {
        if (!ENABLED) return;
        int buffer = number(field(message, "bufferId")), owner = id(receiver);
        CURRENT.set(new Context(owner, buffer));
        long bytes = -1;
        Object buf = field(message, "buffer");
        try {
            // Index getter only: no reads of payload bytes, index mutation or refcount operations.
            bytes = ((Number) buf.getClass().getMethod("writerIndex").invoke(buf)).longValue();
        } catch (Throwable ignored) { untracked.incrementAndGet(); }
        boolean first = Boolean.TRUE.equals(field(message, "isFirst"));
        event("fragment_arrival", owner, buffer, -1, bytes, total(owner, buffer, bytes, first), first, id(buf));
    }
    public static void compute(Object composite, String seam) {
        if (!ENABLED) return;
        Context context = CURRENT.get();
        if (context != null) event(seam, context.receiver, context.buffer, -1, 0, 0,
                composite != null, id(composite));
    }
    public static void fragmentReturn() {
        if (!ENABLED) return;
        Context context = CURRENT.get();
        if (context != null) event("fragment_return", context.receiver, context.buffer, -1, 0, 0, true, 0);
        CURRENT.remove();
    }
    public static void decode(Object receiver, Object payload) {
        if (!ENABLED) return;
        int buffer = number(field(payload, "dtoBufferId"));
        CURRENT.set(new Context(id(receiver), buffer));
        event("decode_start", id(receiver), buffer, -1, 0, 0, true, 0);
    }
    /** ModifyArg observation: MUST return the identical native argument, including null. */
    public static Object observeNativeLookup(Object value) {
        if (ENABLED) {
            Context context = CURRENT.get();
            if (context != null) event("native_cache_lookup", context.receiver, context.buffer,
                    -1, 0, 0, value != null, id(value));
            if (value == null && FLIGHT) RuntimeTrace.RECORDER.flushOnFailure();
        }
        return value;
    }
    public static void remove(Object receiver, Object payload) {
        if (!ENABLED) return;
        event("native_remove_attempt", id(receiver), number(field(payload, "dtoBufferId")), -1, 0, 0, true, 0);
    }
    public static void removed(Object receiver, Object payload) {
        if (ENABLED) event("native_remove_return", id(receiver), number(field(payload, "dtoBufferId")), -1, 0, 0, true, 0);
    }
    public static void decoded() {
        if (!ENABLED) return;
        Context context = CURRENT.get();
        if (context != null) event("decode_return", context.receiver, context.buffer, -1, 0, 0, true, 0);
        CURRENT.remove();
    }
    public static void closed(Object receiver) {
        if (ENABLED) event("receiver_close", id(receiver), -1, -1, 0, 0, true, 0);
    }
    public static void arrival(Object nativeSession, Object message) {
        if (!ENABLED || message == null) return;
        String type = message.getClass().getSimpleName();
        if (!type.equals("FullDataSourceResponseMessage") && !type.equals("FullDataPartialUpdateMessage")) return;
        Object payload = field(message, "payload");
        emit(type.equals("FullDataSourceResponseMessage") ? "response_arrival" : "partial_arrival",
                0, id(nativeSession), number(field(payload, "dtoBufferId")),
                type.equals("FullDataSourceResponseMessage") ? future(message) : -1, 0, 0, payload != null, 0);
    }
    static boolean fixtureTarget(Object request) {
        // Pinned DH encode(section detail 6, x=4, z=0): database detail zero.
        Object pos = field(request, "pos");
        return pos instanceof Number n && n.longValue() == 1030L;
    }
    public static void compression(Object queue, Object request, Object response) {
        if (!ENABLED) return;
        Object state = field(queue, "networkState"), payload = field(response, "payload");
        Object receiver = field(state, "fullDataPayloadReceiver");
        event("request_target_section", id(receiver), number(field(payload, "dtoBufferId")),
                future(response), 0, 0, fixtureTarget(request), 0);
        event("compression_callback", id(receiver), number(field(payload, "dtoBufferId")), future(response), 0, 0, payload != null, 0);
    }
    public static String stats() {
        return ENABLED ? RuntimeTrace.RECORDER.summary() : "{\"enabled\":false}";
    }

    /** Pure bounded logger. All filesystem work belongs to one daemon, never DH callers. */
    static final class Recorder implements AutoCloseable {
        private final boolean enabled;
        private final Path output;
        private final int maxRecords;
        private final long duration, start;
        private final LongSupplier clock;
        private record Observation(String event, long timeNs, long wallMs, int receiver,
                int session, int buffer, long future, long bytes, long total, boolean flag, int objectId) {
            String json(String traceId) {
                return "{\"traceId\":" + quote(traceId) + ",\"event\":" + quote(event) +
                        ",\"timeNs\":" + timeNs + ",\"wallMs\":" + wallMs +
                        ",\"receiver\":" + receiver + ",\"session\":" + session + ",\"buffer\":" + buffer +
                        ",\"future\":" + future + ",\"bytes\":" + bytes + ",\"total\":" + total +
                        ",\"flag\":" + flag + ",\"objectId\":" + objectId + "}";
            }
        }
        private final ArrayBlockingQueue<Observation> queue;
        private final AtomicLong accepted = new AtomicLong(), dropped = new AtomicLong(), ioFailures = new AtomicLong();
        private final AtomicLong serialized = new AtomicLong();
        private final AtomicBoolean writerStarted = new AtomicBoolean();
        private final String traceId = Long.toHexString(System.nanoTime()) + "-" + traceSequence.incrementAndGet();
        private final Runnable beforeWrite;
        private final boolean flight;
        private volatile Thread writer;
        private volatile boolean closed;
        Recorder(boolean enabled, Path output, int maxRecords, int capacity, long duration, LongSupplier clock) {
            this(enabled, output, maxRecords, capacity, duration, clock, () -> { });
        }
        Recorder(boolean enabled, Path output, int maxRecords, int capacity, long duration,
                 LongSupplier clock, Runnable beforeWrite) {
            this(enabled, output, maxRecords, capacity, duration, clock, beforeWrite, false);
        }
        Recorder(boolean enabled, Path output, int maxRecords, int capacity, long duration,
                 LongSupplier clock, Runnable beforeWrite, boolean flight) {
            this.enabled = enabled; this.output = output; this.maxRecords = maxRecords;
            this.duration = duration; this.clock = clock; this.start = clock.getAsLong();
            this.queue = new ArrayBlockingQueue<>(capacity);
            this.beforeWrite = beforeWrite;
            this.flight = flight;
        }
        boolean offer(String event, int receiver, int session, int buffer, long future,
                      long bytes, long total, boolean flag) {
            return offer(event, receiver, session, buffer, future, bytes, total, flag, 0);
        }
        boolean offer(String event, int receiver, int session, int buffer, long future,
                      long bytes, long total, boolean flag, int objectId) {
            if (!enabled) return false;
            if (closed || clock.getAsLong() - start >= duration || accepted.getAndIncrement() >= maxRecords) {
                dropped.incrementAndGet(); return false;
            }
            Observation line = new Observation(event, clock.getAsLong() - start, System.currentTimeMillis(),
                    receiver, session, buffer, future, bytes, total, flag, objectId);
            if (!queue.offer(line)) {
                if (!flight) { dropped.incrementAndGet(); return false; }
                if (queue.poll() != null) dropped.incrementAndGet();
                if (!queue.offer(line)) { dropped.incrementAndGet(); return false; }
            }
            if (!flight) startWriter();
            return true;
        }
        void flushOnFailure() {
            if (enabled && accepted.get() > 0) startWriter();
        }
        private void startWriter() {
            if (!writerStarted.compareAndSet(false, true)) return;
            writer = new Thread(this::writeLoop, "Virgos-QA-DH-Payload-Trace");
            writer.setDaemon(true);
            writer.start();
        }
        private void writeLoop() {
            try {
                beforeWrite.run();
                Files.createDirectories(output.getParent());
                try (BufferedWriter sink = Files.newBufferedWriter(output, StandardOpenOption.CREATE, StandardOpenOption.APPEND)) {
                    long lastFlush = System.nanoTime();
                    while ((!closed && clock.getAsLong() - start < duration) || !queue.isEmpty()) {
                        Observation line = queue.poll(100, TimeUnit.MILLISECONDS);
                        if (line != null) { sink.write(line.json(traceId)); serialized.incrementAndGet(); sink.newLine(); }
                        if (System.nanoTime() - lastFlush >= TimeUnit.SECONDS.toNanos(1)) {
                            sink.write(summary()); sink.newLine(); sink.flush(); lastFlush = System.nanoTime();
                        }
                    }
                    sink.write(summary()); sink.newLine();
                }
            } catch (Throwable ignored) { ioFailures.incrementAndGet(); closed = true; }
        }
        long droppedCount() { return dropped.get(); }
        long serializedCount() { return serialized.get(); }
        boolean writerAlive() { return writer != null && writer.isAlive(); }
        boolean writerDaemon() { return writer != null && writer.isDaemon(); }
        String summary() {
            return "{\"traceId\":" + quote(traceId) + ",\"event\":\"trace_summary\",\"budgetUsed\":" +
                    Math.min(maxRecords, accepted.get()) + ",\"dropped\":" + dropped.get() +
                    ",\"ioFailures\":" + ioFailures.get() + ",\"untracked\":" + untracked.get() +
                    ",\"reflectionFailures\":" + reflectionFailures.get() + ",\"maxRecords\":" + maxRecords +
                    ",\"durationNs\":" + duration + "}";
        }
        @Override public void close() throws InterruptedException {
            closed = true;
            if (flight) flushOnFailure();
            if (writer != null) writer.join(2000); // Tests only; runtime never joins a native callback.
        }
        private static String quote(String value) {
            StringBuilder result = new StringBuilder("\"");
            for (int i = 0; i < Math.min(value.length(), 64); i++) {
                char ch = value.charAt(i);
                switch (ch) {
                    case '\\' -> result.append("\\\\");
                    case '"' -> result.append("\\\"");
                    case '\n' -> result.append("\\n");
                    case '\r' -> result.append("\\r");
                    case '\t' -> result.append("\\t");
                    default -> { if (ch < 32) result.append(String.format("\\u%04x", (int) ch)); else result.append(ch); }
                }
            }
            return result.append('"').toString();
        }
    }
}
