package mc.virgos.dhcompat;

import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.FieldInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.jar.JarFile;

/** Replays publication boundaries extracted from the pinned real constructor bytecode. */
public final class LevelPublicationTest {
    private static final String OWNER = "com/seibel/distanthorizons/core/level/DhClientLevel";
    private static final String FULL = "(Lcom/seibel/distanthorizons/core/file/structure/ISaveStructure;"
        + "Lcom/seibel/distanthorizons/core/wrapperInterfaces/world/IClientLevelWrapper;Ljava/io/File;"
        + "Lcom/seibel/distanthorizons/core/multiplayer/client/ClientNetworkState;)V";
    private static final String ORIGINAL_SHA256 = "a537a71171d935540b56b7598d0de2c106f6f5026336c713d89a1d9ea0ea14e3";

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static ClassNode read(byte[] bytes) {
        ClassNode node = new ClassNode();
        new ClassReader(bytes).accept(node, 0);
        return node;
    }

    private static List<String> constructorEvents(MethodNode constructor) {
        List<String> events = new ArrayList<>();
        for (var instruction : constructor.instructions) {
            if (instruction instanceof MethodInsnNode call) {
                switch (call.name) {
                    case "setDhLevel" -> events.add("wrapper");
                    case "registerNetworkHandlers" -> events.add("handlers");
                    case "createAndSetSupportingRepos" -> events.add("repos");
                    case "runRepoReliantSetup" -> events.add("setup");
                    case "startRenderer" -> events.add("renderer");
                    default -> { }
                }
            } else if (instruction instanceof FieldInsnNode field && field.getOpcode() == Opcodes.PUTFIELD && field.owner.equals(OWNER)) {
                switch (field.name) {
                    case "remoteDataSourceProvider" -> events.add("provider");
                    case "lodRequestModule" -> events.add("lod");
                    case "clientside" -> events.add("clientside");
                    default -> { }
                }
            } else if (instruction.getOpcode() == Opcodes.RETURN) events.add("return");
        }
        return events;
    }

    private static final class ConstructorFixture {
        private final DeferredLevelPublication deferred;
        private final boolean network;
        private boolean provider, lod, repos, setup, renderer, published, registered;
        private boolean earlyPublication;
        private Runnable clientside;
        private int wrapperPublications, registrations, applied;
        private final List<String> observations = new ArrayList<>();

        ConstructorFixture(boolean patched, boolean network) {
            this.deferred = patched ? new DeferredLevelPublication() : null;
            this.network = network;
        }

        void replay(List<String> events, boolean failBeforeReturn) {
            for (String event : events) {
                switch (event) {
                    case "wrapper" -> {
                        Runnable publish = () -> { published = true; wrapperPublications++; observations.add("published"); };
                        if (deferred == null) publish.run(); else deferred.deferWrapper(publish);
                    }
                    case "handlers" -> {
                        if (network) {
                            Runnable register = () -> {
                                registered = true;
                                registrations++;
                                observations.add("registered");
                                // Immediate delivery at native subscription publication: no sleeps or timing assumptions.
                                clientside.run();
                            };
                            if (deferred == null) register.run(); else deferred.deferHandlers(register);
                        }
                    }
                    case "provider" -> provider = true;
                    case "lod" -> lod = true;
                    case "clientside" -> clientside = () -> {
                        check(provider && lod && repos && setup && renderer && published, "Callback observed incomplete constructor state");
                        applied++;
                    };
                    case "repos" -> repos = true;
                    case "setup" -> setup = true;
                    case "renderer" -> renderer = true;
                    case "return" -> {
                        if (failBeforeReturn) return;
                        if (deferred != null) deferred.complete();
                    }
                    default -> throw new AssertionError(event);
                }
                if (!event.equals("return") && published) earlyPublication = true;
            }
        }

        void close() { registered = false; published = false; }
        void deliver() { if (registered) clientside.run(); }
    }

