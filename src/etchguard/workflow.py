"""Verified, fixed-time nearest-recipe evaluation. Not a general model release API.

Caller must retain the expected bundle fingerprint outside the artifact root.
Input bytes are captured and checked before parsing; outputs live outside it.
Single-writer workflow only: no distributed locks or hostile filesystem guarantee.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from .contracts import RECIPE_KEYS, validate_run
from .gate import GateDecision, evaluate_candidate
from .integrity import verify
from .model import NearestRecipeBaseline


def _digest(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def _capture(root, expected):
    manifest = verify(root)
    if manifest['content_fingerprint'] != expected:
        raise ValueError('bundle differs from external fingerprint')
    captured = {}
    for row in manifest['files']:
        raw = (root / row['path']).read_bytes()
        if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('file changed during capture')
        captured[row['path']] = raw
    return captured


def _load_split(captured, name, time_seconds):
    runs = []
    for path, raw in captured.items():
        p = Path(path)
        if p.parent.as_posix() != name or p.suffix != '.json':
            continue
        run = json.loads(raw)
        problems = validate_run(run)
        if problems:
            raise ValueError(f'{path}: {problems}')
        if run['snapshots'][-1]['t_seconds'] != time_seconds:
            raise ValueError(f'{path}: final time differs from evaluation time')
        runs.append(run)
    if not runs:
        raise ValueError(f'{name} split empty')
    return runs


def _split_guard(train, golden):
    # Python numeric equality treats 1 and 1.0 identically without lossy rounding.
    identity = lambda r: tuple(r['recipe'][k] for k in RECIPE_KEYS)
    if {r['run_id'] for r in train} & {r['run_id'] for r in golden}:
        raise ValueError('run_id overlap between train and golden')
    if {identity(r) for r in train} & {identity(r) for r in golden}:
        raise ValueError('recipe overlap between train and golden')
    for split in (train, golden):
        if len({r['run_id'] for r in split}) != len(split):
            raise ValueError('duplicate run_id within split')
        if len({identity(r) for r in split}) != len(split):
            raise ValueError('duplicate recipe within split')


def evaluate_bundle(directory, expected_fingerprint):
    """Return serializable evidence; do not write or silently re-freeze inputs."""
    root = Path(directory).resolve()
    evidence = {'schema': 1, 'bundle_fingerprint': expected_fingerprint,
                'model': 'nearest-recipe-baseline', 'scope': 'research_fixed_time_baseline'}
    stage = 'input'
    try:
        captured = _capture(root, expected_fingerprint)
        policy = json.loads(captured['policy.json'])
        if not isinstance(policy, dict):
            raise ValueError('policy must be an object')
        for key in ('evaluation_time_seconds', 'max_chamfer_um',
                    'max_depth_mae_um', 'max_regression_ratio'):
            value = policy[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{key} must be finite and nonnegative')
        if policy['max_regression_ratio'] < 1:
            raise ValueError('max_regression_ratio must be >= 1')
        t = policy['evaluation_time_seconds']
        train = _load_split(captured, 'train', t)
        golden = _load_split(captured, 'golden', t)
        _split_guard(train, golden)
        evidence.update(policy_digest=_digest(policy), evaluation_time_seconds=t,
                        n_train=len(train), n_golden=len(golden),
                        source_types=sorted({r['provenance']['source_type'] for r in train+golden}))
        model = NearestRecipeBaseline(train)
        # Descriptor ties this baseline to its implementation and captured training bytes.
        evidence['model_digest'] = _digest({
            'implementation_sha256': hashlib.sha256(Path(__file__).with_name('model.py').read_bytes()).hexdigest(),
            'training_files': {p: hashlib.sha256(b).hexdigest() for p, b in captured.items()
                               if Path(p).parent.as_posix() == 'train'},
        })
        stage = 'prediction'
        decision = evaluate_candidate(model, golden,
            max_chamfer_um=policy['max_chamfer_um'],
            max_depth_mae_um=policy['max_depth_mae_um'],
            max_regression_ratio=policy['max_regression_ratio'],
            expected_fingerprint=expected_fingerprint, actual_fingerprint=expected_fingerprint)
        stage = 'input'
        if verify(root)['content_fingerprint'] != expected_fingerprint:
            raise ValueError('bundle changed during evaluation')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError,
            IndexError, OverflowError) as exc:
        code = 1 if stage == 'prediction' else 2
        decision = GateDecision(False, code, [f'{stage}: {exc}'], {}, {})
    evidence['decision'] = decision.as_dict()
    evidence['evidence_digest'] = _digest(evidence)
    return evidence


def run_bundle(directory, expected_fingerprint, registry, model_id):
    """Persist evidence in history before champion update. Single writer required.

    This version builds the same deterministic baseline each time. It does not
    compare unrelated stored champion scores or accept arbitrary checkpoints.
    """
    root = Path(directory).resolve()
    output = registry.root.resolve()
    if output == root or root in output.parents:
        raise ValueError('registry must be outside the verified bundle')
    evidence = evaluate_bundle(root, expected_fingerprint)
    d = evidence['decision']
    registry.submit(model_id, GateDecision(**d), fingerprint=expected_fingerprint,
                    evidence=evidence)
    return evidence
