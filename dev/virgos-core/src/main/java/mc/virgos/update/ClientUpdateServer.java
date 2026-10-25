package mc.virgos.update;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/** Enforces the client release before AuthMe can unlock gameplay. */
public final class ClientUpdateServer {
    private static final long TIMEOUT_MS = 10_000;
    private final ClientReleaseGate.Policy policy;
    private final Map<UUID, Long> pending = new HashMap<>();
    private final Map<UUID, String> accepted = new HashMap<>();

    private ClientUpdateServer(ClientReleaseGate.Policy policy) { this.policy = policy; }

    public static ClientUpdateServer load(Path path, Gson gson) {
        try {
            JsonObject json = gson.fromJson(Files.readString(path), JsonObject.class);
            return new ClientUpdateServer(new ClientReleaseGate.Policy(
                json.get("release").getAsString(),
                json.get("fingerprint").getAsString(),
                json.get("installer").getAsString()));
        } catch (Exception exception) {
            throw new IllegalStateException("Client update policy is unavailable: " + path, exception);
        }
    }

    public void begin(ServerPlayer player) {
        UUID id = player.getUUID();
        if (accepted.containsKey(id)) return;
        pending.put(id, System.currentTimeMillis());
    }

    public void receive(UpdateProtocol.Context message) {
        ServerPlayer player = message.network().get().getSender();
        if (player == null) return;
        ClientReleaseGate.Decision decision = ClientReleaseGate.check(policy, message.hello().release(), message.hello().fingerprint());
        if (decision.accepted()) {
            pending.remove(player.getUUID());
            accepted.put(player.getUUID(), policy.release());
            return;
        }
        reject(player, message.hello().release(), decision.reason());
    }

    public void tick(MinecraftServer server) {
        pending.keySet().removeIf(id -> server.getPlayerList().getPlayer(id) == null);
        expirePending(pending, System.currentTimeMillis(), id -> {
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            if (player != null) reject(player, null, "missing-client");
        });
    }

    static void expirePending(Map<UUID, Long> pending, long now, Consumer<UUID> reject) {
        var expired = new ArrayList<UUID>();
        pending.entrySet().removeIf(entry -> {
            if (now - entry.getValue() < TIMEOUT_MS) return false;
            expired.add(entry.getKey());
            return true;
        });
        // Disconnect can synchronously trigger logout and modify pending again.
        // Finish every iterator operation before invoking external callbacks.
        expired.forEach(reject);
    }

    public boolean accepted(ServerPlayer player) { return accepted.containsKey(player.getUUID()); }

    public void detach(ServerPlayer player) {
        pending.remove(player.getUUID());
        accepted.remove(player.getUUID());
    }

    public String release() { return policy.release(); }

    private void reject(ServerPlayer player, String release, String reason) {
        pending.remove(player.getUUID());
        accepted.remove(player.getUUID());
        if (player.connection.connection.isConnected()) {
            player.connection.disconnect(Component.literal(ClientReleaseGate.disconnectMessage(policy, release, reason)));
        }
    }
}
