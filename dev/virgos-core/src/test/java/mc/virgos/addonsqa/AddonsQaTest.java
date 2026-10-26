package mc.virgos.addonsqa;

import java.nio.file.Path;

public final class AddonsQaTest {
    private static void check(boolean value) { if (!value) throw new AssertionError(); }
    private static void rejects(Runnable action) {
        try { action.run(); throw new AssertionError("accepted invalid input"); }
        catch (IllegalArgumentException expected) { }
    }
    public static void main(String[] args) {
        var sample = new SampleWindow();
        sample.start(30, 100);
        for (int i = 1; i <= 20; i++) sample.add(i * 1_000_000L);
        var values = sample.summary();
        check(values.count() == 20 && values.medianMs() == 10 && values.p95Ms() == 19 && values.maxMs() == 20);
        check(values.averageMs() == 10.5);
        check(Math.abs(values.averageFps() - 1000.0 / 10.5) < 0.0001);
        sample.start(300, 200); check(sample.summary().count() == 0);
        check(!sample.expired(200) && sample.expired(300_000_000_200L));
        rejects(() -> sample.start(29, 0)); rejects(() -> sample.start(301, 0));
        rejects(() -> sample.add(-1));
        check(LabGuard.allowedCanonical(Path.of("D:/proyectos/mc-server-lab/create-addons-20261025/baseline/server"), true, 25575, "virgos_world"));
        check(!LabGuard.allowedCanonical(Path.of("D:/proyectos/mc-server"), true, 25575, "virgos_world"));
        check(!LabGuard.allowedCanonical(Path.of("D:/proyectos/mc-server-lab/create-addons-20261025/baseline/server"), false, 25575, "virgos_world"));
        check(!LabGuard.allowedCanonical(Path.of("D:/proyectos/mc-server-lab/create-addons-20261025/baseline/server"), true, 25565, "virgos_world"));
        check(!LabGuard.allowedCanonical(Path.of("D:/proyectos/mc-server-lab/create-addons-20261025/other/server"), true, 25575, "virgos_world"));
        LabGuard.position(32, 60, -32); LabGuard.position(160, 100, 96);
        rejects(() -> LabGuard.position(31, 60, 0)); rejects(() -> LabGuard.position(32, 101, 0));
        check(LabGuard.id("sample-1")); check(!LabGuard.id("../escape"));
        System.out.println("Addons QA statistics and guard contracts PASS");
    }
}
