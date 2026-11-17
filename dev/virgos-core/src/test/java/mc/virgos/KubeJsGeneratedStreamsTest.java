package mc.virgos;

import java.io.InputStream;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
import org.objectweb.asm.*;

/** Uses the installed native Lazy bytecode, pausing only to force a real interleaving. */
public final class KubeJsGeneratedStreamsTest {
    private static final String LAZY = "dev.latvian.mods.kubejs.util.Lazy";
    private static final byte[] CONTENT = {17, 42, 99};
    private static final AtomicBoolean PAUSE_FIRST = new AtomicBoolean();
    private static CountDownLatch cleared, release;

    public static void afterNativeValueCleared() {
        if (PAUSE_FIRST.compareAndSet(true, false)) {
            cleared.countDown();
            await(release, "release native invalidation");
        }
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void await(CountDownLatch latch, String label) {
        try { check(latch.await(5, TimeUnit.SECONDS), "Timed out: " + label); }
        catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new AssertionError(error); }
    }

    private record Cache(Supplier<byte[]> data, Runnable forget) {}

    private static Cache nativeCache(Supplier<byte[]> factory) throws Exception {
        byte[] original;
        try (var stream = KubeJsGeneratedStreamsTest.class.getResourceAsStream("/" + LAZY.replace('.', '/') + ".class")) {
            check(stream != null, "Installed KubeJS Lazy must be on the test classpath");
            original = stream.readAllBytes();
        }
        ClassWriter writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        AtomicInteger hooks = new AtomicInteger();
        new ClassReader(original).accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                MethodVisitor delegate = super.visitMethod(access, name, descriptor, signature, exceptions);
                if (!name.equals("forget")) return delegate;
                return new MethodVisitor(Opcodes.ASM9, delegate) {
                    @Override public void visitFieldInsn(int opcode, String owner, String field, String type) {
                        super.visitFieldInsn(opcode, owner, field, type);
                        if (opcode == Opcodes.PUTFIELD && field.equals("value")) {
                            hooks.incrementAndGet();
                            super.visitMethodInsn(Opcodes.INVOKESTATIC, "mc/virgos/KubeJsGeneratedStreamsTest",
                                "afterNativeValueCleared", "()V", false);
                        }
                    }
                };
            }
        }, 0);
        check(hooks.get() == 1, "Native invalidation shape changed; inspect the installed version");
        class NativeLoader extends ClassLoader {
            NativeLoader() { super(KubeJsGeneratedStreamsTest.class.getClassLoader()); }
            Class<?> define(byte[] bytes) { return defineClass(LAZY, bytes, 0, bytes.length); }
        }
        Class<?> type = new NativeLoader().define(writer.toByteArray());
        Object instance = type.getMethod("of", Supplier.class).invoke(null, factory);
        Method forget = type.getMethod("forget");
        @SuppressWarnings("unchecked") Supplier<byte[]> supplier = (Supplier<byte[]>) instance;
        return new Cache(supplier, () -> {
            try { forget.invoke(instance); }
            catch (ReflectiveOperationException error) { throw new AssertionError(error); }
        });
    }

    private static Thread reader(Cache cache, ConcurrentLinkedQueue<Throwable> errors, CountDownLatch done) {
        Thread thread = new Thread(() -> {
            try (InputStream stream = KubeJsGeneratedStreams.open(cache.data(), cache.forget(), true)) {
                check(Arrays.equals(CONTENT, stream.readAllBytes()), "Generated resource bytes must be preserved");
            } catch (Throwable error) { errors.add(error); }
            finally { done.countDown(); }
        });
        thread.setDaemon(true);
        return thread;
    }

    private static void forcedNativeRace() throws Exception {
        Cache cache = nativeCache(() -> CONTENT);
        cache.data().get();
        cleared = new CountDownLatch(1); release = new CountDownLatch(1); PAUSE_FIRST.set(true);
        var errors = new ConcurrentLinkedQueue<Throwable>();
        var firstDone = new CountDownLatch(1); var secondDone = new CountDownLatch(1);
        Thread first = reader(cache, errors, firstDone), second = reader(cache, errors, secondDone);
        first.start();
        try {
            await(cleared, "native value=null before cached=false");
            second.start();
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
            while (second.getState() != Thread.State.BLOCKED && secondDone.getCount() != 0 && System.nanoTime() < deadline)
                Thread.sleep(1);
            check(second.getState() == Thread.State.BLOCKED || secondDone.getCount() == 0, "Second reader must attempt the invalidation window");
        } finally { release.countDown(); PAUSE_FIRST.set(false); }
        await(firstDone, "first reader"); await(secondDone, "second reader");
        check(errors.isEmpty(), "Native get/forget race must not return null: " + errors);
    }

    private static void streamSemantics() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        Cache cache = nativeCache(() -> { calls.incrementAndGet(); return CONTENT; });
        try (InputStream first = KubeJsGeneratedStreams.open(cache.data(), cache.forget(), false);
             InputStream second = KubeJsGeneratedStreams.open(cache.data(), cache.forget(), false)) {
            check(first.read() == CONTENT[0], "First cursor");
            check(Arrays.equals(second.readAllBytes(), CONTENT), "Each stream needs its own cursor");
            check(calls.get() == 1, "Non-forgetting resources retain their cache");
        }
        for (int i = 0; i < 2; i++) {
            try (var stream = KubeJsGeneratedStreams.open(cache.data(), cache.forget(), true)) {
                check(Arrays.equals(stream.readAllBytes(), CONTENT), "Forgotten resources must reload without truncation");
            }
        }
        check(calls.get() == 2, "Forgetting semantics must remain intact");
        AtomicInteger forgotten = new AtomicInteger();
        RuntimeException expected = new RuntimeException("supplier failure");
        try { KubeJsGeneratedStreams.open(() -> { throw expected; }, forgotten::incrementAndGet, true); throw new AssertionError("Failure hidden"); }
        catch (RuntimeException error) { check(error == expected, "Supplier failure must propagate unchanged"); }
        check(forgotten.get() == 0, "A failed fetch must not invalidate as if it succeeded");
        try { KubeJsGeneratedStreams.open(() -> null, forgotten::incrementAndGet, true); throw new AssertionError("Null resource hidden"); }
        catch (NullPointerException expectedNull) { }
        try (var empty = KubeJsGeneratedStreams.open(() -> new byte[0], forgotten::incrementAndGet, false)) {
            check(empty.read() == -1, "A genuinely empty resource remains valid");
        }
    }

    private static void independentCaches() throws Exception {
        var entered = new CountDownLatch(1); var finish = new CountDownLatch(1); var otherDone = new CountDownLatch(1);
        var failures = new ConcurrentLinkedQueue<Throwable>();
        Thread first = new Thread(() -> {
            try (var ignored = KubeJsGeneratedStreams.open(() -> { entered.countDown(); await(finish, "first cache"); return CONTENT; }, () -> {}, false)) { }
            catch (Throwable error) { failures.add(error); }
        });
        Thread second = new Thread(() -> {
            try (var stream = KubeJsGeneratedStreams.open(() -> CONTENT, () -> {}, false)) {
                check(Arrays.equals(stream.readAllBytes(), CONTENT), "Independent cache bytes");
            } catch (Throwable error) { failures.add(error); }
            finally { otherDone.countDown(); }
        });
        first.setDaemon(true); second.setDaemon(true); first.start();
        try { await(entered, "slow cache entered"); second.start(); await(otherDone, "unrelated cache is not globally blocked"); }
        finally { finish.countDown(); }
        first.join(2000); second.join(2000);
        check(failures.isEmpty(), "Independent cache failure: " + failures);
    }

    private static void injectionWiring() throws Exception {
        try (var stream = KubeJsGeneratedStreamsTest.class.getResourceAsStream("/virgos_core.mixins.json")) {
            check(stream != null && new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)
                .contains("KubeJsGeneratedDataMixin"), "The production mixin must be registered");
        }
        AtomicBoolean strict = new AtomicBoolean(), descriptor = new AtomicBoolean(), delegated = new AtomicBoolean();
        try (var stream = KubeJsGeneratedStreamsTest.class.getResourceAsStream("/mc/virgos/mixin/KubeJsGeneratedDataMixin.class")) {
            check(stream != null, "Production injection bytecode");
            new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override public MethodVisitor visitMethod(int access, String name, String type, String signature, String[] exceptions) {
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override public AnnotationVisitor visitAnnotation(String annotation, boolean visible) {
                            if (!annotation.endsWith("/Inject;")) return null;
                            return new AnnotationVisitor(Opcodes.ASM9) {
                                @Override public void visit(String key, Object value) {
                                    if (key.equals("require") && value.equals(1)) strict.set(true);
                                }
                                @Override public AnnotationVisitor visitArray(String key) {
                                    return new AnnotationVisitor(Opcodes.ASM9) {
                                        @Override public void visit(String ignored, Object value) {
                                            if (key.equals("method") && value.equals("get()Ljava/io/InputStream;")) descriptor.set(true);
                                        }
                                    };
                                }
                            };
                        }
                        @Override public void visitMethodInsn(int opcode, String owner, String method, String type, boolean isInterface) {
                            if (owner.equals("mc/virgos/KubeJsGeneratedStreams") && method.equals("open")) delegated.set(true);
                        }
                    };
                }
            }, 0);
        }
        check(strict.get() && descriptor.get() && delegated.get(), "Exact required injection must delegate to the tested guard");
    }

    public static void main(String[] args) throws Exception {
        forcedNativeRace(); streamSemantics(); independentCaches(); injectionWiring();
        System.out.println("PASS: native invalidation interleaving, resource bytes, cache lifecycle, failures and independent caches");
    }
}
