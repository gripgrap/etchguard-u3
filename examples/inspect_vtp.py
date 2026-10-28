"""Read-only external fixture inspection; output must be outside the source."""
import argparse
import json
from pathlib import Path

from etchguard.adapters.viennaps import inspect_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--expected-fingerprint', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--material-id', type=int, default=10)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root, output = Path(args.directory).resolve(), Path(args.output).resolve()
    if output == root or root in output.parents:
        parser.error('output must be outside the source directory')
    if output.exists():
        parser.error('refusing to overwrite inspection output')
    try:
        run = inspect_run(root, args.expected_fingerprint, material_id=args.material_id,
                          source_revision=args.source_revision)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as f:
            json.dump(run, f, indent=2, allow_nan=False)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'BLOCK: {exc}\n')
    print(f'Inspected {len(run["snapshots"])} snapshots; source authenticity not certified: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
