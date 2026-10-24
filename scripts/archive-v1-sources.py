"""Archive the v1 maintenance sources and fixed local build inputs, without worlds.

This private archive complements backups/full; it is not a client distribution.
Only explicit project trees and build inputs are admitted, never all of .cache.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
files = set()

def include(path):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Path outside project: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    files.add(path)

for name in ("scripts", "templates", "pack", "docs", "dev/virgos-core/src",
             "dev/virgos-core/gradle", "dev/playit-udp-fix"):
    for path in (ROOT / name).rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            include(path)
for path in (ROOT / "dev/virgos-core").iterdir():
    if path.is_file():
        include(path)
for path in ROOT.glob("*.bat"):
    include(path)
for name in ("README.md", "versions.lock.json",
             "dist/release.json", "dist/Virgos-MC-1.0.0-instalar.zip",
             "dist/Virgos-MC-1.0.0.mrpack",
             "dev/virgos-core/build/libs/virgos_core-1.0.0.jar",
             ".cache/playit_companion-forge-0.1.2.jar",
             ".cache/v02/voicechat-forge-1.20.1-2.6.24.jar"):
    include(ROOT / name)
for module in ("asm", "asm-tree"):
    matches = list((ROOT / f".cache/gradle/caches/modules-2/files-2.1/org.ow2.asm/{module}/9.9.1").rglob("*.jar"))
    if len(matches) != 1:
        raise ValueError(f"Expected one pinned {module} input, found {len(matches)}")
    include(matches[0])
for name in ("audit-v1-final.json", "public-v1.json", "recipe-sync-v1-public.json",
             "installer-v3-unit.json", "installer-v1-repair.json", "v1-final-config.json",
             "v1-class-equivalence.json", "core-v1-checks.txt", "restore-runtime-verification.json",
             "checkpoint-v1.json", "backup-concurrency-v1.json", "auth-registration-v1.json",
             "v1-release-final.json", "playit-rebuild-v1.json"):
    include(ROOT / ".lab/reports" / name)

now = datetime.now(timezone.utc)
dest = ROOT / "backups" / f"virgos-v1-fuentes-{now:%Y%m%d-%H%M%S-%f}.zip"
manifest = {"version": "1.0.0", "created": now.isoformat(),
            "scope": "Private maintenance sources, fixed local build inputs and release evidence. No worlds or live accounts; requires a separate verified full backup.",
            "files": []}
with zipfile.ZipFile(dest, "x", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        data = path.read_bytes()
        name = path.relative_to(ROOT).as_posix()
        archive.writestr(name, data)
        manifest["files"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    archive.writestr("sources-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
with zipfile.ZipFile(dest) as archive:
    assert archive.testzip() is None
    for item in manifest["files"]:
        data = archive.read(item["path"])
        assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
report = {"passed": True, "created": now.isoformat(), "archive": str(dest),
          "verifiedFiles": len(files), "bytes": dest.stat().st_size,
          "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
(ROOT / ".lab/reports/v1-source-archive.json").write_text(json.dumps(report, indent=2) + "\n", "utf-8")
print(json.dumps(report))
