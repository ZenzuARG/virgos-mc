package mc.virgos.qa;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.CountDownLatch;

/** Pure QA trace tests; never starts Minecraft or touches installed profiles. */
public final class DhPayloadTraceTest {
    private static int checks;
    private static void check(boolean result, String message) {
        if (!result) throw new AssertionError(message);
        checks++;
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 1 && args[0].equals("identity-enabled")) {
            check(DhPayloadTrace.enabled(), "Enabled identity probe requires explicit opt-in");
            DhPayloadTrace.decode(new Object(), new Payload());
            Object marker = new Object();
            check(DhPayloadTrace.observeNativeLookup(marker) == marker, "Enabled observer changed native object identity");
            Object missing = DhPayloadTrace.observeNativeLookup(null);
            check(missing == null, "Enabled observer repaired native null");
            try {
                java.util.Objects.requireNonNull(missing, "native missing buffer");
                throw new AssertionError("Native missing-buffer failure was suppressed");
            } catch (NullPointerException expected) {
                check(expected.getMessage().equals("native missing buffer"), "Native failure changed");
            }
            System.out.println(checks + " enabled argument-identity checks passed.");
            return;
        }
        Path scratch = Files.createTempDirectory("virgos-dh-payload-trace-");
        System.out.println("SCRATCH=" + scratch);
        Path disabledPath = scratch.resolve("disabled/virgos-qa/dh-payload-trace.jsonl");
        try (var disabled = new DhPayloadTrace.Recorder(false, disabledPath, 4, 4,
                TimeUnit.SECONDS.toNanos(1), System::nanoTime)) {
            check(!disabled.offer("fragment", 1, 2, 3, 4, 5, 6, false), "Disabled trace accepted an event");
            check(!disabled.writerAlive(), "Disabled trace started a writer");
        }
        check(!Files.exists(disabledPath.getParent()), "Disabled trace performed filesystem I/O");
        Object marker = new Object();
        check(DhPayloadTrace.observeNativeLookup(marker) == marker, "Native non-null identity changed");
        check(DhPayloadTrace.observeNativeLookup(null) == null, "Native null was repaired");

        long[] now = {0};
        Path output = scratch.resolve("enabled/virgos-qa/dh-payload-trace.jsonl");
        try (var recorder = new DhPayloadTrace.Recorder(true, output, 2, 8, 10, () -> now[0])) {
            check(recorder.offer("first\n\"fragment", 1, 2, 3, 4, 5, 6, true), "Enabled event rejected");
            check(recorder.offer("response", 1, 2, 3, 4, 0, 6, false), "Second event rejected");
            check(!recorder.offer("overflow", 1, 2, 3, 4, 0, 6, false), "Record cap ignored");
            check(recorder.droppedCount() == 1, "Record-cap drop not counted");
        }
        String text = Files.readString(output);
        check(text.contains("first\\n\\\"fragment"), "JSON escaping failed");
        check(text.contains("\"event\":\"trace_summary\"") && text.contains("\"dropped\":1"), "Drop summary missing");
        check(text.lines().count() == 3, "Unexpected output record count");

