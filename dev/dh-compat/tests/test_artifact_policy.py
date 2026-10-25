import importlib.util
import tempfile
import unittest
import os
import zipfile
import shutil
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('artifact_builder',Path(__file__).parents[1]/'build-artifacts.py')
BUILDER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BUILDER)
class ArtifactPolicyTest(unittest.TestCase):
 def test_build_uses_host_classpath_and_verifies_patch_footprint(self):
  root=Path(tempfile.mkdtemp(prefix='virgos-patch-portable-'));print('SCRATCH='+str(root))
  original=root/'original.jar';addon=root/BUILDER.ADDON_NAME;asm=root/'asm.jar';output=root/'output';home=root/'jdk'
  with zipfile.ZipFile(original,'w') as z:z.writestr(BUILDER.TARGET,b'original');z.writestr('LICENSE.txt',b'notice')
  addon.write_bytes(b'addon');asm.write_bytes(b'asm')
  java,javac=BUILDER.jdk_tools(home)
  java.parent.mkdir(parents=True);java.touch();javac.touch();calls=[]
  def run(command,**kwargs):
   calls.append(command)
   if command[0]==str(javac):
    cache=Path(command[command.index('-d')+1]);helper=cache/BUILDER.HELPER;helper.parent.mkdir(parents=True);helper.write_bytes(b'compiled helper')
   else:
    with zipfile.ZipFile(Path(command[-1]),'w') as z:z.writestr(BUILDER.TARGET,b'patched');z.writestr('LICENSE.txt',b'notice')
  with patch.object(BUILDER,'ORIGINAL',BUILDER.sha(original)),patch.object(BUILDER.subprocess,'run',side_effect=run):
   BUILDER.build(original,addon,asm,output,home)
  self.assertEqual(calls[0][calls[0].index('-cp')+1],os.pathsep.join([str(asm.resolve()),str(original.resolve())]))
  self.assertIn('--release',calls[0]);self.assertIn('17',calls[0])
  with zipfile.ZipFile(output/BUILDER.DH_NAME) as z:
   self.assertEqual(z.read('LICENSE.txt'),b'notice');self.assertEqual(set(z.namelist()),{BUILDER.TARGET,'LICENSE.txt',BUILDER.HELPER})
 def test_portable_jdk_tool_names(self):
  root=Path(tempfile.gettempdir())/'fixture-jdk'
  self.assertEqual([p.name for p in BUILDER.jdk_tools(root,windows=False)],['java','javac'])
  self.assertEqual([p.name for p in BUILDER.jdk_tools(root,windows=True)],['java.exe','javac.exe'])
 def test_unknown_input_rejected_without_output(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name); original=root/'dh.jar';addon=root/BUILDER.ADDON_NAME;asm=root/'asm.jar';out=root/'out'
   for p in [original,addon,asm]:p.write_bytes(b'fixture')
   with self.assertRaisesRegex(ValueError,'Unrecognized'):BUILDER.validate(original,addon,asm,out)
   self.assertFalse(out.exists());self.assertEqual(original.read_bytes(),b'fixture')
 def test_protected_output_rejected(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);original=root/'dh.jar';addon=root/BUILDER.ADDON_NAME;asm=root/'asm.jar'
   for p in [original,addon,asm]:p.write_bytes(b'fixture')
   protected=root/'public';protected.mkdir(); sentinel=protected/'world';sentinel.write_bytes(b'unchanged')
   with patch.object(BUILDER,'ORIGINAL',BUILDER.sha(original)),patch.object(BUILDER,'FORBIDDEN',[protected]):
    for out in [protected,protected/'artifacts',root]:
     with self.assertRaises(ValueError):BUILDER.validate(original,addon,asm,out)
   self.assertEqual(sentinel.read_bytes(),b'unchanged')
 def test_disjoint_output_accepted(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);original=root/'dh.jar';addon=root/BUILDER.ADDON_NAME;asm=root/'asm.jar'
   for p in [original,addon,asm]:p.write_bytes(b'fixture')
   with patch.object(BUILDER,'ORIGINAL',BUILDER.sha(original)),patch.object(BUILDER,'FORBIDDEN',[]):
    self.assertEqual(BUILDER.validate(original,addon,asm,root/'out')[-1],root/'out')
if __name__=='__main__':unittest.main()
