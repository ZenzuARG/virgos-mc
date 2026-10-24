"""Regression: a file changed after enumeration must use its copied size/hash."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,time,zipfile
ROOT=Path(__file__).resolve().parents[1]
fixture=Path(tempfile.mkdtemp(prefix='backup-concurrency-',dir=ROOT/'.lab'))
(fixture/'server.properties').write_text('level-name=virgos_world\nserver-port=25579\n')
for name in ['virgos_world','virgos_world_nether','virgos_world_the_end','virgos_world_aether','virgos_world_twilight','virgos_world_pocket']:
    (fixture/name).mkdir();(fixture/name/'fixture.txt').write_text('Test data; not a playable world.')
padding=fixture/'aaa-padding.bin'
with padding.open('wb') as f:
    for _ in range(64):f.write(b'x'*1024*1024)
changed=fixture/'zz-changing.txt';changed.write_bytes(b'old')
output=ROOT/'backups/full';existing=set(output.glob('*prueba-concurrencia.zip.partial'))
process=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/respaldo.ps1'),'-ServerPath',str(fixture),'-Label','prueba-concurrencia'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
deadline=time.monotonic()+30
while time.monotonic()<deadline and process.poll() is None:
    if set(output.glob('*prueba-concurrencia.zip.partial'))-existing:break
    time.sleep(.002)
else:raise RuntimeError('Did not observe post-enumeration snapshot start')
payload=b'changed after file enumeration\n'*8192
changed.write_bytes(payload)
stdout,stderr=process.communicate(timeout=60)
if process.returncode:raise RuntimeError(stderr)
archive=Path(stdout.splitlines()[0])
with zipfile.ZipFile(archive) as z:
    manifest=json.loads(z.read('backup-manifest.json'));item=next(f for f in manifest['files'] if f['path']=='zz-changing.txt')
    assert z.read('zz-changing.txt')==payload
    assert item['bytes']==len(payload) and item['sha256']==hashlib.sha256(payload).hexdigest()
    assert all(len(z.read(f['path']))==f['bytes'] and hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
assert archive.resolve().parent==output.resolve()
target=fixture/'verified-test.zip';assert not target.exists();archive.rename(target)
assert padding.resolve().parent==fixture.resolve();padding.unlink()
report={'passed':True,'scope':'Actual backup script, synthetic isolated fixture. Source changes after directory enumeration and before its copy; every archive entry matches its manifest.',
        'changedFileBytes':len(payload),'files':len(manifest['files']),'fixture':str(fixture)}
(ROOT/'.lab/reports/backup-concurrency-v1.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
print(json.dumps(report))
