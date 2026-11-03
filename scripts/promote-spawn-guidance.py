"""Queue the versioned spawn signage/tutorial plan through the managed runner.

The command is deliberately confirmation-gated: it mutates only the live
server world after a caller names a verified backup and demonstrates that no
players are online. It does not rebuild Bastion geometry or invent rewards.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".runtime" / "active-run.json"
COMMANDS = ROOT / ".runtime" / "public-commands.txt"
LOG = ROOT / ".runtime" / "public-console.log"
PLAN = ROOT / "pack" / "spawn" / "signage-plan.json"
REPORT_DIR = ROOT / ".runtime" / "spawn-promotion"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def queue(command: str) -> None:
    with COMMANDS.open("a", encoding="utf-8") as handle:
        handle.write(command + "\n")


def sign_messages(lines: list[str]) -> str:
    messages = list(lines[:4]) + [""] * (4 - len(lines[:4]))
    # Sign text is an SNBT list of single-quoted JSON strings. Using JSON's
    # default `\\uXXXX` escaping makes Minecraft reject the entire merge.
    encoded = []
    for line in messages:
        payload = json.dumps({"text": line}, ensure_ascii=False, separators=(",", ":"))
        encoded.append("'" + payload.replace("'", "\\'") + "'")
    return "[" + ",".join(encoded) + "]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", required=True, help="Ruta relativa a un backup verificado")
    parser.add_argument("--label", default="v5-guidance")
    parser.add_argument("--confirm", action="store_true", help="Confirma la mutación del mundo público")
    args = parser.parse_args()
    if not args.confirm:
        parser.error("agregá --confirm para promover la señalización al mundo público")
    backup = (ROOT / args.backup).resolve()
    if not backup.is_file() or backup.suffix.lower() != ".zip":
        raise SystemExit("--backup debe apuntar a un ZIP de backup existente")
    if not STATE.exists():
        raise SystemExit("No existe .runtime/active-run.json; iniciá el servidor con el runner gestionado.")
    state = read_json(STATE)
    if state.get("mode") != "managed" or state.get("finished") or not state.get("pid"):
        raise SystemExit("El servidor no está activo mediante el runner gestionado.")
    plan = read_json(PLAN)
    if plan.get("schema") != 1 or not plan.get("stations"):
        raise SystemExit("signage-plan.json no tiene un esquema de estaciones válido")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    offset = len(LOG.read_text(encoding="utf-8", errors="replace")) if LOG.exists() else 0
    queue("list")
    evidence = ""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        evidence = LOG.read_text(encoding="utf-8", errors="replace")[offset:] if LOG.exists() else ""
        if re.search(r"There are \d+ of a max of \d+ players online", evidence):
            break
        time.sleep(0.25)
    if not re.search(r"There are 0 of a max of \d+ players online", evidence):
        raise SystemExit("No se pudo demostrar que no hay jugadores conectados; no se promovió el spawn.")

    commands: list[str] = ["save-all flush"]
    for station in plan["stations"]:
        x, y, z = station["position"]
        title = station["title"]
        lines = [title, *station["lines"]]
        commands.append(f"setblock {x} {y} {z} minecraft:spruce_sign[rotation=0,waterlogged=false]")
        commands.append(
            f"data merge block {x} {y} {z} "
            f"{{front_text:{{messages:{sign_messages(lines)},color:\"black\",has_glowing_text:0b}},is_waxed:1b}}"
        )
    for command in commands:
        queue(command)
        time.sleep(0.05)

    report = {
        "schema": 1,
        "label": args.label,
        "backup": str(backup.relative_to(ROOT)),
        "plan": str(PLAN.relative_to(ROOT)),
        "stations": len(plan["stations"]),
        "startedUtc": started.isoformat(),
        "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "commands": commands,
        "result": "queued",
    }
    output = REPORT_DIR / f"{started.strftime('%Y%m%d-%H%M%S')}-{args.label}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
