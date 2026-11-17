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
import xaero.pac.common.server.claims.player.api.IServerPlayerClaimInfoAPI;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigAPI;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigManagerAPI;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigOptionSpecAPI;
import xaero.pac.common.server.player.config.group.custom.api.ICustomPlayerConfigGroupAPI;
import xaero.pac.common.server.player.config.group.api.IServerPlayerConfigGroupManagerAPI;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Persists the Spanish claim policy and mirrors it into Open Parties and Claims groups. */
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
        MACHINES("machines", "Usar máquinas", List.of(
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
                          UUID owner, String subId, String key, String claimName) {}

    private MinecraftServer server;
    private Path file;
    private JsonObject data = new JsonObject();

    public void initialize(MinecraftServer value) {
        server = value;
        file = server.getWorldPath(LevelResource.ROOT).resolve("virgos-claim-permissions.json");
        try {
            data = Files.exists(file) ? VirgosCore.JSON.fromJson(Files.readString(file), JsonObject.class) : new JsonObject();
            if (data == null) data = new JsonObject();
        } catch (Exception e) {
            data = new JsonObject();
            VirgosCore.LOG.error("Could not load claim permissions; edits will fail closed", e);
        }
    }

    public Context current(ServerPlayer player) {
        if (server == null || player == null) return null;
        try {
            OpenPACServerAPI api = OpenPACServerAPI.get(server);
            if (api == null) return null;
            var claim = api.getServerClaimsManager().get(player.level().dimension().location(), player.blockPosition());
            if (claim == null || claim.getPlayerId() == null || !claim.getPlayerId().equals(player.getUUID())) return null;
            IPlayerConfigManagerAPI manager = api.getPlayerConfigManager();
            IPlayerConfigAPI root = manager.getLoadedConfig(claim.getPlayerId());
            if (root == null) return null;
            int index = claim.getSubConfigIndex();
            if (index != -1 && !root.subConfigExists(index)) return null;
            IPlayerConfigAPI config = root.getEffectiveSubConfig(index);
            if (config == null) return null;
            String subId = config.getSubId() == null ? "main" : config.getSubId();
            IServerPlayerConfigGroupManagerAPI groups = config.getPlayerGroups();
            if (groups == null) return null;
            String name = api.getServerClaimsManager().getFullName(claim).getString();
            return new Context(config, groups, claim.getPlayerId(), subId, claim.getPlayerId() + ":" + subId, name);
        } catch (Throwable t) {
            VirgosCore.LOG.warn("Open Parties and Claims API unavailable for claim permissions", t);
            return null;
        }
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

    public boolean isGroupEnabled(Context context, Group group, Permission permission) {
        JsonObject groupData = groupData(context, group.id, false);
        if (groupData == null || !groupData.has("permissions")) return false;
        var value = groupData.getAsJsonObject("permissions").get(permission.id);
        return value != null && value.getAsBoolean();
    }

    public Set<UUID> members(Context context, Group group) {
        JsonObject groupData = groupData(context, group.id, false);
        Set<UUID> result = new HashSet<>();
        if (groupData == null || !groupData.has("members")) return result;
        for (var element : groupData.getAsJsonArray("members")) {
            try { result.add(UUID.fromString(element.getAsJsonObject().get("id").getAsString())); }
            catch (Exception ignored) { }
        }
        return result;
    }

    public String memberLabel(Context context, UUID uuid) {
        for (Group group : Group.values()) {
            JsonObject groupData = groupData(context, group.id, false);
            if (groupData == null || !groupData.has("members")) continue;
            for (var element : groupData.getAsJsonArray("members")) {
                var member = element.getAsJsonObject();
                if (uuid.toString().equals(member.get("id").getAsString())) return member.get("name").getAsString();
            }
        }
        ServerPlayer online = server.getPlayerList().getPlayer(uuid);
        return online == null ? uuid.toString().substring(0, 8) : online.getGameProfile().getName();
    }

    public boolean isIndividualAllowed(Context context, UUID uuid, Permission permission) {
        JsonObject person = individuals(context, false).has(uuid.toString()) ? individuals(context, false).getAsJsonObject(uuid.toString()) : null;
        return person != null && person.has("permissions") && person.getAsJsonObject("permissions").has(permission.id) && "ALLOW".equals(person.getAsJsonObject("permissions").get(permission.id).getAsString());
    }

    public Decision individualDecision(Context context, UUID uuid, Permission permission) {
        JsonObject person = individuals(context, false).has(uuid.toString()) ? individuals(context, false).getAsJsonObject(uuid.toString()) : null;
        if (person == null || !person.has("permissions") || !person.getAsJsonObject("permissions").has(permission.id)) return null;
        return Decision.valueOf(person.getAsJsonObject("permissions").get(permission.id).getAsString());
    }

    public boolean setGroupPermission(Context context, Group group, Permission permission, boolean enabled) {
        JsonObject before = data.deepCopy();
        try {
            JsonObject permissions = permissions(context, group.id);
            permissions.addProperty(permission.id, enabled);
            sync(context);
            save();
            return true;
        } catch (Throwable t) {
            data = before;
            VirgosCore.LOG.error("Could not update claim group permission", t);
            return false;
        }
    }

    public boolean setMember(Context context, Group group, ServerPlayer target, boolean included) {
        return setMember(context, group, target.getGameProfile(), included);
    }

    public boolean setMember(Context context, Group group, com.mojang.authlib.GameProfile target, boolean included) {
        JsonObject before = data.deepCopy();
        try {
            JsonObject groupData = groupData(context, group.id, true);
            JsonArray members = groupData.getAsJsonArray("members");
            for (int i = members.size() - 1; i >= 0; i--) {
                if (target.getId().toString().equals(members.get(i).getAsJsonObject().get("id").getAsString())) members.remove(i);
            }
            if (included) {
                JsonObject member = new JsonObject();
                member.addProperty("id", target.getId().toString());
                member.addProperty("name", target.getName());
                members.add(member);
            }
            sync(context);
            save();
            return true;
        } catch (Throwable t) {
            data = before;
            VirgosCore.LOG.error("Could not update claim group membership", t);
            return false;
        }
    }

    public boolean setIndividual(Context context, ServerPlayer target, Permission permission, Decision decision) {
        JsonObject before = data.deepCopy();
        try {
            JsonObject people = individuals(context, true);
            if (!people.has(target.getUUID().toString())) people.add(target.getUUID().toString(), new JsonObject());
            JsonObject person = people.getAsJsonObject(target.getUUID().toString());
            person.addProperty("name", target.getGameProfile().getName());
            if (!person.has("permissions")) person.add("permissions", new JsonObject());
            if (decision == null) person.getAsJsonObject("permissions").remove(permission.id);
            else person.getAsJsonObject("permissions").addProperty(permission.id, decision.name());
            sync(context);
            save();
            return true;
        } catch (Throwable t) {
            data = before;
            VirgosCore.LOG.error("Could not update individual claim exception", t);
            return false;
        }
    }

    static String nativeGroupId(Permission permission) {
        String id = "virgos_" + permission.id;
        if (id.length() > 16) throw new IllegalArgumentException("Native claim group ID exceeds 16 characters: " + id);
        return id;
    }

    private void sync(Context context) {
        for (Permission permission : Permission.values()) nativeGroupId(permission);
        for (Group group : Group.values()) ensureGroup(context, group.id);
        for (Permission permission : Permission.values()) {
            String nativeGroup = nativeGroupId(permission);
            ICustomPlayerConfigGroupAPI group = ensureGroup(context, nativeGroup);
            clearMembers(group);
            Set<UUID> allowed = new HashSet<>();
            for (Group source : Group.values()) if (isGroupEnabled(context, source, permission)) allowed.addAll(members(context, source));
            JsonObject people = individuals(context, false);
            for (var entry : people.entrySet()) {
                JsonObject person = entry.getValue().getAsJsonObject();
                if (!person.has("permissions") || !person.getAsJsonObject("permissions").has(permission.id)) continue;
                UUID id = UUID.fromString(entry.getKey());
                if ("ALLOW".equals(person.getAsJsonObject("permissions").get(permission.id).getAsString())) allowed.add(id);
                else allowed.remove(id);
            }
            for (UUID id : allowed) group.includeMember(id, memberLabel(context, id));
            for (String optionId : permission.optionIds) setOption(context, optionId, allowed.isEmpty() ? "N" : nativeGroup);
        }
        for (Group source : Group.values()) {
            ICustomPlayerConfigGroupAPI group = ensureGroup(context, source.id);
            clearMembers(group);
            for (UUID id : members(context, source)) group.includeMember(id, memberLabel(context, id));
        }
    }

    private void setOption(Context context, String id, String value) {
        IPlayerConfigManagerAPI manager = OpenPACServerAPI.get(server).getPlayerConfigManager();
        IPlayerConfigOptionSpecAPI option = manager.getOptionForId(id);
        if (option == null || option.getType() != String.class) throw new IllegalStateException("Unsupported claim option: " + id);
        @SuppressWarnings({"rawtypes", "unchecked"})
        IPlayerConfigAPI.SetResult result = context.config().tryToSet(option, value);
        if (result != IPlayerConfigAPI.SetResult.SUCCESS && result != IPlayerConfigAPI.SetResult.DEFAULTED)
            throw new IllegalStateException("Could not set claim option " + id + ": " + result);
    }

    private ICustomPlayerConfigGroupAPI ensureGroup(Context context, String id) {
        ICustomPlayerConfigGroupAPI group = context.groups().getCustom(id);
        if (group == null) {
            var created = context.groups().addCustom(id);
            if (created.right().isPresent())
                throw new IllegalStateException("Could not create claim group " + id + ": " + created.right().get());
            group = context.groups().getCustom(id);
        }
        if (group == null) throw new IllegalStateException("Could not create claim group: " + id);
        return group;
    }

    private static void clearMembers(ICustomPlayerConfigGroupAPI group) {
        for (var member : new ArrayList<>(group.getDirectMembers())) group.excludeMember(member.getId(), member.getDisplayName());
    }

    private JsonObject claimData(Context context, boolean create) {
        if (!data.has(context.key())) {
            if (!create) return null;
            data.add(context.key(), new JsonObject());
        }
        return data.getAsJsonObject(context.key());
    }

    private JsonObject groupData(Context context, String id, boolean create) {
        JsonObject claim = claimData(context, create);
        if (claim == null) return null;
        if (!claim.has("groups")) {
            if (!create) return null;
            claim.add("groups", new JsonObject());
        }
        JsonObject groups = claim.getAsJsonObject("groups");
        if (!groups.has(id)) {
            if (!create) return null;
            JsonObject group = new JsonObject();
            group.add("members", new JsonArray());
            group.add("permissions", new JsonObject());
            groups.add(id, group);
        }
        return groups.getAsJsonObject(id);
    }

    private JsonObject permissions(Context context, String group) {
        return groupData(context, group, true).getAsJsonObject("permissions");
    }

    private JsonObject individuals(Context context, boolean create) {
        JsonObject claim = claimData(context, create);
        if (claim == null) return new JsonObject();
        if (!claim.has("individuals")) {
            if (!create) return new JsonObject();
            claim.add("individuals", new JsonObject());
        }
        JsonObject individuals = claim.getAsJsonObject("individuals");
        if (create) return individuals;
        return individuals;
    }

    private void save() throws Exception {
        Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
        Files.writeString(tmp, VirgosCore.JSON.toJson(data));
        Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }
}
