"""Fetch exact Create addon inputs, then prepare verified per-variant laboratory overlays."""
import argparse
import json
from pathlib import Path
from create_addons_lab import artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    fetch = sub.add_parser('fetch', help='Verify and download exactly the three pinned addon JARs')
    fetch.add_argument('--output-root', required=True)
    fetch.add_argument('--base-lock', default=str(Path(__file__).resolve().parents[1] / 'pack/mods.lock.json'))
    variants = sub.add_parser('variants', help='Copy a verified DH/compat/QA base plus selected addons')
    variants.add_argument('--output-root', required=True)
    variants.add_argument('--base-artifacts', required=True)
    variants.add_argument('--client-source', required=True)
    args = parser.parse_args()
    try:
        if args.operation == 'fetch':
            report = artifacts.fetch(args.output_root, args.base_lock)
            result = {name: {'filename': row['filename'], 'sha256': row['sha256']}
                      for name, row in report['addons'].items()}
        else:
            result = artifacts.variants(args.output_root, args.base_artifacts, args.client_source)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, 'Addon preparation refused: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
