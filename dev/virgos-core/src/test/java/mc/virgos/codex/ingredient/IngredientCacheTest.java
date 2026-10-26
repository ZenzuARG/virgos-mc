package mc.virgos.codex.ingredient;

import mc.virgos.codex.ingredient.mixin.IngredientCacheMixin;
import java.util.stream.Stream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import com.google.gson.JsonParser;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraftforge.event.TagsUpdatedEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.injection.Inject;

/** Exercises the production hook against Forge's epoch and ModernFix's dual-cache contract. */
public final class IngredientCacheTest {
    private static int epoch;

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static final class CachedIngredient extends IngredientCacheMixin {
        private final boolean ordinary;
        private final boolean soft;
        private int validEpoch = -1;
        private int invalidations;
        private String bound = "Empty Tag: create:sandpaper";
        private String strongCache;
        private String softCache;

        CachedIngredient(boolean ordinary, boolean soft) {
            this.ordinary = ordinary;
            this.soft = soft;
        }

        @Override public boolean isVanilla() { return ordinary; }
        @Override public boolean checkInvalidation() {
            if (validEpoch == epoch) return false;
            // Forge invalidate clears the strong cache; ModernFix's RETURN hook clears soft.
            strongCache = null;
            softCache = null;
            invalidations++;
            return true;
        }
        @Override protected void markValid() { validEpoch = epoch; }

        String items() {
            virgos$refreshItems(null);
            if (strongCache != null) return strongCache;
            if (softCache != null) return softCache;
            if (soft) softCache = bound;
            else strongCache = bound;
            return bound;
        }
    }

    private static final class EpochWitness extends Ingredient {
        EpochWitness() { super(Stream.empty()); }
        void acceptEpoch() { markValid(); }
    }

    private static void checkTagPacketEpoch() {
        var witness = new EpochWitness();
        witness.acceptEpoch();
        ClientIngredientTags.tagsUpdated(new TagsUpdatedEvent(null, false, false));
        check(!witness.checkInvalidation(), "Server data-load events must not advance the client epoch");
        for (int connection = 0; connection < 2; connection++) {
            ClientIngredientTags.tagsUpdated(new TagsUpdatedEvent(null, true, false));
            check(witness.checkInvalidation(), "Every received tag binding advances the actual Forge epoch");
            witness.acceptEpoch();
        }
    }

    private static void checkClientWiring() throws Exception {
        // Reading the annotation enum reflectively initializes Forge's launcher-only bus.
        var type = new ClassNode();
        try (var input = ClientIngredientTags.class.getResourceAsStream("ClientIngredientTags.class")) {
            new ClassReader(input).accept(type, ClassReader.SKIP_CODE);
        }
        var subscriber = type.visibleAnnotations.stream()
            .filter(a -> a.desc.equals("Lnet/minecraftforge/fml/common/Mod$EventBusSubscriber;"))
            .findFirst().orElseThrow();
        var sides = (java.util.List<?>) annotationValue(subscriber, "value");
        check(sides.size() == 1 && ((String[]) sides.get(0))[1].equals("CLIENT"), "Tag subscriber must be client-only");
        check(((String[]) annotationValue(subscriber, "bus"))[1].equals("FORGE"), "Tags use the Forge event bus");
        var handler = ClientIngredientTags.class.getMethod("tagsUpdated", TagsUpdatedEvent.class);
        check(handler.getAnnotation(SubscribeEvent.class).priority() == EventPriority.HIGHEST,
            "Invalidate before ordinary client consumers expand ingredients");
        var hook = IngredientCacheMixin.class.getDeclaredMethod("virgos$refreshItems",
            org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable.class).getAnnotation(Inject.class);
        check(hook != null && hook.require() == 1 && !hook.remap(), "Pinned injection must fail visibly if absent");
        check(hook.method().length == 1 && hook.method()[0].equals("m_43908_()[Lnet/minecraft/world/item/ItemStack;"),
            "Inject into the pinned production getItems descriptor");
        check(hook.at().length == 1 && hook.at()[0].value().equals("HEAD"), "Check epoch before cached returns");
        try (var input = IngredientCacheTest.class.getResourceAsStream("/virgos_codex.mixins.json")) {
            check(input != null, "Codex mixin config must be packaged as a resource");
            var config = JsonParser.parseReader(new InputStreamReader(input, StandardCharsets.UTF_8)).getAsJsonObject();
            String reservedPackage = config.get("package").getAsString();
            check(!ClientIngredientTags.class.getName().startsWith(reservedPackage + "."),
                "Ordinary event subscribers must not live in Mixin's reserved package prefix");
            check(IngredientCacheMixin.class.getPackageName().equals(reservedPackage), "Mixin package must match config");
            var classes = Path.of(IngredientCacheMixin.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            try (var paths = Files.walk(classes.resolve(reservedPackage.replace('.', '/')))) {
                for (Path path : paths.filter(p -> p.toString().endsWith(".class")).toList()) {
                    var reservedClass = new ClassNode();
                    new ClassReader(Files.readAllBytes(path)).accept(reservedClass, ClassReader.SKIP_CODE);
                    var annotations = reservedClass.invisibleAnnotations;
                    check(annotations != null && annotations.stream()
                        .anyMatch(a -> a.desc.equals("Lorg/spongepowered/asm/mixin/Mixin;")),
                        "Every class in the reserved prefix must be a mixin: " + path.getFileName());
                }
            }
            check(config.get("required").getAsBoolean() && !config.has("mixins"), "No common/server mixin activation");
            check(config.getAsJsonArray("client").size() == 1
                && config.getAsJsonArray("client").get(0).getAsString().equals("IngredientCacheMixin"),
                "Only the targeted ingredient hook is enabled");
        }
    }

    private static Object annotationValue(AnnotationNode annotation, String key) {
        for (int i = 0; i < annotation.values.size(); i += 2) {
            if (annotation.values.get(i).equals(key)) return annotation.values.get(i + 1);
        }
        throw new AssertionError("Missing annotation value: " + key);
    }

    public static void main(String[] args) throws Exception {
        checkClientWiring();
        checkTagPacketEpoch();
        for (boolean soft : new boolean[] {false, true}) {
            var existing = new CachedIngredient(true, soft);
            check(existing.items().startsWith("Empty Tag:"), "Fixture must begin before tags bind");
            existing.bound = "create:sand_paper,create:red_sand_paper";
            epoch++; // The client tag-packet event invalidates the global Forge epoch.
            check(existing.items().equals(existing.bound), "Existing JEI ingredient must refresh after binding");
            int refreshes = existing.invalidations;
            existing.items();
            check(existing.invalidations == refreshes, "Same epoch must not repeatedly clear caches");
            existing.bound = "create:red_sand_paper";
            epoch++;
            check(existing.items().equals(existing.bound), "Reconnect must refresh the same existing ingredient");
            var custom = new CachedIngredient(false, soft);
            String previous = custom.items();
            custom.bound = "custom:replacement";
            epoch++;
            check(custom.items().equals(previous) && custom.invalidations == 0,
                "Custom ingredient subclasses retain ownership of their cache lifecycle");
            var control = new CachedIngredient(true, soft);
            control.bound = "minecraft:oak_planks";
            check(control.items().equals("minecraft:oak_planks"), "Working ingredient remains unchanged");
            epoch++;
            check(control.items().equals("minecraft:oak_planks"), "Working control survives tag rebinding");
        }
        System.out.println("Ingredient cache: strong/soft binding, reconnect, stable epoch and custom isolation passed");
    }
}
