package mc.virgos.mixin;

import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Ketting cannot wrap the fake level that Supplementaries uses to probe faucet
 * interactions during ServerStartedEvent. The probe is optional and the faucet
 * feature is disabled in the server configuration, so skip only that bootstrap
 * path when the Ketting runtime is present.
 */
@Mixin(targets = "net.mehvahdjukaar.supplementaries.common.events.ServerEvents")
public final class KettingSupplementariesMixin {
    private KettingSupplementariesMixin() {
    }

    @Inject(method = "onServerStart", at = @At("HEAD"), cancellable = true)
    private static void virgos$skipKettingFaucetBootstrap(MinecraftServer server, CallbackInfo callback) {
        try {
            Class.forName("org.kettingpowered.ketting.core.Ketting", false,
                    KettingSupplementariesMixin.class.getClassLoader());
            callback.cancel();
        } catch (ClassNotFoundException ignored) {
            // Vanilla Forge and integrated servers keep Supplementaries' normal bootstrap.
        }
    }
}
