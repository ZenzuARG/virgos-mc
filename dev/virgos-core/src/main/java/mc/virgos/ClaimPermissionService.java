package mc.virgos;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import xaero.pac.common.server.api.OpenPACServerAPI;
import xaero.pac.common.server.player.data.api.ServerPlayerDataAPI;
import xaero.pac.common.claims.player.mode.api.ClaimingModes;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigAPI;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigManagerAPI;
import xaero.pac.common.server.player.config.group.api.IServerPlayerConfigGroupManagerAPI;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.LinkedHashMap;
import java.util.function.Consumer;
import com.mojang.authlib.GameProfile;

/** Owns authoritative area policy; native claim ownership and legacy groups remain untouched. */
public final class ClaimPermissionService {
    public enum Group {
        FAMILY("familia", "Familia"), FRIENDS("amigos", "Amigos"), VISITORS("visitantes", "Visitantes");
        public final String id;
        public final String label;
        Group(String id, String label) { this.id = id; this.label = label; }
    }

    public enum Permission {
        STORAGE("storage", "Abrir almacenamiento", List.of(
            "claims.protection.exceptions.groups.block.interact.Chests",
            "claims.protection.exceptions.groups.block.interact.Barrels",
            "claims.protection.exceptions.groups.block.interact.Ender_Chests",
            "claims.protection.exceptions.groups.block.interact.Shulker_Boxes")),
        MACHINES("machines", "Hornos y tolvas", List.of(
            "claims.protection.exceptions.groups.block.interact.Furnaces",
            "claims.protection.exceptions.groups.block.interact.Hoppers")),
        DOORS("doors", "Usar puertas y botones", List.of(
            "claims.protection.exceptions.groups.block.interact.Controls",
            "claims.protection.exceptions.groups.block.interact.Doors")),
        BUILDING("building", "Construir y romper", List.of("claims.protection.exceptions.blocksByPlayers"));

        public final String id;
        public final String label;
        private final List<String> optionIds;
        Permission(String id, String label, List<String> optionIds) { this.id = id; this.label = label; this.optionIds = optionIds; }
    }

    public enum Decision { ALLOW, DENY }

    public record Context(IPlayerConfigAPI config, IServerPlayerConfigGroupManagerAPI groups,
                          UUID owner, String subId, String key, String claimName, String areaId) {
        public Context(IPlayerConfigAPI config, IServerPlayerConfigGroupManagerAPI groups, UUID owner,
                       String subId, String key, String claimName) {
            this(config, groups, owner, subId, key, claimName, key);
        }
        public ClaimPolicyStore.Key parcel() { return ClaimPolicyStore.Key.decode(key); }
    }

    private MinecraftServer server;
    private final ClaimPolicyStore store;

    public ClaimPermissionService() { this(new ClaimPolicyStore()); }
    ClaimPermissionService(ClaimPolicyStore store) { this.store = store; }

    public void initialize(MinecraftServer value) {
        server = value;
        Path root = server.getWorldPath(LevelResource.ROOT);
        if (!store.load(root.resolve("virgos-claim-permissions-v2.json"), root.resolve("virgos-claim-permissions.json")))
            VirgosCore.LOG.error("Claim policy is unavailable; edits and managed grants are blocked", store.failure());
        ClaimProtectionHooks.bind(this::permissionAt, player -> VirgosCore.AUTH.ready()
            && VirgosCore.AUTH.authenticated(player) && VirgosCore.UPDATE_GATE != null
            && VirgosCore.UPDATE_GATE.accepted(player));
    }

    public boolean ready() { return store.healthy(); }

    public boolean protectionEnabled(Context context) {
        return context.config() != null
            && xaero.pac.common.server.config.ServerConfig.CONFIG.claimsEnabled.get()
            && Boolean.TRUE.equals(context.config().getEffective(
                xaero.pac.common.server.player.config.api.v2.PlayerConfigOptions.PROTECT_CLAIMED_CHUNKS));
    }

    public Context current(ServerPlayer player) {
        if (server == null || player == null) return null;
        try {
            Context context = contextAt(player.level().dimension().location(), player.blockPosition());
            return context != null && context.owner().equals(player.getUUID()) ? context : null;
        } catch (RuntimeException unavailable) {
            VirgosCore.LOG.warn("Could not resolve the current parcel", unavailable);
            return null;
        }
    }

