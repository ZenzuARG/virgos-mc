"""Stage the tested core in the stopped, localhost-only laboratory."""
from pathlib import Path
import ctypes,json,shutil,secrets,zipfile
ROOT=Path(__file__).resolve().parents[1]
lab=ROOT/'.lab/server'
state=json.loads((lab/'process.json').read_text('utf-8'))
if not state.get('finished'):
    handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,state['pid'])
    if handle:ctypes.windll.kernel32.CloseHandle(handle);raise SystemExit('Stop the lab first')
assert 'server-ip=127.0.0.1' in (lab/'server.properties').read_text('utf-8')
jar=ROOT/'dev/virgos-core/build/libs/virgos_core-0.3.0.jar'
assert jar.is_file()
for old in (lab/'mods').glob('virgos_core-*.jar'):
    if old.name==jar.name:continue
    backup=ROOT/'backups/auditoria-lab'/old.name;backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copy2(old,backup)
    old.unlink()
shutil.copy2(jar,lab/'mods'/jar.name)
for target in [ROOT/'pack/server-overrides/config/virgos/maintenance.json',lab/'config/virgos/maintenance.json']:
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'config/virgos/maintenance.json',target)
account=ROOT/'.cache/qa-account-3.json'
if not account.exists():account.write_text(json.dumps({'name':'VirgosQA3','password':secrets.token_urlsafe(18)}),'utf-8')
package=ROOT/'.lab/installer-v3/package'
if package.exists():raise SystemExit('Package folder exists; inspect before overwriting')
package.mkdir(parents=True)
with zipfile.ZipFile(ROOT/'dist/Virgos-MC-0.3.0-rc1-instalador-v3.zip') as z:z.extractall(package)
print('Lab core, maintenance template, isolated QA3 credentials and installer v3 staged.')
