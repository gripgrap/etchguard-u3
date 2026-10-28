import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from etchguard.contracts import RECIPE_KEYS
from etchguard.integrity import freeze
from etchguard.predictions import evaluate_prediction_bundle


class PredictionBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reference = {'run_id': 'sim-1', 'recipe': {k: 1 for k in RECIPE_KEYS},
            'provenance': {'source_type': 'external_research', 'version': 'test',
                           'content_fingerprint': 'a'*64, 'time_basis': 'explicit_process_durations'},
            'snapshots': [{'t_seconds': 0, 'points_um': [[0,0],[1,0]]},
                          {'t_seconds': 1, 'points_um': [[0,-.1],[1,-.1]]}]}
        self.prediction = copy.deepcopy(self.reference)
        self.prediction['model'] = {'id': 'oracle-check', 'kind': 'oracle',
                                    'artifact_sha256': 'b'*64}
        self.policy = {'max_chamfer_um': .02, 'max_depth_mae_um': .02,
                       'max_chamfer_per_snapshot_um': .03}

    def evaluate(self):
        for name, doc in [('reference',self.reference), ('prediction',self.prediction), ('policy',self.policy)]:
            (self.root/f'{name}.json').write_text(json.dumps(doc))
        fp = freeze(self.root)['content_fingerprint']
        return evaluate_prediction_bundle(self.root, fp)

    def test_oracle_pass_is_not_promotable(self):
        r = self.evaluate()
        self.assertEqual(r['exit_code'], 0)
        self.assertFalse(r['promotion_authorized'])
        self.assertEqual(r['metrics']['chamfer_mean_um'], 0)
        self.assertEqual(r['scope'], 'prediction_file_evaluation_only')

    def test_shifted_prediction_block(self):
        for snap in self.prediction['snapshots']:
            snap['points_um'] = [[x,y-.2] for x,y in snap['points_um']]
        self.assertEqual(self.evaluate()['exit_code'], 1)

    def test_time_mismatch_block(self):
        self.prediction['snapshots'][1]['t_seconds'] = 1.1
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_recipe_mismatch_block(self):
        self.prediction['recipe']['ion_flux'] = 2
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_source_fingerprint_mismatch_block(self):
        self.prediction['provenance']['content_fingerprint'] = 'c'*64
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_time_basis_mismatch_block(self):
        self.prediction['provenance']['time_basis'] = 'assumed_uniform_time'
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_missing_snapshot_block(self):
        self.prediction['snapshots'].pop()
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_invalid_shape_block(self):
        self.prediction['snapshots'][1]['points_um'][0][0] = float('nan')
        self.assertEqual(self.evaluate()['exit_code'], 1)

    def test_invalid_threshold_block(self):
        self.policy['max_chamfer_um'] = float('inf')
        self.assertEqual(self.evaluate()['exit_code'], 2)

    def test_single_bad_snapshot_cannot_hide_in_mean(self):
        self.prediction['snapshots'][1]['points_um'] = [[0,-.14],[1,-.14]]
        self.policy['max_chamfer_um'] = .1
        self.policy['max_depth_mae_um'] = .1
        r = self.evaluate()
        self.assertEqual(r['exit_code'], 1)
        self.assertIn('per-snapshot Chamfer exceeds policy', r['reasons'])

    def test_tampering_after_freeze_block(self):
        self.evaluate()
        from etchguard.integrity import verify
        fp = verify(self.root)['content_fingerprint']
        (self.root/'prediction.json').write_text('{}')
        self.assertEqual(evaluate_prediction_bundle(self.root, fp)['exit_code'], 2)

    def test_extra_model_fields_do_not_corrupt_evidence(self):
        self.prediction['model']['unused_value'] = float('nan')
        result = self.evaluate()
        self.assertEqual(result['exit_code'], 0)
        self.assertNotIn('unused_value', result['model'])

    def test_metric_overflow_is_blocked(self):
        self.prediction['snapshots'][1]['points_um'] = [[1e308,1e308],[-1e308,-1e308]]
        self.assertEqual(self.evaluate()['exit_code'], 1)

    def test_final_only_evaluation_excludes_initial_input(self):
        self.policy['evaluation_times_seconds'] = [1]
        result = self.evaluate()
        self.assertEqual(result['metrics']['n'], 1)
        self.assertEqual(result['evaluated_times_seconds'], [1])

    def test_requested_evaluation_time_must_exist(self):
        self.policy['evaluation_times_seconds'] = [2]
        self.assertEqual(self.evaluate()['exit_code'], 2)
