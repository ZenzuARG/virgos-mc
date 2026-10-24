"""Apply reviewed values to generated TOML, preserving comments and validating keys.

Only the lab and distributable templates are changed. Public deployment is separate.
Run with the lab stopped. Requires the first successful boot's generated configs.
"""
from pathlib import Path
import ctypes
import json
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / '.lab/server'
POLICY = json.loads((ROOT / 'pack/balance-policy.json').read_text('utf-8'))


def value_at(document, path):
    for key in path.split('.'):
        document = document[key]
    return document


def patch_toml(source, changes):
    document = tomllib.loads(source)
    for path in changes:
        value_at(document, path)  # Fail on misspelled or obsolete settings.
    section = ''
    found = set()
    lines = []
    for line in source.splitlines():
        match = re.match(r'^\s*\[([^\]]+)\]\s*$', line)
        if match:
            section = match[1]
        match = re.match(r'^(\s*)([A-Za-z0-9_]+)\s*=', line)
        if match:
            path = f'{section}.{match[2]}' if section else match[2]
            if path in changes:
                if path in found:
                    raise ValueError(f'Duplicate key: {path}')
                line = f'{match[1]}{match[2]} = {json.dumps(changes[path], ensure_ascii=False)}'
                found.add(path)
        lines.append(line)
    if found != set(changes):
        raise ValueError(f'Unmatched changes: {set(changes) - found}')
    result = '\n'.join(lines) + '\n'
    updated = tomllib.loads(result)
    for path, value in changes.items():
        assert value_at(updated, path) == value, path
    return result


def main():
    process_file = LAB / 'process.json'
    if process_file.exists():
        process = json.loads(process_file.read_text('utf-8'))
        pid = process.get('pid')
        if pid:
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                raise SystemExit('Stop the lab before configuring it.')
    prepared = []
    report = []
    for relative, changes in POLICY.items():
        is_server = relative.startswith('serverconfig/')
        source = LAB / ('virgos_world/' + relative if is_server else relative)
        original = source.read_text('utf-8')
        rendered = patch_toml(original, changes)
        destination = 'defaultconfigs/' + source.name if is_server else relative
        targets = [source, ROOT / 'pack/server-overrides' / destination]
        if not is_server and source.name != 'simplebackups-common.toml':
            targets += [ROOT / 'pack/client-overrides' / relative, ROOT / 'client/standard' / relative]
        prepared.append((rendered, targets))
        parsed = tomllib.loads(original)
        for key, value in changes.items():
            report.append({'file': relative, 'key': key, 'before': value_at(parsed, key), 'value': value})
    # Validate the complete policy before making any writes.
    for rendered, targets in prepared:
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding='utf-8')
    (ROOT / 'pack/configuration-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(f'{len(report)} settings validated across {len(prepared)} configurations; runtime verification pending.')


if __name__ == '__main__':
    main()
