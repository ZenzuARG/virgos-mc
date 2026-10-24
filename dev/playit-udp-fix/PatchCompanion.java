import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

/** Local, one-instruction repair of the IPv4 UDP flow parser in Companion 0.1.2. */
public final class PatchCompanion {
    private static final String SOURCE_SHA512 = "5b6f0bf5dae4a164e4e02c543cb8f9b4e020d86960b03057b30056424a9436d0d0a9e914ed577c6150b430389948a0d80d42dad6e4ece7a4696471d04fff4b1e";
    private static final String TARGET = "gg/playit/PlayitAgent$ControlChannelHandler$DatagramChannelHandler.class";

    public static void main(String[] args) throws Exception {
        Path input = Path.of(args[0]), output = Path.of(args[1]);
        String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-512").digest(Files.readAllBytes(input)));
        if (!hash.equals(SOURCE_SHA512)) throw new IllegalArgumentException("Unexpected upstream JAR; refusing to patch");
        int replacements = 0;
        Files.createDirectories(output.toAbsolutePath().getParent());
        try (ZipFile source = new ZipFile(input.toFile()); ZipOutputStream dest = new ZipOutputStream(Files.newOutputStream(output))) {
            for (var entries = source.entries(); entries.hasMoreElements();) {
                ZipEntry entry = entries.nextElement();
                byte[] bytes = source.getInputStream(entry).readAllBytes();
                if (entry.getName().equals(TARGET)) {
                    ClassReader reader = new ClassReader(bytes);
                    ClassNode node = new ClassNode(); reader.accept(node, 0);
                    for (MethodNode method : node.methods) {
                        if (!method.name.equals("channelRead0") || !method.desc.endsWith("Lio/netty/channel/socket/DatagramPacket;)V")) continue;
                        List<AbstractInsnNode> ops = new ArrayList<>();
                        for (AbstractInsnNode op : method.instructions) if (op.getOpcode() >= 0) ops.add(op);
                        for (int i = 0; i + 9 < ops.size(); i++) {
                            if (!(ops.get(i) instanceof VarInsnNode outer) || outer.getOpcode() != Opcodes.ALOAD || outer.var != 4) continue;
                            if (!(ops.get(i+1) instanceof VarInsnNode same) || same.getOpcode() != Opcodes.ALOAD || same.var != 4) continue;
                            if (!call(ops.get(i+2), "readableBytes", "()I") || ops.get(i+3).getOpcode() != Opcodes.ICONST_2 || ops.get(i+4).getOpcode() != Opcodes.ISUB) continue;
                            if (!call(ops.get(i+5), "readBytes", "(I)Lio/netty/buffer/ByteBuf;")) continue;
                            if (!(ops.get(i+6) instanceof VarInsnNode store) || store.getOpcode() != Opcodes.ASTORE || store.var != 8) continue;
                            if (!(ops.get(i+7) instanceof VarInsnNode load) || load.getOpcode() != Opcodes.ALOAD || load.var != 8) continue;
                            if (!call(ops.get(i+8), "readUnsignedShort", "()I")) continue;
                            // packetId lives in the two remaining bytes of the outer buffer.
                            // Reading it from the payload instead corrupts all subsequent routing fields.
                            load.var = outer.var; replacements++;
                        }
                    }
                    if (replacements != 1) throw new IllegalStateException("Expected exactly one repair, got " + replacements);
                    ClassWriter writer = new ClassWriter(reader, 0); node.accept(writer); bytes = writer.toByteArray();
                }
                ZipEntry copy = new ZipEntry(entry.getName()); copy.setTime(0);
                dest.putNextEntry(copy); dest.write(bytes); dest.closeEntry();
            }
            if (replacements != 1) throw new IllegalStateException("Target class missing");
            ZipEntry note = new ZipEntry("META-INF/virgos-udp-fix.txt"); note.setTime(0); dest.putNextEntry(note);
            dest.write(("Virgos local patch 1 for Playit Companion Forge 0.1.2.\n" +
                "IPv4 UDP flow packetId: readUnsignedShort() from allExceptFooter, not payload slice.\n" +
                "Upstream: https://github.com/playit-cloud/playit-companion\n" +
                "Reproducer/build: dev/playit-udp-fix/PatchCompanion.java\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            dest.closeEntry();
        }
        System.out.println("Patched exactly one ByteBuf receiver; all other JAR entries preserved: " + output);
    }
    private static boolean call(AbstractInsnNode node, String name, String descriptor) {
        return node instanceof MethodInsnNode m && m.getOpcode() == Opcodes.INVOKEVIRTUAL && m.owner.equals("io/netty/buffer/ByteBuf") && m.name.equals(name) && m.desc.equals(descriptor);
    }
}