    private Context contextAt(ResourceLocation dimension, BlockPos position) {
        var api = OpenPACServerAPI.get(server);
        if (api == null) throw new IllegalStateException("Claim API unavailable");
        var claim = api.getServerClaimsManager().get(dimension, position);
        if (claim == null || claim.getPlayerId() == null) return null;
        var root = api.getPlayerConfigManager().getLoadedConfig(claim.getPlayerId());
        if (root == null) throw new IllegalStateException("Claim configuration unavailable");
        if (root.getType() == xaero.pac.common.server.player.config.api.PlayerConfigType.SERVER) return null;
        int index = claim.getSubConfigIndex();
        if (index != -1 && !root.subConfigExists(index)) throw new IllegalStateException("Missing claim subconfiguration");
        var config = root.getEffectiveSubConfig(index);
        if (config == null) throw new IllegalStateException("Missing effective claim configuration");
        String sub = config.getSubId() == null ? "main" : config.getSubId();
        var parcel = new ClaimPolicyStore.Key(claim.getPlayerId(), dimension.toString(),
            position.getX() >> 4, position.getZ() >> 4, sub);
        return new Context(config, root.getPlayerGroups(), claim.getPlayerId(), sub, parcel.encoded(),
            api.getServerClaimsManager().getFullName(claim).getString(), store.areaId(parcel));
    }

    public ClaimPermissionDecision permissionAt(UUID actor, ResourceLocation dimension, BlockPos position, String permission) {
        if (server == null || !ClaimPolicyRules.PERMISSIONS.contains(permission)) return ClaimPermissionDecision.NATIVE;
        try {
            Context target = contextAt(dimension, position);
            if (target == null || target.owner().equals(actor)) return ClaimPermissionDecision.NATIVE;
            if (!store.healthy()) return ClaimPermissionDecision.DENY;
            JsonObject policy = store.policy(target.parcel());
            return ClaimPolicyRules.decision(policy, actor, permission);
        } catch (RuntimeException unavailable) {
            return ClaimPermissionDecision.DENY;
        }
    }

    public boolean sameContext(ServerPlayer player, Context expected) {
        Context actual = current(player);
        return actual != null && expected != null && actual.key().equals(expected.key())
            && actual.areaId().equals(expected.areaId());
    }

    private boolean mayEdit(ServerPlayer player, Context context) {
        return store.healthy() && player != null && VirgosCore.AUTH.ready()
            && VirgosCore.AUTH.authenticated(player) && VirgosCore.UPDATE_GATE != null
            && VirgosCore.UPDATE_GATE.accepted(player) && sameContext(player, context);
    }

    private boolean edit(Context context, Consumer<JsonObject> mutation) {
        ServerPlayer player = server == null ? null : server.getPlayerList().getPlayer(context.owner());
        return mayEdit(player, context) && store.edit(context.parcel(), mutation);
    }

    public List<ClaimPolicyStore.Key> areaMembers(Context context) {
        return store.areaMembers(context.parcel()).stream().filter(this::owns).toList();
    }

    public List<Context> neighboringAreas(Context context) {
        var key = context.parcel();
        List<Context> result = new ArrayList<>();
        for (int[] offset : new int[][]{{0, -1}, {1, 0}, {0, 1}, {-1, 0}}) {
            try {
                var other = contextAt(new ResourceLocation(key.dimension()),
                    new BlockPos((key.x() + offset[0]) << 4, 0, (key.z() + offset[1]) << 4));
                if (other != null && other.owner().equals(context.owner()) && !other.areaId().equals(context.areaId())
                    && result.stream().noneMatch(existing -> existing.areaId().equals(other.areaId()))) result.add(other);
            } catch (RuntimeException unavailable) { /* An unavailable neighbor is never selectable. */ }
        }
        return List.copyOf(result);
    }

    private boolean owns(ClaimPolicyStore.Key key) {
        try {
            Context actual = contextAt(new ResourceLocation(key.dimension()), new BlockPos(key.x() << 4, 0, key.z() << 4));
            return actual != null && actual.key().equals(key.encoded());
        } catch (RuntimeException unavailable) { return false; }
    }

