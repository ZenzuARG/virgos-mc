package mc.virgos.qa;

import java.util.HashSet;
import java.util.Set;

/** Bounded opt-in input ownership; no Minecraft, network or world mutation API. */
public final class CaptureLease {
    public record Target(int x, int y, int z) {}
    public record Scene(String endpoint, boolean focused, boolean inGame, boolean alive, Target target) {}
    public interface Input {
        void grab();
        boolean captured();
        void click();
        void down(boolean value);
        void release();
    }
    private final Input input;
    private final Set<String> used = new HashSet<>();
    private boolean active;
    private boolean armed;
    private int remaining;
    private long deadline;
    private String id, reason;
    private Target expected;

    public CaptureLease(Input input) { this.input = java.util.Objects.requireNonNull(input); }
    public boolean active() { return active; }
    public boolean armed() { return active && armed; }
    public String id() { return id; }
    public String reason() { return reason; }
    public Target expected() { return expected; }
    public int remaining() { return remaining; }

    private static boolean safe(Scene scene) {
        return scene != null && "127.0.0.1:25575".equals(scene.endpoint())
            && scene.focused() && scene.inGame() && scene.alive();
    }
    /** All preconditions are checked before input or ownership changes. */
    public void start(String id, int ticks, Target expected, Scene scene, long now) {
        if (active) throw new IllegalStateException("Capture already active");
        if (id == null || !id.matches("[A-Za-z0-9_-]{1,48}") || used.contains(id) || used.size() >= 256)
            throw new IllegalArgumentException("Invalid or duplicate capture id");
        if (ticks < 1 || ticks > 100 || expected == null || !safe(scene) || !expected.equals(scene.target()))
            throw new IllegalArgumentException("Capture precondition failed");
        this.id=id; this.expected=expected; remaining=ticks; deadline=now+10_000_000_000L;
        reason="warmup"; used.add(id); active=true; armed=false;
        try {
            input.down(false);
            input.grab();
            if (!input.captured()) throw new IllegalStateException("Mouse capture failed");

        } catch (RuntimeException failure) {
            cancel("input_error");
            throw failure;
        }
    }
    /** Render observations enforce wall time even when client ticks stall. */
    public void observe(Scene scene, long now) {
        if (!active) return;
        if (!safe(scene)) cancel("scene_interrupted");
        else if (!input.captured()) cancel("capture_lost");
        else if (now-deadline >= 0) cancel("wall_timeout");
    }
    public void tick(Scene scene, long now) {
        observe(scene, now);
        if (!active) return;
        if (!armed) {
            // Only the next ClientTick.END enters this branch. The intervening
            // Minecraft tick processes idle continueAttack(false) naturally.
            if (!expected.equals(scene.target())) {
                cancel("target_changed");
                return;
            }
            try {
                input.click();
                input.down(true);
                armed=true;
                reason="armed";
            } catch (RuntimeException failure) {
                cancel("input_error");
                throw failure;
            }
            return; // Warmup does not consume any requested held-input ticks.
        }
        if (--remaining <= 0) cancel("completed");
    }
    public void cancel(String reason) {
        if (!active) return;
        active=false; remaining=0; this.reason=reason;
        try { input.down(false); } finally { input.release(); }
    }
}
