package mc.virgos.dhcompat.mixin;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Keeps B usable while preventing nested backpack opens from corrupting menus. */
@Mixin(targets = "net.p3pp3rf1y.sophisticatedbackpacks.client.KeybindHandler", remap = false)
public abstract class BackpackKeyGuardMixin {
    @Unique private static long virgos$lastActionMs;
    @Unique private static long virgos$pendingOpenUntilMs;

    @Inject(method = "sendBackpackOpenOrCloseMessage", at = @At("HEAD"), cancellable = true, remap = false)
    private static void virgos$preventNestedOpen(CallbackInfoReturnable<Boolean> callback) {
        long now = System.currentTimeMillis();
        var screen = Minecraft.getInstance().screen;
        if (screen != null && screen.getClass().getName().contains("BackpackScreen")) {
            // Never route B through the nested-backpack path.  Once the first
            // screen is open, a held/repeated B can resolve the hovered slot
            // as a storage index (for example 193) while the server is still
            // on the previous menu, which is the inventory-desync trigger.
            callback.setReturnValue(false);
            return;
        }
        if (screen == null && now < virgos$pendingOpenUntilMs) {
            callback.setReturnValue(false);
            return;
        }
        if (now - virgos$lastActionMs < 250L) {
            callback.setReturnValue(false);
            return;
        }
        if (screen instanceof AbstractContainerScreen<?> &&
                !screen.getClass().getName().contains("BackpackScreen")) {
            callback.setReturnValue(false);
            return;
        }
        virgos$lastActionMs = now;
    }

    @Inject(method = "sendBackpackOpenOrCloseMessage", at = @At("RETURN"), remap = false)
    private static void virgos$holdOpenRequest(CallbackInfoReturnable<Boolean> callback) {
        if (!callback.getReturnValueZ() && Minecraft.getInstance().screen == null) {
            virgos$pendingOpenUntilMs = System.currentTimeMillis() + 2_000L;
        }
    }
}
