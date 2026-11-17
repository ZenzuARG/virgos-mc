package mc.virgos;

import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.net.URL;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;
import org.spongepowered.asm.launch.MixinBootstrap;
import org.spongepowered.asm.launch.platform.container.ContainerHandleVirtual;
import org.spongepowered.asm.launch.platform.container.IContainerHandle;
import org.spongepowered.asm.mixin.MixinEnvironment;
import org.spongepowered.asm.mixin.Mixins;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;
import org.spongepowered.asm.service.IClassBytecodeProvider;
import org.spongepowered.asm.service.IClassProvider;
import org.spongepowered.asm.service.IClassTracker;
import org.spongepowered.asm.service.IGlobalPropertyService;
import org.spongepowered.asm.service.IMixinAuditTrail;
import org.spongepowered.asm.service.IPropertyKey;
import org.spongepowered.asm.service.ITransformerProvider;
import org.spongepowered.asm.service.MixinService;
import org.spongepowered.asm.service.MixinServiceAbstract;

/** Real Mixin application to the pinned native bytes, without initializing Minecraft or starting a server.
 * This verifies transformation and untouched-method preservation, not live-world behavior.
 */
public final class ClaimNativeMixinTest {
    private static final String TARGET = "xaero.pac.common.server.claims.protection.ChunkProtection";

    public static void main(String[] args) throws Exception {
        byte[] original = bytes(TARGET);
        ClassNode before = node(original);
        MethodNode block = method(before, "blockAccessCheck");
        require(block.desc.endsWith("Ljava/util/UUID;ZZZ)Lxaero/pac/common/server/claims/protection/ChunkProtection$InteractionTargetResult;"), "Pinned block target descriptor");
        require(calls(block, "checkPlayerGroupExceptionOption") == 3, "Exactly three narrow native callsites");
        MethodNode placement = before.methods.stream().filter(m -> m.name.equals("onEntityPlaceBlock")
            && m.desc.startsWith("(Lxaero/pac/common/server/IServerData;")).findFirst().orElseThrow();
        require(calls(placement, "blockAccessCheck") == 1 && calls(placement, "onUseItemAt") == 1,
            "Pinned placement has item and null-block paths");

        installOfflineService();
        MixinBootstrap.init();
        Mixins.addConfiguration("virgos_claim_permissions.mixins.json");
        var phase = MixinEnvironment.class.getDeclaredMethod("gotoPhase", MixinEnvironment.Phase.class);
        phase.setAccessible(true);
        phase.invoke(null, MixinEnvironment.Phase.DEFAULT);
        var constructor = Class.forName("org.spongepowered.asm.mixin.transformer.MixinTransformer").getDeclaredConstructor();
        constructor.setAccessible(true);
        var transformer = (IMixinTransformer) constructor.newInstance();
        byte[] transformed = transformer.transformClassBytes(TARGET, TARGET, original);
        ClassNode after = node(transformed);
        MethodNode exception = after.methods.stream().filter(m -> m.name.contains("virgos$exception")).findFirst().orElseThrow();
        require(calls(exception, "isOptionDefaulted") == 1,
            "Actual redirect consults native server-option locks");
        require(calls(method(after, "blockAccessCheck"), "checkPlayerGroupExceptionOption") == 0,
            "Real redirect replaces all three exception calls");
        require(callsContaining(method(after, "blockAccessCheck"), "virgos$exception") == 3,
            "Each native exception call reaches the actual adapter");
        require(callsContaining(method(after, "blockAccessCheck"), "virgos$denyBlock") > 0,
            "Deny return hook is applied");
        MethodNode placed = after.methods.stream().filter(m -> m.name.equals(placement.name) && m.desc.equals(placement.desc)).findFirst().orElseThrow();
        require(callsContaining(placed, "virgos$denyPlacement") > 0, "Placement early returns are guarded");
        for (MethodNode previous : before.methods) {
            if (previous.name.equals("blockAccessCheck") || previous == placement || previous.name.equals("<clinit>")) continue;
            MethodNode current = after.methods.stream().filter(m -> m.name.equals(previous.name) && m.desc.equals(previous.desc)).findFirst().orElseThrow();
            require(java.util.Arrays.equals(methodBytes(previous), methodBytes(current)),
                "Unrelated native method unchanged: " + previous.name + previous.desc);
        }
        System.out.println("ClaimNativeMixinTest passed: real native transformation and unrelated-method differential");
    }

