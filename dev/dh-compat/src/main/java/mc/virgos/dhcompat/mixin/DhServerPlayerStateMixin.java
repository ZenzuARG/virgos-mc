package mc.virgos.dhcompat.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Sends the native DH session configuration as soon as a player state exists. */
@Mixin(targets = "com.seibel.distanthorizons.core.multiplayer.server.ServerPlayerState", remap = false)
public abstract class DhServerPlayerStateMixin {
    @Shadow(remap = false)
    private void sendConfigMessage() { }

    @Inject(method = "<init>", at = @At("RETURN"), require = 1, remap = false)
    private void virgos$sendInitialConfig(CallbackInfo callback) {
        sendConfigMessage();
    }
}
