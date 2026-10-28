"""Synthetic walkthrough: external fingerprint -> PASS -> disk mutation -> BLOCK."""
import argparse
import json
from pathlib import Path

from etchguard.demo import generate
from etchguard.integrity import freeze
from etchguard.registry import Registry
from etchguard.workflow import run_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    bundle = generate(output / 'bundle')
    policy = dict(evaluation_time_seconds=15, max_chamfer_um=.15,
                  max_depth_mae_um=.15, max_regression_ratio=1.1)
    (bundle / 'policy.json').write_text(json.dumps(policy, indent=2), encoding='utf-8')
    expected = freeze(bundle)['content_fingerprint']
    (output / 'expected-fingerprint.txt').write_text(expected+'\n', encoding='utf-8')
    registry = Registry(output / 'registry')
    good = run_bundle(bundle, expected, registry, 'baseline-v1')
    before = (registry.root / 'current.json').read_bytes()
    changed = bundle / 'golden/golden-0000.json'
    changed.write_bytes(changed.read_bytes()+b' ')
    bad = run_bundle(bundle, expected, registry, 'changed-data-candidate')
    unchanged = before == (registry.root / 'current.json').read_bytes()
    summary = {'source_type': 'synthetic_fixture', 'baseline_exit': good['decision']['exit_code'],
               'changed_data_exit': bad['decision']['exit_code'], 'champion_unchanged': unchanged}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0 if summary == dict(source_type='synthetic_fixture', baseline_exit=0,
                                changed_data_exit=2, champion_unchanged=True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
