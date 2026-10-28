"""Verify preserved raw/artifacts and replay predictions without fitting a model."""
import argparse
import hashlib
import json
from pathlib import Path

from etchguard.integrity import freeze, manifest_for, verify
from etchguard.metrics import score_pairs
from etchguard.surrogate import RidgeProfileModel, validate_splits


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--record', required=True)
    args=parser.parse_args()
    root=Path(args.directory)
    read=lambda p:json.loads((root/p).read_text())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    summary,started,selection,design=map(read,['summary.json','started.json','selection.json','design.json'])
    if sha(root/'plan.json')!=started['plan_sha256']:
        raise ValueError('original plan hash mismatch')
    completed=[]
    for group in ('pilot','dataset'):
        for folder in sorted((root/group).iterdir()):
            if not folder.is_dir(): continue
            source=json.loads((folder/'source-manifest.json').read_text())
            execution=json.loads((folder/'execution.json').read_text())
            if (manifest_for(folder/'raw')!=source or sha(folder/'request.json')!=execution['request_sha256']
                    or source['content_fingerprint']!=execution['source_fingerprint']):
                raise ValueError(f'case integrity mismatch: {folder}')
            completed.append(str(folder.relative_to(root)))
    if len(completed)!=33: raise ValueError('expected 9 pilot and 24 dataset cases')
    runs={r['run_id']:r for r in read('normalized-runs.json')}
    splits={k:[runs[i] for i in ids] for k,ids in design['splits'].items()}
    validate_splits(splits)
    chosen=selection['chosen']
    model_path=Path(chosen['artifact'])
    if sha(model_path)!=summary['model_artifact_sha256']:
        raise ValueError('selected model changed')
    model=RidgeProfileModel.from_dict(json.loads(model_path.read_text()))
    training_digest=hashlib.sha256(json.dumps(splits['train'],sort_keys=True,allow_nan=False).encode()).hexdigest()
    if training_digest!=model.to_dict()['training_sha256']:
        raise ValueError('training records mismatch')
    if model.to_dict()['train_ids']!=design['splits']['train']:
        raise ValueError('model train identities mismatch')
    pairs=[(model.predict(r['recipe']),r['snapshots'][-1]['points_um']) for r in splits['test']]
    replay=score_pairs(pairs)
    differences={k:abs(replay[k]-summary['test']['ridge']['metrics'][k]) for k in replay}
    if max(differences.values())>1e-12: raise ValueError('saved model replay changed metrics')
    evidence_path=root/'manifest.sha256.json'
    sealed=verify(root) if evidence_path.exists() else freeze(root)
    record={'status':'VERIFIED','verified_cases':len(completed),'refit_performed':False,
            'model_sha256':sha(model_path),'metric_differences':differences,
            'study_fingerprint':sealed['content_fingerprint'],
            'note':'post-run verification of preserved artifacts; original controller ended without final manifest'}
    target=Path(args.record)
    if target.resolve()==root.resolve() or root.resolve() in target.resolve().parents:
        raise ValueError('verification record must be outside study directory')
    with target.open('x') as stream: json.dump(record,stream,indent=2)
    print(json.dumps(record,indent=2))


if __name__=='__main__': main()
