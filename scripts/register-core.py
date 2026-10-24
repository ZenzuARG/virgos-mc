"""Pin our server integration after a successful Gradle build."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'dev/virgos-core/build/libs/virgos_core-0.2.0.jar'
with zipfile.ZipFile(source) as archive:
    assert b'modId="virgos_core"' in archive.read('META-INF/mods.toml').replace(b' ', b'')
    assert 'mc/virgos/VirgosCore.class' in archive.namelist()
    assert not any(name.startswith('mc/virgos/qa/') for name in archive.namelist())
record = {'schema': 1, 'artifacts': [{
    'filename': source.name, 'local_source': source.relative_to(ROOT).as_posix(),
    'hash_algorithm': 'sha256', 'hash': hashlib.sha256(source.read_bytes()).hexdigest(),
    'sides': ['server'], 'mode': 'required', 'name': 'Integración Virgos-MC',
}]}
(ROOT / 'pack/custom-artifacts.lock.json').write_text(json.dumps(record, indent=2, ensure_ascii=False)+'\n', 'utf-8')
print('Server integration pinned; QA is excluded from release artifacts.')
