"""Read-only closure checks for the installed release and distributable."""
from pathlib import Path
import hashlib,json,sqlite3,zipfile
root=Path(__file__).resolve().parents[1]
base=json.loads((root/'versions.lock.json').read_text('utf-8'))
asset=base['playitCompanion']
for p in (root/'mods'/asset['file'],root/asset['local_path']):
    assert hashlib.sha256(p.read_bytes()).hexdigest()==asset['hash']
assert not (root/'mods'/asset['replaces'][0]).exists()
mods=[]
for lock in ('mods.lock.json','custom-artifacts.lock.json'):
    mods+=json.loads((root/'pack'/lock).read_text('utf-8'))['artifacts']
server_mods=[m for m in mods if 'server' in m['sides'] and m.get('mode')!='optional']
for m in server_mods:
    data=(root/'mods'/m['filename']).read_bytes()
    assert hashlib.new(m['hash_algorithm'],data).hexdigest()==m['hash'],m['filename']
installer=root/'dist/Virgos-MC-0.2.0-rc1-instalador-v2.zip'
with zipfile.ZipFile(installer) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert any(n.endswith('EMPEZAR.bat') for n in names)
    assert not any('virgos_local_qa' in n or 'authme.db' in n or 'agent_key' in n for n in names)
conn=sqlite3.connect((root/'plugins/AuthMe/authme.db').as_uri()+'?mode=ro',uri=True)
qa_accounts=conn.execute("select count(*) from authme where lower(username) in ('virgosqa','virgosqa2')").fetchone()[0]
conn.close();assert qa_accounts==0
status=json.loads((root/'.runtime/active-run.json').read_text('utf-8'))
assert not status.get('finished')
report={'serverRunningPid':status['pid'],'serverModHashesChecked':len(server_mods),
        'companionPatchHashVerified':True,'qaAccountsRemaining':qa_accounts,
        'installer':installer.name,'installerSha256':hashlib.sha256(installer.read_bytes()).hexdigest(),
        'installerBytes':installer.stat().st_size,
        'publicVoice':json.loads((root/'.lab/reports/qa-v02-public-voice.json').read_text('utf-8')),
        'pregeneration':json.loads((root/'.lab/reports/pregen-v02.json').read_text('utf-8'))}
(root/'.lab/reports/v02-final.json').write_text(json.dumps(report,indent=2),'utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('publicVoice','pregeneration')}))
