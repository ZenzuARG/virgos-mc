"""Backport four malformed upstream data resources for the locked 1.20.1 pack."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = [ROOT / 'pack/server-overrides/kubejs/data', ROOT / '.lab/server/kubejs/data']


def read(jar, resource):
    with zipfile.ZipFile(ROOT / '.cache/pack/downloads' / jar) as archive:
        return json.loads(archive.read('data/' + resource))


def save(resource, data):
    for base in OUTPUTS:
        file = base / resource
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')


def main():
    tomes = 'irons_spellbooks/loot_tables/chests/citadel/citadel_tomes.json'
    data = read('irons_spellbooks-1.20.1-3.16.3.jar', tomes)
    changed = 0
    for pool in data['pools']:
        for entry in pool['entries']:
            for function in entry.get('functions', []):
                if function['function'] == 'minecraft:set_written_book_pages':
                    pages = [json.dumps(page, ensure_ascii=False) for page in function['pages']]
                    function.clear()
                    function.update({'function': 'minecraft:set_nbt', 'tag': json.dumps({
                        'pages': pages, 'title': 'Crónicas de la Ciudadela', 'author': 'Archivo de la Ciudadela'
                    }, ensure_ascii=False)})
                    changed += 1
    assert changed > 0, 'Expected upstream invalid written-book function changed; review instead of patching blindly.'
    save(tomes, data)
    crypt = 'irons_spellbooks/loot_tables/chests/catacombs/crypt_loot.json'
    data = read('irons_spellbooks-1.20.1-3.16.3.jar', crypt)
    fixed = 0
    for pool in data['pools']:
        for entry in pool['entries']:
            if entry.get('type') == 'minecraft:loot_table' and 'value' in entry:
                entry['name'] = entry.pop('value')
                fixed += 1
    assert fixed == 1
    save(crypt, data)
    batter = 'rusticdelight/recipes/cooking/batter.json'
    data = read('Delightful-1.20.1-3.8.1.jar', batter)
    assert any(c.get('type') == 'forge:false' for c in data['recipes'][0]['conditions'])
    # The upstream recipe is intentionally disabled, but its earlier item_exists
    # condition mistakenly has a tag property. Preserve the intended disable.
    data['recipes'][0]['conditions'] = [{'type': 'forge:false'}]
    save(batter, data)
    save('sob/advancements/get_prickly_pear.json', {
        'criteria': {'unused_in_virgos': {'trigger': 'minecraft:impossible'}}
    })
    print(f'4 data overrides generated; {changed} written-book functions backported to 1.20.1.')


if __name__ == '__main__':
    main()
