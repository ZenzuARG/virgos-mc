"""Exercise the public claim menu with two existing QA clients, never human claims.

Requires both QA clients running with the current client pack and their existing
cached credentials. Uses native UI actions, not direct permission-file writes.
Run with --public to explicitly authorize public temporary fixtures.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import runpy
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / '.lab/reports/qa-claim-permissions.json'
FOLDERS = {1: ROOT/'client/standard/virgos-qa', 2: ROOT/'client/qa-secondary/virgos-qa'}
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
    action(account, {'action': 'disconnect'})
    wait(lambda: state(account).get('screen', '').endswith('TitleScreen'), 'title screen')
    action(account, {'action': 'connect'})
    wait(lambda: state(account).get('name') == name, 'joined QA identity')
    if state(account).get('screen', '').endswith('DeathScreen'):
        action(account, {'action': 'inspect_screen'})
        widgets = read(FOLDERS[account]/'screen.json')
        button = next(w for w in widgets if w.get('active') and w.get('visible')
                      and w.get('text') in ('Reaparecer', 'Respawn'))
        action(account, {'action': 'click', 'x': button['x']+button['width']/2,
                         'y': button['y']+button['height']/2, 'button': 0})
    wait(lambda: state(account).get('screen') == 'game' and state(account).get('health', 0) > 0,
         'alive and world loaded')
    action(account, {'action': 'command', 'value': 'login '+credentials['password']})

    def authenticated():
        with (ROOT/'logs/latest.log').open('rb') as stream:
            stream.seek(offset)
            fresh = stream.read().decode('utf8', errors='replace')
        return (f'[AuthMe] {name} logged in' in fresh
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', action='store_true', required=True)
    parser.parse_args()
    result = {'passed': False, 'checks': [], 'cleanup': False}
    checks = result['checks']
    names = {i: read(ROOT/('.cache/qa-account.json' if i == 1 else '.cache/qa-account-2.json'))['name'] for i in (1, 2)}
    assert names == {1: 'VirgosQA1', 2: 'VirgosQA2'}
    read_nbt = runpy.run_path(str(ROOT/'scripts/inspect-nbt.py'))['read_nbt']
    # Read-only fixture preflight: chunk (62,62) must not belong to anyone.
    for path in (ROOT/'virgos_world/data/openpartiesandclaims/player-claims').glob('*.nbt'):
        claims = read_nbt(path)[''].get('dimensions', {}).get('minecraft:overworld', {}).get('claims', [])
        assert not any(p['x'] == 62 and p['z'] == 62 for c in claims for p in c['positions']), 'Fixture chunk already claimed'
    # Guard saved human configuration bytes as a regression invariant.
    owner_id = '13e2e728-2a7a-36a6-84ee-5c289cf4cc02'
    human = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in
             (ROOT/'virgos_world/data/openpartiesandclaims/player-configs').glob('*.toml')
             if p.stem not in (owner_id, '32fb01e0-3ed4-3ad5-a0c6-e3897ba1fb7e')}
    created = claimed = False
    try:
        for i in (1, 2):
            login(i)
            server('gamemode creative '+names[i])
        checks.append('two-current-clients-authenticated')
        # Require air before touching the temporary sky platform/chest.
        conditions = ' '.join(f'if block {x} 249 {z} minecraft:air' for x in range(998,1003) for z in range(998,1003))
        marker = 'CLAIM_QA_EMPTY_'+str(time.time_ns())
        server(f'execute {conditions} if block 1000 250 998 minecraft:air run say {marker}')
        wait(lambda: marker in (ROOT/'logs/latest.log').read_text('utf8', errors='replace'), 'fixture air preflight')
        server('fill 998 249 998 1002 249 1002 minecraft:glass')
        server('setblock 1000 250 998 minecraft:chest[facing=south]')
        created = True
        for i in (1, 2):
            server(f'tp {names[i]} 1000.5 250 1000.5 180 20')
            wait(lambda: abs(state(i).get('x',0)-1000.5)<.05, 'fixture position')
        action(1, {'action': 'command', 'value': 'oclaims claim'})
        claimed = True
        action(1, {'action': 'command', 'value': 'virgos permisos'})
        menu(1, 'Permisos')
        checks.append('owner-menu-opens')
        chest(False)
        checks.append('foreign-chest-denied-before-grant')
        slot(1, 12); menu(1, 'Amigos')
        slot(1, 19); menu(1, 'Integrantes')
        target = next(s['slot'] for s in slots(1) if names[2] in s['item'])
        slot(1, target)
        wait(lambda: any(m['name'] == names[2] for m in policy(owner_id).get('groups', {}).get('amigos', {}).get('members', [])), 'saved member')
        checks.append('player-added-through-menu')
        slot(1, 22); menu(1, 'Amigos')
        slot(1, 10)
        wait(lambda: policy(owner_id).get('groups', {}).get('amigos', {}).get('permissions', {}).get('storage') is True, 'saved chest permission')
        chest(True)
        checks.append('saved-chest-permission-enforced')
        before = policy(owner_id)
        for i in (1, 2):
            login(i)
        assert policy(owner_id) == before, 'Policy changed on reconnect'
        action(1, {'action': 'command', 'value': 'virgos permisos'}); menu(1, 'Permisos')
        slot(1, 12); menu(1, 'Amigos')
        assert '✓' in next(s['item'] for s in slots(1) if s['slot'] == 10)
        slot(1, 19); menu(1, 'Integrantes')
        assert '✓' in next(s['item'] for s in slots(1) if names[2] in s['item'])
        chest(True)
        checks.append('membership-and-chest-access-survive-both-reconnects')
        slot(1, 22); menu(1, 'Amigos'); slot(1, 10)
        wait(lambda: policy(owner_id)['groups']['amigos']['permissions']['storage'] is False, 'revoked chest permission')
        chest(False)
        checks.append('revoked-chest-access-denied')
        result['passed'] = True
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
            attempt('remove-chest', lambda: server('setblock 1000 250 998 minecraft:air replace'))
            attempt('remove-platform', lambda: server(
                'fill 998 249 998 1002 249 1002 minecraft:air replace minecraft:glass'))
        for account in (1, 2):
            attempt('restore-position', lambda account=account: server(
                f'tp {names[account]} 672.5 80 752.5'))
            attempt('restore-mode', lambda account=account: server('gamemode survival '+names[account]))
            attempt('disconnect', lambda account=account: action(account, {'action': 'disconnect'}))
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
    original = {key: namespace[key] for key in ('server', 'action', 'REPORT')}
    commands = []
    def dead_client(*_args):
        raise TimeoutError('QA client unavailable')
    with tempfile.TemporaryDirectory(prefix='claim-cleanup-') as scratch:
        try:
            namespace.update(server=commands.append, action=dead_client, REPORT=Path(scratch)/'report.json')
            result = {'passed': True}
            with contextlib.redirect_stdout(io.StringIO()):
                cleanup(result, {1: 'VirgosQA1', 2: 'VirgosQA2'}, True, True, {})
            assert len(commands) == 7
            assert commands[0].startswith('oclaims player unclaim')
            assert json.loads(namespace['REPORT'].read_text('utf8'))['passed'] is False
            assert len(result['cleanupErrors']) == 2
        finally:
            namespace.update(original)
    print('PASS: dead-client cleanup still removes fixtures and writes failure report')


if __name__ == '__main__':
    main()
