package mc.virgos;

import com.electronwill.nightconfig.core.CommentedConfig;
import java.util.List;
import java.util.UUID;
import xaero.pac.common.server.config.ServerConfig;
import xaero.pac.common.server.player.config.PlayerConfig;
import xaero.pac.common.server.player.config.PlayerConfigOptionCategory;
import xaero.pac.common.server.player.config.PlayerConfigPlayerGroupOptionSpec;
import xaero.pac.common.server.player.config.api.PlayerConfigType;
import xaero.pac.common.server.player.config.api.v2.PlayerConfigOptions;

/** Actual pinned OPAC options, using SRG Minecraft dependencies without launching the game. */
public final class ClaimNativeOptionsTest {
    public static void main(String[] args) throws Exception {
        var chest = PlayerConfigPlayerGroupOptionSpec.Builder.begin()
            .setId("playerConfig.claims.protection.exceptions.groups.block.interact.Chests")
            .setDefaultValue("N").setComment("fixture")
            .setCategory(PlayerConfigOptionCategory.BLOCK_PROTECTION).build(null);
        require("storage".equals(ClaimPermissionAdmission.permission(chest.getId())),
            "Actual canonical chest option is managed");
        var building = PlayerConfigOptions.CLAIM_EXCEPTION_BLOCKS_BY_PLAYERS;
        require("building".equals(ClaimPermissionAdmission.permission(building.getId())),
            "Actual canonical building option is managed");
        ServerConfig.SPEC.setConfig(CommentedConfig.inMemory());
        ServerConfig.CONFIG.opConfigurablePlayerConfigOptions.set(List.of());
        ServerConfig.CONFIG.playerConfigurablePlayerConfigOptions.set(List.of());
        var constructor = PlayerConfig.class.getDeclaredConstructors()[0];
        constructor.setAccessible(true);
        Object[] parameters = new Object[constructor.getParameterCount()];
        parameters[0] = PlayerConfigType.PLAYER;
        parameters[1] = UUID.randomUUID();
        var config = (PlayerConfig<?>) constructor.newInstance(parameters);
        require(config.isOptionDefaulted(building), "Real server lock is active");
        require(config.isOptionDefaulted(chest), "Dynamic category also honors server lock");
        for (var option : List.of(building, chest)) {
            boolean broad = option == building;
            for (boolean original : new boolean[] {false, true}) {
                require(ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                    true, false, broad, broad, config.isOptionDefaulted(option)) == original,
                    "Locked native option retains its default instead of acquiring a grant");
                require(!ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.DENY,
                    true, false, broad, broad, config.isOptionDefaulted(option)),
                    "Native lock never weakens a stricter parcel denial");
                require(ClaimPermissionAdmission.exception(original, ClaimPermissionDecision.ALLOW,
                    true, false, broad, broad, false), "Unlocked option still accepts parcel grants");
            }
        }
        System.out.println("ClaimNativeOptionsTest passed");
    }

    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
}
