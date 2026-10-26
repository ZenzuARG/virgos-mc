package mc.virgos.codex.ingredient.mixin;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Refresh ordinary ingredients before either vanilla or ModernFix returns cached items. */
@Mixin(value = Ingredient.class, remap = false)
public abstract class IngredientCacheMixin {
    @Shadow public abstract boolean isVanilla();
    @Shadow public abstract boolean checkInvalidation();
    @Shadow protected abstract void markValid();

    // Pinned Minecraft 1.20.1 SRG selector, matching the existing refmap-free mixins.
    @Inject(method = "m_43908_()[Lnet/minecraft/world/item/ItemStack;", at = @At("HEAD"),
        require = 1, remap = false)
    protected void virgos$refreshItems(CallbackInfoReturnable<ItemStack[]> callback) {
        // Forge's virtual invalidate also clears ModernFix's soft reference through its hook.
        // Subclasses own their expansion and are deliberately outside this repair.
        if (isVanilla() && checkInvalidation()) markValid();
    }
}
