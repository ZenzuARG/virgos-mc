"""Pinned public-trial addon metadata; no downloads or native acceptance claims."""
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from create_addons_lab import artifacts

EXPECTED = {'kU1G12Nn': {'filename': 'createaddition-1.20.1-1.3.3.jar',
              'version_id': '9LgyB6Yb',
              'version': 'forge-1.20.1-1.3.3',
              'url': 'https://cdn.modrinth.com/data/kU1G12Nn/versions/9LgyB6Yb/createaddition-1.20.1-1.3.3.jar',
              'hash_algorithm': 'sha512',
              'hash': 'a34f5c3b0226069d2882a3e23ba0e364a78bc5d26983b0cecea8d998718f454d3238ab7c5b4b3ef1749b6f2b26a4e427839c7c32468558fa7a8edb0edc727d10',
              'size': 1577313,
              'mods': {'createaddition': '1.20.1-1.3.3'}},
 'gJ5afkVv': {'filename': 'bellsandwhistles-0.4.5-1.20.x-Create6.0+.jar',
              'version_id': 'kW8DoegV',
              'version': '0.4.5-1.20.x',
              'url': 'https://cdn.modrinth.com/data/gJ5afkVv/versions/kW8DoegV/bellsandwhistles-0.4.5-1.20.x-Create6.0%2B.jar',
              'hash_algorithm': 'sha512',
              'hash': '99fc8e509ff2ed5a3c521e17bb04e574f6cf5d1abc9adb170dd5d311b9cdc762f75bd133b63e1fd56e00fe030674cf87ee1760187fed1c3d30dae429ee00861c',
              'size': 199902,
              'mods': {'bellsandwhistles': '0.4.3-1.20.x'}},
 'JWGBpFUP': {'filename': 'create_enchantment_industry-1.4.1-for-create-6.0.8.jar',
              'version_id': 'caLmFTZ1',
              'version': '1.4.1',
              'url': 'https://cdn.modrinth.com/data/JWGBpFUP/versions/caLmFTZ1/create_enchantment_industry-1.4.1-for-create-6.0.8.jar',
              'hash_algorithm': 'sha512',
              'hash': 'df13070cad7b477d9eab24fdee9af4fddf8b7183a103e5b00efc7def0107ad075159abf1ca551e4270724197070f78f11bd6da3bb630a84341f9c85dcc0207b3',
              'size': 503399,
              'mods': {'create_enchantment_industry': '1.4.1-for-create-6.0.8'}}}
EXPECTED['6YVagaSv'] = {'filename': 'create_netherless-2.0.0-1.20.1.jar',
                         'version_id': 'htwdYiKv',
                         'version': '2.0.0',
                         'url': 'https://cdn.modrinth.com/data/6YVagaSv/versions/htwdYiKv/create_netherless-2.0.0-1.20.1.jar',
                         'hash_algorithm': 'sha512',
                         'hash': 'dfd047100b44916bb56ed57b7ccf0ac9db47b2d6d73ebbe2cc629c4c807a45d7982d531e61fa57f857b3c7f719827cdb615d7a132e4bcc85916a1f495eae199e',
                         'size': 30799,
                         'mods': {'create_netherless': '2.0.0'}}
EXPECTED['ZM3tt6p1'] = {'filename': 'createdieselgenerators-1.20.1-1.3.12.jar',
                        'version_id': 'DTQVvA5H',
                        'version': '1.20.1-1.3.12',
                        'url': 'https://cdn.modrinth.com/data/ZM3tt6p1/versions/DTQVvA5H/createdieselgenerators-1.20.1-1.3.12.jar',
                        'hash_algorithm': 'sha512',
                        'hash': 'fc9aebaa5b654078be4736e1c35cc34edda0986db75fc3ce1391a86a499df6dcb3958d9854d402f5479eeb38d0f9388223b0359a34d594589e75ed3a58dd45a1',
                        'size': 3128610,
                        'mods': {'createdieselgenerators': '1.20.1-1.3.12'}}
EXPECTED['YA6YzEfz'] = {'filename': 'enhancedmastery-1.0.0.jar',
                        'version_id': 'uCI0GdFn',
                        'version': '1.0.0',
                        'url': 'https://cdn.modrinth.com/data/YA6YzEfz/versions/uCI0GdFn/enhancedmastery-1.0.0.jar',
                        'hash_algorithm': 'sha512',
                        'hash': '1f4d049b7938f58c63a2cff186300ccd12b51d44b828882134a1dabe94f72836e93cc8f030fe91569791021d9f04e5a79485efa2cdf21f97aea329527a749792',
                        'size': 187746,
                        'mods': {'enhancedmastery': '1.0.0'}}

class AddonReleaseLock(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((ROOT / 'pack/mods.lock.json').read_text(encoding='utf-8'))

    def test_exact_verified_addons_are_required_on_both_sides(self):
        for project_id, expected in EXPECTED.items():
            with self.subTest(project=project_id):
                rows = [row for row in self.lock['artifacts'] if row.get('project_id') == project_id]
                self.assertEqual(len(rows), 1)
                row = rows[0]
                for key, value in expected.items():
                    if key != 'mods':
                        self.assertEqual(row[key], value)
                self.assertEqual(set(row['sides']), {'client', 'server'})
                self.assertEqual(row['mode'], 'standard')
                self.assertIs(row['root'], True)
                self.assertEqual({m['id']:m['version'] for m in row['descriptor']['mods']}, expected['mods'])
                for mod_id in expected['mods']:
                    owners = [a for a in self.lock['artifacts']
                              if any(m['id'] == mod_id for m in a.get('descriptor', {}).get('mods', []))]
                    self.assertEqual(len(owners), 1)

    def test_selected_descriptors_fit_existing_pack_dependencies(self):
        selected = [row for row in self.lock['artifacts'] if row.get('project_id') in EXPECTED]
        self.assertEqual(len(selected), 6)
        base = dict(self.lock, artifacts=[row for row in self.lock['artifacts']
                                         if row.get('project_id') not in EXPECTED])
        artifacts.check_dependencies([row['descriptor'] for row in selected], artifacts.inventory(base))

if __name__ == '__main__':
    unittest.main()
