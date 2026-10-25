package mc.virgos.dhcompat;

/** Holds constructor publication callbacks, never packets or network payloads. */
public final class DeferredLevelPublication {
    private final OrderedInitialization.InitialConfig wrapper = new OrderedInitialization.InitialConfig();
    private final OrderedInitialization.InitialConfig handlers = new OrderedInitialization.InitialConfig();
    private boolean completed;

    public void deferWrapper(Runnable publish) {
        checkConstructing();
        wrapper.defer(publish);
    }

    public void deferHandlers(Runnable register) {
        checkConstructing();
        handlers.defer(register);
    }

    public void complete() {
        if (completed) return;
        completed = true;
        wrapper.published();
        handlers.published();
    }

    private void checkConstructing() {
        if (completed) throw new IllegalStateException("Level publication already completed");
    }
}
