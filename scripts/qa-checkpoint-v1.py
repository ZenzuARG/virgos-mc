"""Exercise the actual empty-server shutdown/verified-backup/restart controller."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text('utf-8-sig'))
def wait(predicate,seconds=480):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            if read('.runtime/active-run.json').get('backupError'):raise RuntimeError('Wrapper refused restart after backup verification failed')
            value=predicate()
        except (OSError,json.JSONDecodeError):value=False
        if value:return value
        time.sleep(.5)
    raise TimeoutError('Checkpoint condition did not complete')
old=read('.runtime/active-run.json');previous=read('.runtime/last-backup.json')
assert not old.get('finished') and old.get('checkpointSupport')
assert read('.lab/reports/public-v1.json')['passed']
shutil.copy2(ROOT/'.lab/reports/public-v1.json',ROOT/'.lab/reports/public-v1-before-restart.json')
out=ROOT/'.lab/reports/checkpoint-v1.json'
report={'started':datetime.now(timezone.utc).isoformat(),'originalPid':old['pid'],'cases':[]}
def record(name,passed,**details):
    report['cases'].append({'case':name,'passed':bool(passed),**details})
    out.write_text(json.dumps(report,indent=2)+'\n','utf-8')
    print(name,'PASS' if passed else 'FAIL',flush=True)
    if not passed:raise RuntimeError(name)
wait(lambda:'Virgos: AuthMe bridge ready' in (ROOT/'.runtime/public-console.log').read_text('utf-8',errors='replace'))
with (ROOT/'.runtime/public-commands.txt').open('a',encoding='utf-8') as f:f.write('virgos checkpoint\n')
stopped=wait(lambda:read('.runtime/active-run.json') if read('.runtime/active-run.json').get('finished') else None)
record('clean-shutdown',stopped.get('exitCode')==0)
new=wait(lambda:read('.runtime/active-run.json') if not read('.runtime/active-run.json').get('finished') and read('.runtime/active-run.json')['pid']!=old['pid'] else None)
record('wrapper-started-new-process',new['pid']!=old['pid'],newPid=new['pid'])
backup=read('.runtime/last-backup.json');archive=Path(backup['archive'])
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('backup-manifest.json'))
    verified=all(len(z.read(f['path']))==f['bytes'] and hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
    core=json.loads(z.read('pack/custom-artifacts.lock.json'))['artifacts'][0]['filename']
record('new-complete-verified-v1-backup',backup['archive']!=previous['archive'] and verified and len(manifest['worldFolders'])==6 and core=='virgos_core-1.0.0.jar',
       archive=str(archive),files=len(manifest['files']),worlds=manifest['worldFolders'])
wait(lambda:'Virgos: AuthMe bridge ready' in (ROOT/'.runtime/public-console.log').read_text('utf-8',errors='replace'))
record('restarted-core-ready',not read('.runtime/active-run.json').get('finished'))
report.update(passed=True,finished=datetime.now(timezone.utc).isoformat())
out.write_text(json.dumps(report,indent=2)+'\n','utf-8')
print('Empty-server checkpoint completed successfully.',flush=True)