    public boolean joinAreas(ServerPlayer player, Context current, Context selected, boolean keepCurrent) {
        if (!mayEdit(player, current) || !current.owner().equals(selected.owner()) || !owns(selected.parcel())
            || !store.areaId(selected.parcel()).equals(selected.areaId())) return false;
        return store.join(current.parcel(), selected.parcel(), keepCurrent, this::owns);
    }

    public boolean splitParcel(ServerPlayer player, Context context) {
        return mayEdit(player, context) && store.split(context.parcel());
    }

    public ClaimEntryFlow.Target claimTarget(ServerPlayer player) {
        var chunk = player.chunkPosition();
        String dimension = player.level().dimension().location().toString();
        ClaimEntryFlow.State state = ClaimEntryFlow.State.UNAVAILABLE;
        try {
            if (server != null) {
                var api = OpenPACServerAPI.get(server);
                if (api != null) {
                    var claim = api.getServerClaimsManager().get(player.level().dimension().location(), chunk.x, chunk.z);
                    state = ClaimEntryFlow.classify(claim != null, claim == null ? null : claim.getPlayerId(), player.getUUID());
                }
            }
        } catch (RuntimeException failure) {
            VirgosCore.LOG.warn("Could not inspect the claim-menu target", failure);
        }
        return new ClaimEntryFlow.Target(dimension, chunk.x, chunk.z, state);
    }

    public ClaimEntryFlow.Result claimHere(ServerPlayer player, ClaimEntryFlow.Target opened,
                                          java.util.function.BooleanSupplier admitted) {
        return ClaimEntryFlow.claim(opened, () -> claimTarget(player),
            () -> admitted.getAsBoolean() && personalClaimMode(player),
            // Preserve native limits, protection checks and selected personal subconfiguration.
            // Never use a console source, elevate permissions or call the unguarded manager claim API.
            () -> server.getCommands().performPrefixedCommand(player.createCommandSourceStack().withSuppressedOutput(), "oclaims claim"));
    }

    private boolean personalClaimMode(ServerPlayer player) {
        var nativeData = ServerPlayerDataAPI.from(player);
        if (nativeData == null) return false;
        var impersonation = nativeData.getClaimsImpersonationInfo();
        return ClaimEntryFlow.personalModeAllowed(nativeData.isClaimsAdminMode() || nativeData.isClaimsServerMode()
                || nativeData.isClaimsModeratorMode(), nativeData.getClaimingMode() == ClaimingModes.PLAYER,
            player.getUUID(), impersonation == null ? null : impersonation.getPlayerId(),
            impersonation == null ? null : impersonation.getClaimPlayerId(ClaimingModes.PLAYER));
    }

    private JsonObject policy(Context context) {
        JsonObject value = store.policy(context.parcel());
        return value == null ? new JsonObject() : value;
    }
    public boolean hasPolicy(Context context) { return store.policy(context.parcel()) != null; }

    public boolean isGroupEnabled(Context context, Group group, Permission permission) {
        var value = ClaimPolicyRules.object(groupData(policy(context), group.id, false), "permissions").get(permission.id);
        return value != null && value.getAsBoolean();
    }

    public Set<UUID> members(Context context, Group group) {
        Set<UUID> members = new HashSet<>();
        var data = groupData(policy(context), group.id, false);
        if (data.has("members")) for (var row : data.getAsJsonArray("members"))
            members.add(UUID.fromString(row.getAsJsonObject().get("id").getAsString()));
        return Set.copyOf(members);
    }

    public List<GameProfile> storedPlayers(Context context) {
        var people = new LinkedHashMap<UUID, GameProfile>();
        JsonObject data = policy(context);
        for (Group group : Group.values()) {
            var row = groupData(data, group.id, false);
            if (row.has("members")) for (var entry : row.getAsJsonArray("members")) {
                JsonObject member = entry.getAsJsonObject();
                UUID id = UUID.fromString(member.get("id").getAsString());
                people.put(id, new GameProfile(id, label(member, id)));
            }
        }
        ClaimPolicyRules.object(data, "individuals").entrySet().forEach(entry -> {
            UUID id = UUID.fromString(entry.getKey());
            people.putIfAbsent(id, new GameProfile(id, label(entry.getValue().getAsJsonObject(), id)));
        });
        return List.copyOf(people.values());
    }

