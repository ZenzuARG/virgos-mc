package mc.virgos.mixin;

import java.util.Map;
import java.util.UUID;
import mc.virgos.ClaimPermissionAdmission;
import mc.virgos.ClaimPermissionDecision;
import mc.virgos.ClaimProtectionHooks;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.common.util.FakePlayer;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import xaero.pac.common.claims.player.IPlayerChunkClaim;
import xaero.pac.common.claims.player.mode.api.ClaimingModes;
import xaero.pac.common.server.IServerData;
import xaero.pac.common.server.claims.IServerClaimsManager;
import xaero.pac.common.server.claims.protection.ChunkProtection;
import xaero.pac.common.server.claims.protection.ChunkProtection.InteractionTargetResult;
import xaero.pac.common.server.claims.protection.ChunkProtectionExceptionType;
import xaero.pac.common.server.claims.protection.group.ChunkProtectionExceptionGroup;
import xaero.pac.common.server.claims.protection.override.api.ChunkAccessOverrideType;
import xaero.pac.common.server.config.ServerConfig;
import xaero.pac.common.server.player.config.IPlayerConfig;
import xaero.pac.common.server.player.config.IPlayerConfigManager;
import xaero.pac.common.server.player.config.api.PlayerConfigType;
import xaero.pac.common.server.player.config.api.v2.IPlayerConfigOptionSpecAPI;
import xaero.pac.common.server.player.config.api.v2.PlayerConfigOptions;
import xaero.pac.common.server.player.data.api.ServerPlayerDataAPI;

/** Only human block exceptions are replaced; native item/entity/automation checks retain control. */
@Mixin(value = ChunkProtection.class, remap = false)
public abstract class OpenPacClaimPermissionsMixin {
    @Unique private static final String virgos$BLOCK_CHECK = "blockAccessCheck(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/resources/ResourceLocation;Lnet/minecraft/core/BlockPos;Lxaero/pac/common/server/player/config/IPlayerConfig;Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;Ljava/util/UUID;ZZZ)Lxaero/pac/common/server/claims/protection/ChunkProtection$InteractionTargetResult;";
    @Unique private static final String virgos$PLACE = "onEntityPlaceBlock(Lxaero/pac/common/server/IServerData;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/entity/Entity;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/core/BlockPos;Lxaero/pac/common/server/player/config/api/v2/IPlayerConfigOptionSpecAPI;)Z";
    @Shadow @Final private Map<String, ChunkProtectionExceptionGroup<Block>> blockExceptionGroups;
    @Shadow @Final private IServerClaimsManager<?, ?, ?> claimsManager;
    @Shadow private IServerData<?, ?> serverData;
    @Shadow private boolean checkPlayerGroupExceptionOption(IPlayerConfigOptionSpecAPI<String> option,
        IPlayerConfig config, Entity accessor, UUID actor) { throw new AssertionError(); }
    @Shadow private boolean shouldBlockClaimAccessForGoingOverLimit(UUID owner, Entity accessor) { throw new AssertionError(); }
    @Shadow private boolean hasActiveFullPass(Entity accessor) { throw new AssertionError(); }
    @Shadow private IPlayerConfig getClaimConfig(IPlayerConfigManager manager, IPlayerChunkClaim claim,
        ResourceLocation dimension) { throw new AssertionError(); }

    @Unique
    private boolean virgos$human(Entity actual, Entity accessor, UUID actor, boolean explosion) {
        if (explosion || !(actual instanceof ServerPlayer player) || player instanceof FakePlayer
            || actual != accessor || !player.getUUID().equals(actor)) return false;
        UUID impersonation = ServerPlayerDataAPI.from(player).getClaimsImpersonationInfo().getPlayerId();
        return ClaimPermissionAdmission.human(true, false, true, player.getUUID(), actor, impersonation, false);
    }

    @Unique
    private boolean virgos$exempt(IPlayerConfig config, Entity actual, UUID actor) {
        if (!ServerConfig.CONFIG.claimsEnabled.get() || config == null
            || !config.getEffective(PlayerConfigOptions.PROTECT_CLAIMED_CHUNKS)
            || actor.equals(config.getPlayerId()) || hasActiveFullPass(actual)) return true;
        ServerPlayer player = (ServerPlayer) actual;
        var data = ServerPlayerDataAPI.from(player);
        claimsManager.getPermissionHandler().ensureAdminModeStatusPermission(player, data);
        return data.isClaimsAdminMode()
            || data.getClaimingMode() == ClaimingModes.SERVER
                && config.getType() == PlayerConfigType.SERVER
                && claimsManager.getPermissionHandler().playerHasServerClaimPermission(player);
    }

    @Unique
    private boolean virgos$veto(IPlayerConfig config, Entity accessor, UUID actor,
                                ResourceLocation dimension, BlockPos position) {
        return claimsManager.getChunkAccessOverriderManager().overrideChunkAccess(dimension,
            position.getX() >> 4, position.getZ() >> 4, config, accessor, actor, serverData.getServer()).getType()
                == ChunkAccessOverrideType.PROTECT
            || ServerPlayerDataAPI.from((ServerPlayer) accessor).isClaimsNonallyMode()
            || shouldBlockClaimAccessForGoingOverLimit(config.getPlayerId(), accessor);
    }

