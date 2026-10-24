"""Remove only QA player scores, preserving raw NBT types and all mod objectives."""
from pathlib import Path
import argparse,gzip,io,json,runpy,shutil,struct
args=argparse.ArgumentParser();args.add_argument('--public',action='store_true');options=args.parse_args()
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2';L=R if options.public else V/'server'
state=json.loads((R/'.runtime/active-run.json' if options.public else L/'process.json').read_text())
assert state['exitCode']==0 and state.get('finished') and not state.get('backupInProgress')
p=L/'virgos_world/data/scoreboard.dat';read=runpy.run_path(str(R/'scripts/inspect-nbt.py'))['read_nbt'];original=read(p)
raw=gzip.decompress(p.read_bytes());needle=b'\x09\x00\x0cPlayerScores\x0a';assert raw.count(needle)==1
start=raw.index(needle)+len(needle);s=io.BytesIO(raw);s.seek(start)
def num(fmt):return struct.unpack(fmt,s.read(struct.calcsize(fmt)))[0]
def skip(kind):
    if kind in range(1,7):s.seek({1:1,2:2,3:4,4:8,5:4,6:8}[kind],1)
    elif kind==8:s.seek(num('>H'),1)
    elif kind in [7,11,12]:s.seek(num('>i')*{7:1,11:4,12:8}[kind],1)
    elif kind==9:
        child=num('>B');count=num('>i')
        for _ in range(count):skip(child)
    elif kind==10:
        while (child:=num('>B')):skip(8);skip(child)
    else:raise ValueError(kind)
count=num('>i');scores=original['']['data']['PlayerScores'];assert count==len(scores)
qa={'13e2e728-2a7a-36a6-84ee-5c289cf4cc02','32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e','3b6e246d-95b1-37ba-83c4-359423490806'}
kept=[];expected=[];removed=[]
for score in scores:
    offset=s.tell();skip(10)
    if score['Name'].lower().startswith('virgosqa') or score['Name'] in qa:removed.append(score)
    else:kept.append(raw[offset:s.tell()]);expected.append(score)
if removed:
    backup=V/('public-scoreboard-before-cleanup.dat' if options.public else 'scoreboard-before-cleanup.dat');assert not backup.exists();shutil.copy2(p,backup)
    result=raw[:start]+struct.pack('>i',len(kept))+b''.join(kept)+raw[s.tell():]
    p.write_bytes(gzip.compress(result,mtime=0))
    original['']['data']['PlayerScores']=expected;assert read(p)==original
(V/('public-scoreboard-cleanup.json' if options.public else 'scoreboard-cleanup.json')).write_text(json.dumps({'removedQA':removed,'preservedScores':len(expected)},indent=2),'utf-8')
print('Removed',len(removed),'QA scores; preserved',len(expected),'mod scores and all objectives')
