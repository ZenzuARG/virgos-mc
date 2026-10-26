package mc.virgos.addonsqa;

import java.util.ArrayList;
import java.util.Collections;

/** Nearest-rank quantiles of real measured intervals, never nominal target ticks. */
public final class SampleWindow {
    private final ArrayList<Long> nanos = new ArrayList<>();
    private long deadline;
    public void start(int seconds, long now) {
        if (seconds < 30 || seconds > 300) throw new IllegalArgumentException("seconds must be 30..300");
        nanos.clear(); deadline = now + seconds * 1_000_000_000L;
    }
    public void add(long value) {
        if (value < 0 || nanos.size() >= 1_000_000) throw new IllegalArgumentException("invalid/bounded interval");
        nanos.add(value);
    }
    public boolean expired(long now) { return now >= deadline; }
    public Summary summary() {
        if (nanos.isEmpty()) return new Summary(0, 0, 0, 0, 0, 0);
        var sorted = new ArrayList<>(nanos); Collections.sort(sorted);
        double average = nanos.stream().mapToDouble(Long::doubleValue).average().orElse(0) / 1e6;
        return new Summary(sorted.size(), percentile(sorted, .5), percentile(sorted, .95),
            sorted.get(sorted.size()-1) / 1e6, average, average == 0 ? 0 : 1000 / average);
    }
    private static double percentile(ArrayList<Long> values, double quantile) {
        return values.get(Math.max(0, (int)Math.ceil(values.size()*quantile)-1)) / 1e6;
    }
    public record Summary(int count, double medianMs, double p95Ms, double maxMs, double averageMs, double averageFps) { }
}
