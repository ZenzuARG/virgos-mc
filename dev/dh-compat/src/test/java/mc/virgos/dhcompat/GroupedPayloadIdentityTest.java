package mc.virgos.dhcompat;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;
import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayloadReceiver;
import com.seibel.distanthorizons.core.network.messages.fullData.FullDataSplitMessage;
import com.seibel.distanthorizons.core.sql.dto.FullDataSourceV2DTO;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import it.unimi.dsi.fastutil.bytes.ByteArrayList;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.jar.JarFile;

/** Native wire DTO/receiver/PendingTransfer controls, bound to the pinned grouped loop. */
public final class GroupedPayloadIdentityTest {
    private static final String PAYLOAD = "com/seibel/distanthorizons/core/multiplayer/fullData/FullDataPayload";
    private static final String HANDLER = "com/seibel/distanthorizons/core/multiplayer/server/FullDataSourceRequestHandler";
    private static final String METHOD = "lambda$tick$0";
    private static final String DESCRIPTOR = "(Lcom/seibel/distanthorizons/core/multiplayer/server/DataSourceRequestGroup;Ljava/util/Map$Entry;)V";
    private static final String REMOVE = "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;";
    private static int encodes;

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static ClassNode read(byte[] bytes) {
        var node = new ClassNode(); new ClassReader(bytes).accept(node, 0); return node;
    }

    private static Object annotationValue(AnnotationNode node, String name) {
        for (int i = 0; i < node.values.size(); i += 2) if (node.values.get(i).equals(name)) return node.values.get(i + 1);
        throw new AssertionError("Missing annotation value: " + name);
    }

    private static AnnotationNode annotation(List<AnnotationNode> values, String suffix) {
        return values.stream().filter(a -> a.desc.endsWith(suffix + ";")).findFirst().orElseThrow();
    }

