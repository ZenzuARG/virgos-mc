"""Exercise a gifted Ars book's glyph limits through real item use."""
from pathlib import Path
import importlib.util
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_magic',ROOT/'scripts/qa-magic.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
qa.REPORT=ROOT/'.lab/reports/qa-ars-progression.json'

def book(method,effect):
    nbt='{"ars_nouveau:caster":{current_slot:0,spell_count:1,spells:{spell0:{name:"Prueba local",recipe:{size:2,part0:"ars_nouveau:glyph_'+method+'",part1:"ars_nouveau:glyph_'+effect+'"}}}}}'
    qa.server('item replace entity VirgosQA2 hotbar.4 with ars_nouveau:archmage_spell_book'+nbt)
    time.sleep(1)

def main():
    if qa.state().get('name')!='VirgosQA2':raise RuntimeError('Requires QA2')
    qa.action({'action':'close'})
    qa.server('tp VirgosQA2 962.5 83 738.5 180 -35')
    qa.server('gamemode survival VirgosQA2')
    for id in ['explorador','especialista','forja']:
        qa.server('advancement revoke VirgosQA2 only virgos:'+id)
    time.sleep(2)
    qa.action({'action':'key','name':'key.hotbar.5'})
    book('projectile','harm');qa.attempt('ars-basic','arsAllowed',1)
    book('self','heal');qa.attempt('ars-gifted-locked','arsBlocked',1)
    qa.server('advancement grant VirgosQA2 only virgos:explorador');time.sleep(1)
    qa.attempt('ars-recognized','arsAllowed',1)
    time.sleep(15)
    book('self','glide');qa.attempt('ars-tier-three-locked','arsBlocked',1)
    for id in ['especialista','forja']:qa.server('advancement grant VirgosQA2 only virgos:'+id)
    time.sleep(1);qa.attempt('ars-tier-three-recognized','arsAllowed',1)
    for id in ['explorador','especialista','forja']:
        qa.server('advancement revoke VirgosQA2 only virgos:'+id)
    qa.server('effect clear VirgosQA2')
    qa.server('item replace entity VirgosQA2 hotbar.4 with minecraft:air')
    qa.server('tp VirgosQA2 672.5 115 752.5 180 0')
    print('PASS: Ars spells require personal achievements; QA grants/items removed.')

if __name__=='__main__':main()
