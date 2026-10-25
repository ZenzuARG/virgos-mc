package mc.virgos.dhcompat;

import com.seibel.distanthorizons.api.enums.worldGeneration.EDhApiDistantGeneratorMode;
import com.seibel.distanthorizons.api.enums.worldGeneration.EDhApiGeneratorPlan;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarFile;

/** Pin the native hook and retain mutual exclusion in every actual-generation mode. */
public final class ChunkyLodServingTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static ClassNode read(byte[] data) {
        ClassNode node = new ClassNode();
        new ClassReader(data).accept(node, 0);
        return node;
    }

    public static void main(String[] args) throws Exception {
        try (JarFile jar = new JarFile(Path.of(System.getProperty("dh.compat.originalJar")).toFile())) {
            String target = "com/seibel/distanthorizons/core/wrapperInterfaces/modAccessor/AbstractChunkyAccessor.class";
            ClassNode nativeClass = read(jar.getInputStream(jar.getJarEntry(target)).readAllBytes());
            var event = nativeClass.methods.stream().filter(m -> m.name.equals("onGenEvent") && m.desc.equals("()V")).findFirst().orElseThrow();
            check(java.util.stream.StreamSupport.stream(event.instructions.spliterator(), false)
                .anyMatch(n -> n instanceof MethodInsnNode call && call.name.equals("setApiValue")), "Pinned native hook no longer overrides generation");
        }
        try (var input = ChunkyLodServingTest.class.getResourceAsStream("/mc/virgos/dhcompat/mixin/ChunkyReadinessMixin.class")) {
            ClassNode mixin = read(input.readAllBytes());
            int hooks = 0;
            for (var method : mixin.methods) {
                List<AnnotationNode> annotations = new ArrayList<>();
                if (method.visibleAnnotations != null) annotations.addAll(method.visibleAnnotations);
                if (method.invisibleAnnotations != null) annotations.addAll(method.invisibleAnnotations);
                for (var annotation : annotations) {
                    if (!annotation.desc.endsWith("/Inject;")) continue;
                    var values = annotation.values;
                    if (!values.get(values.indexOf("method") + 1).equals(List.of("onGenEvent()V"))) continue;
                    hooks++;
                    check(values.get(values.indexOf("cancellable") + 1).equals(true), "Entry guard must cancel native override");
                    check(values.get(values.indexOf("require") + 1).equals(1), "Guard must fail closed on target drift");
                    var at = (List<?>) values.get(values.indexOf("at") + 1);
                    var head = (AnnotationNode) at.get(0);
                    check(head.values.get(head.values.indexOf("value") + 1).equals("HEAD"), "Guard must precede native timestamp and override");
                    boolean policy = false, cancel = false, underlyingPlan = false;
                    for (var instruction : method.instructions) {
                        if (instruction instanceof MethodInsnNode call) {
                            policy |= call.owner.equals("mc/virgos/dhcompat/ChunkyLodServingPolicy") && call.name.equals("preserveCachedServing");
                            cancel |= call.owner.endsWith("/CallbackInfo") && call.name.equals("cancel");
                            underlyingPlan |= call.name.equals("getTrueValue");
                        }
                    }
                    check(policy && cancel && underlyingPlan, "Hook must use tested policy and underlying configured plan");
                }
            }
            check(hooks == 1, "Expected exactly one narrow Chunky cached-serving guard");
        }
        var policy = Class.forName("mc.virgos.dhcompat.ChunkyLodServingPolicy").getMethod("preserveCachedServing", boolean.class, EDhApiDistantGeneratorMode.class, EDhApiGeneratorPlan.class);
        for (boolean dedicated : new boolean[]{false, true}) {
            for (var mode : EDhApiDistantGeneratorMode.values()) {
                for (var plan : EDhApiGeneratorPlan.values()) {
                    boolean expected = dedicated && mode == EDhApiDistantGeneratorMode.PRE_EXISTING_ONLY && plan == EDhApiGeneratorPlan.CHUNKS_ONLY;
                    check(policy.invoke(null, dedicated, mode, plan).equals(expected), "Native exclusion changed outside the cached-serving configuration");
                }
            }
        }
        System.out.println("Chunky cached serving: pinned entry, cancellation, underlying plan, and all mode/plan/side controls passed");
    }
}
