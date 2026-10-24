"""Share manifest rules with the QA launcher without side effects."""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('qa_prepare', Path(__file__).with_name('prepare-qa-client.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
allowed = module.allowed
