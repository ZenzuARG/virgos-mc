package mc.virgos.dhcompat.payload;

import com.google.common.base.Ticker;
import com.google.common.cache.CacheBuilder;
import com.google.common.collect.ForwardingConcurrentMap;
import com.seibel.distanthorizons.core.multiplayer.fullData.*;
import com.seibel.distanthorizons.core.network.messages.fullData.FullDataSplitMessage;
import com.seibel.distanthorizons.core.sql.dto.FullDataSourceV2DTO;
import io.netty.buffer.*;
import it.unimi.dsi.fastutil.bytes.ByteArrayList;
import java.util.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.jar.JarFile;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Executes the original receiver/DTO decoder; only its exact Map.get seam is adapted. */
public final class PayloadOwnershipTest {
    static int checks;
    static void check(boolean value, String label) {
        checks++; if (!value) throw new AssertionError(label);
    }
    static final class Held implements Executor {
        final Queue<Runnable> tasks = new ArrayDeque<>();
        public void execute(Runnable task) { tasks.add(task); }
        void run() { tasks.remove().run(); }
    }
    static final class Payload extends FullDataPayload implements PayloadOwnership.Payload {
        final PayloadOwnership.Slot slot = new PayloadOwnership.Slot();
        Payload(int id) { dtoBufferId = id; }
        public PayloadOwnership.Slot virgos$slot() { return slot; }
    }
    static final class Receiver extends FullDataPayloadReceiver implements PayloadOwnership.Receiver {
        final PayloadOwnership.Owner owner = new PayloadOwnership.Owner();
        final AtomicLong clock = new AtomicLong();
        final ConcurrentMap<Integer, CompositeByteBuf> nativeMap;
        Payload current;
        Receiver() throws Exception {
            nativeMap = CacheBuilder.newBuilder().expireAfterAccess(30, TimeUnit.SECONDS)
                .ticker(new Ticker() { public long read() { return clock.get(); } })
                .<Integer, CompositeByteBuf>build().asMap();
            var seam = new ForwardingConcurrentMap<Integer, CompositeByteBuf>() {
                protected ConcurrentMap<Integer, CompositeByteBuf> delegate() { return nativeMap; }
                public CompositeByteBuf remove(Object key) {
                    if (current == null) return nativeMap.remove(key);
                    return (CompositeByteBuf) PayloadOwnership.remove(current, () -> nativeMap.remove(key));
                }
                public CompositeByteBuf get(Object key) {
                    if (current == null) return nativeMap.get(key);
                    return (CompositeByteBuf) PayloadOwnership.lookup(Receiver.this, current,
                        () -> nativeMap.get(key));
                }
            };
            var field = FullDataPayloadReceiver.class.getDeclaredField("buffersById");
            field.setAccessible(true); field.set(this, seam);
        }
        public PayloadOwnership.Owner virgos$owner() { return owner; }
        public FullDataSourceV2DTO decodeDataSource(FullDataPayload payload) {
            current = (Payload) payload;
            try { return super.decodeDataSource(payload); }
            finally { current = null; }
        }
        public void close() { owner.close(); super.close(); }
        Runnable claim(Payload payload) {
            return PayloadOwnership.claim(this, payload, () -> nativeMap.remove(payload.dtoBufferId));
        }
        void receive(int id, long pos) {
            receiveChunk(new FullDataSplitMessage(id, encode(pos), true));
        }
        void expire() { clock.set(TimeUnit.SECONDS.toNanos(31)); }
    }
    static ByteBuf encode(long pos) {
        var dto = FullDataSourceV2DTO.CreateEmptyDataSourceForDecoding();
        dto.pos=pos; dto.dataChecksum=(int)pos;
        dto.compressedDataByteArray=new ByteArrayList();
        dto.compressedNorthAdjDataByteArray=new ByteArrayList();
        dto.compressedSouthAdjDataByteArray=new ByteArrayList();
        dto.compressedEastAdjDataByteArray=new ByteArrayList();
        dto.compressedWestAdjDataByteArray=new ByteArrayList();
        dto.compressedColumnGenStepByteArray=new ByteArrayList();
        dto.compressedWorldCompressionModeByteArray=new ByteArrayList();
        dto.compressedMappingByteArray=new ByteArrayList();
        dto.dataFormatVersion=2; dto.compressionModeValue=0;
        dto.createdUnixDateTime=1; dto.lastModifiedUnixDateTime=2;
        ByteBuf buffer=Unpooled.buffer(); dto.encode(buffer); return buffer;
    }
    static void missing(Receiver receiver, Payload payload) {
        try { receiver.decodeDataSource(payload); throw new AssertionError("Expected native missing buffer"); }
        catch (NullPointerException expected) {
            check(expected.getMessage().startsWith("Unable to get a complete buffer"), "native failure unchanged");
        }
    }
    static void nativeExpiryControl() throws Exception {
        try (var receiver = new Receiver()) {
            receiver.receive(1, 1030); receiver.expire(); missing(receiver, new Payload(1));
        }
    }
    static void completedBeforeDeferredDecode() throws Exception {
        try (var receiver = new Receiver()) {
            receiver.receive(2, 1030); var payload = new Payload(2);
            var source = new CompletableFuture<Payload>(); var executor = new Held();
            var result = PayloadOwnership.handleAsync(source, (response, error) -> {
                check(error == null, "successful native callback");
                try (var dto = receiver.decodeDataSource(response)) { return dto.pos; }
            }, executor, receiver::claim);
            source.complete(payload);
            check(executor.tasks.size()==1, "one native asynchronous task");
            receiver.expire(); executor.run();
            check(result.join()==1030L, "completed payload survives held executor beyond 30s");
            missing(receiver, payload);
        }
    }
    static CompletableFuture<Long> requested(Receiver receiver, Payload payload, Held executor) {
        return PayloadOwnership.handleAsync(CompletableFuture.completedFuture(payload), (response, error) -> {
            try (var dto=receiver.decodeDataSource(response)) { return dto.pos; }
        }, executor, receiver::claim);
    }
    static void immediateAndIndependentReceivers() throws Exception {
        try (var a=new Receiver(); var b=new Receiver()) {
            a.receive(3, 30); b.receive(3, 31);
            var first=PayloadOwnership.handleAsync(CompletableFuture.completedFuture(new Payload(3)),
                (payload,error) -> { try(var dto=a.decodeDataSource(payload)) { return dto.pos; } },
                Runnable::run, a::claim);
            check(first.join()==30, "immediate native executor result unchanged");
            check(b.decodeDataSource(new Payload(3)).pos==31, "same ID isolated across receivers");
        }
    }
    static void cancellationAndRejection() throws Exception {
        try(var receiver=new Receiver()) {
            var source=new CompletableFuture<Payload>(); var held=new Held();
            var result=PayloadOwnership.handleAsync(source,(value,error)->0,held,receiver::claim);
            check(result.cancel(false), "cancel dependent before completion");
            receiver.receive(4,40); source.complete(new Payload(4));
            check(held.tasks.isEmpty(), "native canceled dependent never schedules or claims");
            check(receiver.nativeMap.containsKey(4), "cancellation-before-completion leaves unclaimed buffer");
        }
        try(var receiver=new Receiver()) {
            receiver.receive(5,50); var payload=new Payload(5); var held=new Held();
            var result=requested(receiver,payload,held);
            check(!receiver.nativeMap.containsKey(5), "completed claim removes native cache ownership");
            check(result.cancel(false), "cancel after claim before execution");
            missing(receiver,payload); held.run();
            check(result.isCancelled(), "native dependent remains cancelled");
        }
        for(boolean alreadyCompleted:List.of(false,true)) {
            try(var receiver=new Receiver()) {
                receiver.receive(6,60); var payload=new Payload(6); var source=new CompletableFuture<Payload>();
                var rejection=new RejectedExecutionException("fixture rejection");
                if(alreadyCompleted) source.complete(payload);
                var result=PayloadOwnership.handleAsync(source,(value,error)->0,
                    command->{throw rejection;},receiver::claim);
                if(!alreadyCompleted) source.complete(payload);
                try { result.join(); throw new AssertionError("Expected rejection"); }
                catch(CompletionException expected) { check(expected.getCause()==rejection,"rejection identity preserved"); }
                missing(receiver,payload);
            }
        }
    }
    static void activeCancellationDoesNotRevoke() throws Exception {
        try(var receiver=new Receiver()) {
            receiver.receive(7,70); var payload=new Payload(7); var held=new Held();
            var entered=new CountDownLatch(1); var proceed=new CountDownLatch(1);
            var decoded=new AtomicLong(-1); var thrown=new AtomicReference<Throwable>();
            var result=PayloadOwnership.handleAsync(CompletableFuture.completedFuture(payload),(value,error)->{
                entered.countDown();
                try {
                    if(!proceed.await(5,TimeUnit.SECONDS)) throw new AssertionError("test latch deadline");
                    try(var dto=receiver.decodeDataSource(value)) { decoded.set(dto.pos); }
                } catch(Throwable failure) { thrown.set(failure); }
                return 0;
            },held,receiver::claim);
            var worker=new Thread(held::run); worker.start();
            check(entered.await(5,TimeUnit.SECONDS), "callback entered before cancellation");
            try { check(result.cancel(false),"native cancellation while callback active"); }
            finally { proceed.countDown(); }
            worker.join(5000);
            check(!worker.isAlive() && thrown.get()==null && decoded.get()==70,
                "cancellation cannot manufacture missing buffer in active callback");
        }
    }
    static void receiverCloseAndWrongOwner() throws Exception {
        try(var receiver=new Receiver();var other=new Receiver()) {
            receiver.receive(8,80); var payload=new Payload(8); receiver.claim(payload);
            missing(other,payload);
            check(receiver.decodeDataSource(payload).pos==80,"wrong receiver cannot consume owning lease");
            missing(receiver,payload);
        }
        try(var receiver=new Receiver()) {
            receiver.receive(9,90); var payload=new Payload(9); var held=new Held();
            var result=requested(receiver,payload,held); receiver.close(); held.run();
            try { result.join();throw new AssertionError("Expected native close failure"); }
            catch(CompletionException expected) { check(expected.getCause() instanceof NullPointerException,
                "closed receiver cannot be bypassed by queued lease"); }
        }
        try(var receiver=new Receiver()) {
            receiver.receive(10,100); receiver.close(); var payload=new Payload(10);
            receiver.claim(payload); missing(receiver,payload);
        }
    }
    static void callbackControls() throws Exception {
        for(boolean completed:List.of(false,true)) {
            var source=new CompletableFuture<Payload>(); var held=new Held(); var error=new IllegalArgumentException("native error");
            if(completed)source.completeExceptionally(error);
            var result=PayloadOwnership.handleAsync(source,(value,failure)->{
                check(value==null && failure==error,"original Throwable reaches native callback unchanged");return 12;
            },held,value->{throw new AssertionError("error must not claim");});
            if(!completed)source.completeExceptionally(error);
            held.run();check(result.join()==12,"error callback result unchanged");
        }
        var held=new Held();var result=PayloadOwnership.handleAsync(CompletableFuture.<Payload>completedFuture(null),
            (value,error)->{check(value==null && error==null,"null callback unchanged");return 13;},held,
            value->{throw new AssertionError("null must not claim");});
        held.run();check(result.join()==13,"null callback result unchanged");
        var cancelled=new CompletableFuture<Payload>();cancelled.cancel(false);
        var cancellation=PayloadOwnership.handleAsync(cancelled,(value,error)->{
            check(error instanceof CancellationException,"original source cancellation callback");return 14;
        },Runnable::run,value->{throw new AssertionError("cancellation must not claim");});
        check(cancellation.join()==14,"source cancellation handling unchanged");
        try(var receiver=new Receiver()) {
            var missing=new Payload(11);var executor=new Held();var failed=requested(receiver,missing,executor);
            executor.run();check(failed.isCompletedExceptionally(),"genuinely missing buffer still fails");
        }
    }
    static void cancellationDuringClaim() throws Exception {
        try(var receiver=new Receiver()) {
            receiver.receive(12,120);var payload=new Payload(12);var source=new CompletableFuture<Payload>();
            var held=new Held();var claimed=new CountDownLatch(1);var proceed=new CountDownLatch(1);
            var result=PayloadOwnership.handleAsync(source,(value,error)->0,held,value->{
                Runnable release=receiver.claim(value);claimed.countDown();
                try { if(!proceed.await(5,TimeUnit.SECONDS))throw new AssertionError("claim latch deadline"); }
                catch(InterruptedException interrupted) { throw new AssertionError(interrupted); }
                return release;
            });
            var completer=new Thread(()->source.complete(payload));completer.start();
            check(claimed.await(5,TimeUnit.SECONDS),"lease captured while claim has not returned");
            try { check(result.cancel(false),"cancel during claim before cleanup publication"); }
            finally { proceed.countDown(); }
            completer.join(5000);check(!completer.isAlive(),"claim completion bounded");
            check(held.tasks.size()==1,"native canceled task remains held for cleanup control");
            missing(receiver,payload); // Must release before the queued task can run.
            held.run();check(result.isCancelled(),"late cleanup cannot change cancellation");
        }
    }
    static void wrongOwnerCannotClaimCleanup() throws Exception {
        try(var owner=new Receiver();var other=new Receiver()) {
            owner.receive(14,140);var payload=new Payload(14);owner.claim(payload);
            other.claim(payload).run();
            try(var dto=owner.decodeDataSource(payload)) {
                check(dto.pos==140,"wrong-owner claim cleanup cannot discard the owning buffer");
            }
        }
    }
    static void replacementBufferSurvivesClaimedDecode() throws Exception {
        try(var receiver=new Receiver()) {
            receiver.receive(13,130);var claimed=new Payload(13);receiver.claim(claimed);
            receiver.receive(13,131);
            try(var dto=receiver.decodeDataSource(claimed)) { check(dto.pos==130,"claimed A decodes its original buffer"); }
            check(receiver.nativeMap.containsKey(13),"claimed decode must not remove replacement B");
            try(var dto=receiver.decodeDataSource(new Payload(13))) { check(dto.pos==131,"replacement B still decodes normally"); }
            check(!receiver.nativeMap.containsKey(13),"unclaimed native decode still removes its buffer");
        }
        try(var receiver=new Receiver()) {
            receiver.receiveChunk(new FullDataSplitMessage(15,Unpooled.buffer().writeByte(0),true));
            var malformed=new Payload(15);receiver.claim(malformed);receiver.receive(15,151);
            try { receiver.decodeDataSource(malformed);throw new AssertionError("Expected native DTO decode failure"); }
            catch(IndexOutOfBoundsException expected) { check(true,"native DTO failure takes exceptional finally path"); }
            check(receiver.nativeMap.containsKey(15),"exceptional finally cannot remove replacement buffer");
            try(var dto=receiver.decodeDataSource(new Payload(15))) { check(dto.pos==151,"replacement decodes after exceptional finally"); }
        }
    }
    static ClassNode bytecode(byte[] bytes) {
        var node=new ClassNode();new ClassReader(bytes).accept(node,0);return node;
    }
    static int calls(MethodNode method,String owner,String name) {
        int count=0;for(var instruction:method.instructions)
            if(instruction instanceof MethodInsnNode call && call.owner.equals(owner) && call.name.equals(name))count++;
        return count;
    }
    static void pinnedBytecode() throws Exception {
        String input=System.getProperty("dh.compat.originalJar");
        Path jar=input==null ? Path.of(FullDataPayloadReceiver.class.getProtectionDomain()
            .getCodeSource().getLocation().toURI()) : Path.of(input);
        check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(jar)))
            .equals("a537a71171d935540b56b7598d0de2c106f6f5026336c713d89a1d9ea0ea14e3"),"original native DH input pinned");
        try(var zip=new JarFile(jar.toFile())) {
            var receiver=bytecode(zip.getInputStream(zip.getJarEntry(
                "com/seibel/distanthorizons/core/multiplayer/fullData/FullDataPayloadReceiver.class")).readAllBytes());
            var decode=receiver.methods.stream().filter(m->m.name.equals("decodeDataSource")).findFirst().orElseThrow();
            check(decode.desc.equals("(Lcom/seibel/distanthorizons/core/multiplayer/fullData/FullDataPayload;)Lcom/seibel/distanthorizons/core/sql/dto/FullDataSourceV2DTO;"),"native decode descriptor pinned");
            check(calls(decode,"java/util/concurrent/ConcurrentMap","get")==1,"one exact native lookup seam");
            check(calls(decode,"com/seibel/distanthorizons/core/network/INetworkObject","decodeToInstance")==1,
                "fixture executes original DTO decoder");
            check(calls(decode,"java/util/concurrent/ConcurrentMap","remove")==2,"native finally removal unchanged");
            var ctor=receiver.methods.stream().filter(m->m.name.equals("<init>")).findFirst().orElseThrow();
            check(calls(ctor,"com/google/common/cache/CacheBuilder","expireAfterAccess")==1,"native expiry remains configured");
            boolean thirty=false;for(var instruction:ctor.instructions)
                if(instruction instanceof LdcInsnNode constant && Long.valueOf(30).equals(constant.cst))thirty=true;
            check(thirty,"native thirty-second fragment TTL unchanged");
            var queue=bytecode(zip.getInputStream(zip.getJarEntry(
                "com/seibel/distanthorizons/core/multiplayer/client/AbstractFullDataNetworkRequestQueue.class")).readAllBytes());
            var send=queue.methods.stream().filter(m->m.name.equals("sendNextRequest")).findFirst().orElseThrow();
            check(calls(send,"java/util/concurrent/CompletableFuture","handleAsync")==1,"one native async handoff seam");
        }
        int hooks=0;
        for(String mixin:List.of("FullDataPayloadMixin","FullDataPayloadReceiverMixin","FullDataRequestQueueMixin")) {
            String path="/mc/virgos/dhcompat/mixin/"+mixin+".class";
            var node=bytecode(PayloadOwnershipTest.class.getResourceAsStream(path).readAllBytes());
            for(var method:node.methods) {
                for(var instruction:method.instructions)if(instruction instanceof MethodInsnNode call)
                    check(!Set.of("retain","release","readerIndex","writerIndex").contains(call.name),
                        "mixin cannot mutate buffer refcounts or indices");
                if(method.visibleAnnotations==null)continue;
                for(var annotation:method.visibleAnnotations) {
                    if(!annotation.desc.endsWith("/Redirect;") && !annotation.desc.endsWith("/Inject;"))continue;
                    hooks++;
                    var values=new HashMap<String,Object>();
                    for(int j=0;j<annotation.values.size();j+=2)values.put((String)annotation.values.get(j),annotation.values.get(j+1));
                    var selectors=(List<?>)values.get("method");
                    String selector=(String)selectors.get(0);
                    check(selectors.size()==1 && Set.of("sendNextRequest","decodeDataSource","close").contains(selector),
                        "only the three pinned native methods are intercepted");
                    if(annotation.desc.endsWith("/Redirect;")) {
                        var at=(AnnotationNode)values.get("at");
                        String target=null;
                        for(int j=0;j<at.values.size();j+=2)if(at.values.get(j).equals("target"))target=(String)at.values.get(j+1);
                        check(Set.of("Ljava/util/concurrent/ConcurrentMap;get(Ljava/lang/Object;)Ljava/lang/Object;",
                            "Ljava/util/concurrent/ConcurrentMap;remove(Ljava/lang/Object;)Ljava/lang/Object;",
                            "Ljava/util/concurrent/CompletableFuture;handleAsync(Ljava/util/function/BiFunction;Ljava/util/concurrent/Executor;)Ljava/util/concurrent/CompletableFuture;")
                            .contains(target),"redirect descriptors match native bytecode seams");
                    }
                    int required=method.name.equals("virgos$removeOnlyUnclaimed") ? 2 : 1;
                    check(Integer.valueOf(required).equals(values.get("require")),"native hook fails closed on layout mismatch");
                    check(Boolean.FALSE.equals(values.get("remap")),"pinned DH hook is not remapped");
                }
            }
        }
        check(hooks==4,"all four strict hooks are present");
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=0) {
            if(args[0].equals("cancelClaim"))cancellationDuringClaim();
            else if(args[0].equals("replacement"))replacementBufferSurvivesClaimedDecode();
            else if(args[0].equals("wrongClaim"))wrongOwnerCannotClaimCleanup();
            else throw new IllegalArgumentException("Unknown focused regression");
            System.out.println("Regression checks: "+checks);System.exit(0);
        }
        pinnedBytecode(); cancellationDuringClaim(); wrongOwnerCannotClaimCleanup(); replacementBufferSurvivesClaimedDecode(); nativeExpiryControl(); completedBeforeDeferredDecode();
        immediateAndIndependentReceivers(); cancellationAndRejection();
        activeCancellationDoesNotRevoke(); receiverCloseAndWrongOwner(); callbackControls();
        System.out.println("Payload ownership checks: " + checks);
        System.exit(0);
    }
}