    private static void verifyPinnedSelection() throws Exception {
        Path jar = Path.of(System.getProperty("dh.compat.originalJar"));
        check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(jar)))
            .equals("a537a71171d935540b56b7598d0de2c106f6f5026336c713d89a1d9ea0ea14e3"), "Unrecognized native DH jar");
        try (var zip = new JarFile(jar.toFile())) {
            var owner = read(zip.getInputStream(zip.getJarEntry(HANDLER + ".class")).readAllBytes());
            var method = owner.methods.stream().filter(m -> m.name.equals(METHOD) && m.desc.equals(DESCRIPTOR)).findFirst().orElseThrow();
            int creations = 0, stores = 0, removes = 0, removeIndex = -1, sendIndex = -1, captureIndex = -1, captureLoads = 0;
            for (int i = 0; i < method.instructions.size(); i++) {
                var instruction = method.instructions.get(i);
                if (instruction instanceof TypeInsnNode type && type.getOpcode() == Opcodes.NEW && type.desc.equals(PAYLOAD)) creations++;
                if (instruction instanceof VarInsnNode variable && variable.getOpcode() == Opcodes.ASTORE && variable.var == 3) stores++;
                if (instruction instanceof MethodInsnNode call) {
                    if (call.owner.equals("java/util/concurrent/ConcurrentMap") && call.name.equals("remove") && call.desc.equals("(Ljava/lang/Object;)Ljava/lang/Object;")) { removes++; removeIndex = i; }
                    if (call.name.equals("sendInChunks")) sendIndex = i;
                }
                if (instruction instanceof InvokeDynamicInsnNode dynamic && dynamic.desc.contains("FullDataPayload;)Ljava/lang/Runnable;")) captureIndex = i;
            }
            for (int i = removeIndex + 1; i < sendIndex; i++) {
                var instruction = method.instructions.get(i);
                if (instruction instanceof VarInsnNode variable && variable.getOpcode() == Opcodes.ALOAD && variable.var == 3) captureLoads++;
            }
            boolean loop = false;
            for (int i = sendIndex + 1; i < method.instructions.size(); i++) {
                if (method.instructions.get(i) instanceof JumpInsnNode jump && jump.getOpcode() == Opcodes.GOTO
                    && method.instructions.indexOf(jump.label) < removeIndex) loop = true;
            }
            check(creations == 1 && stores == 1 && removes == 1 && removeIndex > 0 && captureIndex > removeIndex
                && sendIndex > captureIndex && captureLoads == 2 && loop,
                "Pinned loop must reuse slot 3 for both sender argument and final-response capture");
            var payload = read(zip.getInputStream(zip.getJarEntry(PAYLOAD + ".class")).readAllBytes());
            check(payload.fields.stream().anyMatch(f -> f.name.equals("lastBufferId")
                && f.desc.equals("Ljava/util/concurrent/atomic/AtomicInteger;") && (f.access & Opcodes.ACC_STATIC) != 0), "Native allocator changed");
        }
        try (var input = GroupedPayloadIdentityTest.class.getResourceAsStream("/mc/virgos/dhcompat/mixin/GroupedFullDataPayloadMixin.class")) {
            var mixin = read(input.readAllBytes());
            var hook = mixin.methods.stream().filter(m -> m.name.equals("virgos$uniqueGroupedResponse")).findFirst().orElseThrow();
            var modify = annotation(hook.visibleAnnotations, "ModifyVariable");
            check(annotationValue(modify, "method").equals(List.of(METHOD + DESCRIPTOR)), "Wrong grouped method selector");
            check(annotationValue(modify, "index").equals(3) && annotationValue(modify, "require").equals(1), "Local slot/match requirement changed");
            var at = (AnnotationNode) annotationValue(modify, "at");
            check(annotationValue(at, "value").equals("INVOKE") && annotationValue(at, "target").equals(REMOVE)
                && annotationValue(at, "ordinal").equals(0), "Hook must precede the one per-iteration removal");
            int helperCalls = 0;
            for (var instruction : hook.instructions) {
                if (instruction instanceof MethodInsnNode call && call.owner.equals("mc/virgos/dhcompat/GroupedPayloads")
                    && call.name.equals("forResponse") && call.desc.equals("(L" + PAYLOAD + ";)L" + PAYLOAD + ";")) helperCalls++;
            }
            check(helperCalls == 1, "Bound hook must invoke the tested response-wrapper helper exactly once");
        }
        try (var input = GroupedPayloadIdentityTest.class.getResourceAsStream("/mc/virgos/dhcompat/mixin/FullDataPayloadIdAccessor.class")) {
            var accessor = read(input.readAllBytes());
            var method = accessor.methods.stream().filter(m -> m.name.equals("virgos$lastBufferId")).findFirst().orElseThrow();
            check((method.access & Opcodes.ACC_STATIC) != 0 && annotationValue(annotation(method.visibleAnnotations, "Accessor"), "value").equals("lastBufferId"), "Accessor must expose the native static allocator");
        }
    }

    private static AtomicInteger nativeIds() throws Exception {
        var field = FullDataPayload.class.getDeclaredField("lastBufferId"); field.setAccessible(true); return (AtomicInteger) field.get(null);
    }

    private static FullDataPayload wrap(FullDataPayload encoded) throws Exception {
        if (Boolean.getBoolean("dh.compat.grouped.disabled")) return encoded; // Observed native RED control.
        var helper = Class.forName("mc.virgos.dhcompat.GroupedPayloads");
        var method = helper.getDeclaredMethod("withNativeId", FullDataPayload.class, AtomicInteger.class); method.setAccessible(true);
        return (FullDataPayload) method.invoke(null, encoded, nativeIds());
    }

    private static FullDataPayload encodedOnce() throws Exception {
        encodes++;
        var dto = FullDataSourceV2DTO.CreateEmptyDataSourceForDecoding(); dto.pos = 4242; dto.dataChecksum = 37;
        dto.compressedDataByteArray = new ByteArrayList(); dto.compressedMappingByteArray = new ByteArrayList();
        dto.compressedNorthAdjDataByteArray = new ByteArrayList(); dto.compressedSouthAdjDataByteArray = new ByteArrayList();
        dto.compressedEastAdjDataByteArray = new ByteArrayList(); dto.compressedWestAdjDataByteArray = new ByteArrayList();
        dto.compressedColumnGenStepByteArray = new ByteArrayList(); dto.compressedWorldCompressionModeByteArray = new ByteArrayList();
        dto.dataFormatVersion = 2; dto.compressionModeValue = 0; dto.applyToParent = false; dto.applyToChildren = false; dto.regenerate = false;
        var payload = new FullDataPayload(); payload.dtoBufferId = nativeIds().getAndIncrement(); payload.dtoBuffer = Unpooled.buffer();
        payload.beaconBeams = List.of(); dto.encode(payload.dtoBuffer); return payload;
    }

    private record Transfer(int id, ByteBuf data, Runnable completed) {}

    private static Transfer nativeTransfer(FullDataPayload payload, Runnable completed) throws Exception {
        Class<?> type = Class.forName("com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayloadSender$PendingTransfer");
        var constructor = type.getDeclaredConstructor(FullDataPayload.class, Runnable.class); constructor.setAccessible(true);
        Object transfer = constructor.newInstance(payload, completed);
        var id = type.getDeclaredField("bufferId"); var data = type.getDeclaredField("buffer"); var end = type.getDeclaredField("sendFinalMessage");
        id.setAccessible(true); data.setAccessible(true); end.setAccessible(true);
        return new Transfer(id.getInt(transfer), (ByteBuf) data.get(transfer), (Runnable) end.get(transfer));
    }

    private static FullDataPayload finalPayload(int id) { var payload = new FullDataPayload(); payload.dtoBufferId = id; return payload; }

    private static void fragment(FullDataPayloadReceiver receiver, Transfer transfer) {
        receiver.receiveChunk(new FullDataSplitMessage(transfer.id(), transfer.data().copy(), true));
    }

    private static void consumedOnce(FullDataPayloadReceiver receiver, int id) {
        check(receiver.decodeDataSource(finalPayload(id)).pos == 4242, "Wrong native decoded DTO");
        try { receiver.decodeDataSource(finalPayload(id)); throw new AssertionError("Repeated consumption must still fail normally"); }
        catch (NullPointerException expected) { check(expected.getMessage().startsWith("Unable to get a complete buffer"), "Unexpected failure"); }
    }

    public static void main(String[] args) throws Exception {
        var shared = encodedOnce(); byte[] bytes = new byte[shared.dtoBuffer.writerIndex()]; shared.dtoBuffer.getBytes(0, bytes);
        shared.dtoBuffer.readerIndex(3); int originalReader = shared.dtoBuffer.readerIndex(), originalId = shared.dtoBufferId;
        try (var reused = new FullDataPayloadReceiver()) {
            fragment(reused, nativeTransfer(shared, () -> {})); fragment(reused, nativeTransfer(shared, () -> {}));
            consumedOnce(reused, originalId);
            System.out.println("Native reused-ID control reproduced the second-consumption missing-buffer failure");
        }
        var one = wrap(shared); var two = wrap(one);
        check(one.dtoBufferId != two.dtoBufferId, "Grouped responses must own distinct native IDs");
        if (!Boolean.getBoolean("dh.compat.grouped.disabled")) verifyPinnedSelection();
        for (var payload : List.of(one, two)) {
            check(payload.dtoBuffer == shared.dtoBuffer && payload.beaconBeams == shared.beaconBeams, "Encoded bytes/beacons must be shared, not recompressed");
        }
        var finals = new ArrayList<Integer>();
        var a = nativeTransfer(one, () -> finals.add(one.dtoBufferId)); var b = nativeTransfer(two, () -> finals.add(two.dtoBufferId));
        check(a.data().readerIndex() == 0 && b.data().readerIndex() == 0, "Native transfer must reset only its duplicate reader");
        a.data().readByte(); check(b.data().readerIndex() == 0 && shared.dtoBuffer.readerIndex() == originalReader, "Transfer read indices must be independent"); a.data().readerIndex(0);
        try (var receiver = new FullDataPayloadReceiver()) {
            fragment(receiver, a); fragment(receiver, b); a.completed().run(); b.completed().run();
            check(finals.equals(List.of(a.id(), b.id())), "Final-response ID must match each transfer's fragments");
            consumedOnce(receiver, finals.get(0)); consumedOnce(receiver, finals.get(1));
        }
        try (var first = new FullDataPayloadReceiver(); var second = new FullDataPayloadReceiver()) {
            fragment(first, a); fragment(second, b); consumedOnce(first, a.id()); consumedOnce(second, b.id());
        }
        try (var direct = new FullDataPayloadReceiver()) {
            var transfer = nativeTransfer(shared, () -> {}); fragment(direct, transfer); consumedOnce(direct, originalId);
        }
        byte[] after = new byte[bytes.length]; shared.dtoBuffer.getBytes(0, after);
        check(encodes == 1 && Arrays.equals(bytes, after) && shared.dtoBuffer.readerIndex() == originalReader
            && shared.dtoBufferId == originalId, "Shared encoded payload was mutated or encoded twice");
        System.out.println("Grouped payload identity: pinned selector/capture, one encode, single/direct/cross-session/same-receiver controls and native DTO consumption passed");
    }
}
