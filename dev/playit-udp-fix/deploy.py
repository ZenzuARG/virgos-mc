"""Pin and deploy the verified local Companion fix, only while the server is stopped."""
from pathlib import Path
import hashlib, json, shutil, zipfile

root = Path(__file__).resolve().parents[2]
state = json.loads((root/'.runtime/active-run.json').read_text('utf-8-sig'))
if not state.get('finished'):
    raise SystemExit('Stop the server normally before deploying')
original = root/'.cache/playit_companion-forge-0.1.2.jar'
patched = root/'pack/local/playit_companion-forge-0.1.2-virgos.1.jar'
target = 'gg/playit/PlayitAgent$ControlChannelHandler$DatagramChannelHandler.class'
with zipfile.ZipFile(original) as before, zipfile.ZipFile(patched) as after:
    changed = [n for n in before.namelist() if before.read(n) != after.read(n)]
    assert changed == [target], changed
    assert set(after.namelist()) - set(before.namelist()) == {'META-INF/virgos-udp-fix.txt'}
    assert after.testzip() is None
lock_path = root/'versions.lock.json'
lock = json.loads(lock_path.read_text('utf-8-sig'))
asset = lock['playitCompanion']
if not asset.get('upstream'):
    asset['upstream'] = {k:asset[k] for k in ('version','url','file','algorithm','hash')}
    asset.pop('url')
asset.update(version='0.1.2-forge+virgos.1', file=patched.name,
             local_path=patched.relative_to(root).as_posix(), algorithm='SHA256',
             hash=hashlib.sha256(patched.read_bytes()).hexdigest(),
             replaces=[original.name])
backup = root/'backups/upgrade-v02'
backup.mkdir(exist_ok=True)
old = root/'mods'/original.name
if old.exists():
    shutil.copy2(old, backup/original.name)
    old.unlink()
shutil.copy2(patched, root/'mods'/patched.name)
lock_path.write_text(json.dumps(lock,indent=2)+'\n','utf-8')
upgrade_path=root/'pack/upgrade-v02.json'
upgrade=json.loads(upgrade_path.read_text('utf-8'))
upgrade['playitCompanionPatch']={k:asset[k] for k in ('version','file','algorithm','hash','local_path')}
upgrade_path.write_text(json.dumps(upgrade,indent=2)+'\n','utf-8')
print(json.dumps({'changedClasses':changed,'patch':asset['file'],'sha256':asset['hash']}))