    private static byte[] methodBytes(MethodNode method) {
        // Mixin recomputes frames/maxima for the whole class. Compare executable instructions,
        // not equivalent frame encodings or debug-label placement.
        MethodNode normalized = new MethodNode(method.access, method.name, method.desc,
            method.signature, method.exceptions.toArray(String[]::new));
        method.accept(normalized);
        for (var instruction : normalized.instructions.toArray())
            if (instruction instanceof org.objectweb.asm.tree.FrameNode
                || instruction instanceof org.objectweb.asm.tree.LineNumberNode)
                normalized.instructions.remove(instruction);
        normalized.localVariables = null;
        normalized.maxStack = 0;
        normalized.maxLocals = 0;
        ClassWriter writer = new ClassWriter(0);
        writer.visit(Opcodes.V17, Opcodes.ACC_PUBLIC, "Fixture", null, "java/lang/Object", null);
        normalized.accept(writer);
        writer.visitEnd();
        return writer.toByteArray();
    }

    private static MethodNode method(ClassNode owner, String name) {
        return owner.methods.stream().filter(m -> m.name.equals(name)).findFirst().orElseThrow();
    }

    private static int calls(MethodNode method, String name) {
        int result = 0;
        for (var instruction : method.instructions)
            if (instruction instanceof MethodInsnNode call && call.name.equals(name)) result++;
        return result;
    }

    private static int callsContaining(MethodNode method, String name) {
        int result = 0;
        for (var instruction : method.instructions)
            if (instruction instanceof MethodInsnNode call && call.name.contains(name)) result++;
        return result;
    }

    private static byte[] bytes(String name) throws IOException {
        try (InputStream stream = ClaimNativeMixinTest.class.getClassLoader().getResourceAsStream(name.replace('.', '/') + ".class")) {
            if (stream == null) throw new IOException("Missing native fixture: " + name);
            return stream.readAllBytes();
        }
    }

    private static ClassNode node(byte[] bytes) {
        ClassNode result = new ClassNode();
        new ClassReader(bytes).accept(result, ClassReader.EXPAND_FRAMES);
        return result;
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void installOfflineService() throws Exception {
        var getter = MixinService.class.getDeclaredMethod("getInstance");
        getter.setAccessible(true);
        Object instance = getter.invoke(null);
        Field service = MixinService.class.getDeclaredField("service");
        service.setAccessible(true);
        service.set(instance, new OfflineService());
        Field properties = MixinService.class.getDeclaredField("propertyService");
        properties.setAccessible(true);
        properties.set(instance, new OfflineProperties());
    }

    public static final class OfflineService extends MixinServiceAbstract implements IClassProvider, IClassBytecodeProvider {
        public String getName() { return "offline-native-fixture"; }
        public boolean isValid() { return true; }
        public IClassProvider getClassProvider() { return this; }
        public IClassBytecodeProvider getBytecodeProvider() { return this; }
        public ITransformerProvider getTransformerProvider() { return null; }
        public IClassTracker getClassTracker() { return null; }
        public IMixinAuditTrail getAuditTrail() { return null; }
        public Collection<String> getPlatformAgents() { return List.of(); }
        public IContainerHandle getPrimaryContainer() { return new ContainerHandleVirtual("offline-native-fixture"); }
        public InputStream getResourceAsStream(String name) { return getClass().getClassLoader().getResourceAsStream(name); }
        public URL[] getClassPath() { return new URL[0]; }
        public Class<?> findClass(String name) throws ClassNotFoundException { return findClass(name, false); }
        public Class<?> findClass(String name, boolean initialize) throws ClassNotFoundException {
            return Class.forName(name, initialize, getClass().getClassLoader());
        }
        public Class<?> findAgentClass(String name, boolean initialize) throws ClassNotFoundException { return findClass(name, initialize); }
        public ClassNode getClassNode(String name) throws ClassNotFoundException, IOException { return node(bytes(name)); }
        public ClassNode getClassNode(String name, boolean transformers) throws ClassNotFoundException, IOException { return getClassNode(name); }
    }

    private record Key(String value) implements IPropertyKey {}

    public static final class OfflineProperties implements IGlobalPropertyService {
        private final Map<IPropertyKey, Object> properties = new HashMap<>();
        public IPropertyKey resolveKey(String name) { return new Key(name); }
        @SuppressWarnings("unchecked") public <T> T getProperty(IPropertyKey key) { return (T) properties.get(key); }
        public void setProperty(IPropertyKey key, Object value) { properties.put(key, value); }
        public <T> T getProperty(IPropertyKey key, T fallback) { T value = getProperty(key); return value == null ? fallback : value; }
        public String getPropertyString(IPropertyKey key, String fallback) { Object value = getProperty(key); return value == null ? fallback : value.toString(); }
    }
}
