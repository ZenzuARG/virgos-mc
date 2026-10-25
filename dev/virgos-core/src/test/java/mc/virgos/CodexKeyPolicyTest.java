package mc.virgos;

import mc.virgos.codex.ManagedKeyPolicy;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class CodexKeyPolicyTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        var policy = new LinkedHashMap<String, ManagedKeyPolicy.Binding>();
        policy.put(ManagedKeyPolicy.CODEX, new ManagedKeyPolicy.Binding("key.keyboard.j", List.of(), true, "global"));
        policy.put(ManagedKeyPolicy.LEGACY, new ManagedKeyPolicy.Binding(ManagedKeyPolicy.UNBOUND, List.of(), false, "legacy"));
        policy.put("iris.keybind.reload", new ManagedKeyPolicy.Binding("key.keyboard.f8", List.of("key.keyboard.r"), false, "global"));
        policy.put("key.ars_nouveau.head_curio_hotkey", new ManagedKeyPolicy.Binding("key.keyboard.k", List.of(), false, "global"));
        var fresh = ManagedKeyPolicy.migrate(Map.of(), policy);
        check("key.keyboard.j".equals(fresh.get(ManagedKeyPolicy.CODEX)), "Missing independent Codex key must get J");
        var unbound = ManagedKeyPolicy.migrate(Map.of(ManagedKeyPolicy.CODEX, ManagedKeyPolicy.UNBOUND), policy);
        check("key.keyboard.j".equals(unbound.get(ManagedKeyPolicy.CODEX)), "Unbound Codex must be repaired");
        var transferred = ManagedKeyPolicy.migrate(Map.of(ManagedKeyPolicy.LEGACY, "key.keyboard.u"), policy);
        check("key.keyboard.u".equals(transferred.get(ManagedKeyPolicy.CODEX)), "Legacy personal Codex key must transfer");
        check(ManagedKeyPolicy.UNBOUND.equals(transferred.get(ManagedKeyPolicy.LEGACY)), "Redundant legacy action must be unbound");
        var modified = ManagedKeyPolicy.migrate(Map.of(ManagedKeyPolicy.LEGACY, "key.keyboard.u:CONTROL"), policy);
        check("key.keyboard.u:CONTROL".equals(modified.get(ManagedKeyPolicy.CODEX)), "Legacy custom modifier combination must transfer intact");
        var custom = new LinkedHashMap<String, String>();
        custom.put(ManagedKeyPolicy.CODEX, "key.keyboard.k");
        custom.put(ManagedKeyPolicy.LEGACY, "key.keyboard.u");
        custom.put("iris.keybind.reload", "key.keyboard.f12");
        custom.put("key.forward", "key.keyboard.w");
        var migrated = ManagedKeyPolicy.migrate(custom, policy);
        check("key.keyboard.k".equals(migrated.get(ManagedKeyPolicy.CODEX)), "Explicit own key wins over legacy custom key");
        check("key.keyboard.f12".equals(migrated.get("iris.keybind.reload")), "Personal shader key must survive");
        check("key.keyboard.w".equals(migrated.get("key.forward")), "Vanilla movement must survive");
        check(ManagedKeyPolicy.conflicts(migrated, policy, List.of("key.forward")).containsKey("key.keyboard.k"), "Personal global conflicts must be reported without reassignment");
        var old = ManagedKeyPolicy.migrate(Map.of("iris.keybind.reload", "key.keyboard.r"), policy);
        check("key.keyboard.f8".equals(old.get("iris.keybind.reload")), "Known shader reload collision must migrate");
        var disabled = ManagedKeyPolicy.migrate(Map.of("iris.keybind.reload", ManagedKeyPolicy.UNBOUND), policy);
        check(ManagedKeyPolicy.UNBOUND.equals(disabled.get("iris.keybind.reload")), "Deliberately disabled non-Codex action must stay disabled");
        check(migrated.equals(ManagedKeyPolicy.migrate(migrated, policy)), "Migration must be idempotent");
        System.out.println("Codex controls: independent default, legacy transfer, custom preservation and shader migration passed");
    }
}
