package mc.virgos.codex.ingredient;

import net.minecraft.world.item.crafting.Ingredient;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TagsUpdatedEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Advance Forge's cache epoch after received tags are bound, including reconnects. */
@Mod.EventBusSubscriber(modid = "virgos_codex", value = Dist.CLIENT,
    bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class ClientIngredientTags {
    private ClientIngredientTags() {}

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void tagsUpdated(TagsUpdatedEvent event) {
        // Do not react to the integrated server's separate data-load event.
        if (event.getUpdateCause() == TagsUpdatedEvent.UpdateCause.CLIENT_PACKET_RECEIVED) {
            Ingredient.invalidateAll();
        }
    }
}
