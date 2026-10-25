package mc.virgos.codex;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Pure migration rules; Minecraft and installer adapters preserve unrelated options. */
public final class ManagedKeyPolicy {
    public static final String CODEX = "key.virgos_codex.open";
    public static final String LEGACY = "key.heracles.open_quests";
    public static final String UNBOUND = "key.keyboard.unknown";

    public record Binding(String key, List<String> previous, boolean repairUnbound, String context) {}

    private ManagedKeyPolicy() {}

    public static Map<String, String> migrate(Map<String, String> current, Map<String, Binding> policy) {
        Map<String, String> result = new LinkedHashMap<>(current);
        String own = current.get(CODEX);
        String legacy = current.get(LEGACY);
        if ((own == null || own.equals(UNBOUND)) && legacy != null && !legacy.equals(UNBOUND)) {
            result.put(CODEX, legacy);
        }
        for (var entry : policy.entrySet()) {
            String value = result.get(entry.getKey());
            Binding binding = entry.getValue();
            if (value == null || binding.previous().contains(value)
                || (binding.repairUnbound() && value.equals(UNBOUND))) {
                result.put(entry.getKey(), binding.key());
            }
        }
        // Both mappings open the same intercepted screen; retain one owner of the action.
        result.put(LEGACY, UNBOUND);
        return result;
    }

    public static Map<String, List<String>> conflicts(Map<String, String> current,
        Map<String, Binding> policy, List<String> preservedKeys) {
        Map<String, List<String>> byKey = new LinkedHashMap<>();
        current.forEach((name, key) -> {
            Binding binding = policy.get(name);
            if (!key.equals(UNBOUND) && ((binding != null && binding.context().equals("global"))
                || preservedKeys.contains(name))) {
                byKey.computeIfAbsent(key, ignored -> new java.util.ArrayList<>()).add(name);
            }
        });
        byKey.entrySet().removeIf(entry -> entry.getValue().size() < 2);
        return byKey;
    }
}
