"""Create a second isolated local test profile using the same game libraries.

Mods are copied, not shared mutable config. No account credentials are copied.
"""
from pathlib import Path
import json
import ctypes
import shutil
import argparse

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--instance',choices=['secondary','tertiary'],default='secondary');args=p.parse_args()
target=ROOT/('client/qa-'+args.instance)
record=target/'virgos-qa/process.json'
if record.exists():
    p=json.loads(record.read_text('utf-8'))
    if p.get('pid') and not p.get('finished'):
        handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,p['pid'])
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise SystemExit('Close the secondary QA client before preparing it.')
(target/'mods').mkdir(parents=True,exist_ok=True)
lock=json.loads((ROOT/'pack/mods.lock.json').read_text('utf-8'))
expected=set()
for item in lock['artifacts']:
    if 'client' not in item['sides'] or item['mode'] in ['tool','optional']:continue
    expected.add(item['filename'])
    shutil.copy2(ROOT/'.cache/pack/downloads'/item['filename'],target/'mods'/item['filename'])
qa=ROOT/'dev/virgos-core/build/libs/virgos_local_qa-0.1.0.jar'
shutil.copy2(qa,target/'mods'/qa.name);expected.add(qa.name)
if {p.name for p in (target/'mods').glob('*.jar')}-expected:raise SystemExit('Unexpected secondary QA mods; inspect before launch.')
for source in (ROOT/'pack/client-overrides').rglob('*'):
    if source.is_file():
        output=target/source.relative_to(ROOT/'pack/client-overrides')
        output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,output)
shutil.copy2(ROOT/'pack/client-overrides/config/defaultoptions/options.txt',target/'options.txt')
print('Prepared isolated secondary QA profile with',len(expected),'mods. Shared libraries/assets remain in the standard profile.')
