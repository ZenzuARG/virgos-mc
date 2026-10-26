"""Foreground bounded runner; operates only its own newly spawned process."""
import argparse
import json
import os
import subprocess
import shutil
import time
import uuid
from pathlib import Path
from dh_fullpack_lab import policy as p


def client_state(status, fixture=None, role=None):
    """Only observed title/game states establish startup; loading errors are fatal."""
    screen = status.get('screen', '')
    if not isinstance(screen, str):
        return 'pending'
    if screen.rsplit('.', 1)[-1] == 'LoadingErrorScreen':
        return 'loading-error'
    if screen == 'net.minecraft.client.gui.screens.TitleScreen':
        return 'ready'
    if screen == 'game' and status.get('name') in {'VirgosQA1', 'VirgosQA2'}:
        return 'ready'
    expected = {'name': 'Notch', 'uuid': p.identity('Notch'), 'role': 'client2', 'ownershipVerified': False}
    if (screen == 'game' and role == 'client2' and fixture == expected
            and status.get('name') == 'Notch' and status.get('uuid') == expected['uuid']):
        return 'ready'
    return 'pending'


def reset_client_observations(cwd, run_id):
    """Preserve old evidence, but never replay its controls or report it as current."""
    qa = cwd / 'virgos-qa'
    previous = list(qa.glob('*.json'))
    queue = p.regular(qa / 'commands.jsonl')
    history = qa / 'history' / run_id
    history.mkdir(parents=True)
    for old in [queue, *previous]:
        shutil.copy2(p.regular(old), history / old.name)
    p.write(queue, '')
    names = {old.name for old in previous} | {'dh-audit.json', 'loading-audit.json'}
    for name in names:
        p.write(qa / name, json.dumps({'pending': True, 'runId': run_id}))
    p.write(qa / 'status.json', json.dumps({'screen': 'starting', 'runId': run_id}))


def run(lab, role, lifetime=1200, boot_timeout=300):
    if not 1 <= lifetime <= 1200 or not 1 <= boot_timeout <= 300:
        raise ValueError('Maximum lifetime is 1200 seconds; boot timeout is 300 seconds')
    lab = Path(lab).resolve()
    manifest = p.validate_run(lab, role)
    cwd = lab / role
    state = cwd / 'process.json'
    if state.exists() and not json.loads(p.regular(state).read_text()).get('finished'):
        raise ValueError('Unfinished lab process record; inspect manually before relaunch')
    java = p.regular(manifest['java'][role])
    args = json.loads(p.regular(lab / (role + '-args.json')).read_text())
    if not isinstance(args, list) or any(not isinstance(x, str) for x in args):
        raise ValueError('Invalid launch argument array')
    # Validate every writable control path before opening a process or output file.
    for relative in [role + '/process.json', role + '/console.log', 'server/commands.txt',
                     role + '/virgos-qa/commands.jsonl', role + '/virgos-qa/status.json']:
        target = lab / relative
        if any(x.is_symlink() or (hasattr(x, 'is_junction') and x.is_junction()) for x in [target, *target.parents]):
            raise ValueError('Linked control path forbidden')
    command_queue = cwd / ('commands.txt' if role == 'server' else 'virgos-qa/commands.jsonl')
    run_id = uuid.uuid4().hex
    if role != 'server':
        reset_client_observations(cwd, run_id)
    cursor = command_queue.stat().st_size if command_queue.exists() and role == 'server' else 0
    console_start = (cwd / 'console.log').stat().st_size if (cwd / 'console.log').exists() else 0
    start = time.monotonic()
    with (cwd / 'console.log').open('ab', buffering=0) as log:
        child = subprocess.Popen([str(java), *args], cwd=cwd, stdin=subprocess.PIPE if role == 'server' else subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        p.write(state, json.dumps({'pid': child.pid, 'runner': os.getpid(), 'role': role,
                                  'cwd': str(cwd), 'finished': False, 'runId': run_id}))
        stopping, ready = False, False
        stop_at = None
        reason = 'process exited'
        try:
            while child.poll() is None:
                elapsed = time.monotonic() - start
                failure = None
                if role == 'server':
                    if command_queue.exists():
                        # Only commands appended after this runner starts are accepted.
                        with command_queue.open('r', encoding='utf-8') as stream:
                            stream.seek(cursor)
                            lines = stream.readlines()
                            cursor = stream.tell()
                        for line in lines:
                            if line.strip():
                                child.stdin.write((line.rstrip() + '\n').encode())
                                child.stdin.flush()
                    with (cwd / 'console.log').open('rb') as current:
                        current.seek(console_start)
                        ready = ready or b'Done (' in current.read()[-100000:]
                else:
                    status = cwd / 'virgos-qa/status.json'
                    if status.exists():
                        try:
                            observation = json.loads(status.read_text())
                            current = client_state(observation, manifest.get('skinFixture'), role)
                            if current == 'loading-error':
                                ready = False
                                failure = 'client loading error'
                                if not stopping:
                                    p.write(cwd / 'virgos-qa/runner-failure.json', json.dumps({
                                        'runId': run_id, 'reason': failure, 'status': observation}))
                            else:
                                ready = ready or current == 'ready'
                        except (ValueError, OSError):
                            pass
                if not stopping and (failure or elapsed >= lifetime or (not ready and elapsed >= boot_timeout)):
                    reason = failure or ('lifetime expired' if elapsed >= lifetime else 'boot timeout')
                    stopping, stop_at = True, time.monotonic()
                    if role == 'server':
                        child.stdin.write(b'stop\n')
                        child.stdin.flush()
                    else:
                        with command_queue.open('a', encoding='utf-8') as stream:
                            stream.write('{"action":"quit"}\n')
                if stopping and time.monotonic() - stop_at >= 30:
                    child.terminate()  # This Popen handle only; never a discovered public PID.
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                    break
                time.sleep(0.25)
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            p.write(state, json.dumps({'pid': child.pid, 'role': role, 'cwd': str(cwd), 'finished': True,
                                      'exitCode': child.returncode, 'ready': ready, 'reason': reason, 'runId': run_id}))
    return child.returncode if ready and reason == 'process exited' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lab', required=True)
    parser.add_argument('--role', required=True, choices=['server', 'client', 'client2'])
    parser.add_argument('--lifetime', type=int, default=1200)
    parser.add_argument('--boot-timeout', type=int, default=300)
    args = parser.parse_args()
    try:
        if not p.authorized_lab(args.lab):
            raise ValueError('Only the explicitly authorized full-pack destination is permitted')
        raise SystemExit(run(args.lab, args.role, args.lifetime, args.boot_timeout))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, 'Launch refused: ' + str(error) + '\n')
