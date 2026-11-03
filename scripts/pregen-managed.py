"""Run a bounded, operator-confirmed Chunky job through the managed runner."""
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
REPORT_DIR = ROOT / ".runtime" / "pregen"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def send(command: str) -> None:
    with COMMANDS.open("a", encoding="utf-8") as handle:
        handle.write(command + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True, help="Chunky world id, e.g. minecraft:overworld")
    parser.add_argument("--center", nargs=2, type=int, metavar=("X", "Z"), required=True)
    parser.add_argument("--radius", type=int, required=True)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--label", required=True)
    parser.add_argument("--confirm", action="store_true", help="Required because this queues a production world mutation")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", args.world):
        parser.error("--world debe ser un identificador namespaced válido")
    if args.radius < 64 or args.radius > 4096:
        parser.error("--radius debe estar entre 64 y 4096 bloques")
    if args.seconds < 60 or args.seconds > 3600:
        parser.error("--seconds debe estar entre 60 y 3600")
    if not args.confirm:
        parser.error("agregá --confirm para iniciar una tarea de Chunky")
    if not STATE.exists():
        raise SystemExit("No existe .runtime/active-run.json; iniciá el servidor con el runner gestionado.")
    state = read_json(STATE)
    if state.get("mode") != "managed" or state.get("finished") or not state.get("pid"):
        raise SystemExit("El servidor no está activo mediante el runner gestionado.")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    log_offset = len(LOG.read_text(encoding="utf-8", errors="replace")) if LOG.exists() else 0
    send("list")
    initial = ""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        initial = LOG.read_text(encoding="utf-8", errors="replace")[log_offset:] if LOG.exists() else ""
        if re.search(r"There are \d+ of a max of \d+ players online", initial):
            break
        time.sleep(0.25)
    if not re.search(r"There are 0 of a max of \d+ players online", initial):
        raise SystemExit("No se pudo demostrar que no hay jugadores conectados; no se inició Chunky.")
    x, z = args.center
    commands = [
        f"chunky world {args.world}",
        f"chunky center {x} {z}",
        "chunky shape circle",
        f"chunky radius {args.radius}",
        "chunky start",
    ]
    for command in commands:
        send(command)
        time.sleep(0.35)
    deadline = time.monotonic() + args.seconds
    result = "time_budget"
    while time.monotonic() < deadline:
        text = LOG.read_text(encoding="utf-8", errors="replace")[log_offset:] if LOG.exists() else ""
        if re.search(r"joined the game|There are [1-9]\d* of a max", text):
            send("chunky pause")
            result = "paused_for_player"
            break
        if re.search(r"Task finished|Task completed", text):
            result = "complete"
            break
        time.sleep(5)
    else:
        send("chunky pause")
    text = LOG.read_text(encoding="utf-8", errors="replace")[log_offset:] if LOG.exists() else ""
    report = {
        "schema": 1,
        "label": args.label,
        "world": args.world,
        "center": [x, z],
        "radius": args.radius,
        "shape": "circle",
        "startedUtc": started.isoformat(),
        "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "secondsBudget": args.seconds,
        "commands": commands,
        "result": result,
        "chunkyLog": [line for line in text.splitlines() if "[Chunky]" in line][-80:],
    }
    output = REPORT_DIR / f"{started.strftime('%Y%m%d-%H%M%S')}-{args.label}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
