import importlib.util,tempfile,unittest
from pathlib import Path
S=importlib.util.spec_from_file_location('proof',Path(__file__).parents[1]/'scripts/check-dh-fullpack-lab.py')
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class ProofPolicyTests(unittest.TestCase):
 def test_unapproved_root_refused_without_writes(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'public'
   with self.assertRaises(ValueError):M.Proof(path,'client2')
   self.assertFalse(path.exists())
 def test_row_identity_requires_both_data_and_mapping(self):
  proof=object.__new__(M.Proof)
  self.assertTrue(proof.same({'Data':1,'Mapping':2},{'Data':1,'Mapping':2}))
  self.assertFalse(proof.same({'Data':1,'Mapping':2},{'Data':1,'Mapping':3}))
  self.assertFalse(proof.same(None,{'Data':1,'Mapping':2}))
 def test_observer_has_no_network_repairs(self):
  source=(Path(__file__).parents[1]/'dev/dh-compat/qa/mc/virgos/qa/ClientProbe.java').read_text()
  for forbidden in ['negotiate_dh','traceLabConnection','channel.read()','sendConfigMessage']:self.assertNotIn(forbidden,source)
if __name__=='__main__':unittest.main()
