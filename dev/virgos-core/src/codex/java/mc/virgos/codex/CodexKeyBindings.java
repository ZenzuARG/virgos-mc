package mc.virgos.codex;

import com.google.gson.JsonParser;
import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.logging.LogUtils;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.client.settings.KeyModifier;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.glfw.GLFW;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Owns the discoverable Codex action independently of Heracles' defaults. */
public final class CodexKeyBindings {
    public static final KeyMapping OPEN = new KeyMapping(ManagedKeyPolicy.CODEX,
        KeyConflictContext.IN_GAME, InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_J, "key.categories.virgos_codex");
    private static boolean repaired;
    private static String conflictNotice;

    private CodexKeyBindings() {}

    @Mod.EventBusSubscriber(modid = "virgos_codex", value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
    public static final class Registration {
        @SubscribeEvent public static void register(RegisterKeyMappingsEvent event) {
            event.register(OPEN);
        }
    }

    @Mod.EventBusSubscriber(modid = "virgos_codex", value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.FORGE)
    public static final class Events {
        @SubscribeEvent public static void tick(TickEvent.ClientTickEvent event) {
            if (event.phase != TickEvent.Phase.END) return;
            Minecraft client = Minecraft.getInstance();
            if (client.options == null) return;
            if (!repaired) {
                repaired = true;
                repair(client);
            }
            if (client.player != null && conflictNotice != null) {
                client.player.displayClientMessage(Component.translatable("virgos_codex.controls.conflicts", conflictNotice), false);
                conflictNotice = null;
            }
            while (OPEN.consumeClick()) {
                if (client.player != null && client.screen == null) VirgosCodex.openCodex();
            }
        }
    }

    private static void repair(Minecraft client) {
        try (var stream = CodexKeyBindings.class.getResourceAsStream("/virgos-keybindings.json")) {
            if (stream == null) throw new IllegalStateException("Bundled controls policy is missing");
            var json = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
            if (json.get("schema").getAsInt() != 1) throw new IllegalStateException("Unknown controls policy");
            Map<String, ManagedKeyPolicy.Binding> policy = new LinkedHashMap<>();
            json.getAsJsonObject("bindings").entrySet().forEach(entry -> {
                var row = entry.getValue().getAsJsonObject();
                List<String> previous = new ArrayList<>();
                row.getAsJsonArray("previous").forEach(value -> previous.add(value.getAsString()));
                policy.put(entry.getKey(), new ManagedKeyPolicy.Binding(row.get("key").getAsString(), previous,
                    row.get("repairUnbound").getAsBoolean(), row.get("context").getAsString()));
            });
            Map<String, String> current = new LinkedHashMap<>();
            var options = client.gameDirectory.toPath().resolve("options.txt");
            if (Files.isRegularFile(options)) {
                for (String line : Files.readAllLines(options, StandardCharsets.UTF_8)) {
                    int separator = line.indexOf(':');
                    if (line.startsWith("key_") && separator > 4) {
                        String name = line.substring(4, separator);
                        if (current.putIfAbsent(name, line.substring(separator + 1)) != null) {
                            throw new IllegalStateException("Duplicate saved control: " + name);
                        }
                    }
                }
            }
            Map<String, KeyMapping> mappings = new LinkedHashMap<>();
            for (KeyMapping mapping : client.options.keyMappings) {
                mappings.put(mapping.getName(), mapping);
                if (!policy.containsKey(mapping.getName())) current.putIfAbsent(mapping.getName(), mapping.getKey().getName());
            }
            Map<String, String> migrated = ManagedKeyPolicy.migrate(current, policy);
            boolean changed = false;
            for (String name : policy.keySet()) {
                KeyMapping mapping = mappings.get(name);
                String desired = migrated.get(name);
                if (mapping != null && !desired.equals(current.get(name))) {
                    // Personal modifier combinations are not managed defaults and remain untouched.
                    String[] parts = desired.split(":", 2);
                    KeyModifier modifier = parts.length == 2 ? KeyModifier.valueOf(parts[1]) : KeyModifier.NONE;
                    mapping.setKeyModifierAndCode(modifier, InputConstants.getKey(parts[0]));
                    changed = true;
                }
            }
            if (changed) {
                KeyMapping.resetMapping();
                client.options.save();
            }
            List<String> preserved = new ArrayList<>();
            json.getAsJsonArray("preserve").forEach(value -> preserved.add(value.getAsString()));
            var conflicts = ManagedKeyPolicy.conflicts(migrated, policy, preserved);
            if (!conflicts.isEmpty()) {
                conflictNotice = String.join(", ", conflicts.keySet());
                LogUtils.getLogger().warn("Virgos Codex: personal global control conflicts retained: {}", conflicts);
            }
        } catch (Exception error) {
            LogUtils.getLogger().error("Virgos Codex: could not repair managed controls; existing bindings retained", error);
        }
    }
}
