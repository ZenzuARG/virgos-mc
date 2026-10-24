import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

/** Narrow, reproducible adapter patch; upstream JAR stays intact in cache. */
public class PatchCoreProtect {
    public static void main(String[] args) throws Exception {
        int changed=0;
        try (ZipFile input=new ZipFile(args[0]); ZipOutputStream output=new ZipOutputStream(Files.newOutputStream(Path.of(args[1])))) {
            for (ZipEntry e:Collections.list(input.entries())) {
                byte[] bytes=input.getInputStream(e).readAllBytes();
                if(e.getName().equals("net/coreprotect/utility/MaterialUtils.class")) {
                    ClassNode c=new ClassNode();new ClassReader(bytes).accept(c,0);
                    for(MethodNode m:c.methods) {
                        if(m.name.equals("getPaintingArtName") && m.desc.equals("(Lorg/bukkit/entity/Painting;)Ljava/lang/String;")) {
                            if((m.access&Opcodes.ACC_STATIC)==0)throw new IllegalStateException("Expected static bridge");
                            m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;
                            m.instructions.add(new VarInsnNode(Opcodes.ALOAD,0));
                            m.instructions.add(new MethodInsnNode(Opcodes.INVOKESTATIC,"mc/virgos/KettingPaintingCompat","key","(Ljava/lang/Object;)Ljava/lang/String;",false));
                            m.instructions.add(new InsnNode(Opcodes.ARETURN));m.maxStack=1;m.maxLocals=1;changed++;
                        }
                    }
                    ClassWriter w=new ClassWriter(0);c.accept(w);bytes=w.toByteArray();
                }
                ZipEntry out=new ZipEntry(e.getName());out.setTime(0);output.putNextEntry(out);output.write(bytes);output.closeEntry();
            }
        }
        if(changed!=1)throw new IllegalStateException("Expected exactly one bridge, found "+changed);
        System.out.println("Patched painting registry lookup only.");
    }
}
