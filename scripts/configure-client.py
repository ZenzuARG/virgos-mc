"""Generate managed first-launch controls without accessing a staging installation."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply_defaults(text, policy):
    updates = {"key_" + name: row["key"] for name, row in policy["bindings"].items()}
    lines = text.splitlines()
    seen = set()
    for index, line in enumerate(lines):
        name = line.split(":", 1)[0]
        if name in updates:
            if name in seen:
                raise ValueError("Duplicate managed control: " + name)
            lines[index] = name + ":" + updates[name]
            seen.add(name)
    lines.extend(name + ":" + value for name, value in updates.items() if name not in seen)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = ROOT / "pack/client-overrides/config/defaultoptions/options.txt"
    parser.add_argument("--input", type=Path, default=defaults, help="Source options fixture/defaults (default: tracked first-launch options)")
    parser.add_argument("--output", type=Path, default=defaults, help="Generated options destination (default: tracked first-launch options; never a live instance)")
    parser.add_argument("--policy", type=Path, default=ROOT / "pack/keybindings.json")
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    result = apply_defaults(args.input.read_text(encoding="utf-8"), policy)
    args.output.write_text(result, encoding="utf-8")
    print("Managed first-launch controls generated:", len(policy["bindings"]))


if __name__ == "__main__":
    main()
