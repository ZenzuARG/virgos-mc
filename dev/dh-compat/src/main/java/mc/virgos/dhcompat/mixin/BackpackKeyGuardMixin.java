package mc.virgos.dhcompat.mixin;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Keeps B usable while preventing nested backpack opens from corrupting menus. */
@Mixin(targets = "net.p3pp3rf1y.sophisticatedbackpacks.client.KeybindHandler", remap = false)
public abstract class BackpackKeyGuardMixin {
    @Inject(method = "sendBackpackOpenOrCloseMessage", at = @At("HEAD"), cancellable = true, remap = false)
    private static void virgos$preventNestedOpen(CallbackInfoReturnable<Boolean> callback) {
        var screen = Minecraft.getInstance().screen;
        if (screen instanceof AbstractContainerScreen<?> &&
                !screen.getClass().getName().contains("BackpackScreen")) {
            callback.setReturnValue(false);
        }
    }
}
