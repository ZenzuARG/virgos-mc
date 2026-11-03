"""Capture a bounded, scenario-labelled spark performance audit from the managed server.

The script never changes server.properties or starts the server. It only queues
read-only spark commands when the managed runner is live and records the exact
scenario, fixed distance settings, and log evidence in .runtime/.
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
REPORT_DIR = ROOT / ".runtime" / "performance-audit"

SCENARIOS = {
    "exploration": "Exploración controlada; recorrer una ruta marcada sin cargar una fábrica.",
    "create": "Fábrica grande de Create; operar la instalación más pesada disponible.",
    "multiplayer": "Varios jugadores; reproducir actividad normal con el grupo de prueba.",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def server_distances() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in (ROOT / "server.properties").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(view-distance|simulation-distance)=(\d+)$", line)
        if match:
            values[match.group(1)] = int(match.group(2))
    return values


def queue(command: str) -> None:
    with COMMANDS.open("a", encoding="utf-8") as handle:
        handle.write(command + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--label", default="", help="Optional operator note included in the report")
    args = parser.parse_args()
    if args.seconds < 15 or args.seconds > 900:
        parser.error("--seconds debe estar entre 15 y 900")
    distances = server_distances()
    if distances != {"view-distance": 8, "simulation-distance": 6}:
        raise SystemExit(
            "Abortado: la auditoría exige view-distance=8 y simulation-distance=6; "
            f"se observó {distances!r}."
        )
    if not STATE.exists():
        raise SystemExit("No existe .runtime/active-run.json; iniciá el servidor con el runner gestionado.")
    state = read_json(STATE)
    if state.get("mode") != "managed" or state.get("finished") or not state.get("pid"):
        raise SystemExit("El servidor no está activo mediante el runner gestionado.")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    log_offset = len(LOG.read_text(encoding="utf-8", errors="replace")) if LOG.exists() else 0
    commands = [
        "spark health --memory",
        "spark tps",
        f"spark profiler start --timeout {args.seconds} --comment virgos-{args.scenario}",
    ]
    for command in commands:
        queue(command)
        time.sleep(0.25)
    deadline = time.monotonic() + args.seconds + 45
    while time.monotonic() < deadline:
        if not STATE.exists():
            break
        current = read_json(STATE)
        if current.get("finished"):
            break
        time.sleep(5)
    log_text = LOG.read_text(encoding="utf-8", errors="replace") if LOG.exists() else ""
    evidence = log_text[log_offset:]
    report = {
        "schema": 1,
        "scenario": args.scenario,
        "description": SCENARIOS[args.scenario],
        "operatorLabel": args.label,
        "startedUtc": started_at.isoformat(),
        "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": args.seconds,
        "serverDistances": distances,
        "commands": commands,
        "logEvidence": [line for line in evidence.splitlines() if "[spark]" in line.lower() or "tps" in line.lower() or "profiler" in line.lower()][-80:],
        "status": read_json(STATE) if STATE.exists() else {"missing": True},
        "operatorResult": "complete_when_profile_link_or_saved_file_is_reviewed",
    }
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    output = REPORT_DIR / f"{stamp}-{args.scenario}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
