import copy
import importlib.util
import unittest

from etchguard.contracts import RECIPE_KEYS
from etchguard.surrogate import resample_profile, validate_splits, RidgeProfileModel


def run(ident, flux):
    return {'run_id': ident, 'recipe': {k: flux if k=='ion_flux' else 1. for k in RECIPE_KEYS},
            'provenance': {'source_type':'synthetic_fixture','version':'analytic-test'},
            'snapshots': [{'t_seconds':0,'points_um':[[0,0],[1,0]]},
                          {'t_seconds':1,'points_um':[[0,-flux/100],[1,-flux/100]]}]}


class SplitAndSamplingTests(unittest.TestCase):
    def test_arc_length_sampling_preserves_undercut_order(self):
        pts = [[0,0],[2,0],[1,-1]]
        result = resample_profile(pts, 20)
        self.assertEqual(result[0], pts[0])
        self.assertEqual(result[-1], pts[-1])
        self.assertGreater(max(p[0] for p in result), result[-1][0])

    def test_recipe_overlap_with_different_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'recipe overlap'):
            validate_splits({'train':[run('a',1)],'val':[run('b',1)],'test':[run('c',3)]})

    def test_time_mismatch_rejected(self):
        r = run('b',2); r['snapshots'][-1]['t_seconds'] = 2
        with self.assertRaisesRegex(ValueError, 'time'):
            validate_splits({'train':[run('a',1)],'val':[r],'test':[run('c',3)]})

    def test_empty_split_rejected(self):
        with self.assertRaises(ValueError):
            validate_splits({'train':[],'val':[run('b',2)],'test':[run('c',3)]})

    def test_invalid_point_count_rejected(self):
        with self.assertRaises(ValueError): resample_profile([[0,0],[1,0]], 1)


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'optional numpy training dependency')
class RidgeTests(unittest.TestCase):
    def test_fit_predict_serialization(self):
        model = RidgeProfileModel.fit([run('a',1),run('b',2),run('c',3)], alpha=1e-8, n_points=8)
        restored = RidgeProfileModel.from_dict(model.to_dict())
        recipe = run('x',2.5)['recipe']
        self.assertEqual(model.predict(recipe), restored.predict(recipe))
        self.assertAlmostEqual(restored.predict(recipe)[0][1], -.025, places=5)

    def test_scaler_comes_from_training_only(self):
        model = RidgeProfileModel.fit([run('a',1),run('b',3)], alpha=.01, n_points=8)
        self.assertEqual(model.to_dict()['mean'][0], 2.)
        self.assertEqual(model.to_dict()['train_ids'], ['a','b'])

    def test_invalid_alpha_rejected(self):
        for alpha in (-1,float('nan'),True):
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                RidgeProfileModel.fit([run('a',1)],alpha=alpha)

    def test_empty_training_rejected(self):
        with self.assertRaises(ValueError): RidgeProfileModel.fit([],alpha=.01)

    def test_malformed_saved_model_rejected(self):
        source = RidgeProfileModel.fit([run('a',1),run('b',2)], alpha=.01, n_points=8).to_dict()
        for change in (lambda d: d['std'].__setitem__(0,0),
                       lambda d: d['weights'].pop(),
                       lambda d: d.update(n_points=1)):
            doc = copy.deepcopy(source); change(doc)
            with self.assertRaises(ValueError): RidgeProfileModel.from_dict(doc)
