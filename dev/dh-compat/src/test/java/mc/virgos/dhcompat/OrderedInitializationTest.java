package mc.virgos.dhcompat;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public final class OrderedInitializationTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        List<String> events = new ArrayList<>();
        ArrayDeque<Runnable> queue = new ArrayDeque<>();
        queue.add(() -> events.add("enable"));
        OrderedInitialization.onEventLoop(() -> false, queue::add, () -> events.add("disable"));
        queue.add(() -> events.add("send"));
        check(events.isEmpty(), "Off-loop transition must not mutate channel state on caller thread");
        while (!queue.isEmpty()) queue.remove().run();
        check(events.equals(List.of("enable", "disable", "send")), "Transition must follow existing enable and precede queued send");

        events.clear();
        OrderedInitialization.onEventLoop(() -> true, queue::add, () -> events.add("disable"));
        check(events.equals(List.of("disable")) && queue.isEmpty(), "Already-on-loop behavior must stay immediate");

        events.clear();
        var initial = new OrderedInitialization.InitialConfig();
        initial.defer(() -> events.add("config"));
        check(events.isEmpty(), "Constructor must not send config before publication");
        events.add("published");
        events.add("pools-ready");
        initial.published();
        initial.published();
        check(events.equals(List.of("published", "pools-ready", "config")), "Initial config must send once after publication and pool setup");
        new OrderedInitialization.InitialConfig().published();
        System.out.println("Ordered initialization: off-loop FIFO, immediate control, deferred once-only config passed");
    }
}
