"""Apply the pack's initial controls to staging and first-launch defaults.

DefaultOptions preserves a player's subsequent changes. Run staging changes
only while the QA client is stopped, or its Options.save() will overwrite them.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
bindings = {
    'key.heracles.open_quests': 'j',
    'key.sophisticatedbackpacks.open_backpack': 'b',
    'gui.xaero_new_waypoint': 'n',
    'gui.xaero_waypoints_key': 'u',
    'key.corpse.death_history': 'h',
    'key.simplytooltips.capture_gif': 'unknown',
    'gui.xaero_pac_key_open_menu': 'p',
    'key.socialInteractions': 'unknown',
    'key.ars_nouveau.selection_hud': 'y',
    'key.ars_nouveau.head_curio_hotkey': 'k',
    'gui.xaero_minimap_settings': 'unknown',
    'gui.xaero_enlarge_map': 'minus',
    'key.sophisticatedbackpacks.inventory_interaction': 'insert',
    'key.sophisticatedbackpacks.toggle_upgrade_1': 'unknown',
    'key.sophisticatedbackpacks.toggle_upgrade_2': 'unknown',
    'key.cataclysm.ability': 'keypad.6',
    'key.cataclysm.helmet_ability': 'keypad.7',
    'key.cataclysm.chestplate_ability': 'keypad.8',
    'key.cataclysm.boots_ability': 'keypad.9',
    'key.aether.invisibility_toggle.desc': 'period',
    'supplementaries.keybind.quiver': 'comma',
    'key.special_ability': 'right.control',
}
path = ROOT / 'client/standard/options.txt'
lines = path.read_text('utf-8').splitlines()
updates = {'key_' + name: 'key.keyboard.' + key for name, key in bindings.items()}
updates.update({'lang': 'es_ar', 'renderDistance': '8', 'simulationDistance': '6',
                'maxFps': '60', 'autoJump': 'false', 'guiScale': '2'})
seen = set()
for i, line in enumerate(lines):
    key = line.split(':', 1)[0]
    if key in updates:
        lines[i] = key + ':' + updates[key]
        seen.add(key)
lines += [key + ':' + value for key, value in updates.items() if key not in seen]
text = '\n'.join(lines) + '\n'
path.write_text(text, 'utf-8')
for base in ['client/standard', 'pack/client-overrides']:
    target = ROOT / base / 'config/defaultoptions'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'options.txt').write_text(text, 'utf-8')
(ROOT / 'pack/keybindings.json').write_text(json.dumps(bindings, indent=2), 'utf-8')
print('Controls and first-launch defaults updated:', len(bindings))
