"""Private source snapshot for the published release, separate from world backups."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2';release=json.loads((R/'pack/current-release.json').read_text('utf-8'))
assert release['version']=='2.0.0' and release['published'];files=set()
def include(p):
    assert p.resolve().is_relative_to(R.resolve()) and p.is_file() and not p.is_symlink(),p
    files.add(p)
for folder in ['scripts','templates','pack','docs','dev/virgos-core/src','dev/virgos-core/gradle','dev/playit-udp-fix']:
    for p in (R/folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':include(p)
for p in (R/'dev/virgos-core').iterdir():
    if p.is_file():include(p)
for p in R.glob('*.bat'):include(p)
for name in ['README.md','versions.lock.json','dist/release.json','dist/Virgos-MC-2.0.0-instalar.zip','dist/Virgos-MC-2.0.0.mrpack','.cache/playit_companion-forge-0.1.2.jar','.cache/v02/voicechat-forge-1.20.1-2.6.24.jar','.cache/pack/downloads/CoreProtect-CE-24.1.jar','.lab/v2/CoreProtect-CE-24.1-virgos.1.jar']:
    include(R/name)
for name in ['virgos_core-2.0.0.jar','virgos_codex-2.0.0.jar']:include(R/'dev/virgos-core/build/libs'/name)
for module in ['asm','asm-tree']:
    matches=list((R/f'.cache/gradle/caches/modules-2/files-2.1/org.ow2.asm/{module}/9.9.1').rglob('*.jar'));assert len(matches)==1
    include(matches[0])
for name in ['acceptance.json','final.json','public-test.json','public-cleanup.json','clean-backup.json','production-audit.json','discord-delivery.json','installer-integration.json','runtime-checks.json','worldgen-tests.json','generated-content.json','user-client-upgrade.json','final-ui.json','profile-offline-test.json','promotion.json','balance-report.json','config-report.json']:
    include(V/name)
now=datetime.now(timezone.utc);dest=R/'backups'/f'virgos-v2-fuentes-{now:%Y%m%d-%H%M%S}.zip'
manifest={'version':release['version'],'created':now.isoformat(),'scope':'Private sources and published artifacts; separate world backup required','files':[]}
with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        data=p.read_bytes();name=p.relative_to(R).as_posix();z.writestr(name,data)
        manifest['files'].append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    z.writestr('sources-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(dest) as z:
    assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in manifest['files'])
out={'passed':True,'archive':str(dest),'verifiedFiles':len(files),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(V/'source-archive.json').write_text(json.dumps(out,indent=2),'utf-8');print(json.dumps(out))
