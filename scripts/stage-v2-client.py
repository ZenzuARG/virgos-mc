"""Fresh QA client profile sharing only existing official assets through the runner."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];CLIENT=ROOT/'client/qa-v2'
assert not CLIENT.exists(),'Inspect existing QA profile instead of replacing it.'
CLIENT.mkdir()
for rel in ['config','resourcepacks']:
    shutil.copytree(ROOT/'client/standard'/rel,CLIENT/rel)
for rel in ['options.txt','servers.dat']:
    if (ROOT/'client/standard'/rel).exists():shutil.copy2(ROOT/'client/standard'/rel,CLIENT/rel)
for file in (ROOT/'.lab/v2/client-overrides').rglob('*'):
    if file.is_file():
        target=CLIENT/file.relative_to(ROOT/'.lab/v2/client-overrides');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
mods=CLIENT/'mods';mods.mkdir()
for a in json.loads((ROOT/'.lab/v2/mods.lock.json').read_text())['artifacts']:
    if 'client' not in a['sides'] or a.get('mode') in {'tool','optional'}:continue
    source=ROOT/'.cache/pack/downloads'/a['filename']
    assert hashlib.new(a['hash_algorithm'],source.read_bytes()).hexdigest()==a['hash']
    shutil.copy2(source,mods/a['filename'])
shutil.copy2(ROOT/'dev/virgos-core/build/libs/virgos_local_qa-2.0.0.jar',mods/'virgos_local_qa-0.1.0.jar')
print(json.dumps({'profile':str(CLIENT),'jarsIncludingTestHelper':len(list(mods.glob('*.jar')))}))