    @Unique
    private ClaimPermissionDecision virgos$decision(Block block, boolean breaking, boolean emptyHand,
            IPlayerConfig config, ServerPlayer actor, ResourceLocation dimension, BlockPos position) {
        var binding = ClaimProtectionHooks.snapshot();
        if (breaking || block == null) return binding.resolve(actor, dimension, position, "building");
        ClaimPermissionDecision result = ClaimPermissionDecision.NATIVE;
        for (var group : blockExceptionGroups.values()) {
            if (group.getType() == ChunkProtectionExceptionType.BREAK
                || !emptyHand && group.getType() == ChunkProtectionExceptionType.EMPTY_HAND_INTERACTION
                || !group.contains(block)) continue;
            var option = group.getPlayerConfigOption();
            String permission = ClaimPermissionAdmission.permission(option.getId());
            if (permission == null || "building".equals(permission)
                || config.getManager().getOptionForId(option.getId()) != option) continue;
            var decision = binding.resolve(actor, dimension, position, permission);
            if (decision == ClaimPermissionDecision.DENY) return decision;
            if (decision == ClaimPermissionDecision.ALLOW) result = decision;
        }
        return result;
    }

    @Redirect(method = virgos$BLOCK_CHECK, at = @At(value = "INVOKE", target = "Lxaero/pac/common/server/claims/protection/ChunkProtection;checkPlayerGroupExceptionOption(Lxaero/pac/common/server/player/config/api/v2/IPlayerConfigOptionSpecAPI;Lxaero/pac/common/server/player/config/IPlayerConfig;Lnet/minecraft/world/entity/Entity;Ljava/util/UUID;)Z"), require = 3, remap = false)
    private boolean virgos$exception(ChunkProtection<?> protection, IPlayerConfigOptionSpecAPI<String> option,
            IPlayerConfig optionConfig, Entity optionAccessor, UUID optionActor,
            Block block, ResourceLocation dimension, BlockPos position, IPlayerConfig config,
            Entity actual, Entity accessor, UUID actor, boolean emptyHand, boolean breaking, boolean explosion) {
        boolean nativeValue = checkPlayerGroupExceptionOption(option, optionConfig, optionAccessor, optionActor);
        if (!virgos$human(actual, accessor, actor, explosion) || virgos$exempt(config, actual, actor)) return nativeValue;
        var decision = virgos$decision(block, breaking, emptyHand, config, (ServerPlayer) actual, dimension, position);
        boolean broad = option == PlayerConfigOptions.CLAIM_EXCEPTION_BLOCKS_BY_PLAYERS;
        String permission = ClaimPermissionAdmission.permission(option.getId());
        if (!broad && (permission == null || config.getManager().getOptionForId(option.getId()) != option)) return nativeValue;
        return ClaimPermissionAdmission.exception(nativeValue, decision, true,
            decision == ClaimPermissionDecision.ALLOW && virgos$veto(config, accessor, actor, dimension, position),
            broad, breaking || block == null, optionConfig.isOptionDefaulted(option));
    }

    @Inject(method = virgos$BLOCK_CHECK, at = @At("RETURN"), cancellable = true, require = 1, remap = false)
    private void virgos$denyBlock(Block block, ResourceLocation dimension, BlockPos position, IPlayerConfig config,
            Entity actual, Entity accessor, UUID actor, boolean emptyHand, boolean breaking, boolean explosion,
            CallbackInfoReturnable<InteractionTargetResult> callback) {
        if (!virgos$human(actual, accessor, actor, explosion) || virgos$exempt(config, actual, actor)) return;
        var decision = virgos$decision(block, breaking, emptyHand, config, (ServerPlayer) actual, dimension, position);
        if (ClaimPermissionAdmission.protect(false, decision, true, false))
            callback.setReturnValue(InteractionTargetResult.PROTECT);
    }

    /** Native placement can return before blockAccessCheck when item use is permitted. Deny only. */
    @Inject(method = virgos$PLACE, at = @At("RETURN"), cancellable = true, require = 1, remap = false)
    private void virgos$denyPlacement(IServerData<?, ?> data, BlockState state, Entity actual, ServerLevel level,
            BlockPos position, IPlayerConfigOptionSpecAPI<String> option, CallbackInfoReturnable<Boolean> callback) {
        if (callback.getReturnValueZ() || !(actual instanceof ServerPlayer player)
            || !virgos$human(actual, actual, player.getUUID(), false)) return;
        var dimension = level.dimension().location();
        var claim = claimsManager.get(dimension, new ChunkPos(position));
        var config = getClaimConfig(data.getPlayerConfigManager(), claim, dimension);
        if (virgos$exempt(config, actual, player.getUUID())) return;
        if (ClaimProtectionHooks.snapshot().resolve(player, dimension, position, "building") == ClaimPermissionDecision.DENY)
            callback.setReturnValue(true);
    }
}
