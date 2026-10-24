package mc.virgos.update;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

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
        long now = System.currentTimeMillis();
        pending.entrySet().removeIf(entry -> {
            ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
            if (player == null) return true;
            if (now - entry.getValue() < TIMEOUT_MS) return false;
            reject(player, null, "missing-client");
            return true;
        });
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
