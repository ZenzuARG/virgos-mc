package mc.virgos.update;

import java.util.Objects;

/** Pure release comparison shared by the server gate and compatibility tests. */
public final class ClientReleaseGate {
    private ClientReleaseGate() {}

    public record Policy(String release, String fingerprint, String installer) {
        public Policy {
            release = require(release, "release");
            fingerprint = require(fingerprint, "fingerprint");
            installer = require(installer, "installer");
        }

        private static String require(String value, String name) {
            if (value == null || value.isBlank() || value.length() > 160) {
                throw new IllegalArgumentException("Invalid " + name);
            }
            return value;
        }
    }

    public record Decision(boolean accepted, String reason) {}

    public static Decision check(Policy policy, String release, String fingerprint) {
        Objects.requireNonNull(policy, "policy");
        if (release == null || fingerprint == null) return new Decision(false, "missing-client");
        if (!policy.release().equals(release)) return new Decision(false, "release-mismatch");
        if (!policy.fingerprint().equals(fingerprint)) return new Decision(false, "fingerprint-mismatch");
        return new Decision(true, "accepted");
    }

    public static String disconnectMessage(Policy policy, String receivedRelease, String reason) {
        String client = receivedRelease == null || receivedRelease.isBlank() ? "sin Códice" : receivedRelease;
        return "Virgos-MC necesita una actualización. Cliente: " + client + ". Servidor: " + policy.release()
            + ". Descargá " + policy.installer() + " y volvé a conectarte. Motivo: " + reason + ".";
    }
}
