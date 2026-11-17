"""Exercise the public claim menu with one QA client and two fixed identities, never human claims.

Requires one standard QA client running with the current client pack and their existing
cached credentials. Uses native UI actions, not direct permission-file writes.
Run with --public to explicitly authorize public temporary fixtures.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import runpy
import sqlite3
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / '.lab/reports/qa-claim-permissions.json'
FOLDERS = {1: ROOT/'client/standard/virgos-qa', 2: ROOT/'client/standard/virgos-qa'}
BASE = 'http://127.0.0.1:8765'


def read(path):
    try:
        return json.loads(path.read_text('utf-8-sig'))
    except (OSError, ValueError):
        return {}


def wait(test, label, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = test()
        if result:
            return result
        time.sleep(.25)
    raise RuntimeError('Timed out: ' + label)


def state(account):
    return read(FOLDERS[account]/'status.json')


def action(account, command):
    folder = FOLDERS[account]
    path = folder/'commands.jsonl'
    with path.open('a', encoding='utf8') as stream:
        stream.write(json.dumps(command) + '\n')
    line = len(path.read_text('utf8').splitlines())
    wait(lambda: state(account).get('line', 0) >= line, 'QA action acknowledgment')
    error = read(folder/'last-error.json')
    if error.get('line') == line:
        raise RuntimeError('QA driver rejected action: ' + error.get('error', 'unknown'))
    return state(account)


def panel(route, body=None):
    html = urllib.request.urlopen(BASE+'/', timeout=10).read().decode()
    token = re.search(r'name="panel-token" content="([^"]+)"', html)[1]
    headers = {'X-Panel-Token': token, 'Origin': BASE, 'Content-Type': 'application/json'}
    request = urllib.request.Request(BASE+'/api/'+route, headers=headers,
                                    data=json.dumps(body).encode() if body else None)
    return json.load(urllib.request.urlopen(request, timeout=15))


def server(command):
    return panel('action', {'action': 'command', 'command': command, 'confirm': 'command'})


def login(account):
    credentials = read(ROOT/('.cache/qa-account.json' if account == 1 else '.cache/qa-account-2.json'))
    name = credentials['name']
    offset = (ROOT/'logs/latest.log').stat().st_size
    previous = state(account)
    if previous.get('name') in ('VirgosQA1', 'VirgosQA2') and previous.get('health', 0) > 0:
        action(account, {'action': 'close'})
        server('tp '+previous['name']+' 672.5 80 752.5')
        server('gamemode survival '+previous['name'])
        wait(lambda: abs(state(account).get('x', 0)-672.5)<.1
             and not state(account).get('mayfly', True), 'restore departing QA identity')
    action(account, {'action': 'disconnect'})
    wait(lambda: state(account).get('screen', '').endswith('TitleScreen'), 'title screen')
    action(account, {'action': 'qa_identity', 'name': name})
    action(account, {'action': 'connect'})
    wait(lambda: state(account).get('name') == name, 'joined QA identity', seconds=180)
    wait(lambda: state(account).get('screen') == 'game'
         or state(account).get('screen', '').endswith('DeathScreen'), 'world or respawn screen')
    if state(account).get('screen', '').endswith('DeathScreen'):
        time.sleep(1.5)  # Vanilla enables the respawn button after its death-screen delay.
        action(account, {'action': 'inspect_screen'})
        widgets = read(FOLDERS[account]/'screen.json')
        button = next(w for w in widgets if w.get('active') and w.get('visible')
                      and w.get('text') in ('Reaparecer', 'Respawn'))
        action(account, {'action': 'click', 'x': button['x']+button['width']/2,
                         'y': button['y']+button['height']/2, 'button': 0})
    wait(lambda: state(account).get('screen') == 'game' and state(account).get('health', 0) > 0,
         'alive and world loaded')
    with sqlite3.connect((ROOT/'plugins/AuthMe/authme.db').as_uri()+'?mode=ro', uri=True) as db:
        registered = db.execute('SELECT count(*) FROM authme WHERE lower(realname)=lower(?)', (name,)).fetchone()[0]
    if registered:
        command = 'login '+credentials['password']
    else:
        assert name in ('VirgosQA1', 'VirgosQA2'), 'Only QA accounts may be registered'
        command = 'register '+credentials['password']+' '+credentials['password']
    action(account, {'action': 'command', 'value': command})

    def authenticated():
        with (ROOT/'logs/latest.log').open('rb') as stream:
            stream.seek(offset)
            fresh = stream.read().decode('utf8', errors='replace')
        return ((f'[AuthMe] {name} logged in' in fresh or f'[AuthMe] {name} registered' in fresh)
                and f'OPAC resynchronized after authentication for {name}' in fresh)
    wait(authenticated, 'fresh AuthMe login and OPAC synchronization')


def menu(account, title):
    return wait(lambda: state(account).get('screen', '').endswith('ContainerScreen')
                and title in state(account).get('screenTitle', ''), title)


def slot(account, number):
    action(account, {'action': 'slot', 'slot': number, 'button': 0, 'type': 'PICKUP'})


def slots(account):
    action(account, {'action': 'slots'})
    return read(FOLDERS[account]/'slots.json')['slots']


def policy(owner):
    return read(ROOT/'virgos_world/virgos-claim-permissions.json').get(owner+':main', {})


def chest(allowed):
    action(2, {'action': 'close'})
    action(2, {'action': 'look', 'yaw': 180, 'pitch': 20})
    action(2, {'action': 'use'})
    time.sleep(1)
    opened = state(2).get('screen', '').endswith('ContainerScreen')
    assert opened == allowed, f'Chest access: expected {allowed}, got {state(2).get("screen")}'
    if opened:
        assert state(2).get('screenTitle') in ('Cofre', 'Chest'), 'Unexpected container'


def position(account):
    name = 'VirgosQA'+str(account)
    server('gamemode creative '+name)
    server(f'tp {name} 1000.5 250 1000.5 180 20')
    wait(lambda: abs(state(account).get('x', 0)-1000.5)<.05
         and abs(state(account).get('y', 0)-250)<.1, 'fixture position')


def open_friends():
    action(1, {'action': 'close'})
    action(1, {'action': 'key', 'name': 'key.virgos_codex.claim_permissions'})
    menu(1, 'Permisos')
    slot(1, 12)
    menu(1, 'Amigos')


def find_member(name):
    for _ in range(100):
        rows = slots(1)
        target = next((row for row in rows if name in row['item']), None)
        if target:
            return target
        if not any(row['slot'] == 20 and 'arrow' in row['item'] for row in rows):
            raise AssertionError('Known player missing from all pages: '+name)
        slot(1, 20)
    raise AssertionError('Member pagination did not terminate')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', action='store_true', required=True)
    parser.add_argument('--single-client', action='store_true', required=True)
    parser.parse_args()
    result = {'passed': False, 'checks': [], 'cleanup': False, 'maxConcurrentClients': 1}
    checks = result['checks']
    names = {1: 'VirgosQA1', 2: 'VirgosQA2'}
    read_nbt = runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt']
    for path in (ROOT/'virgos_world/data/openpartiesandclaims/player-claims').glob('*.nbt'):
        claims = read_nbt(path)[''].get('dimensions', {}).get('minecraft:overworld', {}).get('claims', [])
        assert not any(p['x'] == 62 and p['z'] == 62 for c in claims for p in c['positions']), 'Fixture chunk already claimed'
    owner_id = '13e2e728-2a7a-36a6-84ee-5c289cf4cc02'
    human = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in
             (ROOT/'virgos_world/data/openpartiesandclaims/player-configs').glob('*.toml')
             if p.stem not in (owner_id, '32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e')}
    created = claimed = False
    try:
        login(1)
        server('gamemode creative VirgosQA1')
        server('tp VirgosQA1 1000.5 252 1000.5')
        wait(lambda: abs(state(1).get('x', 0)-1000.5)<.05, 'load fixture chunk')
        marker = 'CLAIM_QA_EMPTY_'+str(time.time_ns())
        positions = [(x, 249, z) for x in range(998, 1003) for z in range(998, 1003)]
        positions.append((1000, 250, 998))
        for index, (x, y, z) in enumerate(positions):
            token = marker+'_'+str(index)+'_OK'
            server(f'execute if block {x} {y} {z} minecraft:air run say {token}')
            wait(lambda token=token: token in (ROOT/'logs/latest.log').read_text('utf8', errors='replace'),
                 'fixture air preflight '+str(index), seconds=15)
        server('fill 998 249 998 1002 249 1002 minecraft:glass')
        server('setblock 1000 250 998 minecraft:chest[facing=south]')
        created = True
        position(1)
        action(1, {'action': 'command', 'value': 'oclaims claim'})
        wait(lambda: 'Successfully claimed the chunk at (62, 62)' in
             (ROOT/'logs/latest.log').read_text('utf8', errors='replace'), 'QA claim created')
        claimed = True
        open_friends()
        checks.append('P-opens-Spanish-permission-menu')
        if policy(owner_id).get('groups', {}).get('amigos', {}).get('permissions', {}).get('storage'):
            slot(1, 10)
        slot(1, 19); menu(1, 'Integrantes')
        row = find_member(names[2])
        if '\u2713' in row['item']:
            slot(1, row['slot'])
            row = find_member(names[2])
        slot(1, row['slot'])
        wait(lambda: any(m['name'] == names[2] for m in policy(owner_id).get('groups', {}).get('amigos', {}).get('members', [])), 'saved offline member')
        checks.append('offline-player-added-through-menu')
        login(2); position(2); chest(False)
        checks.append('foreign-chest-denied-before-grant')
        login(1); position(1); open_friends(); slot(1, 10)
        wait(lambda: policy(owner_id)['groups']['amigos']['permissions']['storage'] is True, 'saved chest permission')
        before = policy(owner_id)
        login(2); position(2); chest(True)
        checks.append('saved-chest-permission-enforced')
        login(2); position(2); chest(True)
        checks.append('chest-access-survives-reconnect')
        login(1); position(1); open_friends()
        assert policy(owner_id) == before, 'Policy changed on reconnect'
        assert '\u2713' in next(row['item'] for row in slots(1) if row['slot'] == 10)
        slot(1, 19); menu(1, 'Integrantes')
        assert '\u2713' in find_member(names[2])['item']
        checks.append('saved-membership-and-chest-toggle-survive-owner-reconnect')
        slot(1, 22); menu(1, 'Amigos'); slot(1, 10)
        wait(lambda: policy(owner_id)['groups']['amigos']['permissions']['storage'] is False, 'revoked chest permission')
        login(2); position(2); chest(False)
        checks.append('revoked-chest-access-denied')
        result['passed'] = True
    except Exception as error:
        result['failure'] = type(error).__name__+': '+str(error)
        raise
    finally:
        cleanup(result, names, claimed, created, human)


def cleanup(result, names, claimed, created, human):
    """Teardown uses server authority even when either QA driver has failed."""
    errors = result.setdefault('cleanupErrors', [])

    def attempt(label, operation):
        try:
            operation()
        except Exception as error:
            errors.append(label+':'+type(error).__name__)

    try:
        if claimed:
            attempt('unclaim', lambda: server(
                'oclaims player unclaim as VirgosQA1 in minecraft:overworld 992 992 992 992 anyway'))
        if created:
            attempt('load-fixture', lambda: server('forceload add 1000 1000'))
            time.sleep(1)
            attempt('remove-chest', lambda: server('setblock 1000 250 998 minecraft:air replace'))
            attempt('remove-platform', lambda: server(
                'fill 998 249 998 1002 249 1002 minecraft:air replace minecraft:glass'))
            attempt('release-fixture', lambda: server('forceload remove 1000 1000'))
        active = state(1).get('name')
        if active in names.values():
            attempt('restore-position', lambda: server(f'tp {active} 672.5 80 752.5'))
            attempt('restore-mode', lambda: server('gamemode survival '+active))
        attempt('disconnect', lambda: action(1, {'action': 'disconnect'}))
        result['humanConfigUnchanged'] = all(
            p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in human.items())
    finally:
        result['cleanup'] = not errors
        result['passed'] &= result['cleanup'] and result.get('humanConfigUnchanged', False)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(result, indent=2), 'utf8')
        print(json.dumps(result))


def test_cleanup_without_clients():
    """Regression: dead clients must not prevent native teardown or evidence."""
    import tempfile
    import contextlib
    import io
    namespace = cleanup.__globals__
    original = {key: namespace[key] for key in ('server', 'action', 'REPORT', 'state')}
    commands = []
    def dead_client(*_args):
        raise TimeoutError('QA client unavailable')
    with tempfile.TemporaryDirectory(prefix='claim-cleanup-') as scratch:
        try:
            namespace.update(server=commands.append, action=dead_client, REPORT=Path(scratch)/'report.json', state=lambda _: {'name':'VirgosQA1'})
            result = {'passed': True}
            with contextlib.redirect_stdout(io.StringIO()):
                cleanup(result, {1: 'VirgosQA1', 2: 'VirgosQA2'}, True, True, {})
            assert len(commands) == 7
            assert commands[0].startswith('oclaims player unclaim')
            assert json.loads(namespace['REPORT'].read_text('utf8'))['passed'] is False
            assert len(result['cleanupErrors']) == 1
        finally:
            namespace.update(original)
    print('PASS: dead-client cleanup still removes fixtures and writes failure report')


if __name__ == '__main__':
    main()
