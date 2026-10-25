import org.objectweb.asm.*;
import java.nio.file.*;
import java.util.zip.*;
import java.io.*;
public class PatchDh {
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[0]).toRealPath(),input=Path.of(args[1]).toRealPath(),output=Path.of(args[2]).toAbsolutePath().normalize();
  if(!output.startsWith(root)||input.equals(output))throw new IllegalArgumentException("Only separate laboratory files allowed");
  int[] edits={0};
  try(var zip=new ZipFile(input.toFile());var out=new ZipOutputStream(Files.newOutputStream(output))){
   var entries=zip.entries();
   while(entries.hasMoreElements()){
    var entry=entries.nextElement();byte[] bytes;try(var in=zip.getInputStream(entry)){bytes=in.readAllBytes();}
    if(entry.getName().equals("com/seibel/distanthorizons/core/dataObjects/fullData/sources/FullDataSourceV2.class")){
     var reader=new ClassReader(bytes);var writer=new ClassWriter(reader,ClassWriter.COMPUTE_MAXS);
     reader.accept(new ClassVisitor(Opcodes.ASM9,writer){
      @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
       var target=super.visitMethod(access,name,descriptor,signature,exceptions);
       if(!name.equals("updateFromSameDetailLevel")||!descriptor.equals("(Lcom/seibel/distanthorizons/core/dataObjects/fullData/sources/FullDataSourceV2;[I)Z"))return target;
       return new MethodVisitor(Opcodes.ASM9,target){
        @Override public void visitInsn(int opcode){
         if(opcode==Opcodes.LCMP){
          super.visitInsn(Opcodes.POP2);super.visitInsn(Opcodes.POP2);
          super.visitVarInsn(Opcodes.ALOAD,0);super.visitVarInsn(Opcodes.ALOAD,2);
          super.visitVarInsn(Opcodes.LLOAD,13);super.visitVarInsn(Opcodes.LLOAD,15);
          super.visitMethodInsn(Opcodes.INVOKESTATIC,"com/seibel/distanthorizons/core/lab/SemanticPointComparison","compare","(Lcom/seibel/distanthorizons/core/dataObjects/fullData/sources/FullDataSourceV2;[IJJ)I",false);edits[0]++;
         }else super.visitInsn(opcode);
        }
       };
      }
     },0);bytes=writer.toByteArray();
    }
    var copy=new ZipEntry(entry.getName());copy.setTime(entry.getTime());out.putNextEntry(copy);out.write(bytes);out.closeEntry();
   }
  }
  if(edits[0]!=1)throw new IllegalStateException("Expected exactly one comparison edit, got "+edits[0]);
  System.out.println("PATCHED_COMPARISONS="+edits[0]);
 }
}
