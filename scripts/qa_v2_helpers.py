"""Local candidate helpers; never packaged in the client installer."""
from pathlib import Path
import importlib.util,json,time,shutil
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/qa-expeditions.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.LAB=ROOT/'.lab/v2/server';q.PROFILES[2]='qa-v2';QA=ROOT/'client/qa-v2/virgos-qa'
def action(kind,**kwargs):return q.action(2,{'action':kind,**kwargs})
def state():return q.state(2)
def server(text):q.server(text)
def widgets():action('inspect_screen');return json.loads((QA/'screen.json').read_text('utf-8'))
def click(text):
    matches=[w for w in widgets() if w['text']==text and w['visible'] and w['active']]
    assert len(matches)==1,(text,matches)
    w=matches[0];action('click',x=w['x']+w['width']/2,y=w['y']+w['height']/2);time.sleep(.7)
def photo(name):
    line=action('screenshot');source=ROOT/f'client/qa-v2/screenshots/virgos-qa-{line}.png'
    def complete():
        try:return source.read_bytes().endswith(b'IEND\xaeB`\x82')
        except OSError:return False
    q.wait(complete,60);shutil.copy2(source,ROOT/'.lab/v2'/f'{name}.png')
