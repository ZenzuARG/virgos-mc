"""Download and hash-verify the locked client dependencies for a clean release build."""
from __future__ import annotations

import hashlib
import json
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
    request = urllib.request.Request(record["url"], headers={"User-Agent": "VirgosMC-ReleaseBuilder/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        data = response.read()
    actual = hashlib.new(algorithm, data).hexdigest()
    if actual != expected:
        raise SystemExit(f"Hash mismatch: {name}")
    temporary = target.with_name(target.name + ".partial")
    temporary.write_bytes(data)
    temporary.replace(target)


def main() -> None:
    lock = json.loads((ROOT / "pack/mods.lock.json").read_text(encoding="utf-8"))
    downloads = ROOT / ".cache/pack/downloads"
    client = [a for a in lock["artifacts"] if "client" in a["sides"] and a["mode"] != "tool"]
    for record in client:
        fetch(record, downloads / record["filename"])
    runtime = json.loads((ROOT / "pack/client-runtime.lock.json").read_text(encoding="utf-8"))
    fetch(runtime["java"], ROOT / ".cache" / runtime["java"]["file"])
    fetch(runtime["forge"], ROOT / ".cache/pack" / runtime["forge"]["file"])
    print(json.dumps({"clientArtifacts": len(client), "runtime": "verified"}))


if __name__ == "__main__":
    main()
