package mc.virgos.dhcompat;

/** Implemented only by the client-world mixin; called after native world setup. */
public interface DeferredConfigWorld {
    void virgos$sendInitialConfig();
}
