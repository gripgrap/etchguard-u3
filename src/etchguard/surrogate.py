"""Small polynomial ridge profile model; not an FNO/MGN or physical model."""
import hashlib
import json
import math

from .contracts import RECIPE_KEYS, validate_profile, validate_recipe, validate_run


def resample_profile(points, n_points=64):
    if type(n_points) is not int or n_points < 2 or validate_profile(points):
        raise ValueError('valid profile and at least two sample points required')
    lengths = [math.dist(a,b) for a,b in zip(points,points[1:])]
    total = sum(lengths)
    if not math.isfinite(total) or total <= 0:
        raise ValueError('invalid profile arc length')
    output, segment, accumulated = [], 0, 0.
    for i in range(n_points):
        target = total*i/(n_points-1)
        while segment < len(lengths)-1 and accumulated+lengths[segment] < target:
            accumulated += lengths[segment]; segment += 1
        fraction = min(1., max(0., (target-accumulated)/lengths[segment]))
        a,b = points[segment:segment+2]
        output.append([a[j]+fraction*(b[j]-a[j]) for j in range(2)])
    output[0],output[-1] = list(points[0]),list(points[-1])
    return output


def validate_splits(splits):
    ids, recipes, times = set(), set(), set()
    for split in ('train','val','test'):
        if not splits.get(split):
            raise ValueError(f'{split} split empty')
        for run in splits[split]:
            issues = validate_run(run)
            if issues: raise ValueError(str(issues))
            identity = tuple(run['recipe'][k] for k in RECIPE_KEYS)
            if identity in recipes: raise ValueError('recipe overlap across/within splits')
            if run['run_id'] in ids: raise ValueError('run ID overlap across/within splits')
            recipes.add(identity); ids.add(run['run_id'])
            times.add(run['snapshots'][-1]['t_seconds'])
    if len(times) != 1: raise ValueError('final evaluation time mismatch')


def _features(values):
    return [1., *values, *(a*a for a in values),
            *(values[i]*values[j] for i in range(len(values)) for j in range(i+1,len(values)))]


class RidgeProfileModel:
    def __init__(self, document):
        if (not isinstance(document, dict) or document.get('schema') != 1
                or document.get('model') != 'quadratic_ridge_profile'
                or document.get('recipe_keys') != list(RECIPE_KEYS)):
            raise ValueError('unsupported ridge model format')
        finite = lambda v: type(v) in (int,float) and math.isfinite(v)
        n = document.get('n_points')
        if type(n) is not int or n < 2:
            raise ValueError('invalid model point count')
        for field in ('mean','std'):
            values = document.get(field)
            if (not isinstance(values,list) or len(values) != len(RECIPE_KEYS)
                    or not all(finite(v) and (field != 'std' or v > 0) for v in values)):
                raise ValueError('invalid training normalization')
        weights = document.get('weights')
        if (not isinstance(weights,list) or len(weights) != len(_features([0.]*len(RECIPE_KEYS)))
                or any(not isinstance(row,list) or len(row) != 2*n or not all(finite(v) for v in row)
                       for row in weights)):
            raise ValueError('invalid model coefficient dimensions')
        ids = document.get('train_ids')
        if (not isinstance(ids,list) or not ids or any(not isinstance(i,str) or not i for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError('invalid training identities')
        if not finite(document.get('alpha')) or document['alpha'] <= 0:
            raise ValueError('invalid model alpha')
        if not finite(document.get('evaluation_time_seconds')) or document['evaluation_time_seconds'] < 0:
            raise ValueError('invalid model evaluation time')
        self.document = json.loads(json.dumps(document,allow_nan=False))

    @classmethod
    def fit(cls, train_runs, *, alpha, n_points=64):
        import numpy as np
        if not train_runs or type(alpha) not in (int,float) or not math.isfinite(alpha) or alpha <= 0:
            raise ValueError('nonempty training set and finite positive alpha required')
        for run in train_runs:
            issues = validate_run(run)
            if issues: raise ValueError(str(issues))
        if len({r['snapshots'][-1]['t_seconds'] for r in train_runs}) != 1:
            raise ValueError('training time mismatch')
        x = np.array([[r['recipe'][k] for k in RECIPE_KEYS] for r in train_runs],dtype=float)
        mean,std = x.mean(axis=0),x.std(axis=0)
        std[std < 1e-12] = 1.
        features = np.array([_features(z) for z in (x-mean)/std])
        targets = np.array([resample_profile(r['snapshots'][-1]['points_um'],n_points)
                            for r in train_runs]).reshape(len(train_runs),-1)
        penalty = np.eye(features.shape[1])*alpha
        penalty[0,0] = 0.
        weights = np.linalg.solve(features.T@features+penalty, features.T@targets)
        if not np.isfinite(weights).all(): raise ValueError('nonfinite model coefficients')
        train_bytes = json.dumps(train_runs,sort_keys=True,allow_nan=False).encode()
        return cls({'schema':1,'model':'quadratic_ridge_profile','alpha':alpha,'n_points':n_points,
            'recipe_keys':list(RECIPE_KEYS),'mean':mean.tolist(),'std':std.tolist(),
            'weights':weights.tolist(),'train_ids':[r['run_id'] for r in train_runs],
            'training_sha256':hashlib.sha256(train_bytes).hexdigest(),
            'evaluation_time_seconds':train_runs[0]['snapshots'][-1]['t_seconds']})

    @classmethod
    def from_dict(cls, document):
        return cls(document)

    def to_dict(self):
        return json.loads(json.dumps(self.document,allow_nan=False))

    def predict(self, recipe):
        issues = validate_recipe(recipe)
        if issues: raise ValueError(str(issues))
        d = self.document
        z = [(recipe[k]-d['mean'][i])/d['std'][i] for i,k in enumerate(RECIPE_KEYS)]
        values = _features(z)
        flat = [sum(v*row[j] for v,row in zip(values,d['weights']))
                for j in range(d['n_points']*2)]
        profile = [flat[i:i+2] for i in range(0,len(flat),2)]
        issues = validate_profile(profile)
        if issues: raise ValueError(str(issues))
        return profile