    public String memberLabel(Context context, UUID uuid) {
        for (GameProfile profile : storedPlayers(context)) if (profile.getId().equals(uuid)) return profile.getName();
        ServerPlayer online = server == null ? null : server.getPlayerList().getPlayer(uuid);
        return online == null ? uuid.toString().substring(0, 8) : online.getGameProfile().getName();
    }
    private static String label(JsonObject row, UUID id) {
        return row.has("name") ? row.get("name").getAsString() : id.toString().substring(0, 8);
    }

    public ClaimPolicyRules.Effective effectivePermission(Context context, UUID player, Permission permission) {
        return ClaimPolicyRules.effective(policy(context), player, permission.id);
    }
    public boolean isIndividualAllowed(Context context, UUID uuid, Permission permission) {
        return individualDecision(context, uuid, permission) == Decision.ALLOW;
    }
    public Decision individualDecision(Context context, UUID uuid, Permission permission) {
        for (var entry : ClaimPolicyRules.object(policy(context), "individuals").entrySet()) {
            if (!UUID.fromString(entry.getKey()).equals(uuid)) continue;
            var value = ClaimPolicyRules.object(entry.getValue().getAsJsonObject(), "permissions").get(permission.id);
            return value == null ? null : Decision.valueOf(value.getAsString());
        }
        return null;
    }

    public boolean setGroupPermission(Context context, Group group, Permission permission, boolean enabled) {
        return edit(context, row -> groupData(row, group.id, true).getAsJsonObject("permissions").addProperty(permission.id, enabled));
    }
    public boolean setMember(Context context, Group group, ServerPlayer target, boolean included) {
        return setMember(context, group, target.getGameProfile(), included);
    }
    public boolean setMember(Context context, Group group, GameProfile target, boolean included) {
        return edit(context, row -> {
            JsonArray members = groupData(row, group.id, true).getAsJsonArray("members");
            for (int i = members.size() - 1; i >= 0; i--)
                if (target.getId().equals(UUID.fromString(members.get(i).getAsJsonObject().get("id").getAsString()))) members.remove(i);
            if (included) {
                JsonObject member = new JsonObject();
                member.addProperty("id", target.getId().toString());
                member.addProperty("name", target.getName() == null ? target.getId().toString().substring(0, 8) : target.getName());
                members.add(member);
            }
        });
    }
    public boolean setIndividual(Context context, ServerPlayer target, Permission permission, Decision decision) {
        return setIndividual(context, target.getGameProfile(), permission, decision);
    }
    public boolean setIndividual(Context context, GameProfile target, Permission permission, Decision decision) {
        return edit(context, row -> {
            JsonObject people = mutableObject(row, "individuals");
            JsonObject person = new JsonObject();
            String oldKey = null;
            for (var entry : people.entrySet()) if (UUID.fromString(entry.getKey()).equals(target.getId())) {
                person = entry.getValue().getAsJsonObject();
                oldKey = entry.getKey();
                break;
            }
            if (oldKey != null) people.remove(oldKey);
            people.add(target.getId().toString(), person);
            person.addProperty("name", target.getName() == null ? target.getId().toString().substring(0, 8) : target.getName());
            JsonObject permissions = mutableObject(person, "permissions");
            if (decision == null) permissions.remove(permission.id);
            else permissions.addProperty(permission.id, decision.name());
        });
    }

    /** Retained only to identify legacy native groups; new policy never mutates them. */
    static String nativeGroupId(Permission permission) { return "virgos_" + permission.id; }
    private static JsonObject mutableObject(JsonObject parent, String name) {
        if (!parent.has(name)) parent.add(name, new JsonObject());
        return parent.getAsJsonObject(name);
    }
    private static JsonObject groupData(JsonObject policy, String id, boolean create) {
        JsonObject groups = create ? mutableObject(policy, "groups") : ClaimPolicyRules.object(policy, "groups");
        if (!groups.has(id)) {
            if (!create) return new JsonObject();
            JsonObject row = new JsonObject();
            row.add("members", new JsonArray());
            row.add("permissions", new JsonObject());
            groups.add(id, row);
        }
        JsonObject row = groups.getAsJsonObject(id);
        if (create) {
            if (!row.has("members")) row.add("members", new JsonArray());
            mutableObject(row, "permissions");
        }
        return row;
    }
}
