"""Evaluate sealed reference/prediction files, without authorizing promotion."""
import hashlib
import json
import math
import re
from pathlib import Path

from .contracts import RECIPE_KEYS, validate_run
from .integrity import verify
from .metrics import score_pairs
from .workflow import _capture


def evaluate_prediction_bundle(directory, expected_fingerprint):
    root = Path(directory).resolve()
    result = {'schema': 1, 'scope': 'prediction_file_evaluation_only',
              'promotion_authorized': False, 'model_artifact_verified': False,
              'bundle_fingerprint': expected_fingerprint, 'metrics': {}, 'reasons': []}
    stage = 'input'
    try:
        captured = _capture(root, expected_fingerprint)
        reference = json.loads(captured['reference.json'])
        prediction = json.loads(captured['prediction.json'])
        policy = json.loads(captured['policy.json'])
        problems = validate_run(reference)
        if problems:
            raise ValueError(f'invalid reference: {problems}')
        if not isinstance(prediction, dict) or not isinstance(policy, dict):
            raise ValueError('prediction and policy must be objects')
        for k in ('max_chamfer_um', 'max_depth_mae_um', 'max_chamfer_per_snapshot_um'):
            value = policy[k]
            if type(value) not in (int,float) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{k} must be finite and nonnegative')
        model = prediction['model']
        if (not isinstance(model, dict) or not isinstance(model.get('id'), str) or not model['id']
                or model.get('kind') not in {'model','baseline','oracle','fault_injection'}
                or not re.fullmatch('[0-9a-f]{64}', model.get('artifact_sha256', ''))):
            raise ValueError('model id, kind and artifact SHA256 required')
        if prediction['run_id'] != reference['run_id']:
            raise ValueError('run_id mismatch')
        if (set(prediction['recipe']) != set(RECIPE_KEYS)
                or any(prediction['recipe'][k] != reference['recipe'][k] for k in RECIPE_KEYS)):
            raise ValueError('recipe mismatch')
        for k in ('content_fingerprint', 'time_basis'):
            value = reference['provenance'].get(k)
            if not isinstance(value, str) or not value or prediction['provenance'].get(k) != value:
                raise ValueError(f'{k} mismatch or missing')
        a, b = reference['snapshots'], prediction['snapshots']
        if len(a) != len(b) or any(x['t_seconds'] != y['t_seconds'] for x,y in zip(a,b)):
            raise ValueError('snapshot times/count mismatch')
        requested = policy.get('evaluation_times_seconds', [s['t_seconds'] for s in a])
        if (not isinstance(requested, list) or not requested
                or any(type(t) not in (int,float) or not math.isfinite(t) or t < 0 for t in requested)
                or len(set(requested)) != len(requested)
                or not set(requested).issubset({s['t_seconds'] for s in a})):
            raise ValueError('requested evaluation times must be unique and present in reference')
        result.update(model={k: model[k] for k in ('id','kind','artifact_sha256')}, reference_source_type=reference['provenance']['source_type'],
                      time_basis=reference['provenance']['time_basis'],
                      files_sha256={k: hashlib.sha256(v).hexdigest() for k,v in captured.items()})
        stage = 'prediction'
        problems = validate_run(prediction)
        if problems:
            raise ValueError(f'invalid prediction: {problems}')
        selected = [(x,y) for x,y in zip(a,b) if x['t_seconds'] in requested]
        pairs = [(y['points_um'],x['points_um']) for x,y in selected]
        result['evaluated_times_seconds'] = [x['t_seconds'] for x,y in selected]
        metrics = score_pairs(pairs)
        if not all(math.isfinite(v) for v in metrics.values()):
            raise ValueError('nonfinite evaluation metric')
        result['metrics'] = metrics
        result['per_snapshot'] = [dict(t_seconds=x['t_seconds'], **score_pairs([pair]))
                                  for (x,y),pair in zip(selected,pairs)]
        if metrics['chamfer_mean_um'] > policy['max_chamfer_um']:
            result['reasons'].append('mean Chamfer exceeds policy')
        if metrics['depth_mae_um'] > policy['max_depth_mae_um']:
            result['reasons'].append('depth MAE exceeds policy')
        if metrics['max_chamfer_um'] > policy['max_chamfer_per_snapshot_um']:
            result['reasons'].append('per-snapshot Chamfer exceeds policy')
        stage = 'input'
        if verify(root)['content_fingerprint'] != expected_fingerprint:
            raise ValueError('bundle changed during evaluation')
        result['exit_code'] = 1 if result['reasons'] else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError) as exc:
        result['exit_code'] = 1 if stage == 'prediction' else 2
        result['reasons'].append(f'{stage}: {exc}')
    result['decision'] = 'PASS' if result['exit_code'] == 0 else 'BLOCK'
    result['evidence_digest'] = hashlib.sha256(json.dumps(result, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return result
