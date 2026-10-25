package mc.virgos.dhcompat.mixin;

import com.seibel.distanthorizons.core.level.IDhLevel;
import com.seibel.distanthorizons.core.level.DhClientLevel;
import com.seibel.distanthorizons.core.wrapperInterfaces.world.IClientLevelWrapper;
import mc.virgos.dhcompat.DeferredLevelPublication;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Publish a client level only after its native modules, repositories and renderer exist. */
@Mixin(value = DhClientLevel.class, remap = false)
public abstract class DhClientLevelMixin {
    @Unique private static final String VIRGOS_FULL_CONSTRUCTOR = "<init>("
        + "Lcom/seibel/distanthorizons/core/file/structure/ISaveStructure;"
        + "Lcom/seibel/distanthorizons/core/wrapperInterfaces/world/IClientLevelWrapper;"
        + "Ljava/io/File;Lcom/seibel/distanthorizons/core/multiplayer/client/ClientNetworkState;)V";
    @Unique private DeferredLevelPublication virgos$publication;

    @Shadow private void registerNetworkHandlers() { throw new AssertionError("Mixin shadow was not applied"); }

    @Unique private DeferredLevelPublication virgos$publication() {
        // Constructor redirects execute before mixin field initializers would be injected.
        if (virgos$publication == null) virgos$publication = new DeferredLevelPublication();
        return virgos$publication;
    }

    @Redirect(method = VIRGOS_FULL_CONSTRUCTOR, at = @At(value = "INVOKE",
        target = "Lcom/seibel/distanthorizons/core/wrapperInterfaces/world/IClientLevelWrapper;setDhLevel(Lcom/seibel/distanthorizons/core/level/IDhLevel;)V"),
        require = 1, remap = false)
    private void virgos$deferWrapperPublication(IClientLevelWrapper wrapper, IDhLevel level) {
        virgos$publication().deferWrapper(() -> wrapper.setDhLevel(level));
    }

    @Redirect(method = VIRGOS_FULL_CONSTRUCTOR, at = @At(value = "INVOKE",
        target = "Lcom/seibel/distanthorizons/core/level/DhClientLevel;registerNetworkHandlers()V"),
        require = 1, remap = false)
    private void virgos$deferHandlerPublication(DhClientLevel level) {
        virgos$publication().deferHandlers(this::registerNetworkHandlers);
    }

    @Inject(method = VIRGOS_FULL_CONSTRUCTOR, at = @At("RETURN"), require = 1, remap = false)
    private void virgos$publishCompletedLevel(CallbackInfo callback) {
        if (virgos$publication != null) virgos$publication.complete();
    }
}