    private static void verifyMixinBindings() throws Exception {
        try (var input = LevelPublicationTest.class.getResourceAsStream("/mc/virgos/dhcompat/mixin/DhClientLevelMixin.class")) {
            check(input != null, "Compiled client-level mixin is missing");
            ClassNode mixin = read(input.readAllBytes());
            int hooks = 0;
            for (MethodNode method : mixin.methods) {
                List<AnnotationNode> annotations = new ArrayList<>();
                if (method.visibleAnnotations != null) annotations.addAll(method.visibleAnnotations);
                if (method.invisibleAnnotations != null) annotations.addAll(method.invisibleAnnotations);
                for (AnnotationNode annotation : annotations) {
                    if (!annotation.desc.endsWith("/Redirect;") && !annotation.desc.endsWith("/Inject;")) continue;
                    hooks++;
                    int index = annotation.values.indexOf("method");
                    check(index >= 0 && annotation.values.get(index + 1).equals(List.of("<init>" + FULL)), "Hook must target only the full constructor");
                    check(annotation.values.get(annotation.values.indexOf("require") + 1).equals(1), "Hook must require its pinned call site");
                }
            }
            check(hooks == 3, "Expected exactly wrapper redirect, registration redirect and return injection");
        }
        try (var input = LevelPublicationTest.class.getResourceAsStream("/virgos_dh_compat.mixins.json")) {
            String config = new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
            check(java.util.regex.Pattern.compile("\"client\"\\s*:\\s*\\[[^]]*\"DhClientLevelMixin\"", java.util.regex.Pattern.DOTALL).matcher(config).find(), "Level mixin must be client-only");
        }
    }

    public static void main(String[] args) throws Exception {
        Path jarPath = Path.of(System.getProperty("dh.compat.originalJar"));
        check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(jarPath))).equals(ORIGINAL_SHA256), "Use the pinned original DH input");
        ClassNode target;
        try (JarFile jar = new JarFile(jarPath.toFile())) {
            target = read(jar.getInputStream(jar.getJarEntry(OWNER + ".class")).readAllBytes());
        }
        MethodNode constructor = target.methods.stream().filter(method -> method.name.equals("<init>") && method.desc.equals(FULL)).findFirst().orElseThrow();
        List<String> events = constructorEvents(constructor);
        check(events.equals(List.of("wrapper", "handlers", "provider", "lod", "clientside", "repos", "setup", "renderer", "return")), "Pinned native publication/module order changed");
        try {
            new ConstructorFixture(false, true).replay(events, false);
            throw new AssertionError("Native early callback must reproduce null clientside");
        } catch (NullPointerException expected) {
            System.out.println("Pinned native constructor control reproduced null clientside at handler publication");
        }
        ConstructorFixture fixed = new ConstructorFixture(true, true);
        fixed.replay(events, false);
        check(!fixed.earlyPublication && fixed.wrapperPublications == 1 && fixed.registrations == 1 && fixed.applied == 1, "Publish and bind exactly once after all native initialization");
        check(fixed.observations.equals(List.of("published", "registered")), "Wrapper publication must precede handler registration");
        fixed.deferred.complete();
        check(fixed.registrations == 1 && fixed.wrapperPublications == 1, "Repeated completion cannot publish twice");
        ConstructorFixture noNetwork = new ConstructorFixture(true, false);
        noNetwork.replay(events, false);
        check(noNetwork.wrapperPublications == 1 && noNetwork.registrations == 0 && noNetwork.applied == 0, "Null-network branch must not create handlers");
        ConstructorFixture failed = new ConstructorFixture(true, true);
        failed.replay(events, true);
        check(!failed.published && !failed.registered, "Failed constructor must never publish or bind");
        MethodNode delegate = target.methods.stream().filter(method -> method.name.equals("<init>") && !method.desc.equals(FULL)).findFirst().orElseThrow();
        long delegations = java.util.stream.StreamSupport.stream(delegate.instructions.spliterator(), false)
            .filter(node -> node instanceof MethodInsnNode call && call.owner.equals(OWNER) && call.name.equals("<init>") && call.desc.equals(FULL)).count();
        check(delegations == 1 && !constructorEvents(delegate).contains("wrapper") && !constructorEvents(delegate).contains("handlers"), "Convenience constructor must only delegate publication to full constructor");
        MethodNode close = target.methods.stream().filter(method -> method.name.equals("close") && method.desc.equals("()V")).findFirst().orElseThrow();
        check(java.util.stream.StreamSupport.stream(close.instructions.spliterator(), false).anyMatch(node -> node instanceof MethodInsnNode call && call.owner.endsWith("/ScopedNetworkEventSource") && call.name.equals("close")), "Native close must retain scoped unregistration");
        fixed.close();
        fixed.deliver();
        check(!fixed.registered && !fixed.published && fixed.applied == 1, "Native-style close must clear publication and unsubscribe without replay");
        verifyMixinBindings();
        System.out.println("Level publication: actual-bytecode ordering, ready callback, once-only/delegated/null/failed controls and close passed");
    }
}
