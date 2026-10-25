"""Download and hash-verify the locked client dependencies for a clean release build."""
from __future__ import annotations

import hashlib
import json
import concurrent.futures
import time
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dh_targets(root: Path) -> list:
    """Optional build-only inputs; older releases without the record are unchanged."""
    path = root / 'pack/dh-upstream.lock.json'
    if not path.exists():
        return []
    record = json.loads(path.read_text(encoding='utf-8'))
    if record.get('schema') != 1 or len(record.get('source_archives', [])) != 2:
        raise ValueError('Unknown DH build-input schema')
    inputs = [(record, 'downloads', record['filename']), (record['asm'], 'tools', record['asm']['file'])]
    inputs += [(dict(item, hash=item['sha256'], hash_algorithm='sha256'), 'sources', item['filename'])
               for item in record['source_archives']]
    targets = []
    for item, folder, name in inputs:
        if not re.fullmatch(r'[A-Za-z0-9_.+ ()-]+', name) or name in {'.', '..'}:
            raise ValueError('Unsafe DH build-input filename')
        targets.append((item, root / '.cache/pack' / folder / name))
    return targets


def fetch(record: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = record["hash"].lower()
    algorithm = record.get("hash_algorithm", record.get("algorithm", "sha256"))
    name = record.get("filename", record.get("file", target.name))
    if target.is_file() and hashlib.new(algorithm, target.read_bytes()).hexdigest() == expected:
        return
    for attempt in range(5):
        try:
            request = urllib.request.Request(record["url"], headers={"User-Agent": "VirgosMC-ReleaseBuilder/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response:
                data = response.read()
            actual = hashlib.new(algorithm, data).hexdigest()
            if actual != expected:
                raise ValueError(f"Hash mismatch: {name}")
            temporary = target.with_name(target.name + ".partial")
            temporary.write_bytes(data)
            temporary.replace(target)
            print(f"Fetched {name}", flush=True)
            return
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def main() -> None:
    lock = json.loads((ROOT / "pack/mods.lock.json").read_text(encoding="utf-8"))
    downloads = ROOT / ".cache/pack/downloads"
    client = [a for a in lock["artifacts"] if "client" in a["sides"] and a["mode"] != "tool"]
    client_targets = [(record, downloads / record["filename"]) for record in client]
    runtime = json.loads((ROOT / "pack/client-runtime.lock.json").read_text(encoding="utf-8"))
    runtime_targets = [
        (runtime["java"], ROOT / ".cache" / runtime["java"]["file"]),
        (runtime["forge"], ROOT / ".cache/pack" / runtime["forge"]["file"]),
    ]
    optional = dh_targets(ROOT)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        if not optional:
            list(pool.map(lambda pair: fetch(*pair), client_targets + runtime_targets))
        else:
            # Verify duplicate target digests serially instead of racing .partial writes.
            groups = {}
            for record, target in client_targets + runtime_targets + optional:
                groups.setdefault(target, []).append(record)
            def fetch_group(pair):
                target, records = pair
                for record in records: fetch(record, target)
            list(pool.map(fetch_group, groups.items()))
    print(json.dumps({"clientArtifacts": len(client), "runtime": "verified"}))


if __name__ == "__main__":
    main()
