package mc.virgos;

import mc.virgos.update.ClientReleaseGate;

/** Dependency-free regression tests for current, stale, and missing clients. */
public final class ClientReleaseGateTest {
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }

    public static void main(String[] args) {
        var policy = new ClientReleaseGate.Policy("2.0.0-r11", "virgos-client-2.0.0-r11", "Virgos-MC-2.0.0-instalar.zip");
        check(ClientReleaseGate.check(policy, "2.0.0-r11", "virgos-client-2.0.0-r11").accepted(), "Current client must pass");
        check(!ClientReleaseGate.check(policy, "2.0.0-r10", "virgos-client-2.0.0-r10").accepted(), "Old release must fail");
        check(!ClientReleaseGate.check(policy, null, null).accepted(), "Missing Códice must fail");
        check(ClientReleaseGate.disconnectMessage(policy, null, "missing-client").contains("sin Códice"), "Missing client message must explain the cause");
        check(ClientReleaseGate.disconnectMessage(policy, "2.0.0-r10", "release-mismatch").contains("Virgos-MC-2.0.0-instalar.zip"), "Stale client message must name the installer");
        System.out.println("Client release gate: current, stale, and missing-client checks passed");
    }
}