        Path duration = scratch.resolve("duration/virgos-qa/dh-payload-trace.jsonl");
        try (var recorder = new DhPayloadTrace.Recorder(true, duration, 8, 8, 10, () -> now[0])) {
            now[0] = 11;
            check(!recorder.offer("late", 1, 2, 3, 4, 0, 0, false), "Duration cap ignored");
            check(recorder.droppedCount() == 1, "Duration drop not counted");
        }
        check(!Files.exists(duration), "Expired trace unexpectedly opened a writer");
        CountDownLatch releaseWriter = new CountDownLatch(1);
        Path bounded = scratch.resolve("bounded/virgos-qa/dh-payload-trace.jsonl");
        try (var recorder = new DhPayloadTrace.Recorder(true, bounded, 8, 1,
                TimeUnit.SECONDS.toNanos(5), System::nanoTime, () -> {
                    try { releaseWriter.await(); } catch (InterruptedException error) { Thread.currentThread().interrupt(); }
                })) {
            check(recorder.offer("first", 1, 2, 3, 4, 5, 6, true), "First queue event rejected");
            long started = System.nanoTime();
            check(!recorder.offer("full", 1, 2, 3, 4, 5, 6, true), "Full queue unexpectedly accepted event");
            check(recorder.writerDaemon(), "Trace writer can prolong JVM shutdown");
            check(System.nanoTime() - started < TimeUnit.SECONDS.toNanos(1), "Overflow offer blocked on writer");
            check(recorder.droppedCount() == 1, "Queue drop not counted");
            releaseWriter.countDown();
        } finally { releaseWriter.countDown(); }
        check(Files.readString(bounded).contains("\"dropped\":1"), "Queue overflow absent from summary");
        Path invalidSink = scratch.resolve("directory-not-a-file");
        Files.createDirectories(invalidSink);
        try (var recorder = new DhPayloadTrace.Recorder(true, invalidSink, 8, 8,
                TimeUnit.SECONDS.toNanos(1), System::nanoTime)) {
            recorder.offer("io_failure", 1, 2, 3, 4, 0, 0, true);
            recorder.close();
            check(recorder.summary().contains("\"ioFailures\":1"), "Asynchronous I/O failure is invisible");
        }
        DhPayloadTrace.fragment(new Object(), new Payload());
        check(!Files.exists(Path.of("virgos-qa/dh-payload-trace.jsonl")), "Disabled global observer performed I/O");
        check(DhPayloadTrace.field(new Payload(), "bufferId") == null, "Missing field should remain unknown");
        Path flight = scratch.resolve("flight/trace.jsonl");
        try (var recorder = new DhPayloadTrace.Recorder(true, flight, 8, 2,
                TimeUnit.SECONDS.toNanos(5), System::nanoTime, () -> { }, true)) {
            check(recorder.offer("old", 1, 2, 3, 4, 0, 0, true), "Flight first event rejected");
            check(recorder.offer("recent", 1, 2, 3, 4, 0, 0, true), "Flight second event rejected");
            check(recorder.offer("latest", 1, 2, 3, 4, 0, 0, true), "Flight overwrite rejected");
            check(!recorder.writerAlive() && !Files.exists(flight), "Flight mode wrote before failure/close");
            check(recorder.serializedCount() == 0, "Flight callback serialized JSON before flush");
            check(recorder.droppedCount() == 1, "Flight overwrite was not counted");
        }
        String flightText = Files.readString(flight);
        check(!flightText.contains("\"event\":\"old\"") && flightText.contains("\"event\":\"latest\""), "Flight did not retain recent events");
        Path failure = scratch.resolve("failure/trace.jsonl");
        try (var recorder = new DhPayloadTrace.Recorder(true, failure, 8, 8,
                TimeUnit.SECONDS.toNanos(5), System::nanoTime, () -> { }, true)) {
            recorder.offer("missing", 1, 2, 3, 4, 0, 0, false);
            recorder.flushOnFailure();
            check(recorder.writerDaemon(), "Failure flush started a non-daemon writer");
        }
        check(Files.readString(failure).contains("\"event\":\"missing\""), "Failure event was not flushed");
        check(DhPayloadTrace.fixtureTarget(new Request(1030L)), "Target request was not identified");
        check(!DhPayloadTrace.fixtureTarget(new Request(774L)), "Other section was identified as target");
        check(!DhPayloadTrace.fixtureTarget(null), "Missing request was identified as target");
        System.out.println(checks + " pure trace checks passed.");
    }
    private static final class Payload { private final int dtoBufferId = 7; }
    private static final class Request {
        private final long pos;
        Request(long pos) { this.pos = pos; }
    }
}
