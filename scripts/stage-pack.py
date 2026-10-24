"""Materialize a locked pack in the isolated lab and client staging folders."""
from pathlib import Path
import hashlib
import json
import shutil
import argparse
import ctypes

parser=argparse.ArgumentParser()
parser.add_argument('--check',action='store_true',help='Verify sources without changing staging')
parser.add_argument('--qa',action='store_true',help='Include the local-only QA driver in client staging')
args=parser.parse_args()

ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'pack/mods.lock.json').read_text(encoding='utf-8'))
if lock['missing_declared_mod_ids']:
    raise SystemExit('Resolve missing mandatory dependencies before staging')
targets={
    'server':ROOT/'.lab/server/mods',
    'client':ROOT/'client/standard/mods',
    'optional':ROOT/'client/optional-mods',
}
counts={key:0 for key in targets}
for target in targets.values():
    target.resolve().relative_to(ROOT.resolve())
expected={key:set() for key in targets}
artifacts=list(lock['artifacts'])
custom=ROOT/'pack/custom-artifacts.lock.json'
if not custom.exists():raise SystemExit('Build and register the Virgos integration before staging.')
artifacts+=json.loads(custom.read_text('utf-8'))['artifacts']
prepared=[]
for item in artifacts:
    if Path(item['filename']).name!=item['filename']:raise ValueError('Unsafe artifact filename')
    source=ROOT/item['local_source'] if 'local_source' in item else ROOT/'.cache/pack/downloads'/item['filename']
    source.resolve().relative_to(ROOT.resolve())
    if hashlib.new(item['hash_algorithm'],source.read_bytes()).hexdigest()!=item['hash']:
        raise ValueError('Hash mismatch: '+item['filename'])
    for side in item['sides']:
        if item['mode']=='tool' and side=='client':continue
        key='optional' if item['mode']=='optional' else side
        if key not in targets:continue
        destination=targets[key]/item['filename']
        destination.resolve().relative_to(targets[key].resolve())
        prepared.append((source,destination))
        expected[key].add(item['filename'])
        counts[key]+=1
if args.qa:
    source=ROOT/'dev/virgos-core/build/libs/virgos_local_qa-0.1.0.jar'
    if not source.is_file():raise FileNotFoundError(source)
    prepared.append((source,targets['client']/source.name))
    expected['client'].add(source.name)
    counts['client']+=1
if args.check:
    print(json.dumps({'verified':len(artifacts),'staging':counts,'mutated':False}))
    raise SystemExit(0)
for record in [ROOT/'.lab/server/process.json', *ROOT.glob('client/*/virgos-qa/process.json')]:
    if not record.exists():continue
    pid=json.loads(record.read_text('utf-8')).get('pid')
    if pid:
        handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise SystemExit('Close the lab and QA client before staging mods.')
# All source hashes and process guards pass before any copy or quarantine.
for target in targets.values():target.mkdir(parents=True,exist_ok=True)
for source,destination in prepared:shutil.copy2(source,destination)
for key,target in targets.items():
    for existing in target.glob('*.jar'):
        if existing.name not in expected[key]:
            disabled=target/'.disabled'
            disabled.mkdir(exist_ok=True)
            if (disabled/existing.name).exists():
                raise ValueError('Quarantine already exists: '+existing.name)
            existing.rename(disabled/existing.name)
(ROOT/'pack/staged-lab.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
print(json.dumps(counts))
