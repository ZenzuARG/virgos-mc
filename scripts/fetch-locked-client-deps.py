"""Download and hash-verify the locked client dependencies for a clean release build."""
from __future__ import annotations

import hashlib
import json
import concurrent.futures
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda pair: fetch(*pair), client_targets + runtime_targets))
    print(json.dumps({"clientArtifacts": len(client), "runtime": "verified"}))


if __name__ == "__main__":
    main()
